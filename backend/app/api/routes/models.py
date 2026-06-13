"""LLM 模型清单路由。

前端进入 agent 工作台时调一次 /api/models，
拿到可用模型列表后渲染下拉框；后续 LLM 调用必须显式带上 model_id。
"""

from fastapi import APIRouter

from app.models.common import ApiResponse
from app.providers import list_models

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=ApiResponse[list[dict]])
def list_available_models() -> ApiResponse[list[dict]]:
    """返回前端可选模型清单（不含 key 等敏感字段）。"""
    return ApiResponse(data=list_models())
