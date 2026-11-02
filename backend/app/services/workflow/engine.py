"""四阶段项目状态、任务调度、DeepAgents 编排和产物归档。

项目与事件使用小型 JSON 文件原子落盘，LangGraph 检查点使用 SQLite。
只允许 games/ 中明确指定的项目工作区，参考资料与 Skill 通过单独只读工具访问。
"""

import asyncio
import hashlib
import json
import mimetypes
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.profiles import HarnessProfile, GeneralPurposeSubagentProfile, register_harness_profile
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.config import DATA_DIR, KNOWLEDGE_DIR
from app.services.workflow import workspace as workspace_files
from app.services.workflow.codex_model import CodexChatModel, inspect_runtime
from app.services.workflow.prompts import build_run_prompts
from app.services.workflow.submissions import describe_submission, find_submission
from app.services.workflow.tools import create_tool_guard, create_workflow_tools
# 兼容原有路由及调用方；校验与文件实现已迁移到独立模块。
from app.services.workflow.validation import (
    ASSET_SUFFIXES, PROCEDURAL_SUFFIXES, read_frozen_knowledge, required_validations,
    successful_file_result, verify_art_manifest, verify_knowledge_reads,
    verify_validation_evidence, written_file_evidence,
)
from app.services.workflow.workspace import checked_child, snapshot, source_fingerprint

ROOT = Path(__file__).resolve().parents[4]
STORE = DATA_DIR / "workflow"
STAGES = [("prototype", "原型定义"), ("art", "美术资源"), ("code", "代码与集成"), ("test", "测试验收")]
ACTIVE = {"queued", "running"}
LOCK = threading.RLock()
WORKERS: dict[str, asyncio.Task] = {}
# 本工程的阶段流由主图直接执行，不启用隐式子 Agent，便于记录每一步证据。
register_harness_profile("codexchatmodel", HarnessProfile(general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False)))


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(kind: str, identifier: str) -> dict:
    """所有标识先检查格式，避免文件 API 通过路径穿越读取任意状态。"""
    if not identifier or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for char in identifier):
        raise ValueError("无效的记录标识")
    path = STORE / kind / f"{identifier}.json"
    if not path.is_file():
        raise FileNotFoundError("记录不存在")
    return json.loads(path.read_text(encoding="utf-8"))


def save(kind: str, value: dict) -> None:
    """同一进程内串行写入并原子替换，接口永远不会读到半份 JSON。"""
    with LOCK:
        path = STORE / kind / f"{value['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)


def event(run_id: str, kind: str, message: str, data: dict | None = None) -> None:
    """模型、工具、验证、状态变更全部写入带序号的持久事件。"""
    with LOCK:
        run = load("runs", run_id)
        run["events"].append({"seq": len(run["events"]) + 1, "time": now(), "type": kind, "message": message, "data": data or {}})
        run["updated_at"] = now()
        save("runs", run)


def resolve_workspace(relative: str) -> Path:
    """保留现有入口，显式传递项目根目录给路径校验模块。"""
    return workspace_files.resolve_workspace(ROOT, relative)


def list_projects() -> list[dict]:
    return sorted([get_project(path.stem) for path in (STORE / "projects").glob("*.json")], key=lambda project: project["created_at"], reverse=True)


def get_project(identifier: str) -> dict:
    project = load("projects", identifier)
    base, entry = preview_location(project)
    project["preview_url"] = f"/api/workflow/projects/{identifier}/preview/{entry}" if (base / entry).is_file() else None
    return project


def preview_location(project: dict) -> tuple[Path, str]:
    """新项目按冻结的框架入口定位 Web 构建；旧项目维持原有目录回退。"""
    workspace = resolve_workspace(project["workspace"])
    profile = project.get("production_profile")
    if profile:
        relative = profile["framework"]["preview_entry"]
        raw = Path(relative)
        if raw.is_absolute() or ".." in raw.parts or not raw.name:
            raise ValueError("框架预览入口必须是工作区内的相对文件路径")
        target = checked_child(workspace, relative)
        return target.parent, target.name
    base = workspace / "dist" if (workspace / "dist" / "index.html").is_file() else workspace
    return base, "index.html"


def normalize_reference(path: str) -> str:
    """保留参考路径入口，统一使用工作区模块的目录边界检查。"""
    return workspace_files.normalize_reference(ROOT, path)


def create_project(name: str, brief: str | dict, workspace: str | None, references: list[str],
                   genre_id: str | None = None, framework_id: str | None = None, knowledge_paths: list[str] | None = None,
                   *, request_id: str | None = None, request_scope: str = "rest") -> dict:
    """创建项目并按调用方去重；锁覆盖查重和落盘，重试不会产生第二个工作区。"""
    submission = describe_submission(request_id, request_scope, {
        "name": name, "brief": brief, "workspace": workspace, "references": references,
        "genre_id": genre_id, "framework_id": framework_id, "knowledge_paths": knowledge_paths or [],
    })
    with LOCK:
        previous = find_submission(STORE / "projects", submission)
        if previous:
            return get_project(previous["id"])
        return _create_project(name, brief, workspace, references, genre_id, framework_id, knowledge_paths, submission)


def _create_project(name: str, brief: str | dict, workspace: str | None, references: list[str],
                    genre_id: str | None, framework_id: str | None, knowledge_paths: list[str] | None,
                    submission: dict | None) -> dict:
    """在引擎锁内执行原有项目初始化；旧调用不附加品类和框架门禁。"""
    profile = None
    if genre_id is not None or framework_id is not None or knowledge_paths:
        from app.services.production_library import resolve_profile, snapshot_knowledge
        profile = resolve_profile(genre_id or "general", framework_id or "cocos-web")
        paths = list(dict.fromkeys([*profile.get("knowledge_paths", []), *(knowledge_paths or [])]))
        # 创建时先核验手选资料合法性，执行时再冻结届时正文，恢复不重新读取知识库。
        snapshot_knowledge(paths)
        profile["knowledge_paths"] = paths
        profile.pop("sha256", None)
        profile["sha256"] = hashlib.sha256(json.dumps(profile, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    identifier = uuid4().hex
    workspace = workspace or f"games/{identifier}"
    workspace_path = resolve_workspace(workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)
    workspace = workspace_path.relative_to(ROOT.resolve()).as_posix()
    project = {"id": identifier, "name": name, "brief": brief, "workspace": workspace,
               "references": list(dict.fromkeys(normalize_reference(path) for path in references)),
               "created_at": now(), "stages": [{"id": key, "label": label, "status": "pending", "run_id": None,
                                                    "confirmed_at": None} for key, label in STAGES]}
    if submission:
        project["submission"] = submission
    if profile is not None:
        project.update(genre_id=profile["genre"]["id"], framework_id=profile["framework"]["id"],
                       knowledge_paths=profile["knowledge_paths"], production_profile=profile)
        preview_location(project)
    save("projects", project)
    return get_project(project["id"])


def list_skills() -> list[dict]:
    """动态发现知识库中的 Skill 元数据；新增包通过既有导入入口归档。"""
    import yaml
    result = []
    base = KNOWLEDGE_DIR / "skill" / "docs"
    for path in sorted(base.rglob("SKILL.md")):
        if path.is_symlink():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        metadata = {}
        if content.startswith("---"):
            try:
                loaded = yaml.safe_load(content.split("---", 2)[1])
                metadata = loaded if isinstance(loaded, dict) else {}
            except (yaml.YAMLError, IndexError):
                pass
        display = metadata.get("metadata") if isinstance(metadata.get("metadata"), dict) else {}
        result.append({"path": path.relative_to(base).as_posix(), "name": str(display.get("display_name") or metadata.get("name") or path.parent.name),
                       "description": str(metadata.get("description") or "知识库技能说明"),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def project_runs(project_id: str) -> list[dict]:
    load("projects", project_id)
    return sorted([json.loads(path.read_text()) for path in (STORE / "runs").glob("*.json")
                   if json.loads(path.read_text()).get("project_id") == project_id], key=lambda item: item["created_at"], reverse=True)


def set_status(run_id: str, status: str, **fields) -> dict:
    with LOCK:
        run = load("runs", run_id)
        run.update(status=status, updated_at=now(), **fields)
        save("runs", run)
        project = load("projects", run["project_id"])
        stage = next(item for item in project["stages"] if item["id"] == run["stage"])
        if stage["run_id"] == run_id:
            stage["status"] = status
            save("projects", project)
        return run


def ensure_workspace_available(project: dict) -> None:
    """同一真实目录和父子目录共用互斥边界，不能靠不同路径拼写绕过。"""
    workspace = resolve_workspace(project["workspace"])
    for other in list_projects():
        other_workspace = resolve_workspace(other["workspace"])
        overlap = workspace.is_relative_to(other_workspace) or other_workspace.is_relative_to(workspace)
        if overlap and any(run["status"] in ACTIVE for run in project_runs(other["id"])):
            raise ValueError("该工作区或其父子目录已有运行中的任务，请先等待或取消")


def verify_confirmed_dependencies(project: dict, stage_id: str) -> None:
    """只核验已确认的阶段交接输入，避免锁住无关的工作区观测文件。

    报告、资源清单及明确引用的资源必须仍与归档一致；代码阶段还绑定已执行
    构建和测试的最终源码指纹。外部编辑不能悄悄沿用之前的人工确认。
    """
    index = [key for key, _ in STAGES].index(stage_id)
    workspace = resolve_workspace(project["workspace"])
    for stage in project["stages"][:index]:
        if stage["status"] != "completed" or not stage["run_id"]:
            raise ValueError("必须先确认所有前置阶段的真实产物")
        try:
            upstream = load("runs", stage["run_id"])
            if upstream["status"] != "completed":
                raise ValueError("上游运行尚未确认")

            def verify_file(relative: str) -> dict:
                artifact = next((item for item in upstream["artifacts"] if item["path"] == relative), None)
                if not artifact:
                    raise ValueError(f"交接文件缺少归档快照：{relative}")
                artifact_file(upstream["id"], artifact["id"])
                current = checked_child(workspace, relative)
                if not current.is_file() or hashlib.sha256(current.read_bytes()).hexdigest() != artifact["sha256"]:
                    raise ValueError(f"交接文件已修改或丢失：{relative}")
                return artifact

            verify_file(f"workflow/{stage['id']}.md")
            if stage["id"] == "art":
                manifest_artifact = verify_file("workflow/art-manifest.json")
                # 从已确认快照读取清单，不能信任外部替换后的资源列表。
                manifest = json.loads(artifact_file(upstream["id"], manifest_artifact["id"]).read_text(encoding="utf-8"))
                for asset in manifest["assets"]:
                    resource = verify_file(asset["path"])
                    if resource["sha256"] != asset["sha256"]:
                        raise ValueError(f"资源快照与已确认清单不一致：{asset['path']}")
            if stage["id"] == "code":
                verify_validation_evidence(upstream, workspace)
        except (ValueError, FileNotFoundError, KeyError, TypeError, OSError) as error:
            raise ValueError(f"前置阶段「{stage['label']}」的已确认输入已变化或证据缺失，请重跑并确认该阶段：{error}") from error


def start_run(project_id: str, stage_id: str, prompt: str = "", skill_paths: list[str] | None = None,
              *, request_id: str | None = None, request_scope: str = "rest") -> dict:
    """提交阶段并立即返回；请求标识随运行落盘，客户端重试只取回原运行。"""
    submission = describe_submission(request_id, request_scope, {
        "project_id": project_id, "stage": stage_id, "prompt": prompt, "skill_paths": skill_paths or [],
    })
    with LOCK:
        project = load("projects", project_id)
        previous = find_submission(STORE / "runs", submission)
        if previous:
            return previous
        if stage_id not in dict(STAGES):
            raise ValueError("未知研发阶段")
        ensure_workspace_available(project)
        index = [key for key, _ in STAGES].index(stage_id)
        verify_confirmed_dependencies(project, stage_id)
        known = {skill["path"] for skill in list_skills()}
        if any(path not in known for path in (skill_paths or [])):
            raise ValueError("所选 Skill 不存在于技能知识库")
        run = {"id": uuid4().hex, "project_id": project_id, "stage": stage_id, "status": "queued", "progress": 0,
               "prompt": prompt, "skill_paths": skill_paths or [], "model": "gpt-6.1-sol", "provider": "codex-login",
               "created_at": now(), "updated_at": now(), "summary": "", "error": None, "events": [], "artifacts": [], "attempt": 1}
        if submission:
            run["submission"] = submission
        if project.get("production_profile"):
            from app.services.production_library import snapshot_knowledge
            # 运行记录独立保存配置与资料全文；目录更新、资料编辑不会改变恢复输入。
            run["production_profile"] = json.loads(json.dumps(project["production_profile"], ensure_ascii=False))
            run["knowledge_snapshot"] = snapshot_knowledge(run["production_profile"].get("knowledge_paths", []))
        # 上游重跑使所有下游确认失效，历史运行保留供追溯。
        for stage in project["stages"][index:]:
            stage.update(status="pending", run_id=None, confirmed_at=None)
        project["stages"][index].update(status="queued", run_id=run["id"])
        save("runs", run)
        save("projects", project)
        event(run["id"], "queued", "阶段任务已入队，所有下游确认已失效")
        WORKERS[run["id"]] = asyncio.create_task(execute_run(run["id"]))
        return load("runs", run["id"])


async def cancel_run(run_id: str) -> dict:
    run = load("runs", run_id)
    if run["status"] not in ACTIVE:
        raise ValueError("只有排队或运行中的任务可以取消")
    task = WORKERS.get(run_id)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    event(run_id, "cancelled", "用户取消了任务，已终止实际执行进程")
    return set_status(run_id, "cancelled", error="用户取消")


def resume_run(run_id: str, *, request_id: str | None = None, request_scope: str = "rest") -> dict:
    """恢复原检查点；远程重试同一次恢复不会额外增加执行 attempt。"""
    submission = describe_submission(request_id, request_scope, {"run_id": run_id})
    with LOCK:
        run = load("runs", run_id)
        if submission and submission in run.get("resumptions", []):
            return run
        if run["status"] not in {"failed", "cancelled", "interrupted"}:
            raise ValueError("仅失败、取消或中断任务可以恢复")
        project = load("projects", run["project_id"])
        index = [key for key, _ in STAGES].index(run["stage"])
        if project["stages"][index]["run_id"] != run_id:
            raise ValueError("该任务已被新运行取代，不能恢复过期检查点")
        verify_confirmed_dependencies(project, run["stage"])
        ensure_workspace_available(project)
        resumptions = run.get("resumptions", []) + ([submission] if submission else [])
        set_status(run_id, "queued", error=None, attempt=run.get("attempt", 1) + 1, resumptions=resumptions)
        event(run_id, "resumed", "从持久检查点恢复，保留此前工具结果与产物")
        WORKERS[run_id] = asyncio.create_task(execute_run(run_id, resume=True))
        return load("runs", run_id)


def confirm_stage(project_id: str, stage_id: str, note: str = "") -> dict:
    with LOCK:
        project = load("projects", project_id)
        stage = next((item for item in project["stages"] if item["id"] == stage_id), None)
        if not stage or stage["status"] != "awaiting_confirmation":
            raise ValueError("该阶段尚无可确认的真实运行结果")
        run = load("runs", stage["run_id"])
        if not run["artifacts"] or run["status"] != "awaiting_confirmation":
            raise ValueError("阶段产物不完整，不能确认")
        verify_knowledge_reads(run)
        if run["stage"] in {"code", "test"}:
            verify_validation_evidence(run, resolve_workspace(project["workspace"]))
        for artifact in run["artifacts"]:
            artifact_file(run["id"], artifact["id"])
        event(run["id"], "confirmed", "用户确认了阶段产物", {"note": note})
        set_status(run["id"], "completed", progress=100)
        project = load("projects", project_id)
        stage = next(item for item in project["stages"] if item["id"] == stage_id)
        stage["confirmed_at"] = now()
        save("projects", project)
        return get_project(project_id)


def artifact_file(run_id: str, artifact_id: str) -> Path:
    run = load("runs", run_id)
    artifact = next((item for item in run["artifacts"] if item["id"] == artifact_id), None)
    if not artifact:
        raise FileNotFoundError("产物不存在")
    # 快照位于当前运行目录，返回时再次校验边界与哈希，避免链接替换。
    path = checked_child(STORE / "artifacts" / run_id, artifact["stored_path"])
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
        raise ValueError("产物已丢失或哈希不匹配")
    return path


def reconcile_artifact_provenance(run_id: str) -> dict:
    """为旧版运行补来源元数据；保持状态、产物内容和原哈希完全不变。"""
    with LOCK:
        run = load("runs", run_id)
        written = written_file_evidence(run)
        for artifact in run["artifacts"]:
            artifact["provenance"] = "agent_edit" if written.get(artifact["path"]) == artifact["sha256"] else "workspace_observation"
        save("runs", run)
        event(run_id, "metadata_reconciled", "依据真实历史工具日志补齐产物来源；状态、正文和哈希保持不变", {
            "provenance": {kind: sum(item["provenance"] == kind for item in run["artifacts"]) for kind in {item["provenance"] for item in run["artifacts"]}}})
        return load("runs", run_id)


def collect_artifacts(run_id: str, workspace: Path, before: dict) -> list[dict]:
    """把本次生成和改动文件复制为不可变运行快照，历史阶段不受后续覆盖影响。"""
    import shutil
    after = snapshot(workspace)
    paths = [name for name, digest in after.items() if before.get(name) != digest]
    current = load("runs", run_id)
    report = f"workflow/{current['stage']}.md"
    write_hashes = written_file_evidence(current)
    written_paths = set(write_hashes)
    validation_paths = set()
    reference_paths = set()
    for item in current["events"]:
        if item["type"] == "validation_completed":
            validation_paths.update(item["data"].get("changed_paths", []))
    # 相同正文的合法重写仍需真实工具成功证据，单纯读取旧报告不能通过门禁。
    rewritten = report in written_paths
    if report in after and report not in paths and rewritten:
        paths.append(report)
    # 已有授权资源也属于美术交接产物；依据实际清单快照，供前端直接预览。
    if current["stage"] == "art":
        manifest = workspace / "workflow" / "art-manifest.json"
        if manifest.is_file():
            if "workflow/art-manifest.json" in after and "workflow/art-manifest.json" not in paths:
                paths.append("workflow/art-manifest.json")
            try:
                for asset in json.loads(manifest.read_text(encoding="utf-8")).get("assets", []):
                    name = asset.get("path")
                    # 明确交接的资源即使超过普通快照大小上限，也必须有完整证据快照。
                    if isinstance(name, str) and name not in after:
                        resource = checked_child(workspace, name)
                        if resource.is_file() and not resource.is_symlink():
                            after[name] = hashlib.sha256(resource.read_bytes()).hexdigest()
                    if name in after and name not in paths:
                        paths.append(name)
                    if name in after:
                        reference_paths.add(name)
            except (ValueError, TypeError, AttributeError):
                pass
    result = []
    for name in paths:
        source = checked_child(workspace, name)
        target = checked_child(STORE / "artifacts" / run_id, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        identifier = uuid4().hex
        provenance = "workspace_observation"
        if name in reference_paths:
            provenance = "reference_asset"
        if name in validation_paths:
            provenance = "validation_output"
        if name in written_paths and write_hashes[name] == after[name]:
            provenance = "agent_edit"
        result.append({"id": identifier, "name": source.name, "path": name, "stored_path": name,
                       "kind": "image" if mime.startswith("image/") else "text" if mime.startswith("text/") or source.suffix in {".json", ".ts", ".js", ".md"} else "file",
                       "size": source.stat().st_size, "sha256": after[name], "provenance": provenance,
                       "url": f"/api/workflow/artifacts/{run_id}/{identifier}"})
    return result


async def execute_run(run_id: str, resume: bool = False) -> None:
    """实际主链：官方建图→登录模型推理→工具执行→产物证据→等待人工确认。"""
    run = load("runs", run_id)
    project = load("projects", run["project_id"])
    workspace = resolve_workspace(project["workspace"])
    # 空工程的合法基线就是 {}；恢复时不能把前一次生成文件重新认作初始输入。
    before = run["initial_snapshot"] if run.get("initial_snapshot") is not None else snapshot(workspace)
    with LOCK:
        run["initial_snapshot"] = before
        save("runs", run)
    emit = lambda kind, message, data=None: event(run_id, kind, message, data)
    try:
        set_status(run_id, "running", progress=max(5, run.get("progress", 0)), error=None)
        runtime = await inspect_runtime()
        emit("runtime_checked", "已核验官方登录和指定模型", runtime)
        if not runtime["available"]:
            raise RuntimeError("当前 Codex 登录未提供 gpt-6.1-sol，不能替换其他模型")

        tools = create_workflow_tools(
            root=ROOT, knowledge_dir=KNOWLEDGE_DIR, workspace=workspace, run=run,
            emit=emit, load_run=lambda: load("runs", run_id),
        )

        model = CodexChatModel(event_callback=emit)
        instructions, prompt = build_run_prompts(run, project, resume)
        STORE.mkdir(parents=True, exist_ok=True)
        async with AsyncSqliteSaver.from_conn_string(str(STORE / "checkpoints.sqlite")) as checkpointer:
            agent = create_deep_agent(model=model, backend=FilesystemBackend(root_dir=workspace, virtual_mode=True),
                                      tools=tools,
                                      system_prompt=instructions, middleware=[create_tool_guard(workspace, emit)], checkpointer=checkpointer, name="game_workflow")
            config = {"configurable": {"thread_id": run_id}, "recursion_limit": 150}
            state = await agent.aget_state(config) if resume else None
            # 有未完成节点时续跑检查点，不插入Human打断待完成工具消息；当前attempt
            # 与重验要求已写进新建图的system_prompt，恢复后的下一次推理仍能看到。
            inputs = None if state and state.next else {"messages": [{"role": "user", "content": prompt}]}
            async for update in agent.astream(inputs, config, stream_mode="updates"):
                for node, values in update.items():
                    if not isinstance(values, dict):
                        continue
                    for message in values.get("messages", []):
                        data = message.model_dump(mode="json") if hasattr(message, "model_dump") else message
                        emit("graph_update", "DeepAgents 节点执行完成", {"node": node, "message": data})
                current = load("runs", run_id)
                set_status(run_id, "running", progress=min(85, current["progress"] + 3))
            state = await agent.aget_state(config)
            messages = state.values.get("messages", [])
            summary = next((str(message.content) for message in reversed(messages) if message.type == "ai" and not getattr(message, "tool_calls", [])), "")
        artifacts = collect_artifacts(run_id, workspace, before)
        current = load("runs", run_id)
        # 产物、技能读取和构建执行均从实际事件校验，不采信模型自述。
        if not any(item["path"] == f"workflow/{run['stage']}.md" for item in artifacts):
            raise RuntimeError("模型未产出当前阶段的真实报告，不能进入确认")
        reads = {item["data"].get("path") for item in current["events"] if item["type"] == "skill_read"}
        if set(run["skill_paths"]) - reads:
            raise RuntimeError("模型未实际读取全部选中 Skill，阶段验证失败")
        verify_knowledge_reads(current)
        if run["stage"] == "art":
            manifest = json.loads((workspace / "workflow" / "art-manifest.json").read_text(encoding="utf-8"))
            verify_art_manifest(workspace, manifest)
        if run["stage"] in {"code", "test"}:
            verify_validation_evidence(current, workspace)
        event(run_id, "artifacts_collected", "已归档真实产物快照、来源类别与哈希", {"count": len(artifacts),
              "provenance": {kind: sum(item["provenance"] == kind for item in artifacts) for kind in {item["provenance"] for item in artifacts}}})
        set_status(run_id, "awaiting_confirmation", progress=100, summary=summary, artifacts=artifacts)
    except asyncio.CancelledError:
        set_status(run_id, "cancelled", error="执行已取消")
        raise
    except Exception as error:
        event(run_id, "failed", "阶段执行失败", {"error": str(error)})
        set_status(run_id, "failed", error=str(error), artifacts=collect_artifacts(run_id, workspace, before))
    finally:
        WORKERS.pop(run_id, None)


def recover_interrupted_runs() -> None:
    """服务启动后识别此前未结束任务；保留检查点，等待用户明确恢复。"""
    for path in (STORE / "runs").glob("*.json"):
        run = json.loads(path.read_text(encoding="utf-8"))
        if run["status"] in ACTIVE:
            event(run["id"], "interrupted", "服务重启导致运行中断，可从检查点恢复")
            set_status(run["id"], "interrupted", error="服务重启，等待恢复")


async def shutdown_workers() -> None:
    """优雅关闭先取消并等待进程退出，再标记中断供下次恢复。"""
    active = list(WORKERS.items())
    for _, task in active:
        task.cancel()
    await asyncio.gather(*(task for _, task in active), return_exceptions=True)
    for run_id, _ in active:
        set_status(run_id, "interrupted", error="服务关闭，等待恢复")
