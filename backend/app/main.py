"""FastAPI 应用入口。

启动方式（在 backend/ 目录下，conda activate base 后）：
    uvicorn app.main:app --reload --port 8003
"""

# 务必在 import app.config 之前加载 .env，否则 config 读到的就是默认空值
from dotenv import load_dotenv

load_dotenv()  # 默认从当前工作目录的 .env 加载；启动命令一般在 backend/ 下

import os
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import BASE_DIR, CORS_ALLOW_ORIGINS
from app.api.routes import art, chat, dev_demo, health, knowledge, models, planning, tasks, workflow
from app.services.skill_library import import_skill_library
from app.services.production_library import import_production_library
from app.services.workflow.engine import recover_interrupted_runs, shutdown_workers


def create_app() -> FastAPI:
    """组装 REST 与可选 MCP，共用一个工作流执行器和应用生命周期。"""
    mcp_app = None
    config_path = os.getenv("GAME_MCP_CONFIG", "").strip()
    if config_path:
        from app.mcp.auth import load_settings
        from app.mcp.server import create_mcp_app

        path = Path(config_path).expanduser()
        settings = load_settings(path if path.is_absolute() else BASE_DIR / path)
        mcp_app = create_mcp_app(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """保留资料导入和中断恢复；MCP 必须显式启动，退出时先清理真实任务。"""
        import_skill_library()
        import_production_library()
        recover_interrupted_runs()
        async with AsyncExitStack() as stack:
            if mcp_app is not None:
                await stack.enter_async_context(mcp_app.lifespan(app))
            try:
                yield
            finally:
                await shutdown_workers()

    app = FastAPI(
        title="Game Agent Backend",
        description="游戏 AI Agent 系统后端：策划 / 美术 / 知识库 / 任务",
        version="0.1.0", lifespan=lifespan,
    )
    # 跨域只服务现有工作台；MCP 使用显式 Bearer 认证，没有 OAuth 浏览器流程。
    app.add_middleware(
        CORSMiddleware, allow_origins=CORS_ALLOW_ORIGINS, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )
    for router in (health.router, models.router, planning.router, art.router, knowledge.router,
                   tasks.router, chat.router, dev_demo.router, workflow.router):
        app.include_router(router, prefix="/api")
    if mcp_app is not None:
        app.mount("/mcp", mcp_app)

    @app.get("/")
    def root() -> dict:
        """根路径返回服务信息，便于浏览器确认服务存活。"""
        return {"name": "Game Agent Backend", "version": "0.1.0", "docs": "/docs"}

    return app


app = create_app()
