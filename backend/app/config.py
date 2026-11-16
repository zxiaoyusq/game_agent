"""应用路径、知识库分类与模型服务配置，密钥从环境变量读取。"""

import os
from pathlib import Path

# 项目根路径（backend/）
BASE_DIR = Path(__file__).resolve().parent.parent

# 运行时数据根目录，约定不入版本控制
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"

# 知识库模块 -> 允许的子分类。子分类对应物理子目录，
# 例如 art.images 落到 data/knowledge/art/images/。
# 与前端 frontend/src/data/knowledgeBase.js 中的 KB_MODULES 一致。
KB_MODULE_CATEGORIES: dict[str, list[str]] = {
    "selection": ["docs"],
    "planning": ["docs"],
    "art": ["docs", "images", "videos", "motion", "facial"],
    "dev": ["docs"],
    "ops": ["docs"],
    "skill": ["docs"],
    "genre": ["docs"],
    "framework": ["docs"],
}

# 单文件上传大小上限（字节）。默认 50MB，可通过环境变量调整。
KB_MAX_UPLOAD_BYTES = int(os.getenv("KB_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))

# 同步确保所有知识库子分类目录存在（即便用户未提前手动建好）
for _module, _cats in KB_MODULE_CATEGORIES.items():
    for _cat in _cats:
        (KNOWLEDGE_DIR / _module / _cat).mkdir(parents=True, exist_ok=True)

# CORS 允许的前端来源；本地开发时 Vite 默认 5173/5174 都放行
CORS_ALLOW_ORIGINS = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://pagent.ahagamecenter.com,http://pagent.ahagamecenter.com:24681",
).split(",")

# ---- LLM 配置 -------------------------------------------------------------
# 统一走中转网关：不同 provider 共享同一份 key，base_url 在大多数网关下也共享。
# 但部分网关对不同 provider 转发到不同子路径（例如 OpenAI 兼容协议要求 /v1）；
# 因此允许通过 LLM_GATEWAY_URL_<PROVIDER> 单独覆盖某个 provider 的 base_url。
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
# 新版OpenAI推理模型的原生工具调用使用Responses；旧网关可显式选chat-completions。
LLM_OPENAI_API = os.getenv("LLM_OPENAI_API", "responses")


def get_llm_base_url(provider: str) -> str:
    """按 provider 解析最终 base_url：先看 provider 专用变量，找不到再回退全局。"""
    specific = os.getenv(f"LLM_GATEWAY_URL_{provider.upper()}", "")
    return specific or LLM_GATEWAY_URL

# 同步到 langchain 各 provider 期望的官方环境变量名，避免再去显式 setenv
# 仅当用户没有单独配置 ANTHROPIC_API_KEY / DEEPSEEK_API_KEY 时才用 LLM_API_KEY 兜底
if LLM_API_KEY:
    os.environ.setdefault("ANTHROPIC_API_KEY", LLM_API_KEY)
    os.environ.setdefault("DEEPSEEK_API_KEY", LLM_API_KEY)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# ---- Azure OpenAI 图片生成 -------------------------------------------------
# 工作流生图工具可使用独立的 Azure OpenAI 部署，与文本模型网关分开管理。
AZURE_IMAGE_ENDPOINT = os.getenv("AZURE_IMAGE_ENDPOINT", "").rstrip("/")
AZURE_IMAGE_DEPLOYMENT = os.getenv("AZURE_IMAGE_DEPLOYMENT", "gpt-image-2")
AZURE_IMAGE_API_VERSION = os.getenv("AZURE_IMAGE_API_VERSION", "2025-04-01-preview")
AZURE_IMAGE_API_KEY = os.getenv("AZURE_IMAGE_API_KEY", "")

# 图片服务显式选择协议；OpenAI兼容网关可复用已授权的工程Key与API基址。
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "azure")
IMAGE_API_BASE_URL = os.getenv("IMAGE_API_BASE_URL", get_llm_base_url("openai")).rstrip("/")
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY", LLM_API_KEY)
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-2")


# 前端可选模型白名单。
# 前端调用 LLM 时必须显式传入其中之一的 id；后端校验通过才会构造 chat model。
# 字段含义：
#   id        -> 路由层与前端协议中的稳定标识
#   upstream_model -> 可选的网关实际模型名称；未指定时与 id 相同
#   provider  -> langchain 的 model_provider 取值
#   openai_api -> 可选的 OpenAI 兼容协议覆盖，避免其他厂商模型误用 Responses
#   label     -> 前端下拉框展示用
#   tags      -> 前端可基于 tag 给模型加图标 / 提示
LLM_AVAILABLE_MODELS: list[dict] = [
    {
        "id": "gpt-6.1-sol",
        "provider": "openai",
        "label": "GPT 6.1 Sol · API Key 网关",
        "tags": ["工具调用", "代码"],
    },
    {
        "id": "claude-opus-5-5",
        "upstream_model": "claude-opus-5-5-20260820",
        "provider": "anthropic",
        "label": "Claude Opus 5.5",
        "tags": ["推理", "代码"],
    },
    {
        "id": "deepseek-v4-pro",
        "provider": "deepseek",
        "label": "DeepSeek v4 Pro",
        "tags": ["低成本", "中文"],
    },
    {
        "id": "deepseek-v4.1-flash",
        "provider": "deepseek",
        "label": "DeepSeek v4.1 Flash",
        "tags": ["工具调用", "代码"],
    },
    {
        "id": "gemini-3.8-flash",
        "provider": "openai",
        "openai_api": "chat-completions",
        "label": "Gemini 3.8 Flash",
        "tags": ["工具调用", "多模态"],
    },
]

# id -> 完整 spec，便于路由层 O(1) 查找
LLM_MODEL_INDEX = {m["id"]: m for m in LLM_AVAILABLE_MODELS}
