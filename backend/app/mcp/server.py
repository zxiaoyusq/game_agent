"""将业务操作显式注册为 MCP 工具；保持异步入口，共享工作流所在的事件循环。"""

import asyncio
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
from app.services.workflow import engine, model_runtime, pipeline, remote, remote_actions, reference_inputs
from app.services.workflow.templates import ProductionPlan, list_templates as workflow_templates

RequestId = Annotated[str, Field(
    pattern=r"^[A-Za-z0-9_.:-]{1,128}$",
    description="本次操作的唯一标识；重试须复用，新操作须换新标识",
)]
Stage = Literal["prototype", "art", "code", "test"]
ModelProvider = Literal["api-key", "codex-login"]
ModelId = Annotated[str, Field(min_length=1, max_length=200)]
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
        raise ToolError(model_runtime.safe_error(error)) from None


def create_mcp_app(settings: MCPSettings):
    """创建可挂载的 ASGI 应用；自身不启动第二个执行器或维护第二套任务状态。"""
    verifier = ClientTokenVerifier(settings.clients)
    action_lock = asyncio.Lock()
    server = FastMCP(
        "游戏研发工作流", version="1.2.0", auth=verifier, mask_error_details=True,
        instructions=(
            "先查看能力和项目状态，再提交研发阶段。创建、启动、恢复均须提供 request_id；"
            "网络重试复用原标识。手动阶段启动返回run_id；全流程启动返回项目，先get_project取得pipeline.run_id，每3秒查询状态。"
            "完整流程先用get_template读取配置，再create_project传入references与production_plan，确认需求后start_pipeline。"
            "awaiting_input 时把get_run的interrupts展示给用户；问题多时分页get_pending_questions，收到全部回答后answer_questions。"
            "awaiting_confirmation 表示手动阶段等待确认，核对产物后confirm_stage，不能当作 completed；"
            "resume_run只恢复手动阶段，完整流程用resume_pipeline；二者都不能代替人工回答。客户端断开不会取消后台任务。"
            "产物通过 read_artifact 或带相同 Bearer 认证的下载地址读取。"
            f"创建项目默认model_provider=api-key、model_id={model_runtime.DEFAULT_MODEL}；"
            "api-key直接复用服务器backend/.env中已配置的模型凭据，调用方无需提供自己的API Key，也不需要配置本机模型密钥；不要向用户索要模型API Key。"
            "只有显式选择model_provider=codex-login才使用Codex登录；启动阶段省略参数继承项目配置，已有项目及恢复任务保留原模型来源。"
            "Mac本地文件须先通过get_reference_upload_info提供的认证HTTP地址上传，再使用返回的reference_path；不要把本地绝对路径或密钥写入配置。"
        ),
    )

    def current_client() -> MCPClient:
        """身份只取认证上下文，工具参数不能覆盖调用方或授权项目。"""
        token = get_access_token()
        if token is None or token.client_id not in verifier.clients:
            raise ToolError("需要有效的客户端身份")
        return verifier.clients[token.client_id]

    async def project_action(project_id: str, operation: str, request_id: str, **parameters) -> dict:
        """鉴权与串行边界共用，防止同一 MCP 请求并发重试重复恢复或取消。"""
        client = current_client()
        with business_errors():
            remote.require_project(project_id, client.project_ids)
            async with action_lock:
                project = await remote_actions.perform_project_action(
                    project_id, operation, request_id, f"mcp:{client.client_id}", **parameters)
            return remote.project_view(project)

    @server.tool(annotations=READ_ONLY)
    async def get_capabilities(
        model_provider: ModelProvider = "api-key", model_id: ModelId = model_runtime.DEFAULT_MODEL,
    ) -> dict:
        """查看阶段、框架、权限与指定模型来源的配置状态；默认只检查API配置，不发起计费推理或更改任务默认值。"""
        client = current_client()
        with business_errors():
            runtime = await remote.runtime_view(model_provider, model_id)
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
            "model_runtime": runtime,
            "model_providers": [{"id": "api-key", "label": "服务器 API Key"},
                                {"id": "codex-login", "label": "服务器 Codex 登录"}],
            "default_model_selection": {"model_provider": "api-key", "model_id": model_runtime.DEFAULT_MODEL},
            "requires_human_confirmation": True, "automatic_restart_recovery": False,
            "workflow_features": {"templates": True, "production_plans": True, "reference_inputs": True,
                                  "human_input": True, "autonomous_mode": True, "pipeline_control": True,
                                  "manual_stage_confirmation": True, "publishing": True},
            "reference_upload": {"allowed": client.can_create_projects, "max_bytes": reference_inputs.MAX_UPLOAD_BYTES},
            "instructions": "技能索引通过 list_skills 获取，preview_skill_selection 可预览自动选择及能力限制；start_stage 默认自动路由，可补充或排除。创建项目默认model_provider=api-key，直接使用服务器已配置的API Key，调用方无需提供或在本机配置模型密钥，不向用户索要API Key。启动阶段继承项目配置，模型检查不改变项目默认，恢复保留原模型来源、技能选择及版本；同一工作区只允许一个运行。",
        }

    @server.tool(annotations=READ_ONLY)
    async def list_templates(offset: Offset = 0, limit: Limit = 20) -> dict:
        """分页列出可用模板；get_template取得完整四阶段配置后可按需求修改并传给create_project。"""
        current_client()
        with business_errors():
            templates = workflow_templates()
            items = [{key: value[key] for key in ("id", "name", "description", "schema_version", "genre_id", "framework_id", "model_provider", "model_id")}
                     for value in templates[offset:offset + limit]]
            return {"items": items, "total": len(templates), "next_offset": offset + len(items), "has_more": offset + len(items) < len(templates)}

    @server.tool(annotations=READ_ONLY)
    async def get_template(template_id: Annotated[str, Field(min_length=1, max_length=120)]) -> dict:
        """读取完整模板，包含references、美术需求、四阶段提示词及Skill；只读，不启动模型。"""
        current_client()
        with business_errors():
            template = next((item for item in workflow_templates() if item["id"] == template_id), None)
            if template is None:
                raise ValueError("模板不存在，请先调用list_templates")
            return template

    @server.tool(annotations=READ_ONLY)
    async def list_references(query: Annotated[str, Field(max_length=200)] = "", offset: Offset = 0, limit: Limit = 20) -> dict:
        """查询公共参考资料和本客户端上传内容，返回可用于create_project.references的服务端相对路径。"""
        with business_errors():
            return reference_inputs.list_references(engine.ROOT, current_client().client_id, query=query, offset=offset, limit=limit)

    @server.tool(annotations=READ_ONLY)
    async def get_reference_upload_info() -> dict:
        """取得附件上传方法和限制；文件字节走认证HTTP，不需要模型生成base64。"""
        client = current_client()
        if not client.can_create_projects:
            raise ToolError("当前客户端没有上传项目参考资料的权限")
        return {"url": f"{settings.public_url.rstrip('/')}/references/upload", "method": "POST",
                "query_parameters": ["filename", "request_id"], "body": "本机文件的原始字节，Content-Type: application/octet-stream",
                "authentication": "携带与 MCP 相同的 Authorization: Bearer 令牌",
                "max_bytes": reference_inputs.MAX_UPLOAD_BYTES,
                "max_text_bytes": reference_inputs.MAX_TEXT_BYTES,
                "max_image_bytes": reference_inputs.MAX_IMAGE_BYTES,
                "max_client_bytes": reference_inputs.MAX_CLIENT_BYTES,
                "allowed_suffixes": sorted(reference_inputs.ALLOWED_UPLOAD_SUFFIXES),
                "result_usage": "返回的reference_path填入create_project.references；网络重试复用同一request_id和文件"}

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
        brief: Annotated[str | dict[str, str], Field(description="游戏需求正文，或模板的结构化brief对象")] = "",
        genre_id: str = "general",
        framework_id: str = "cocos-web",
        knowledge_paths: Annotated[list[str], Field(max_length=100)] | None = None,
        model_provider: ModelProvider = "api-key",
        model_id: ModelId = model_runtime.DEFAULT_MODEL,
        references: Annotated[list[str], Field(max_length=100)] | None = None,
        production_plan: ProductionPlan | None = None,
    ) -> dict:
        """创建独立工作区的游戏项目；默认api-key直接使用服务器已配置的模型凭据，调用方无需提供API Key；Codex登录须显式选择codex-login；重试使用相同request_id和原模型参数。"""
        client = current_client()
        with business_errors():
            if not client.can_create_projects:
                raise PermissionError("当前客户端无权创建项目")
            if ((isinstance(brief, str) and len(brief) > 20000)
                    or (isinstance(brief, dict) and (len(brief) > 20 or any(len(value) > 12000 for value in brief.values())))):
                raise ValueError("项目需求过长；正文最多20000字，结构化字段最多20项、每项12000字")
            reference_paths = reference_inputs.validate_references(engine.ROOT, client.client_id, references or [])
            project = engine.create_project(
                name, brief, None, reference_paths, genre_id, framework_id, knowledge_paths or [],
                request_id=request_id, request_scope=f"mcp:{client.client_id}",
                model_provider=model_provider, model_id=model_id,
                production_plan=production_plan.model_dump() if production_plan is not None else None,
            )
            return remote.project_view(project)

    @server.tool(annotations=WRITE)
    async def start_pipeline(project_id: Identifier, request_id: RequestId) -> dict:
        """用户确认已保存的需求、模型、自主决策和发布选项后开始全流程；重试使用原request_id，不逐阶段索取输入。"""
        return await project_action(project_id, "start_pipeline", request_id)

    @server.tool(annotations=WRITE)
    async def resume_pipeline(project_id: Identifier, request_id: RequestId) -> dict:
        """继续失败、取消或重启中断的全流程；已完成阶段保留，不能用来回答awaiting_input的问题。"""
        return await project_action(project_id, "resume_pipeline", request_id)

    @server.tool(annotations={**WRITE, "destructiveHint": True})
    async def cancel_pipeline(project_id: Identifier, request_id: RequestId) -> dict:
        """取消全流程及当前实际运行，等待用户补充时也可取消；相同request_id重试不影响之后新恢复的运行。"""
        return await project_action(project_id, "cancel_pipeline", request_id)

    @server.tool(annotations=WRITE)
    async def confirm_stage(project_id: Identifier, stage: Stage, run_id: Identifier, request_id: RequestId,
                            note: Annotated[str, Field(max_length=2000)] = "") -> dict:
        """仅用于用户确认手动阶段的真实产物；必须绑定当前run_id，完整流程按已确认计划自动验收。"""
        return await project_action(project_id, "confirm_stage", request_id, stage=stage, run_id=run_id, note=note)

    @server.tool(annotations=WRITE)
    async def publish_project(project_id: Identifier, slug: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")],
                              request_id: RequestId) -> dict:
        """用户授权后将通过验收的当前构建发布到独立试玩路径；源码、构建字节和阶段确认仍完整校验。"""
        return await project_action(project_id, "publish_project", request_id, slug=slug)

    @server.tool(annotations=READ_ONLY)
    async def get_project(project_id: Identifier) -> dict:
        """查看各阶段、pipeline.run_id和publication.url；全流程按计划自动衔接，手动阶段确认后才能启动下游。"""
        with business_errors():
            return remote.project_view(remote.require_project(project_id, current_client().project_ids))

    @server.tool(annotations=READ_ONLY)
    async def preview_skill_selection(
        project_id: Identifier, stage: Stage,
        prompt: Annotated[str, Field(max_length=20000)] = "",
        skill_paths: Annotated[list[str], Field(max_length=50)] | None = None,
        skill_mode: Literal["auto", "manual"] = "auto",
        excluded_skill_paths: Annotated[list[str], Field(max_length=50)] | None = None,
    ) -> dict:
        """只读预览本项目当前阶段的技能选择与原因，不创建运行或改写确认状态。"""
        with business_errors():
            remote.require_project(project_id, current_client().project_ids)
            return engine.preview_skill_selection(project_id, stage, prompt, skill_paths,
                                                  skill_mode=skill_mode, excluded_skill_paths=excluded_skill_paths)

    @server.tool(annotations={**WRITE, "destructiveHint": True})
    async def start_stage(
        project_id: Identifier, stage: Stage, request_id: RequestId,
        prompt: Annotated[str, Field(max_length=20000)] = "",
        skill_paths: Annotated[list[str], Field(max_length=50)] | None = None,
        skill_mode: Literal["auto", "manual"] = "auto",
        excluded_skill_paths: Annotated[list[str], Field(max_length=50)] | None = None,
        model_provider: ModelProvider | None = None,
        model_id: ModelId | None = None,
    ) -> dict:
        """提交阶段并返回run_id；省略模型参数继承项目来源，显式参数只作用于本次运行；重跑上游使下游确认失效，断线重试复用request_id。"""
        client = current_client()
        with business_errors():
            remote.require_project(project_id, client.project_ids)
            return remote.run_view(engine.start_run(
                project_id, stage, prompt, skill_paths,
                skill_mode=skill_mode, excluded_skill_paths=excluded_skill_paths,
                request_id=request_id, request_scope=f"mcp:{client.client_id}",
                model_provider=model_provider, model_id=model_id,
            ))

    @server.tool(annotations=READ_ONLY)
    async def get_run(run_id: Identifier) -> dict:
        """查询进度、产物及待补充问题；awaiting_input时展示interrupts并调用answer_questions，问题多时get_pending_questions分页取全。"""
        with business_errors():
            return remote.run_view(remote.require_run(run_id, current_client().project_ids))

    @server.tool(annotations=READ_ONLY)
    async def get_pending_questions(run_id: Identifier, offset: Offset = 0, limit: Limit = 20) -> dict:
        """分页读取当前待回答的问题；回答时按问题ID一次提交全部答案，已回答或旧运行的问题不能重复提交。"""
        with business_errors():
            return remote.interrupt_page(remote.require_run(run_id, current_client().project_ids), offset, limit)

    @server.tool(annotations=WRITE)
    async def answer_questions(run_id: Identifier, request_id: RequestId,
                               answers: Annotated[dict[str, Annotated[str, Field(min_length=1, max_length=12000)]], Field(min_length=1, max_length=100)]) -> dict:
        """将用户对全部待补充问题的回答按ID提交，继续原检查点；答案不能伪称用户确认，断线重试复用request_id与原答案。"""
        client = current_client()
        with business_errors():
            remote.require_run(run_id, client.project_ids)
            result = pipeline.answer_run(run_id, answers, request_id=request_id, request_scope=f"mcp:{client.client_id}")
            return remote.run_view(result)

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
            if run["status"] in engine.ACTIVE | {"awaiting_input"}:
                project = engine.load("projects", run["project_id"])
                if run.get("pipeline_id") and project.get("pipeline", {}).get("status") in pipeline.OWNED:
                    await pipeline.cancel_pipeline(project["id"])
                    run = engine.load("runs", run_id)
                else:
                    run = await engine.cancel_run(run_id)
            return remote.run_view(run)

    @server.custom_route("/references/upload", methods=["POST"])
    async def upload_reference(request: Request):
        """上传与下载一样单独认证；流式读取限制内存，客户端不能指定服务端落盘目录。"""
        scheme, _, credential = request.headers.get("authorization", "").partition(" ")
        token = await verifier.verify_token(credential) if scheme.lower() == "bearer" and credential else None
        if token is None:
            return JSONResponse({"error": "需要有效的 Bearer 令牌"}, status_code=401,
                                headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"})
        client = verifier.clients[token.client_id]
        if not client.can_create_projects:
            return JSONResponse({"error": "当前客户端没有上传项目参考资料的权限"}, status_code=403)
        try:
            content_length = request.headers.get("content-length")
            if content_length is not None and int(content_length) > reference_inputs.MAX_UPLOAD_BYTES:
                return JSONResponse({"error": "参考文件超过64MB限制"}, status_code=413)
            result = await reference_inputs.upload_reference(
                engine.ROOT, client.client_id, request.query_params.get("filename", ""),
                request.query_params.get("request_id", ""), request.stream())
            return JSONResponse(result, headers={"Cache-Control": "no-store"})
        except PermissionError as error:
            return JSONResponse({"error": model_runtime.safe_error(error)}, status_code=403)
        except (ValueError, FileNotFoundError) as error:
            return JSONResponse({"error": model_runtime.safe_error(error)}, status_code=409)

    @server.tool(annotations=WRITE)
    async def resume_run(run_id: Identifier, request_id: RequestId) -> dict:
        """从检查点恢复失败、取消或中断的手动阶段；完整流程用resume_pipeline，待补充问题用answer_questions；重试复用request_id。"""
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
