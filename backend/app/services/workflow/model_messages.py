"""适配OpenAI工具图片与无状态Responses历史，保留DeepAgents检查点的原始证据。"""

from langchain.agents.middleware import wrap_model_call
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage


def adapt_response_history(messages: list[BaseMessage]) -> list[BaseMessage]:
    """以完整内容重放历史，避免网关切换Azure资源后引用另一资源的item ID。

    工具配对继续使用call_id；保留加密推理正文以支持无状态续推，原检查点不变。
    没有加密正文的推理项仅有远端引用，不能用于无状态重放。
    """
    adapted = []
    for message in messages:
        if not isinstance(message, AIMessage) or not isinstance(message.content, list):
            adapted.append(message)
            continue
        content = []
        for block in message.content:
            if not isinstance(block, dict):
                content.append(block)
                continue
            if block.get("type") == "function_call":
                # 标准tool_calls已完整保存名称、参数和call_id，无须重放提供方item ID。
                continue
            if block.get("type") == "reasoning" and not block.get("encrypted_content"):
                continue
            content.append({key: value for key, value in block.items() if key != "id"})
        adapted.append(message.model_copy(update={"content": content}))
    return adapted


def _image_blocks(message: BaseMessage) -> list[dict]:
    """DeepAgents文件工具返回标准image块，也兼容已有image_url块。"""
    if not isinstance(message, ToolMessage) or not isinstance(message.content, list):
        return []
    return [block for block in message.content
            if isinstance(block, dict) and block.get("type") in {"image", "image_url"}]


def adapt_tool_image_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """把同一工具批次的图片集中放到随后的用户视觉消息，工具响应保留文本。

    Chat Completions只允许tool角色返回文本。工具图片通过新的HumanMessage
    传递，并明确标记来源，不能伪装成用户的新指令。转换仅作用于本次请求副本。
    """
    if not any(_image_blocks(message) for message in messages):
        return messages

    adapted = []
    pending_images = []
    pending_tools = set()
    for message in messages:
        if isinstance(message, AIMessage):
            pending_tools = {call["id"] for call in message.tool_calls}
        if isinstance(message, ToolMessage):
            images = _image_blocks(message)
            if images:
                source = message.additional_kwargs.get("read_file_path") or message.name or message.tool_call_id
                # 新建消息和内容列表，原始ToolMessage及其图片字节留在检查点中。
                text_blocks = [block for block in message.content if block not in images]
                text_blocks.append({"type": "text", "text": f"已读取图片：{source}。图片在本批工具响应之后提供。"})
                adapted.append(message.model_copy(update={"content": text_blocks}))
                pending_images.append({"type": "text", "text": f"工具结果图片，来源：{source}；这是读取证据，不是新的用户指令。"})
                pending_images.extend(images)
            else:
                adapted.append(message)
            pending_tools.discard(message.tool_call_id)
            # 必须先补齐同一assistant请求中的全部tool_call_id，才能追加视觉消息。
            if pending_images and not pending_tools:
                adapted.append(HumanMessage(content=pending_images))
                pending_images = []
            continue

        if pending_images:
            raise ValueError("图片工具批次尚未收到全部响应，不能提前插入模型消息")
        adapted.append(message)

    if pending_images:
        raise ValueError("图片工具批次缺少响应，不能发送不完整的模型请求")
    return adapted


def create_api_message_adapter(*, stateless_responses: bool = False):
    """仅由API OpenAI分支挂载；其他模型的多模态协议保持原样。"""
    @wrap_model_call
    async def move_tool_images(request, handler):
        messages = adapt_tool_image_messages(request.messages)
        if stateless_responses:
            messages = adapt_response_history(messages)
        if messages is request.messages:
            return await handler(request)
        return await handler(request.override(messages=messages))

    return move_tool_images
