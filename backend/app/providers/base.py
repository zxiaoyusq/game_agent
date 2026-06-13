"""LLM Provider 错误类型。

具体的模型构造逻辑都收敛在 providers/llm.py 内，
这里只定义 service / route 层会用到的领域异常，
让上层无需直接引用 langchain 的内部异常类。
"""


class LLMConfigError(RuntimeError):
    """LLM 配置缺失或不合法（缺 key、未知 model_id 等）。"""


class LLMUnknownModelError(LLMConfigError):
    """前端传入的 model_id 不在白名单里。"""
