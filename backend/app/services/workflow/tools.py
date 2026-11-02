"""按运行创建 DeepAgents 工具和中间件，隔离项目目录与事件回调。"""

import asyncio
import hashlib
import json
import shlex
from collections.abc import Callable
from pathlib import Path

from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, tool

from app.services.workflow.codex_model import stop_process
from app.services.workflow.validation import ASSET_SUFFIXES, read_frozen_knowledge, successful_file_result
from app.services.workflow.workspace import checked_child, normalize_reference, snapshot, source_fingerprint


def create_tool_guard(workspace: Path, emit: Callable[[str, str, dict], None]):
    """每次运行使用同一个文件锁，串行执行文件读写及依赖完整文件的验证。

    DeepAgents 会并发执行同一模型回复中的工具调用。FilesystemBackend 的 edit
    是读、替换、写三个步骤，必须把整个工具调用放在锁内，读取和哈希记录也不能
    越过下一次写入。不同参考资料读取仍可并行。
    """
    file_io_lock = asyncio.Lock()
    file_io_tools = {"read_file", "write_file", "edit_file", "ls", "glob", "grep", "inspect_assets", "run_validation"}

    async def call_and_record(request, handler):
        result = await handler(request)
        if successful_file_result(request.tool_call, getattr(result, "status", None), getattr(result, "content", None)):
            name = request.tool_call["args"]["file_path"].lstrip("/")
            path = checked_child(workspace, name)
            if path.is_file():
                emit("file_written", "DeepAgents 工具已实际写入项目文件", {"path": name, "tool": request.tool_call["name"], "call_id": request.tool_call["id"],
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        return result

    @wrap_tool_call
    async def recover_tool_errors(request, handler):
        """按官方中间件模式串行文件操作，并把可纠正错误交回模型。"""
        try:
            if request.tool_call["name"] in file_io_tools:
                async with file_io_lock:
                    return await call_and_record(request, handler)
            return await call_and_record(request, handler)
        except Exception as error:
            emit("tool_error", "工具调用失败，已返回模型修正参数", {"tool": request.tool_call["name"], "error": str(error)})
            return ToolMessage(content=f"工具调用错误：{error}。请检查路径、参数或允许的命令后修正重试，不得声称本次操作成功。",
                               tool_call_id=request.tool_call["id"], status="error")

    return recover_tool_errors


def create_workflow_tools(
    *,
    root: Path,
    knowledge_dir: Path,
    workspace: Path,
    run: dict,
    emit: Callable[[str, str, dict], None],
    load_run: Callable[[], dict],
) -> list[BaseTool]:
    """显式绑定当前运行依赖，保留知识快照并实时读取验证所属的尝试次数。"""
    run_id = run["id"]

    @tool
    def read_reference(path: str, offset: int = 0, limit: int = 24000) -> str:
        """只读工程 ref/ 内的证据文件或列出参考资料目录，path 相对 ref/。"""
        path = normalize_reference(root, path)
        target = checked_child(root / "ref", path)
        emit("reference_read", "读取参考工程证据", {"path": path, "offset": offset})
        if target.is_dir():
            return "\n".join(child.relative_to(root / "ref").as_posix() + ("/" if child.is_dir() else "") for child in sorted(target.iterdir())[:200])
        return target.read_text(encoding="utf-8", errors="replace")[max(0, offset):max(0, offset) + min(max(limit, 1), 60000)]

    @tool
    def read_skill(path: str) -> str:
        """读取归档 Skill 入口并记录内容哈希；兼容读取同包配套文本，入口 path 使用技能列表中的路径。"""
        target = checked_child(knowledge_dir / "skill" / "docs", path)
        if target.name != "SKILL.md":
            return read_skill_resource.invoke({"path": path})
        if not target.is_file():
            raise ValueError("所选 Skill 入口不存在，请先检查技能列表")
        content = target.read_text(encoding="utf-8")
        emit("skill_read", "读取归档技能规范", {"path": path, "sha256": hashlib.sha256(content.encode()).hexdigest(), "content": content})
        return content

    @tool
    def read_skill_resource(path: str, offset: int = 0, limit: int = 24000) -> str:
        """读取已归档技能包的 references/scripts 等文本或列出目录；path 相对技能知识库，读取记录包含实际哈希。"""
        base = knowledge_dir / "skill" / "docs"
        parts = Path(path).parts
        if not parts or any(part.startswith(".") for part in parts) or not (base / parts[0] / "SKILL.md").is_file():
            raise ValueError("只能读取已归档技能包内的公开资料")
        target = checked_child(base, path)
        if target.is_dir():
            listing = "\n".join(child.relative_to(base).as_posix() + ("/" if child.is_dir() else "") for child in sorted(target.iterdir())[:200] if not child.name.startswith("."))
            emit("skill_resource_read", "查看技能包资料目录", {"path": path, "listing": listing})
            return listing
        if target.stat().st_size > 2_000_000:
            raise ValueError("技能文本资料超过 2MB，请选择更小的资料文件")
        content = target.read_bytes()
        if b"\x00" in content:
            raise ValueError("技能资料是二进制文件，不能作为文本读取")
        emit("skill_resource_read", "读取已归档技能配套资料", {"path": path, "sha256": hashlib.sha256(content).hexdigest(), "offset": offset})
        return content.decode("utf-8", errors="replace")[max(0, offset):max(0, offset) + min(max(limit, 1), 60000)]

    @tool
    def read_game_knowledge(path: str, offset: int = 0, limit: int = 24000) -> str:
        """读取本次运行已冻结的品类或技术框架资料；仅允许资料索引中的路径，记录正文哈希和读取范围。"""
        content, evidence = read_frozen_knowledge(run, path, offset, limit)
        emit("knowledge_read", "读取本次运行冻结的品类与技术资料", evidence)
        return content

    @tool
    def inspect_assets(paths: list[str] | None = None) -> str:
        """清点真实图像、音频、字体、模型、动画和配置。程序化视觉可传设计或生成文件 paths，返回路径、字节数、SHA256。"""
        suffixes = ASSET_SUFFIXES | {".json"}
        candidates = [checked_child(workspace, path) for path in paths] if paths is not None else workspace.rglob("*")
        inventory = [{"path": path.relative_to(workspace).as_posix(), "size": path.stat().st_size,
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                     for path in candidates if path.is_file() and not path.is_symlink()
                     and (paths is not None or path.suffix.lower() in suffixes)
                     and not {"node_modules", ".git", "dist", "build"}.intersection(path.relative_to(workspace).parts)]
        emit("assets_inspected", "已核验当前项目实际资源文件", {"count": len(inventory), "assets": inventory})
        return json.dumps(inventory, ensure_ascii=False)

    @tool
    def save_skill(path: str, content: str, reason: str) -> str:
        """创建或修订工程 skills/ 的 SKILL.md，并显式发布同路径知识库副本；保留源/库前后版本、理由及校验记录。"""
        import yaml
        if not content.startswith("---") or len(content.split("---", 2)) != 3:
            raise ValueError("Skill 必须包含 YAML 元数据区")
        metadata = yaml.safe_load(content.split("---", 2)[1])
        if not isinstance(metadata, dict) or not metadata.get("name") or not metadata.get("description") or len(content.split("---", 2)[2].strip()) < 40:
            raise ValueError("Skill 必须有 name、description 和足够清晰的规范正文")
        source = checked_child(root / "skills", path)
        target = checked_child(knowledge_dir / "skill" / "docs", path)
        if target.name != "SKILL.md" or len(Path(path).parts) < 2:
            raise ValueError("Skill 路径必须为技能目录/SKILL.md")
        previous_source = source.read_text(encoding="utf-8") if source.exists() else None
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(content, encoding="utf-8")
        from app.services.skill_library import sync_skill_revision
        revision = sync_skill_revision(path, reason, run_id, project_root=root)
        revision["previous_source"] = previous_source
        emit("skill_updated", "工程技能修订已显式发布到知识库并归档", revision)
        return "工程 Skill 源与知识库副本已同步，前后版本和验证证据已关联本次运行"

    @tool
    async def run_validation(command: str, timeout_seconds: int = 180) -> str:
        """在当前游戏工作区运行真实验证。仅允许 npm run build/test/check、npm test、node --test、node scripts/ 下脚本；禁止 shell 拼接。"""
        args = shlex.split(command)
        allowed = (args[:2] == ["npm", "test"] and len(args) == 2) or (args[:2] == ["npm", "run"] and len(args) == 3 and args[2] in {"build", "test", "check"})
        allowed = allowed or (len(args) >= 2 and args[0] == "node" and (args[1] == "--test" or args[1].startswith("scripts/")))
        if not allowed or any(any(char in arg for char in [";", "|", "&", "`", "\n", "$", ">", "<"]) or ".." in Path(arg).parts for arg in args):
            raise ValueError("验证命令不在当前项目允许列表内")
        emit("validation_started", "开始执行真实项目验证", {"command": command})
        before_validation = snapshot(workspace)
        source_before = source_fingerprint(workspace)
        process = await asyncio.create_subprocess_exec(*args, cwd=workspace, stdout=asyncio.subprocess.PIPE,
                                                      stderr=asyncio.subprocess.STDOUT, start_new_session=True)
        try:
            output, _ = await asyncio.wait_for(process.communicate(), min(max(timeout_seconds, 1), 300))
        finally:
            await stop_process(process)
        after_validation = snapshot(workspace)
        result = {"command": command, "exit_code": process.returncode, "output": output.decode(errors="replace")[-40000:],
                  "attempt": load_run().get("attempt", 1), "source_before": source_before,
                  "source_after": source_fingerprint(workspace),
                  "changed_paths": [name for name, digest in after_validation.items() if before_validation.get(name) != digest]}
        emit("validation_completed", "真实验证完成" if process.returncode == 0 else "真实验证失败", result)
        return json.dumps(result, ensure_ascii=False)

    return [read_reference, read_skill, read_skill_resource, read_game_knowledge, inspect_assets, save_skill, run_validation]
