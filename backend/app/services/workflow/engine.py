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
from langgraph.types import Command

from app.config import DATA_DIR, KNOWLEDGE_DIR, LLM_AVAILABLE_MODELS, LLM_MODEL_INDEX
from app.services.workflow import workspace as workspace_files
from app.services.workflow import model_runtime
from app.services.workflow.codex_model import CodexChatModel, inspect_runtime
from app.services.workflow.prompts import build_run_prompts
from app.services.workflow.skill_routing import plan_skill_selection
from app.services.workflow.skill_inputs import freeze_skill_inputs
from app.services.workflow.submissions import describe_submission, find_submission
from app.services.workflow.tools import create_tool_guard, create_workflow_tools
# 兼容原有路由及调用方；校验与文件实现已迁移到独立模块。
from app.services.workflow.validation import (
    ASSET_SUFFIXES, PROCEDURAL_SUFFIXES, read_frozen_knowledge, required_validations,
    successful_file_result, verify_art_manifest, verify_knowledge_reads, verify_skill_reads,
    verify_code_handoff, verify_validation_evidence, written_file_evidence,
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
# 原生模型按 provider:model 匹配，而不是按 ChatOpenAI 类名匹配。
for model_spec in LLM_AVAILABLE_MODELS:
    register_harness_profile(f"{model_spec['provider']}:{model_spec['id']}",
                             HarnessProfile(general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False)))


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
    from app.services.produced_game_deletion import pending_projects
    with LOCK:
        projects = {path.stem: get_project(path.stem) for path in (STORE / "projects").glob("*.json")}
        # 待清理项目继续显示重试入口，避免部分删除后失去唯一可见操作路径。
        projects.update(pending_projects(STORE))
        return sorted(projects.values(), key=lambda project: project["created_at"], reverse=True)


def get_project(identifier: str) -> dict:
    from app.services.workflow.preview import describe_preview
    project = load("projects", identifier)
    base, entry = preview_location(project)
    project["preview"] = describe_preview(identifier, base, entry)
    project["preview_url"] = project["preview"]["url"]
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
                   *, request_id: str | None = None, request_scope: str = "rest",
                   model_provider: str = "codex-login", model_id: str = "gpt-6.1-sol",
                   production_plan: dict | None = None) -> dict:
    """创建项目并按调用方去重；锁覆盖查重和落盘，重试不会产生第二个工作区。"""
    payload = {
        "name": name, "brief": brief, "workspace": workspace, "references": references,
        "genre_id": genre_id, "framework_id": framework_id, "knowledge_paths": knowledge_paths or [],
    }
    # 历史默认保持原提交摘要，升级前尚在重试的MCP请求仍能找到原项目。
    if (model_provider, model_id) != ("codex-login", "gpt-6.1-sol"):
        payload.update(model_provider=model_provider, model_id=model_id)
    if production_plan is not None:
        from app.services.workflow.pipeline import validate_plan
        production_plan = validate_plan(production_plan)
        payload["production_plan"] = dict(production_plan)
        # 未开启时保持升级前的提交摘要，旧创建请求重试仍能找到同一项目。
        if not production_plan["autonomous"]:
            payload["production_plan"].pop("autonomous")
    submission = describe_submission(request_id, request_scope, payload)
    with LOCK:
        previous = find_submission(STORE / "projects", submission)
        if previous:
            return get_project(previous["id"])
        selection = model_runtime.validate_selection(model_provider, model_id)
        return _create_project(name, brief, workspace, references, genre_id, framework_id, knowledge_paths,
                               submission, selection, production_plan)


def _create_project(name: str, brief: str | dict, workspace: str | None, references: list[str],
                    genre_id: str | None, framework_id: str | None, knowledge_paths: list[str] | None,
                    submission: dict | None, model_selection: dict, production_plan: dict | None = None) -> dict:
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
    from app.services.produced_game_deletion import ensure_workspace_not_deleting
    ensure_workspace_not_deleting(ROOT, STORE, workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    workspace = workspace_path.relative_to(ROOT.resolve()).as_posix()
    project = {"id": identifier, "name": name, "brief": brief, "workspace": workspace, **model_selection,
               "references": list(dict.fromkeys(normalize_reference(path) for path in references)),
               "created_at": now(), "stages": [{"id": key, "label": label, "status": "pending", "run_id": None,
                                                    "confirmed_at": None} for key, label in STAGES]}
    if submission:
        project["submission"] = submission
    if production_plan is not None:
        project["production_plan"] = production_plan
        project["pipeline"] = {"id": uuid4().hex, "status": "draft", "run_id": None}
    if profile is not None:
        project.update(genre_id=profile["genre"]["id"], framework_id=profile["framework"]["id"],
                       knowledge_paths=profile["knowledge_paths"], production_profile=profile)
        preview_location(project)
    save("projects", project)
    return get_project(project["id"])


def list_skills() -> list[dict]:
    """动态发现知识库中的 Skill 元数据；新增包通过既有导入入口归档。"""
    import yaml
    from app.services.skill_library import SKILL_DESCRIPTIONS
    result = []
    base = KNOWLEDGE_DIR / "skill" / "docs"
    for path in sorted(base.rglob("SKILL.md")):
        if any(part.startswith(".") for part in path.relative_to(base).parts) or any(
                parent.is_symlink() for parent in (path, *path.parents)):
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
        # 共用知识库中文名称；描述优先采用当前正文，避免沿用旧版本能力说明。
        known_title = SKILL_DESCRIPTIONS.get(path.parent.name, (None, None))[0]
        result.append({"path": path.relative_to(base).as_posix(), "name": str(display.get("display_name") or known_title or metadata.get("name") or path.parent.name),
                       "description": str(metadata.get("description") or "知识库技能说明"),
                       "version": str(display.get("version") or metadata.get("version") or ""),
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


def ensure_workspace_available(project: dict, *, exclude_run: str | None = None) -> None:
    """同一真实目录和父子目录共用互斥边界，不能靠不同路径拼写绕过。"""
    workspace = resolve_workspace(project["workspace"])
    from app.services.produced_game_deletion import ensure_workspace_not_deleting
    ensure_workspace_not_deleting(ROOT, STORE, workspace)
    for other in list_projects():
        other_workspace = resolve_workspace(other["workspace"])
        overlap = workspace.is_relative_to(other_workspace) or other_workspace.is_relative_to(workspace)
        if overlap and any(run["status"] in ACTIVE | {"awaiting_input"} and run["id"] != exclude_run
                           for run in project_runs(other["id"])):
            raise ValueError("该工作区或其父子目录已有运行中的任务，请先等待或取消")
        if overlap and other["id"] != project["id"] and other.get("pipeline", {}).get("status") in {
                "running", "awaiting_input", "interrupted", "failed"}:
            raise ValueError("该工作区已由另一个全流程任务占用，请先完成或取消该任务")


def verify_confirmed_dependencies(project: dict, stage_id: str) -> None:
    """只核验已确认的阶段交接输入，避免锁住无关的工作区观测文件。

    报告、资源清单及明确引用的资源必须仍与归档一致；代码阶段还绑定已执行
    构建和测试的最终源码清单。测试阶段可新增有记录的补测脚本，不能改写上游输入。
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
                test_stage = next(item for item in project["stages"] if item["id"] == "test")
                test_run = load("runs", test_stage["run_id"]) if test_stage.get("run_id") else None
                verify_code_handoff(upstream, workspace, test_run)
        except (ValueError, FileNotFoundError, KeyError, TypeError, OSError) as error:
            raise ValueError(f"前置阶段「{stage['label']}」的已确认输入已变化或证据缺失，请重跑并确认该阶段：{error}") from error


def preview_skill_selection(project_id: str, stage_id: str, prompt: str = "", skill_paths: list[str] | None = None,
                            *, skill_mode: str = "auto", excluded_skill_paths: list[str] | None = None) -> dict:
    """页面和远程工具共用只读路由，不能通过预览修改运行或阶段状态。"""
    return plan_skill_selection(load("projects", project_id), stage_id, prompt, list_skills(),
                                mode=skill_mode, include_paths=skill_paths, exclude_paths=excluded_skill_paths)


def start_run(project_id: str, stage_id: str, prompt: str = "", skill_paths: list[str] | None = None,
              *, skill_mode: str = "auto", excluded_skill_paths: list[str] | None = None,
              request_id: str | None = None, request_scope: str = "rest",
              model_provider: str | None = None, model_id: str | None = None,
              pipeline_id: str | None = None) -> dict:
    """提交阶段并立即返回；请求标识随运行落盘，客户端重试只取回原运行。"""
    payload = {
        "project_id": project_id, "stage": stage_id, "prompt": prompt, "skill_paths": skill_paths or [],
        "skill_mode": skill_mode, "excluded_skill_paths": excluded_skill_paths or [],
    }
    # 省略模型参数表示继承项目，保留升级前同一请求的幂等摘要。
    if model_provider is not None or model_id is not None:
        payload.update(model_provider=model_provider, model_id=model_id)
    submission = describe_submission(request_id, request_scope, payload)
    with LOCK:
        project = load("projects", project_id)
        previous = find_submission(STORE / "runs", submission)
        if previous:
            return previous
        from app.services.workflow.pipeline import require_owner
        require_owner(project, pipeline_id)
        if stage_id not in dict(STAGES):
            raise ValueError("未知研发阶段")
        model_selection = model_runtime.validate_selection(model_provider or project.get("model_provider", "codex-login"),
                                                            model_id or project.get("model_id", "gpt-6.1-sol"))
        ensure_workspace_available(project)
        index = [key for key, _ in STAGES].index(stage_id)
        verify_confirmed_dependencies(project, stage_id)
        # 运行时重新选择并冻结，不能信任浏览器缓存的建议或把历史选择套给新阶段。
        available_skills = list_skills()
        selection = plan_skill_selection(project, stage_id, prompt, available_skills,
                                         mode=skill_mode, include_paths=skill_paths, exclude_paths=excluded_skill_paths)
        run = {"id": uuid4().hex, "project_id": project_id, "stage": stage_id, "status": "queued", "progress": 0,
               "autonomous": project.get("production_plan", {}).get("autonomous") is True,
               "prompt": prompt, "skill_paths": selection["selected_paths"], "skill_selection": selection,
               "model": model_selection["model_id"], "provider": model_selection["model_provider"],
               "created_at": now(), "updated_at": now(), "summary": "", "error": None, "events": [], "artifacts": [], "attempt": 1}
        if submission:
            run["submission"] = submission
        if pipeline_id:
            run["pipeline_id"] = pipeline_id
        # 只交接当前已确认上游的 AI 决策，旧的失效运行不参与下游上下文。
        run["upstream_decisions"] = [
            {"stage": stage["id"], **item["data"]}
            for stage in project["stages"][:index] if stage.get("run_id")
            for item in load("runs", stage["run_id"])["events"]
            if item["type"] == "autonomous_decision"
        ]
        if project.get("production_profile"):
            from app.services.production_library import snapshot_knowledge
            # 运行记录独立保存配置与资料全文；目录更新、资料编辑不会改变恢复输入。
            run["production_profile"] = json.loads(json.dumps(project["production_profile"], ensure_ascii=False))
            run["knowledge_snapshot"] = snapshot_knowledge(run["production_profile"].get("knowledge_paths", []))
        # 技能与配套文本归档到输入目录，模型按需读取；不把整个技能库注入上下文。
        run.update(freeze_skill_inputs(run["skill_paths"], available_skills, KNOWLEDGE_DIR,
                                       STORE / "inputs" / run["id"] / "skills"))
        # 上游重跑使所有下游确认失效，历史运行保留供追溯。
        for stage in project["stages"][index:]:
            stage.update(status="pending", run_id=None, confirmed_at=None)
        project["stages"][index].update(status="queued", run_id=run["id"])
        save("runs", run)
        save("projects", project)
        event(run["id"], "queued", "阶段任务已入队，所有下游确认已失效")
        event(run["id"], "skills_selected", "已按品类、技术框架与当前阶段确定 Skill 并冻结版本",
              {"selection": selection, "snapshot": run["skill_snapshot"]})
        WORKERS[run["id"]] = asyncio.create_task(execute_run(run["id"]))
        return load("runs", run["id"])


async def cancel_run(run_id: str) -> dict:
    run = load("runs", run_id)
    if run["status"] not in ACTIVE | {"awaiting_input"}:
        raise ValueError("只有排队或运行中的任务可以取消")
    task = WORKERS.get(run_id)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    event(run_id, "cancelled", "用户取消了任务，已终止实际执行进程")
    result = set_status(run_id, "cancelled", error="用户取消")
    if run.get("pipeline_id"):
        # MCP 等旧入口也能取消阶段；必须同步停止所属全流程，防止界面一直显示运行中。
        from app.services.workflow.pipeline import update_pipeline
        update_pipeline(run["project_id"], status="cancelled", error="用户取消了全流程中的任务")
    return result


def resume_run(run_id: str, *, request_id: str | None = None, request_scope: str = "rest",
               pipeline_id: str | None = None) -> dict:
    """恢复原检查点；远程重试同一次恢复不会额外增加执行 attempt。"""
    submission = describe_submission(request_id, request_scope, {"run_id": run_id})
    with LOCK:
        run = load("runs", run_id)
        if submission and submission in run.get("resumptions", []):
            return run
        if run["status"] not in {"failed", "cancelled", "interrupted"}:
            raise ValueError("仅失败、取消或中断任务可以恢复")
        project = load("projects", run["project_id"])
        from app.services.workflow.pipeline import require_owner
        require_owner(project, pipeline_id)
        index = [key for key, _ in STAGES].index(run["stage"])
        if project["stages"][index]["run_id"] != run_id:
            raise ValueError("该任务已被新运行取代，不能恢复过期检查点")
        verify_confirmed_dependencies(project, run["stage"])
        ensure_workspace_available(project)
        resumptions = run.get("resumptions", []) + ([submission] if submission else [])
        set_status(run_id, "queued", error=None, last_error=run.get("error"),
                   attempt=run.get("attempt", 1) + 1, resumptions=resumptions)
        event(run_id, "resumed", "从持久检查点恢复，保留此前工具结果与产物")
        WORKERS[run_id] = asyncio.create_task(execute_run(run_id, resume=True))
        return load("runs", run_id)


def confirm_stage(project_id: str, stage_id: str, note: str = "", *, pipeline_id: str | None = None) -> dict:
    with LOCK:
        project = load("projects", project_id)
        from app.services.workflow.pipeline import require_owner
        require_owner(project, pipeline_id)
        stage = next((item for item in project["stages"] if item["id"] == stage_id), None)
        if not stage or stage["status"] != "awaiting_confirmation":
            raise ValueError("该阶段尚无可确认的真实运行结果")
        run = load("runs", stage["run_id"])
        if not run["artifacts"] or run["status"] != "awaiting_confirmation":
            raise ValueError("阶段产物不完整，不能确认")
        verify_knowledge_reads(run)
        # 旧运行没有技能快照时保持原确认契约，新运行必须实际读完冻结版本。
        if "skill_snapshot" in run:
            verify_skill_reads(run, STORE / "inputs" / run["id"] / "skills")
        if run["stage"] == "test":
            verify_confirmed_dependencies(project, "test")
        confirmed_inputs = {}
        if run["stage"] in {"code", "test"}:
            workspace = resolve_workspace(project["workspace"])
            inputs = workspace_files.source_snapshot(workspace)
            verify_validation_evidence(run, workspace, inputs=inputs)
            if run["stage"] == "code":
                # 保存通过实际验证的完整输入，后续不把补测脚本混入上游确认范围。
                confirmed_inputs["confirmed_source_snapshot"] = inputs
        for artifact in run["artifacts"]:
            artifact_file(run["id"], artifact["id"])
        event(run["id"], "confirmed", "按用户确认的全流程计划通过阶段校验" if pipeline_id else "用户确认了阶段产物",
              {"note": note, "confirmed_by": "pipeline" if pipeline_id else "user"})
        set_status(run["id"], "completed", progress=100, **confirmed_inputs)
        project = load("projects", project_id)
        stage = next(item for item in project["stages"] if item["id"] == stage_id)
        stage["confirmed_at"] = now()
        stage["confirmed_by"] = "pipeline" if pipeline_id else "user"
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


def publish_project(project_id: str, slug: str) -> dict:
    """发布已确认的测试构建，发布与同工作区任务启动共用一把锁。"""
    from app.services.workflow.publishing import publish_game

    with LOCK:
        project = load("projects", project_id)
        ensure_workspace_available(project)
        stage = next(item for item in project["stages"] if item["id"] == "test")
        if not stage.get("run_id"):
            raise ValueError("请先完成并确认测试阶段，再发布游戏")
        run = load("runs", stage["run_id"])
        # 同时检查归档副本，不能仅依赖工作区内可修改的报告。
        for artifact in run.get("artifacts", []):
            artifact_file(run["id"], artifact["id"])
        publication = publish_game(ROOT, resolve_workspace(project["workspace"]), project, run, slug,
                                   verify_dependencies=verify_confirmed_dependencies)
        project["publication"] = publication
        save("projects", project)
        event(run["id"], "game_published", "已发布通过验收的网页构建", publication)
        return publication


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
    generated_hashes = {}
    processed_hashes = {}
    for item in current["events"]:
        if item["type"] == "validation_completed":
            validation_paths.update(item["data"].get("changed_paths", []))
        if item["type"] == "image_generated":
            generated_hashes[item["data"]["path"]] = item["data"]["sha256"]
        if item["type"] == "image_processed":
            processed_hashes[item["data"]["path"]] = item["data"]["sha256"]
        if item["type"] == "reference_asset_copied":
            reference_paths.add(item["data"]["path"])
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
        if generated_hashes.get(name) == after[name]:
            provenance = "generated_asset"
        # 只标记仍与实际处理结果相同的版本，后续外部改动不能沿用旧来源。
        if processed_hashes.get(name) == after[name]:
            provenance = "processed_asset"
        result.append({"id": identifier, "name": source.name, "path": name, "stored_path": name,
                       "kind": "image" if mime.startswith("image/") else "text" if mime.startswith("text/") or source.suffix in {".json", ".ts", ".js", ".md"} else "file",
                       "size": source.stat().st_size, "sha256": after[name], "provenance": provenance,
                       "url": f"/api/workflow/artifacts/{run_id}/{identifier}"})
    return result


async def execute_run(run_id: str, resume: bool = False) -> None:
    """实际主链：官方建图→指定身份模型推理→工具执行→产物证据→等待确认。"""
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
        api_mode = run.get("provider") == "api-key"
        runtime = await model_runtime.inspect_runtime("api-key", run["model"]) if api_mode else await inspect_runtime()
        emit("runtime_checked", "已检查本次模型身份与配置，真实调用以model_completed为准", runtime)
        if not runtime["available"]:
            raise RuntimeError(runtime.get("error") or "指定身份下的模型不可用，不能替换模型或身份")
        with LOCK:
            run = load("runs", run_id)
            run["capabilities"] = runtime.get("capabilities", model_runtime.capabilities())
            save("runs", run)

        tools = create_workflow_tools(
            root=ROOT, knowledge_dir=KNOWLEDGE_DIR, workspace=workspace, run=run,
            emit=emit, load_run=lambda: load("runs", run_id),
            skill_input_dir=STORE / "inputs" / run_id / "skills",
        )

        model = model_runtime.create_api_model(run["model"], emit) if api_mode else CodexChatModel(event_callback=emit)
        instructions, prompt = build_run_prompts(run, project, resume)
        middleware = [create_tool_guard(workspace, emit)]
        if api_mode and LLM_MODEL_INDEX[run["model"]]["provider"] == "openai":
            from app.services.workflow.model_messages import create_api_message_adapter
            # 与模型实例使用相同协议，兼容模型不能套用 GPT 的 Responses 历史处理。
            middleware.append(create_api_message_adapter(stateless_responses=bool(model.use_responses_api)))
        STORE.mkdir(parents=True, exist_ok=True)
        async with AsyncSqliteSaver.from_conn_string(str(STORE / "checkpoints.sqlite")) as checkpointer:
            agent = create_deep_agent(model=model, backend=FilesystemBackend(root_dir=workspace, virtual_mode=True),
                                      tools=tools,
                                      system_prompt=instructions, middleware=middleware, checkpointer=checkpointer, name="game_workflow")
            # 上限按图节点步数计算；模型、消息适配与工具都会占步，完整游戏生产需留出调试空间。
            config = {"configurable": {"thread_id": run_id}, "recursion_limit": 300}
            state = await agent.aget_state(config) if resume else None
            # 有未完成节点时续跑检查点，不插入Human打断待完成工具消息；当前attempt
            # 与重验要求已写进新建图的system_prompt，恢复后的下一次推理仍能看到。
            inputs = None if state and state.next else {"messages": [{"role": "user", "content": prompt}]}
            from app.services.workflow.human_input import pending_interrupts
            pending = pending_interrupts(state) if state else []
            if pending:
                answers = run.get("pending_answers", {})
                if set(answers) == {item["id"] for item in pending}:
                    inputs = Command(resume=answers)
                else:
                    set_status(run_id, "awaiting_input", interrupts=pending)
                    return
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
            pending = pending_interrupts(state)
            if pending:
                emit("human_input_requested", "Agent 需要补充或确认，已保存检查点并暂停", {"interrupts": pending})
                set_status(run_id, "awaiting_input", interrupts=pending, pending_answers={})
                return
            messages = state.values.get("messages", [])
            summary = next((str(message.text) for message in reversed(messages) if message.type == "ai" and not getattr(message, "tool_calls", [])), "")
        artifacts = collect_artifacts(run_id, workspace, before)
        current = load("runs", run_id)
        # 产物、技能读取和构建执行均从实际事件校验，不采信模型自述。
        if not any(item["path"] == f"workflow/{run['stage']}.md" for item in artifacts):
            raise RuntimeError("模型未产出当前阶段的真实报告，不能进入确认")
        verify_skill_reads(current, STORE / "inputs" / run_id / "skills")
        verify_knowledge_reads(current)
        if run["stage"] == "art":
            manifest = json.loads((workspace / "workflow" / "art-manifest.json").read_text(encoding="utf-8"))
            verify_art_manifest(workspace, manifest)
        if run["stage"] == "test":
            verify_confirmed_dependencies(project, "test")
        if run["stage"] in {"code", "test"}:
            verify_validation_evidence(current, workspace)
        event(run_id, "artifacts_collected", "已归档真实产物快照、来源类别与哈希", {"count": len(artifacts),
              "provenance": {kind: sum(item["provenance"] == kind for item in artifacts) for kind in {item["provenance"] for item in artifacts}}})
        set_status(run_id, "awaiting_confirmation", progress=100, summary=summary, artifacts=artifacts,
                   interrupts=[], pending_answers={})
    except asyncio.CancelledError:
        set_status(run_id, "cancelled", error="执行已取消")
        raise
    except Exception as error:
        message = model_runtime.safe_error(error)
        event(run_id, "failed", "阶段执行失败", {"error": message})
        set_status(run_id, "failed", error=message, artifacts=collect_artifacts(run_id, workspace, before))
    finally:
        WORKERS.pop(run_id, None)


def recover_interrupted_runs() -> None:
    """服务启动后识别此前未结束任务；保留检查点，等待用户明确恢复。"""
    for path in (STORE / "runs").glob("*.json"):
        run = json.loads(path.read_text(encoding="utf-8"))
        if run["status"] in ACTIVE:
            event(run["id"], "interrupted", "服务重启导致运行中断，可从检查点恢复")
            set_status(run["id"], "interrupted", error="服务重启，等待恢复")
    from app.services.workflow.pipeline import recover_pipelines
    recover_pipelines()


async def shutdown_workers() -> None:
    """优雅关闭先取消并等待进程退出，再标记中断供下次恢复。"""
    from app.services.workflow.pipeline import shutdown_pipelines
    await shutdown_pipelines()
    active = list(WORKERS.items())
    for _, task in active:
        task.cancel()
    await asyncio.gather(*(task for _, task in active), return_exceptions=True)
    for run_id, _ in active:
        set_status(run_id, "interrupted", error="服务关闭，等待恢复")
