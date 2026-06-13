"""任务管理路由（占位）。

对应前端各 Agent 左侧的"任务侧栏"：任务的增删改查、与各模块产物的关联。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/ping")
def ping() -> dict:
    """占位接口，确认路由挂载成功。"""
    return {"module": "tasks", "status": "ok"}
