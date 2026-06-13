"""健康检查路由：用于前端启动时确认后端可用。"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """简单返回服务存活状态。"""
    return {"status": "ok"}
