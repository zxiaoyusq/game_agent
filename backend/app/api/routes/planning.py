"""策划 Agent 路由。

当前阶段只实现了一条端到端的流式接口：
    POST /api/planning/stream
入参示例：
    {
      "user_input":     "我想在春节活动里加入一个家族 PK 玩法",
      "model_id":       "claude-opus-4-7",
      "sub_module":     "gameplay",          # 当前只接了 gameplay，其它先复用其 prompt
      "project_brief":  "...",                # 来自 InputPanel 的项目设定
      "kb_refs":        ["art:images:abc"]    # 已选知识库的三段式 key 列表
    }

知识库的实际读取（含图片 base64）统一由 services/kb_context 完成；
本路由只负责入参校验 + SSE 包装。

返回 SSE：
    data: {"delta":"你"}
    data: {"delta":"好"}
    ...
    data: {"done": true}
出错时：
    data: {"error":"..."}
    data: {"done": true}
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.providers import LLMConfigError, LLMUnknownModelError
from app.services.planning import stream_planning

router = APIRouter(prefix="/planning", tags=["planning"])

logger = logging.getLogger(__name__)


# ---- 请求 schema ----------------------------------------------------------

class PlanningStreamReq(BaseModel):
    """策划 Agent 流式请求体。"""

    user_input: str = Field(..., min_length=1, description="用户最新一条消息")
    model_id: str = Field(..., description="前端选择的模型 id，需在后端白名单内")
    sub_module: str = Field("gameplay", description="子模块 id，当前接入 gameplay")
    project_brief: str = Field("", description="项目设定（左侧 InputPanel 文本）")
    kb_refs: List[str] = Field(
        default_factory=list,
        description="已选知识库三段式 key 列表，例如 ['art:images:abc']",
    )


# ---- SSE 包装 -------------------------------------------------------------

def _sse_pack(payload: dict) -> str:
    """把一条事件按 SSE 协议序列化。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _sse_stream(req: PlanningStreamReq) -> AsyncIterator[str]:
    """把 service 层的 token 流封装成 SSE 字符串迭代器。

    出错时不抛 HTTP 异常，而是用一个 error 事件 + done 事件优雅收尾，
    前端 EventSource / fetch reader 才能拿到错误展示给用户。
    """
    try:
        async for delta in stream_planning(
            user_input=req.user_input,
            model_id=req.model_id,
            project_brief=req.project_brief,
            kb_refs=req.kb_refs,
            sub_module=req.sub_module,
        ):
            yield _sse_pack({"delta": delta})
    except LLMUnknownModelError as e:
        yield _sse_pack({"error": f"未知模型：{e}"})
    except LLMConfigError as e:
        yield _sse_pack({"error": f"LLM 配置错误：{e}"})
    except Exception as e:
        # 兜底：记录详细日志，但只把简短错误返回给前端，避免泄漏内部细节
        logger.exception("planning stream failed")
        yield _sse_pack({"error": f"调用失败：{type(e).__name__}: {e}"})
    finally:
        # 不论正常结束还是异常，都发一条 done 让前端关闭流
        yield _sse_pack({"done": True})


@router.post("/stream")
async def planning_stream(req: PlanningStreamReq) -> StreamingResponse:
    """策划 Agent 流式生成入口。"""
    return StreamingResponse(
        _sse_stream(req),
        media_type="text/event-stream",
        headers={
            # 关闭中间代理 / nginx 的缓冲，确保 token 即时下发
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/ping")
def ping() -> dict:
    """占位接口，确认路由挂载成功。"""
    return {"module": "planning", "status": "ok"}
