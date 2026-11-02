"""四阶段研发 REST 接口；状态、证据和产物均来自实际执行记录。"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.workflow import engine
from app.services.workflow.codex_model import inspect_runtime

router = APIRouter(prefix="/workflow", tags=["四阶段研发"])


class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    brief: str | dict = ""
    workspace: str | None = None
    references: list[str] = Field(default_factory=list)
    genre_id: str = "general"
    framework_id: str = "cocos-web"
    knowledge_paths: list[str] = Field(default_factory=list)
    request_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.:-]{1,128}$")


class RunRequest(BaseModel):
    stage: str
    prompt: str = ""
    skill_paths: list[str] = Field(default_factory=list)
    request_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.:-]{1,128}$")


class ConfirmRequest(BaseModel):
    note: str = ""


class SkillRevisionRequest(BaseModel):
    path: str
    reason: str
    run_id: str


def invoke(function, *args, **kwargs):
    """把预期业务冲突转换为可读响应，未知异常交给服务日志处理。"""
    try:
        return function(*args, **kwargs)
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error


@router.get("/runtime")
async def runtime():
    try:
        return await inspect_runtime()
    except (OSError, RuntimeError, TimeoutError) as error:
        return {"provider": "codex-login", "model": "gpt-6.1-sol", "framework": "deepagents", "available": False,
                "logged_in": False, "error": str(error), "models": []}


@router.get("/skills")
async def skills():
    return engine.list_skills()


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
    return invoke(engine.create_project, **body.model_dump())


@router.get("/projects/{project_id}")
async def project(project_id: str):
    return invoke(engine.get_project, project_id)


@router.get("/projects/{project_id}/runs")
async def project_runs(project_id: str):
    return invoke(engine.project_runs, project_id)


@router.post("/projects/{project_id}/runs", status_code=202)
async def start_run(project_id: str, body: RunRequest):
    return invoke(engine.start_run, project_id, body.stage, body.prompt, body.skill_paths, request_id=body.request_id)


@router.get("/runs/{run_id}")
async def run(run_id: str):
    return invoke(engine.load, "runs", run_id)


@router.get("/runs/{run_id}/events")
async def events(run_id: str, after: int = 0):
    return [item for item in invoke(engine.load, "runs", run_id)["events"] if item["seq"] > after]


@router.post("/runs/{run_id}/cancel")
async def cancel(run_id: str):
    try:
        return await engine.cancel_run(run_id)
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error


@router.post("/runs/{run_id}/resume", status_code=202)
async def resume(run_id: str):
    return invoke(engine.resume_run, run_id)


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
    project = invoke(engine.get_project, project_id)
    base, _ = invoke(engine.preview_location, project)
    path = invoke(engine.checked_child, base, file_path)
    if not path.is_file():
        raise HTTPException(404, "游戏构建文件不存在")
    return FileResponse(path)
