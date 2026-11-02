"""阶段验收规则：资源清单、冻结资料读取、验证指纹与真实写入证据。"""

import hashlib
import re
from pathlib import Path

from app.services.workflow.workspace import checked_child, source_fingerprint

# 清点与验收共用同一资源类型表，避免 JPEG 等文件可清点却无法交接。
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".avif", ".bmp", ".tga",
                  ".wav", ".mp3", ".ogg", ".m4a", ".aac", ".flac", ".ttf", ".otf", ".woff", ".woff2",
                  ".glb", ".gltf", ".fbx", ".obj", ".atlas", ".skel", ".spine"}
PROCEDURAL_SUFFIXES = {".md", ".json", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".py", ".glsl", ".wgsl", ".svg"}


def required_validations(run: dict) -> list[str]:
    """门禁只采用本次运行冻结的命令，历史运行继续使用原来的两项验证。"""
    profile = run.get("production_profile")
    return profile["framework"]["required_validations"] if profile else ["npm run build", "npm test"]


def verify_validation_evidence(run: dict, workspace: Path) -> None:
    """结束及确认都核验当前尝试的命令、指纹和最终工作区，防止测试后再改代码。"""
    final_fingerprint = source_fingerprint(workspace)
    validations = {item["data"].get("command"): item["data"] for item in run["events"]
                   if item["type"] == "validation_completed" and item["data"].get("attempt") == run.get("attempt", 1)}
    for command in required_validations(run):
        evidence = validations.get(command, {})
        if evidence.get("exit_code") != 0:
            raise ValueError("当前恢复尝试必须重新完成真实构建和测试，不能沿用旧成功记录")
        if evidence.get("source_before") != final_fingerprint or evidence.get("source_after") != final_fingerprint:
            raise ValueError("构建或测试后源码/资源已变更，必须对最终文件重新验证")


def verify_knowledge_reads(run: dict) -> None:
    """按冻结正文合并实际读取区间，分页和恢复可累计，不能只读首字符通过。"""
    for document in run.get("knowledge_snapshot", []):
        content = document["content"]
        length = len(content)
        if not length or hashlib.sha256(content.encode("utf-8")).hexdigest() != document["sha256"]:
            raise ValueError("模型未实际读取有效的完整知识快照，阶段验证失败")
        intervals = []
        for item in run["events"]:
            evidence = item["data"]
            if (item["type"] != "knowledge_read" or evidence.get("path") != document["path"]
                    or evidence.get("sha256") != document["sha256"]):
                continue
            start, end = evidence.get("offset"), evidence.get("end")
            # 长度以可信正文为准，不采信事件自报的 total_chars；异常范围不计入证据。
            if type(start) is int and type(end) is int and 0 <= start < end <= length:
                intervals.append((start, end))
        covered = 0
        for start, end in sorted(intervals):
            if start > covered:
                break
            covered = max(covered, end)
        if covered != length:
            raise ValueError(f"模型未实际读取完整的品类与技术资料：{document['path']}，阶段验证失败")


def read_frozen_knowledge(run: dict, path: str, offset: int = 0, limit: int = 24000) -> tuple[str, dict]:
    """按需返回运行内的资料正文与读取范围，绝不回退读取最新知识库文件。"""
    document = next((item for item in run.get("knowledge_snapshot", []) if item["path"] == path), None)
    if document is None:
        raise ValueError("资料不在本次运行选定的知识快照中")
    content = document["content"]
    if hashlib.sha256(content.encode("utf-8")).hexdigest() != document["sha256"]:
        raise ValueError("运行知识快照哈希不匹配")
    start = min(max(0, offset), len(content))
    end = min(start + min(max(limit, 1), 60000), len(content))
    return content[start:end], {"path": path, "sha256": document["sha256"], "offset": start, "end": end,
                               "total_chars": len(content)}


def verify_art_manifest(workspace: Path, manifest: dict) -> None:
    """资源型和程序化视觉都必须交接非空的真实文件、哈希、用途与来源。"""
    assets = manifest.get("assets", [])
    procedural = manifest.get("mode") == "procedural"
    if not isinstance(assets, list) or not assets:
        raise ValueError("美术清单必须包含真实资源，程序化视觉也不能使用空清单")
    allowed = PROCEDURAL_SUFFIXES if procedural else ASSET_SUFFIXES
    if not any(isinstance(item, dict) and Path(item.get("path", "")).suffix.lower() in allowed for item in assets):
        raise ValueError("程序化视觉须提供设计或生成文件" if procedural else "美术清单须引用真实图像、音频、字体、模型或动画资源")
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("path"), str):
            raise ValueError("美术清单资源路径格式错误")
        path = checked_child(workspace, asset["path"])
        if (not path.is_file() or path.stat().st_size == 0 or hashlib.sha256(path.read_bytes()).hexdigest() != asset.get("sha256")
                or not isinstance(asset.get("usage"), str) or not asset["usage"].strip()
                or not isinstance(asset.get("source"), str) or not asset["source"].strip()):
            raise ValueError("美术清单文件、哈希或用途来源校验失败")


def successful_file_result(call: dict, status: str | None, content) -> bool:
    """同时核对状态和官方成功语义，不能把默认 success 的错误正文算作写入。"""
    if status != "success" or not isinstance(content, str):
        return False
    if call["name"] == "write_file" and content.startswith("Updated file "):
        reported_path = content[len("Updated file "):]
    elif call["name"] == "edit_file":
        matched = re.fullmatch(r"Successfully replaced ([1-9]\d*) instance\(s\) of the string in '(.+)'", content)
        if not matched:
            return False
        reported_path = matched.group(2)
    else:
        return False
    requested_path = call.get("args", {}).get("file_path")
    return isinstance(requested_path, str) and Path(reported_path).as_posix().lstrip("/") == Path(requested_path).as_posix().lstrip("/")


def written_file_evidence(run: dict) -> dict[str, str | None]:
    """只认真实工具成功结果；结构化模型请求本身不算写入成功证明。"""
    requests = {}
    attestations = {}
    written = {}
    for item in run["events"]:
        if item["type"] == "model_completed":
            for call in item["data"].get("tool_calls", []):
                if call["name"] in {"write_file", "edit_file"}:
                    requests[call["id"]] = call
        if item["type"] == "file_written":
            attestations[item["data"].get("call_id")] = item["data"]
        if item["type"] != "graph_update":
            continue
        message = item["data"].get("message", {})
        if not isinstance(message, dict) or message.get("type") != "tool":
            continue
        call_id = message.get("tool_call_id")
        call = requests.get(call_id)
        if not call or not successful_file_result(call, message.get("status"), message.get("content")):
            continue
        path = str(call["args"].get("file_path", "")).lstrip("/")
        if call_id in attestations:
            written[path] = attestations[call_id]["sha256"]
        elif call["name"] == "write_file" and isinstance(call["args"].get("content"), str):
            written[path] = hashlib.sha256(call["args"]["content"].encode()).hexdigest()
        else:
            # 老版 edit_file 有成功事件但未保存落盘哈希，不能据此认定最终内容作者。
            written[path] = None
    return written

