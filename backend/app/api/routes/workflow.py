"""四阶段研发 REST 接口；状态、证据和产物均来自实际执行记录。"""

from typing import Literal
import logging
import sqlite3

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.workflow import engine
from app.services.workflow.model_runtime import inspect_runtime
from app.services.workflow import pipeline
from app.services.workflow.templates import ProductionPlan, WorkflowTemplate, list_templates

router = APIRouter(prefix="/workflow", tags=["四阶段研发"])
logger = logging.getLogger(__name__)


class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    brief: str | dict = ""
    workspace: str | None = None
    references: list[str] = Field(default_factory=list)
    genre_id: str = "general"
    framework_id: str = "cocos-web"
    knowledge_paths: list[str] = Field(default_factory=list)
    model_provider: Literal["api-key", "codex-login"] = "api-key"
    model_id: str = Field(default="gpt-6.1-sol", min_length=1, max_length=120)
    request_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    production_plan: ProductionPlan | None = None
    start_immediately: bool = False


class RunRequest(BaseModel):
    stage: str
    prompt: str = ""
    skill_paths: list[str] = Field(default_factory=list, max_length=50)
    skill_mode: Literal["auto", "manual"] = "auto"
    excluded_skill_paths: list[str] = Field(default_factory=list, max_length=50)
    model_provider: Literal["api-key", "codex-login"] | None = None
    model_id: str | None = Field(default=None, min_length=1, max_length=120)
    request_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.:-]{1,128}$")


class ConfirmRequest(BaseModel):
    note: str = ""


class HumanAnswersRequest(BaseModel):
    answers: dict[str, str] = Field(min_length=1, max_length=20)


class PublishRequest(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")


class SkillRevisionRequest(BaseModel):
    path: str
    reason: str
    run_id: str


class SkillSourceSyncRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)
    expected_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


def invoke(function, *args, **kwargs):
    """把预期业务冲突转换为可读响应，未知异常交给服务日志处理。"""
    try:
        return function(*args, **kwargs)
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error


@router.get("/runtime")
async def runtime(provider: Literal["api-key", "codex-login"] = "api-key", model_id: str = "gpt-6.1-sol"):
    try:
        return await inspect_runtime(provider, model_id)
    except (OSError, RuntimeError, TimeoutError, ValueError) as error:
        return {"provider": provider, "model": model_id, "framework": "deepagents", "available": False,
                "configured": False, "connection_checked": False, "error": str(error), "models": []}


@router.get("/skills")
async def skills():
    return engine.list_skills()


@router.get("/templates")
async def templates():
    return invoke(list_templates)


@router.post("/templates/validate")
async def validate_template(body: WorkflowTemplate):
    """导入只校验输入，不创建项目、启动模型或接受模板中的工作区/凭据。"""
    value = body.model_dump()
    value["production_plan"] = invoke(pipeline.validate_plan, value["production_plan"])
    value["references"] = [invoke(engine.normalize_reference, path) for path in value["references"]]
    invoke(engine.model_runtime.validate_selection, body.model_provider, body.model_id)
    from app.services.production_library import resolve_profile
    invoke(resolve_profile, body.genre_id, body.framework_id)
    return value


@router.get("/skills/source-sync")
async def skill_source_sync_plan():
    """只读比较工程与公司技能来源，不在页面查询时补导或覆盖资料。"""
    from app.services.skill_library import plan_company_skill_sync
    return invoke(plan_company_skill_sync)


@router.post("/skills/source-sync")
async def skill_source_sync_apply(body: SkillSourceSyncRequest):
    """显式同步当前计划，旧正文先备份；计划过期时要求重新查看差异。"""
    from app.services.skill_library import apply_company_skill_sync
    return invoke(apply_company_skill_sync, body.reason, body.expected_digest)


@router.get("/catalog")
async def catalog():
    """品类、技术框架及可选资料索引，创建项目后由运行冻结实际输入。"""
    from app.services.production_library import get_catalog
    return invoke(get_catalog)


@router.post("/skills/publish")
async def publish_skill(body: SkillRevisionRequest):
    """本次明确指定的技能修订发布，完整记录关联运行与版本证据。"""
    from app.services.skill_library import sync_skill_revision
    invoke(engine.load, "runs", body.run_id)
    revision = invoke(sync_skill_revision, body.path, body.reason, body.run_id)
    engine.event(body.run_id, "skill_published", "已发布并归档指定 Skill 修订", revision)
    return revision


@router.get("/projects")
async def projects():
    return engine.list_projects()


@router.post("/projects", status_code=201)
async def create_project(body: ProjectRequest):
    payload = body.model_dump(exclude={"start_immediately"})
    if body.start_immediately and body.production_plan is None:
        raise HTTPException(409, "立即执行需要完整的全流程计划")
    project = invoke(engine.create_project, **payload)
    # 同一请求内完成保存与启动，用户提交后关闭页面不会留下尚未启动的半步操作。
    return invoke(pipeline.start_pipeline, project["id"]) if body.start_immediately else project


@router.get("/projects/{project_id}")
async def project(project_id: str):
    return invoke(engine.get_project, project_id)


@router.delete("/projects/{project_id}")
def delete_project(project_id: str):
    """永久清理对应项目；实际执行任务未结束时返回明确冲突，供用户先停止。"""
    from app.services import produced_game_deletion
    try:
        return produced_game_deletion.delete_project(project_id)
    except produced_game_deletion.GameDeletionConflict as error:
        raise HTTPException(409, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except (OSError, sqlite3.Error) as error:
        logger.exception("项目及产出清理失败，项目标识为 %s", project_id)
        raise HTTPException(503, "删除未完成，请重试删除。") from error


@router.get("/projects/{project_id}/runs")
async def project_runs(project_id: str):
    return invoke(engine.project_runs, project_id)


@router.get("/projects/{project_id}/activity")
def project_activity(project_id: str):
    """网页同步轻量的活动视图，完整证据仍通过原有运行详情读取。"""
    from app.services.workflow.activity import activity_run
    return {"project": invoke(engine.get_project, project_id),
            "runs": [activity_run(run) for run in invoke(engine.project_runs, project_id)]}


@router.post("/projects/{project_id}/pipeline/start", status_code=202)
async def start_pipeline(project_id: str):
    return invoke(pipeline.start_pipeline, project_id)


@router.post("/projects/{project_id}/pipeline/resume", status_code=202)
async def resume_pipeline(project_id: str):
    return invoke(pipeline.resume_pipeline, project_id)


@router.post("/projects/{project_id}/pipeline/cancel")
async def cancel_pipeline(project_id: str):
    try:
        return await pipeline.cancel_pipeline(project_id)
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error


@router.post("/projects/{project_id}/runs", status_code=202)
async def start_run(project_id: str, body: RunRequest):
    return invoke(engine.start_run, project_id, body.stage, body.prompt, body.skill_paths,
                  skill_mode=body.skill_mode, excluded_skill_paths=body.excluded_skill_paths,
                  request_id=body.request_id, model_provider=body.model_provider, model_id=body.model_id)


@router.post("/projects/{project_id}/publish")
async def publish_project(project_id: str, body: PublishRequest):
    """只有已确认且文件未变化的测试构建可以公开发布。"""
    return invoke(engine.publish_project, project_id, body.slug)


@router.post("/projects/{project_id}/skill-selection")
async def preview_skill_selection(project_id: str, body: RunRequest):
    """只读计算当前输入的技能选择；运行开始时仍由同一后端逻辑重新核定。"""
    return invoke(engine.preview_skill_selection, project_id, body.stage, body.prompt,
                  body.skill_paths, skill_mode=body.skill_mode, excluded_skill_paths=body.excluded_skill_paths)


@router.get("/runs/{run_id}")
async def run(run_id: str):
    return invoke(engine.load, "runs", run_id)


@router.get("/runs/{run_id}/events")
async def events(run_id: str, after: int = 0):
    return [item for item in invoke(engine.load, "runs", run_id)["events"] if item["seq"] > after]


@router.post("/runs/{run_id}/cancel")
async def cancel(run_id: str):
    try:
        run = engine.load("runs", run_id)
        project = engine.load("projects", run["project_id"])
        if run.get("pipeline_id") and project.get("pipeline", {}).get("status") in pipeline.OWNED:
            await pipeline.cancel_pipeline(run["project_id"])
            return engine.load("runs", run_id)
        return await engine.cancel_run(run_id)
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error


@router.post("/runs/{run_id}/resume", status_code=202)
async def resume(run_id: str):
    return invoke(engine.resume_run, run_id)


@router.post("/runs/{run_id}/answers", status_code=202)
async def answer_run(run_id: str, body: HumanAnswersRequest):
    return invoke(pipeline.answer_run, run_id, body.answers)


@router.post("/projects/{project_id}/stages/{stage_id}/confirm")
async def confirm(project_id: str, stage_id: str, body: ConfirmRequest):
    return invoke(engine.confirm_stage, project_id, stage_id, body.note)


@router.get("/artifacts/{run_id}/{artifact_id}")
async def artifact(run_id: str, artifact_id: str):
    path = invoke(engine.artifact_file, run_id, artifact_id)
    # 保留 inline 类型，前端可以直接展示文本、图片和文档。
    return FileResponse(path)


@router.get("/projects/{project_id}/preview/{file_path:path}")
async def preview(project_id: str, file_path: str):
    from app.services.workflow.preview import preview_file
    project = invoke(engine.load, "projects", project_id)
    base, _ = invoke(engine.preview_location, project)
    path = invoke(preview_file, base, file_path)
    # 开发构建允许随时变化，子资源也必须重新读取，避免只刷新 HTML 却沿用旧贴图。
    return FileResponse(path, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
