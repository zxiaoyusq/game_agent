"""FastAPI 应用入口。

启动方式（在 backend/ 目录下，conda activate 313 后）：
    uvicorn app.main:app --reload --port 8000
"""

# 务必在 import app.config 之前加载 .env，否则 config 读到的就是默认空值
from dotenv import load_dotenv

load_dotenv()  # 默认从当前工作目录的 .env 加载；启动命令一般在 backend/ 下

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ALLOW_ORIGINS
from app.api.routes import art, chat, dev_demo, health, knowledge, models, planning, tasks

# 全局 FastAPI 应用实例
app = FastAPI(
    title="Game Agent Backend",
    description="游戏 AI Agent 系统后端：策划 / 美术 / 知识库 / 任务",
    version="0.1.0",
)

# 跨域：允许 Vite 开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 统一挂载 /api 前缀，便于前端通过 /api/xxx 访问
API_PREFIX = "/api"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(models.router, prefix=API_PREFIX)
app.include_router(planning.router, prefix=API_PREFIX)
app.include_router(art.router, prefix=API_PREFIX)
app.include_router(knowledge.router, prefix=API_PREFIX)
app.include_router(tasks.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(dev_demo.router, prefix=API_PREFIX)


@app.get("/")
def root() -> dict:
    """根路径，返回简单提示，便于浏览器直接访问确认服务存活。"""
    return {
        "name": "Game Agent Backend",
        "version": "0.1.0",
        "docs": "/docs",
    }
