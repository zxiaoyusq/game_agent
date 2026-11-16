"""冻结运行所用技能文本，并通过独立只读入口校验和读取。

快照放在工作流输入目录，不混入游戏工作区，也不会执行 Skill 内的脚本。
入口固定到本次选择；同包支持文本一并保存，供后续按需读取。
"""

import hashlib
import os
import shutil
from pathlib import Path

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
EXCLUDED_DIRS = {"__pycache__", "node_modules"}
NON_TEXT_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".svg", ".ico", ".tga",
    ".zip", ".gz", ".bz2", ".xz", ".7z", ".rar", ".pdf", ".woff", ".woff2", ".ttf",
    ".mp3", ".wav", ".ogg", ".mp4", ".mov", ".glb", ".fbx", ".skel", ".exe", ".dll",
}


def _relative_path(value: str) -> Path:
    """拒绝绝对路径、隐式归一化和隐藏文件，路径统一使用正斜杠。"""
    if (not isinstance(value, str) or not value or "\\" in value
            or any(ord(char) < 32 for char in value)
            or any(not part or part.startswith(".") or ":" in part for part in value.split("/"))):
        raise ValueError("技能路径必须是公开的普通相对路径")
    path = Path(value)
    if path.is_absolute():
        raise ValueError("技能路径不能是绝对路径")
    return path


def _no_links(path: Path) -> Path:
    """校验目标及全部祖先，先检查原始路径再解析，防止根目录本身绕过检查。"""
    path = path.absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("技能输入及其父目录不能使用符号链接")
    return path


def _child(base: Path, relative: str) -> Path:
    """所有源文件和快照文件均保持在各自显式根目录内。"""
    path = _no_links(base / _relative_path(relative))
    if not path.resolve().is_relative_to(base.resolve()):
        raise ValueError("技能路径超出输入目录")
    return path


def _text_bytes(path: Path, *, required: bool = False) -> tuple[bytes, str] | None:
    """普通配套资料跳过二进制和大文件；必读入口有问题时拒绝整个运行输入。"""
    if not path.is_file():
        if required:
            raise ValueError("选中的 Skill 入口已不存在")
        return None
    if path.stat().st_size > MAX_FILE_BYTES:
        if required:
            raise ValueError("选中的 Skill 入口超过 2 MB")
        return None
    if not required and path.suffix.lower() in NON_TEXT_SUFFIXES:
        return None
    content = path.read_bytes()
    try:
        if len(content) > MAX_FILE_BYTES or b"\x00" in content:
            raise ValueError("文件不是可冻结的小型文本")
        text = content.decode("utf-8")
    except ValueError as error:
        if required:
            raise ValueError("选中的 Skill 入口必须是 2 MB 以内的 UTF-8 文本") from error
        return None
    if required and not text.strip():
        raise ValueError("选中的 Skill 入口正文为空")
    return content, text


def freeze_skill_inputs(selected_paths: list[str], available_skills: list[dict],
                        knowledge_dir: Path, destination: Path) -> dict:
    """按包去重冻结文本，入口同时核对发现时的哈希；失败只清理本轮新目录。"""
    source_root = _no_links(knowledge_dir / "skill" / "docs")
    destination = _no_links(destination)
    if destination.exists():
        raise ValueError("技能输入快照目录已存在，不能覆盖历史运行")
    if destination.resolve().is_relative_to(source_root.resolve()) or source_root.resolve().is_relative_to(destination.resolve()):
        raise ValueError("技能输入快照目录不能与知识库来源重叠")
    selected = list(dict.fromkeys(selected_paths))
    available = {item["path"]: item for item in available_skills}
    contents = {}
    snapshots = []
    for relative in selected:
        path = _relative_path(relative)
        if len(path.parts) < 2 or path.name != "SKILL.md" or relative not in available:
            raise ValueError("选中的 Skill 不在当前技能目录中")
        source = _child(source_root, relative)
        content, text = _text_bytes(source, required=True)
        digest = hashlib.sha256(content).hexdigest()
        metadata = available[relative]
        if digest != metadata.get("sha256"):
            raise ValueError("Skill 来源在选择后已变化，请重新检查技能选择")
        contents[relative] = (content, text)
        snapshots.append({"path": relative, "name": str(metadata.get("name") or path.parent.name),
                          "description": str(metadata.get("description") or ""),
                          "version": str(metadata.get("version") or ""), "sha256": digest,
                          "size": len(content), "total_chars": len(text)})

    # 先保存入口字节；遍历包时复用缓存，不因同包多个子技能重复读取入口。
    total = sum(len(content) for content, _ in contents.values())
    if total > MAX_TOTAL_BYTES:
        raise ValueError("本次技能文本超过 16 MB，请减少选中的技能包")
    resources = []
    created = False
    try:
        destination.mkdir(parents=True)
        created = True
        packages = sorted({Path(relative).parts[0] for relative in selected})
        for package in packages:
            package_root = _child(source_root, package)
            if not package_root.is_dir():
                raise ValueError("选中 Skill 的来源包已不存在")
            for directory, directories, files in os.walk(package_root, followlinks=False):
                directories[:] = sorted(name for name in directories if not name.startswith(".")
                                        and name not in EXCLUDED_DIRS and not (Path(directory) / name).is_symlink())
                for filename in sorted(files):
                    source = Path(directory) / filename
                    if filename.startswith(".") or source.is_symlink():
                        continue
                    relative = source.relative_to(source_root).as_posix()
                    source = _child(source_root, relative)
                    data = contents.get(relative)
                    if data is None:
                        data = _text_bytes(source)
                        if data is None:
                            continue
                        total += len(data[0])
                        if total > MAX_TOTAL_BYTES:
                            raise ValueError("本次技能文本超过 16 MB，请减少选中的技能包")
                    content, text = data
                    target = _child(destination, relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                    resources.append({"path": relative, "sha256": hashlib.sha256(content).hexdigest(),
                                      "size": len(content), "total_chars": len(text)})
        # 来源入口在目录遍历期间被删掉，也不能交付缺少必读输入的半份快照。
        if set(selected) - {item["path"] for item in resources}:
            raise ValueError("技能来源在冻结期间发生变化，请重新检查技能选择")
        return {"skill_snapshot": snapshots, "skill_resources": resources}
    except Exception:
        if created:
            shutil.rmtree(destination)
        raise


def read_frozen_skill(run: dict, path: str, input_dir: Path, *, entry: bool = False,
                      offset: int = 0, limit: int = 24000) -> tuple[str, dict]:
    """只读取本次归档文本，校验哈希后返回真实范围；禁止借配套入口绕过选择。"""
    relative = _relative_path(path).as_posix()
    input_dir = _no_links(input_dir)
    if not input_dir.is_dir():
        raise ValueError("运行技能快照目录缺失")
    target = _child(input_dir, relative)
    entries = {item["path"]: item for item in run.get("skill_snapshot", [])}
    resources = {item["path"]: item for item in run.get("skill_resources", [])}
    if (entry or Path(relative).name == "SKILL.md") and relative not in entries:
        raise ValueError("该 Skill 入口未被本次运行选中")
    if entry:
        metadata = entries[relative]
    else:
        metadata = resources.get(relative)
    if metadata is None:
        prefix = relative + "/"
        names = set()
        for candidate in resources:
            if candidate.endswith("/SKILL.md") and candidate not in entries:
                continue
            if candidate.startswith(prefix):
                remainder = candidate[len(prefix):]
                name = remainder.split("/", 1)[0]
                names.add(prefix + name + ("/" if "/" in remainder else ""))
        if not names:
            raise ValueError("资料不在本次运行冻结的技能文本中")
        content = "文本快照目录（图片、压缩包与大型资料未纳入）：\n" + "\n".join(sorted(names))
        return content, {"path": relative, "kind": "directory", "frozen": True,
                         "sha256": hashlib.sha256(content.encode()).hexdigest(),
                         "offset": 0, "end": len(content), "total_chars": len(content)}
    if not target.is_file():
        raise ValueError("运行技能快照文件缺失")
    if target.stat().st_size != metadata["size"]:
        raise ValueError("运行技能快照哈希不匹配")
    raw = target.read_bytes()
    if len(raw) != metadata["size"] or hashlib.sha256(raw).hexdigest() != metadata["sha256"]:
        raise ValueError("运行技能快照哈希不匹配")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("运行技能快照不是 UTF-8 文本") from error
    start = 0 if entry else min(max(0, offset), len(content))
    end = len(content) if entry else min(start + min(max(limit, 1), 60000), len(content))
    evidence = {"path": relative, "sha256": metadata["sha256"], "frozen": True,
                "offset": start, "end": end, "total_chars": len(content)}
    if relative in entries:
        evidence["version"] = entries[relative].get("version", "")
    return content[start:end], evidence
