"""工作流模型选择与API调用证据；API模式从不回退到Codex登录。"""

from collections.abc import Callable

from langchain_core.callbacks import BaseCallbackHandler

from app import config
from app.providers import get_chat_model
from app.services.workflow.codex_model import inspect_runtime as inspect_codex_runtime

DEFAULT_MODEL = "gpt-6.1-sol"


def validate_selection(provider: str, model_id: str) -> dict:
    """模型标识和身份来源都显式冻结，不允许把失败请求替换成另一种身份。"""
    if provider not in {"api-key", "codex-login"}:
        raise ValueError("模型来源必须是 API Key 网关或 Codex 登录")
    if provider == "codex-login" and model_id != DEFAULT_MODEL:
        raise ValueError("历史 Codex 适配器仅支持 gpt-6.1-sol")
    if provider == "api-key" and model_id not in config.LLM_MODEL_INDEX:
        raise ValueError("模型不在工程API白名单内")
    if provider == "api-key" and config.LLM_OPENAI_API not in {"responses", "chat-completions"}:
        raise ValueError("LLM_OPENAI_API 必须为 responses 或 chat-completions")
    return {"model_provider": provider, "model_id": model_id}


def capabilities() -> dict:
    """区分已接入工具与已配置服务，不把工具名称当作外部调用成功。"""
    image_ready = (bool(config.IMAGE_API_BASE_URL and config.IMAGE_API_KEY) if config.IMAGE_PROVIDER == "openai"
                   else bool(config.AZURE_IMAGE_ENDPOINT and config.AZURE_IMAGE_API_KEY) if config.IMAGE_PROVIDER == "azure" else False)
    return {"reference_archives": True, "web_validation": True, "publishing": True,
            "image_generation": image_ready}


async def inspect_runtime(provider: str = "api-key", model_id: str = DEFAULT_MODEL) -> dict:
    """页面查询只检查配置，不产生计费推理；真实连通性由运行事件证明。"""
    validate_selection(provider, model_id)
    if provider == "codex-login":
        result = await inspect_codex_runtime()
        return {**result, "configured": result["available"], "connection_checked": True,
                "models": [item for item in result.get("models", []) if item["id"] == DEFAULT_MODEL],
                "capabilities": capabilities()}
    spec = config.LLM_MODEL_INDEX[model_id]
    api = spec.get("openai_api", config.LLM_OPENAI_API)
    configured = bool(config.LLM_API_KEY and config.get_llm_base_url(spec["provider"]))
    result = {"provider": "api-key", "model": model_id, "upstream_model": spec.get("upstream_model", model_id), "framework": "deepagents",
              "configured": configured, "available": configured, "connection_checked": False,
              "transport": f"langchain {spec['provider']} " + (api if spec['provider'] == 'openai' else 'API'), "capabilities": capabilities(),
              "models": [{"id": item["id"], "name": item["label"]} for item in config.LLM_AVAILABLE_MODELS]}
    if not configured:
        result["error"] = "尚未配置服务器 backend/.env 的 LLM_API_KEY 和 LLM_GATEWAY_URL（或对应 provider 专用地址）"
    return result


def safe_error(error: Exception) -> str:
    """事件可展示错误原因，但不能将上游回显的服务器凭据写入运行记录。"""
    message = str(error)
    for name in ("LLM_API_KEY", "IMAGE_API_KEY", "AZURE_IMAGE_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"):
        secret = getattr(config, name, "")
        if secret:
            message = message.replace(secret, "[凭据已隐藏]")
    return message[:3000]


class ModelEvents(BaseCallbackHandler):
    """保留原生AIMessage/tool_calls，记录API来源、响应模型和实际token用量。"""

    def __init__(self, model_id: str, emit: Callable):
        self.model_id = model_id
        self.emit = emit

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        self.emit("model_started", "开始API Key模型推理", {
            "model": self.model_id, "provider": "api-key", "call_id": str(run_id),
            "messages": sum(len(batch) for batch in messages),
        })

    def on_llm_end(self, response, *, run_id, **kwargs):
        for generations in response.generations:
            for generation in generations:
                message = getattr(generation, "message", None)
                if message is None:
                    continue
                metadata = getattr(message, "response_metadata", {})
                self.emit("model_completed", "API Key真实推理完成", {
                    "model": self.model_id, "provider": "api-key", "call_id": str(run_id),
                    "response_model": metadata.get("model_name") or metadata.get("model"),
                    "response_id": getattr(message, "id", None),
                    "content": message.content, "tool_calls": getattr(message, "tool_calls", []),
                    "usage": getattr(message, "usage_metadata", None) or metadata.get("token_usage", {}),
                })

    def on_llm_error(self, error, *, run_id, **kwargs):
        self.emit("model_error", "API模型调用失败，没有切换身份或模型", {
            "model": self.model_id, "provider": "api-key", "call_id": str(run_id), "error": safe_error(error),
        })


def create_api_model(model_id: str, emit: Callable):
    """复用工程已有provider工厂，每次运行单独绑定事件回调，避免缓存串写日志。"""
    validate_selection("api-key", model_id)
    spec = config.LLM_MODEL_INDEX[model_id]
    # 生成完整规格或代码文件可能耗时数分钟，后台任务可取消，避免四分钟读超时重复计费请求。
    options = {"timeout": 600, "max_retries": 1}
    if spec["provider"] == "openai":
        # 单个兼容模型的协议优先于全局设置，GPT 和 Gemini 可以在同一网关并存。
        api = spec.get("openai_api", config.LLM_OPENAI_API)
        options.update(stream_usage=False, use_responses_api=api == "responses")
        if api == "responses":
            options.update(store=False, use_previous_response_id=False, include=("reasoning.encrypted_content",))
    model = get_chat_model(model_id, **options)
    return model.model_copy(update={"callbacks": [ModelEvents(model_id, emit)]})
