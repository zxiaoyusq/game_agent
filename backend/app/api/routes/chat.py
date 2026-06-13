"""通用对话路由（占位）。

对应前端 ChatPanel：用户与 Agent 多轮对话，未来按 module / task 分流到不同 provider。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/ping")
def ping() -> dict:
    """占位接口，确认路由挂载成功。"""
    return {"module": "chat", "status": "ok"}
