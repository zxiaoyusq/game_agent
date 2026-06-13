"""通用响应 / 请求模型。"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应外壳：success 标记 + 业务数据 + 错误信息。"""

    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
