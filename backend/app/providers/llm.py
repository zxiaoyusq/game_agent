"""LLM Provider：统一走 langchain 的 init_chat_model 入口。

设计要点：
- 模型必须由前端显式指定 model_id，且要在 LLM_MODEL_INDEX 白名单内；
- 同一个 (model_id, 关键参数) 的 chat model 会被缓存，避免每次请求都重新构造 client；
- base_url / api_key 来自 .env 中的统一网关配置，所有 provider 共用。

典型用法：
    from app.providers import get_chat_model
    from langchain_core.messages import HumanMessage

    model = get_chat_model("claude-opus-4-7", temperature=0)
    resp = model.invoke([HumanMessage(content="hi")])
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain.chat_models import init_chat_model

from app.config import (
    LLM_API_KEY,
    LLM_GATEWAY_URL,
    LLM_MODEL_INDEX,
    get_llm_base_url,
)
from app.providers.base import LLMConfigError, LLMUnknownModelError


def _resolve_spec(model_id: str) -> dict:
    """从白名单里取出完整模型 spec，未知 id 直接抛错。"""
    if not model_id:
        raise LLMUnknownModelError("model_id 必传")
    spec = LLM_MODEL_INDEX.get(model_id)
    if spec is None:
        allowed = ", ".join(LLM_MODEL_INDEX.keys()) or "（白名单为空，请检查 config.LLM_AVAILABLE_MODELS）"
        raise LLMUnknownModelError(f"未知模型 id：{model_id}；可选：{allowed}")
    return spec


def _check_credentials() -> None:
    """启动时不强制 key 必填（方便先跑骨架），真正调用前再校验。"""
    if not LLM_API_KEY:
        raise LLMConfigError(
            "未配置 LLM_API_KEY；请在 backend/.env 中填写后再调用 LLM 接口"
        )
    if not LLM_GATEWAY_URL:
        raise LLMConfigError(
            "未配置 LLM_GATEWAY_URL；请在 backend/.env 中填写后再调用 LLM 接口"
        )


# lru_cache key 必须是 hashable，所以把 overrides 转成 frozenset(items()) 再传入
@lru_cache(maxsize=32)
def _build_cached(model_id: str, override_items: frozenset) -> Any:
    """真正构造 chat model 的内部入口（带缓存）。

    overrides 通过 frozenset 形式传入，避免 dict 不可哈希的问题。
    """
    spec = _resolve_spec(model_id)
    _check_credentials()

    # 这里把网关 URL 与 key 显式传入，覆盖 langchain 默认从官方 base_url 走的行为
    # 不同 provider 的 base_url 可能不一样（例如 OpenAI 协议要求 /v1 前缀），
    # 通过 get_llm_base_url 按 provider 单独解析。
    provider = spec["provider"]
    kwargs: dict[str, Any] = {
        "model": model_id,
        "model_provider": provider,
        "api_key": LLM_API_KEY,
        "base_url": get_llm_base_url(provider),
    }
    # 用户层 overrides 优先级最高，可覆盖默认 temperature 之类
    kwargs.update(dict(override_items))
    return init_chat_model(**kwargs)


def get_chat_model(model_id: str, **overrides: Any) -> Any:
    """获取一个 langchain BaseChatModel 实例。

    Args:
        model_id: 必填。前端选择的模型 id，必须在 LLM_MODEL_INDEX 白名单内。
        **overrides: 透传给 init_chat_model 的额外参数（temperature、max_tokens 等）。

    Raises:
        LLMUnknownModelError: model_id 不在白名单
        LLMConfigError: 缺 LLM_API_KEY / LLM_GATEWAY_URL
    """
    # frozenset(items()) 保证缓存命中：相同参数命中同一个客户端实例
    return _build_cached(model_id, frozenset(overrides.items()))


def list_models() -> list[dict]:
    """列出前端可选模型清单（不含 key 等敏感字段）。"""
    return [
        {"id": m["id"], "provider": m["provider"], "label": m["label"], "tags": m.get("tags", [])}
        for m in LLM_MODEL_INDEX.values()
    ]
