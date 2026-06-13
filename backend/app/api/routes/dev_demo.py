"""研发 Agent - Demo 生成路由。

两阶段流式接口：
- POST /api/dev/demo/plan      根据需求生成 Plan
- POST /api/dev/demo/generate  按确认后的 Plan 生成 H5 工程并落盘

SSE 协议（每行 data: <json>\\n\\n）：

阶段 1：
    data: {"type":"thinking","text":"..."}
    data: {"type":"plan","steps":[{"title":"...","desc":"..."}]}
    data: {"type":"error","message":"..."}
    data: {"type":"done"}

阶段 2：
    data: {"type":"step_start","index":0}
    data: {"type":"step_thinking","index":0,"text":"..."}
    data: {"type":"step_artifact","index":0,"artifact":{...}}
    data: {"type":"step_done","index":0}
    data: {"type":"step_error","index":0,"message":"..."}
    data: {"type":"done"}

错误处理与策划路由保持一致：异常转 error 事件 + done 事件，HTTP 不抛 500。
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.dev_demo import DemoGenerateReq, DemoPlanReq
from app.providers import LLMConfigError, LLMUnknownModelError
from app.services.dev_demo import stream_generate, stream_plan

router = APIRouter(prefix="/dev/demo", tags=["dev-demo"])
logger = logging.getLogger(__name__)


def _sse_pack(payload: Dict) -> str:
    """SSE 序列化：单行 data + 双换行结束。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _wrap_plan(req: DemoPlanReq) -> AsyncIterator[str]:
    """阶段 1 service → SSE。"""
    try:
        async for ev in stream_plan(req):
            yield _sse_pack(ev)
    except LLMUnknownModelError as e:
        yield _sse_pack({"type": "error", "message": f"未知模型：{e}"})
    except LLMConfigError as e:
        yield _sse_pack({"type": "error", "message": f"LLM 配置错误：{e}"})
    except Exception as e:  # noqa: BLE001
        logger.exception("dev_demo plan failed")
        yield _sse_pack({"type": "error", "message": f"调用失败：{type(e).__name__}: {e}"})
    finally:
        yield _sse_pack({"type": "done"})


async def _wrap_generate(req: DemoGenerateReq) -> AsyncIterator[str]:
    """阶段 2 service → SSE。"""
    try:
        async for ev in stream_generate(req):
            yield _sse_pack(ev)
    except LLMUnknownModelError as e:
        yield _sse_pack({"type": "error", "message": f"未知模型：{e}"})
    except LLMConfigError as e:
        yield _sse_pack({"type": "error", "message": f"LLM 配置错误：{e}"})
    except ValueError as e:
        # 非法 task_id / path 越权等，前端可见的友好错误
        yield _sse_pack({"type": "error", "message": str(e)})
    except Exception as e:  # noqa: BLE001
        logger.exception("dev_demo generate failed")
        yield _sse_pack({"type": "error", "message": f"调用失败：{type(e).__name__}: {e}"})
    finally:
        yield _sse_pack({"type": "done"})


_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


@router.post("/plan")
async def demo_plan(req: DemoPlanReq) -> StreamingResponse:
    """阶段 1：流式生成 Plan。"""
    return StreamingResponse(
        _wrap_plan(req), media_type="text/event-stream", headers=_SSE_HEADERS
    )


@router.post("/generate")
async def demo_generate(req: DemoGenerateReq) -> StreamingResponse:
    """阶段 2：按 Plan 流式生成代码并落盘。"""
    return StreamingResponse(
        _wrap_generate(req), media_type="text/event-stream", headers=_SSE_HEADERS
    )


@router.get("/ping")
def ping() -> dict:
    """占位接口。"""
    return {"module": "dev-demo", "status": "ok"}
