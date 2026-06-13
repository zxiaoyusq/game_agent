"""应用全局配置。

后续接入 LLM provider 时，把对应 API key 加到 .env，并在这里通过 os.getenv 读取。
"""

import os
from pathlib import Path

# 项目根路径（backend/）
BASE_DIR = Path(__file__).resolve().parent.parent

# 运行时数据根目录，约定不入版本控制
DATA_DIR = BASE_DIR / "data"
TASKS_DIR = DATA_DIR / "tasks"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
LOGS_DIR = DATA_DIR / "logs"
# 研发 Agent - Demo 生成的 H5 工程落盘根目录，
# 每个任务一个子目录：data/dev_demo/<task_id>/
DEV_DEMO_DIR = DATA_DIR / "dev_demo"

# 知识库模块 -> 允许的子分类。子分类对应物理子目录，
# 例如 art.images 落到 data/knowledge/art/images/。
# 与前端 frontend/src/data/knowledgeBase.js 中的 KB_MODULES 一致。
KB_MODULE_CATEGORIES: dict[str, list[str]] = {
    "planning": ["docs"],
    "art": ["docs", "images", "videos", "motion", "facial"],
    "dev": ["docs"],
    "ops": ["docs"],
}

# 单文件上传大小上限（字节）。默认 50MB，可通过环境变量调整。
KB_MAX_UPLOAD_BYTES = int(os.getenv("KB_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))

# 启动时确保目录存在，避免后续读写报 FileNotFoundError
for _dir in (TASKS_DIR, KNOWLEDGE_DIR, LOGS_DIR, DEV_DEMO_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# 同步确保所有知识库子分类目录存在（即便用户未提前手动建好）
for _module, _cats in KB_MODULE_CATEGORIES.items():
    for _cat in _cats:
        (KNOWLEDGE_DIR / _module / _cat).mkdir(parents=True, exist_ok=True)

# CORS 允许的前端来源；本地开发时 Vite 默认 5173/5174 都放行
CORS_ALLOW_ORIGINS = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5173,http://localhost:5174",
).split(",")

# ---- LLM 配置 -------------------------------------------------------------
# 统一走中转网关：不同 provider 共享同一份 key，base_url 在大多数网关下也共享。
# 但部分网关对不同 provider 转发到不同子路径（例如 OpenAI 兼容协议要求 /v1）；
# 因此允许通过 LLM_GATEWAY_URL_<PROVIDER> 单独覆盖某个 provider 的 base_url。
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")


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
# 美术 Agent 的「AI 图片生成」走独立的 Azure OpenAI 部署，
# 与上面的 LLM 网关分开管理。
AZURE_IMAGE_ENDPOINT = os.getenv("AZURE_IMAGE_ENDPOINT", "").rstrip("/")
AZURE_IMAGE_DEPLOYMENT = os.getenv("AZURE_IMAGE_DEPLOYMENT", "gpt-image-2")
AZURE_IMAGE_API_VERSION = os.getenv("AZURE_IMAGE_API_VERSION", "2025-04-01-preview")
AZURE_IMAGE_API_KEY = os.getenv("AZURE_IMAGE_API_KEY", "")


# 前端可选模型白名单。
# 前端调用 LLM 时必须显式传入其中之一的 id；后端校验通过才会构造 chat model。
# 字段含义：
#   id        -> 路由层与前端协议中的稳定标识，传入 init_chat_model 的 model 参数
#   provider  -> langchain 的 model_provider 取值
#   label     -> 前端下拉框展示用
#   tags      -> 前端可基于 tag 给模型加图标 / 提示
LLM_AVAILABLE_MODELS: list[dict] = [
    {
        "id": "claude-opus-4-7",
        "provider": "anthropic",
        "label": "Claude Opus 4.7",
        "tags": ["综合最强", "推理"],
    },
    {
        "id": "deepseek-v4-pro",
        "provider": "deepseek",
        "label": "DeepSeek v4 Pro",
        "tags": ["低成本", "中文"],
    },
]

# id -> 完整 spec，便于路由层 O(1) 查找
LLM_MODEL_INDEX = {m["id"]: m for m in LLM_AVAILABLE_MODELS}
