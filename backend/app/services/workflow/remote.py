"""面向远程调用的授权检查和有限结果视图，不依赖 MCP 协议或 HTTP 路由。"""

from pathlib import Path
from typing import Collection

from app.services.workflow import engine


def require_project(project_id: str, allowed_projects: Collection[str]) -> dict:
    """每次操作重新检查项目权限，不能凭已知 run_id 绕过白名单。"""
    if "*" not in allowed_projects and project_id not in allowed_projects:
        raise PermissionError("无权访问该项目")
    return engine.load("projects", project_id)


def require_run(run_id: str, allowed_projects: Collection[str]) -> dict:
    """从持久运行记录解析所属项目，调用方不能自行声明归属。"""
    run = engine.load("runs", run_id)
    require_project(run["project_id"], allowed_projects)
    return run


def project_view(project: dict) -> dict:
    """只返回协调工作需要的字段，不展开冻结资料、服务端路径和内部提交元数据。"""
    return {key: project.get(key) for key in (
        "id", "name", "created_at", "genre_id", "framework_id", "stages",
    )}


def run_view(run: dict) -> dict:
    """状态与正文分开获取；等待确认不等于已通过验收，恢复也不会替代确认。"""
    result = {key: run.get(key) for key in (
        "id", "project_id", "stage", "status", "progress", "attempt", "created_at", "updated_at",
    )}
    result.update(
        summary=str(run.get("summary") or "")[:4000],
        error=str(run["error"])[:2000] if run.get("error") else None,
        event_cursor=run["events"][-1]["seq"] if run["events"] else 0,
        artifact_count=len(run["artifacts"]),
        requires_confirmation=run["status"] == "awaiting_confirmation",
        poll_after_seconds=3 if run["status"] in engine.ACTIVE else None,
    )
    return result


def event_page(run: dict, after: int, limit: int) -> dict:
    """按持久序号分页；保留精简消息，避免把模型上下文和整份工具正文重复传输。"""
    remaining = [item for item in run["events"] if item["seq"] > after]
    selected = remaining[:limit]
    events = [{"seq": item["seq"], "time": item["time"], "type": item["type"],
               "message": str(item["message"])[:1000]} for item in selected]
    return {"run_id": run["id"], "status": run["status"], "events": events,
            "next_cursor": selected[-1]["seq"] if selected else after, "has_more": len(remaining) > limit}


def artifact_view(run_id: str, artifact: dict, public_url: str) -> dict:
    """文件通过专用认证入口交付；不返回无鉴权的旧 REST 链接或服务端绝对路径。"""
    result = {key: artifact.get(key) for key in ("id", "name", "path", "kind", "size", "sha256", "provenance")}
    result["download_url"] = f"{public_url.rstrip('/')}/artifacts/{run_id}/{artifact['id']}"
    result["authentication"] = "下载时携带与 MCP 相同的 Authorization: Bearer 令牌"
    return result


def artifact_file(run_id: str, artifact_id: str, allowed_projects: Collection[str]) -> tuple[dict, Path]:
    """授权后复用引擎的路径与快照哈希检查，读取和下载共用同一入口。"""
    run = require_run(run_id, allowed_projects)
    path = engine.artifact_file(run_id, artifact_id)
    artifact = next(item for item in run["artifacts"] if item["id"] == artifact_id)
    return artifact, path


def text_page(path: Path, offset: int, limit: int) -> dict:
    """按字符分页读取 UTF-8 文本；分块跳过前缀，避免整份大文件进入内存。"""
    with path.open(encoding="utf-8", errors="replace") as source:
        remaining = offset
        while remaining:
            skipped = source.read(min(remaining, 8192))
            if not skipped:
                break
            remaining -= len(skipped)
        content = source.read(limit + 1)
    return {"text": content[:limit], "offset": offset, "next_offset": offset + len(content[:limit]),
            "has_more": len(content) > limit}
