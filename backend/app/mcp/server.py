"""将业务操作显式注册为 MCP 工具；保持异步入口，共享工作流所在的事件循环。"""

from contextlib import contextmanager
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token
from pydantic import Field
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from app.mcp.auth import ClientTokenVerifier, Identifier, MCPClient, MCPSettings
from app.services import production_library
from app.services.workflow import engine, remote

RequestId = Annotated[str, Field(
    pattern=r"^[A-Za-z0-9_.:-]{1,128}$",
    description="本次操作的唯一标识；重试须复用，新操作须换新标识",
)]
Stage = Literal["prototype", "art", "code", "test"]
Limit = Annotated[int, Field(ge=1, le=50)]
Offset = Annotated[int, Field(ge=0)]
READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True}
WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True}


@contextmanager
def business_errors():
    """预期业务失败作为 MCP 工具错误返回；未知异常由框架屏蔽细节。"""
    try:
        yield
    except (FileNotFoundError, PermissionError, ValueError) as error:
        raise ToolError(str(error)) from None


def create_mcp_app(settings: MCPSettings):
    """创建可挂载的 ASGI 应用；自身不启动第二个执行器或维护第二套任务状态。"""
    verifier = ClientTokenVerifier(settings.clients)
    server = FastMCP(
        "游戏研发工作流", version="1.0.0", auth=verifier, mask_error_details=True,
        instructions=(
            "先查看能力和项目状态，再提交研发阶段。创建、启动、恢复均须提供 request_id；"
            "网络重试复用原标识。启动立即返回 run_id，按提示间隔查询进度。"
            "awaiting_confirmation 表示产物等待用户在工作台确认，不能当作 completed；"
            "resume_run 只恢复中断运行，不会确认阶段。客户端断开不会取消后台任务。"
            "产物通过 read_artifact 或带相同 Bearer 认证的下载地址读取。"
        ),
    )

    def current_client() -> MCPClient:
        """身份只取认证上下文，工具参数不能覆盖调用方或授权项目。"""
        token = get_access_token()
        if token is None or token.client_id not in verifier.clients:
            raise ToolError("需要有效的客户端身份")
        return verifier.clients[token.client_id]

    @server.tool(annotations=READ_ONLY)
    async def get_capabilities() -> dict:
        """查看阶段、可用框架和当前身份的权限；阶段完成后需用户在工作台确认。"""
        client = current_client()
        return {
            "stages": [{"id": key, "name": label} for key, label in engine.STAGES],
            "genres": [
                {key: item.get(key) for key in ("id", "label", "description", "knowledge_paths")}
                for item in production_library.GENRES
            ],
            "frameworks": [
                {key: item.get(key) for key in ("id", "label", "status", "knowledge_paths")}
                for item in production_library.FRAMEWORKS
            ],
            "project_ids": client.project_ids, "can_create_projects": client.can_create_projects,
            "requires_human_confirmation": True, "automatic_restart_recovery": False,
            "instructions": "技能索引通过 list_skills 获取；同一工作区只允许一个运行。服务重启后的 interrupted 任务可显式恢复。",
        }

    @server.tool(annotations=READ_ONLY)
    async def list_skills(offset: Offset = 0, limit: Limit = 20) -> dict:
        """分页查看可选 Skill 路径、摘要和版本哈希，供 start_stage 的 skill_paths 使用。"""
        current_client()
        skills = engine.list_skills()
        items = [{**item, "description": item["description"][:1000]} for item in skills[offset:offset + limit]]
        return {"items": items, "total": len(skills), "next_offset": offset + len(items),
                "has_more": offset + len(items) < len(skills)}

    @server.tool(annotations=READ_ONLY)
    async def list_projects(offset: Offset = 0, limit: Limit = 20) -> dict:
        """分页列出当前令牌允许访问的项目。"""
        client = current_client()
        projects = [item for item in engine.list_projects()
                    if "*" in client.project_ids or item["id"] in client.project_ids]
        items = [remote.project_view(item) for item in projects[offset:offset + limit]]
        return {"items": items, "total": len(projects), "next_offset": offset + len(items),
                "has_more": offset + len(items) < len(projects)}

    @server.tool(annotations=WRITE)
    async def create_project(
        request_id: RequestId,
        name: Annotated[str, Field(min_length=1, max_length=120)],
        brief: Annotated[str, Field(max_length=20000)] = "",
        genre_id: str = "general",
        framework_id: str = "cocos-web",
        knowledge_paths: Annotated[list[str], Field(max_length=20)] | None = None,
    ) -> dict:
        """创建独立工作区的游戏项目；需要创建权限，重试使用相同 request_id 和参数。"""
        client = current_client()
        with business_errors():
            if not client.can_create_projects:
                raise PermissionError("当前客户端无权创建项目")
            project = engine.create_project(
                name, brief, None, [], genre_id, framework_id, knowledge_paths or [],
                request_id=request_id, request_scope=f"mcp:{client.client_id}",
            )
            return remote.project_view(project)

    @server.tool(annotations=READ_ONLY)
    async def get_project(project_id: Identifier) -> dict:
        """查看项目各阶段状态及当前 run_id，启动下游前必须确认所有前置阶段。"""
        with business_errors():
            return remote.project_view(remote.require_project(project_id, current_client().project_ids))

    @server.tool(annotations={**WRITE, "destructiveHint": True})
    async def start_stage(
        project_id: Identifier, stage: Stage, request_id: RequestId,
        prompt: Annotated[str, Field(max_length=20000)] = "",
        skill_paths: Annotated[list[str], Field(max_length=50)] | None = None,
    ) -> dict:
        """提交指定阶段并立即返回 run_id；重跑上游会使下游确认失效，断线重试须复用 request_id。"""
        client = current_client()
        with business_errors():
            remote.require_project(project_id, client.project_ids)
            return remote.run_view(engine.start_run(
                project_id, stage, prompt, skill_paths or [],
                request_id=request_id, request_scope=f"mcp:{client.client_id}",
            ))

    @server.tool(annotations=READ_ONLY)
    async def get_run(run_id: Identifier) -> dict:
        """查询简短状态、摘要和产物数量；完整事件及文件分别分页读取。"""
        with business_errors():
            return remote.run_view(remote.require_run(run_id, current_client().project_ids))

    @server.tool(annotations=READ_ONLY)
    async def get_run_events(run_id: Identifier, after: Offset = 0, limit: Limit = 20) -> dict:
        """增量读取事件摘要，下一次传入 next_cursor；不会返回完整模型上下文。"""
        with business_errors():
            run = remote.require_run(run_id, current_client().project_ids)
            return remote.event_page(run, after, limit)

    @server.tool(annotations=READ_ONLY)
    async def list_artifacts(run_id: Identifier, offset: Offset = 0, limit: Limit = 20) -> dict:
        """分页列出产物、来源和哈希；下载时仍会再次核验快照完整性。"""
        with business_errors():
            run = remote.require_run(run_id, current_client().project_ids)
            artifacts = run["artifacts"]
            items = [remote.artifact_view(run_id, item, settings.public_url)
                     for item in artifacts[offset:offset + limit]]
            return {"items": items, "total": len(artifacts), "next_offset": offset + len(items),
                    "has_more": offset + len(items) < len(artifacts)}

    @server.tool(annotations=READ_ONLY)
    async def read_artifact(
        run_id: Identifier, artifact_id: Identifier,
        offset: Annotated[int, Field(ge=0, le=10000000)] = 0,
        limit: Annotated[int, Field(ge=1, le=16000)] = 8000,
    ) -> dict:
        """校验并读取产物；文本按字符分页，图片等二进制文件返回受保护的下载地址。"""
        with business_errors():
            artifact, path = remote.artifact_file(run_id, artifact_id, current_client().project_ids)
            result = remote.artifact_view(run_id, artifact, settings.public_url)
            if artifact["kind"] == "text":
                result.update(remote.text_page(path, offset, limit))
            return result

    @server.tool(annotations={**WRITE, "destructiveHint": True})
    async def cancel_run(run_id: Identifier) -> dict:
        """取消实际后台运行；重复取消返回当前状态，不把已完成任务改成已取消。"""
        with business_errors():
            run = remote.require_run(run_id, current_client().project_ids)
            if run["status"] in engine.ACTIVE:
                run = await engine.cancel_run(run_id)
            return remote.run_view(run)

    @server.tool(annotations=WRITE)
    async def resume_run(run_id: Identifier, request_id: RequestId) -> dict:
        """从检查点恢复失败、取消或中断任务；同一次恢复的重试须复用 request_id。"""
        client = current_client()
        with business_errors():
            remote.require_run(run_id, client.project_ids)
            run = engine.resume_run(run_id, request_id=request_id, request_scope=f"mcp:{client.client_id}")
            return remote.run_view(run)

    @server.custom_route("/artifacts/{run_id}/{artifact_id}", methods=["GET"])
    async def download_artifact(request: Request):
        """自定义 HTTP 路由显式认证，不能假定 MCP 工具的认证自动覆盖文件下载。"""
        scheme, _, credential = request.headers.get("authorization", "").partition(" ")
        token = await verifier.verify_token(credential) if scheme.lower() == "bearer" and credential else None
        if token is None:
            return JSONResponse({"error": "需要有效的 Bearer 令牌"}, status_code=401,
                                headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"})
        try:
            client = verifier.clients[token.client_id]
            artifact, path = remote.artifact_file(
                request.path_params["run_id"], request.path_params["artifact_id"], client.project_ids,
            )
            # 下载始终作为附件；HTML、SVG 等产物不在服务自身源下执行。
            return FileResponse(path, filename=artifact["name"], media_type="application/octet-stream",
                                headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
        except PermissionError:
            return JSONResponse({"error": "无权访问该项目"}, status_code=403)
        except FileNotFoundError:
            return JSONResponse({"error": "产物不存在"}, status_code=404)
        except ValueError as error:
            return JSONResponse({"error": str(error)}, status_code=409)

    # 运行状态已经按 run_id 持久化，无需让 MCP 会话承担业务状态或客户端重连语义。
    return server.http_app(path="/", stateless_http=True)
