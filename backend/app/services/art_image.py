"""美术 Agent - AI 图片生成业务核心。

封装 Azure OpenAI gpt-image 的两个端点：
- generate(prompt, size, quality)            → 文生图
- edit(prompt, size, quality, references=[]) → 参考图编辑（多参考图）

数据流：上层只关心 (prompt, size, quality, references) → 拿到 PNG bytes。
本文件不感知 HTTP 框架，路由层负责请求/响应包装。

Azure 网关返回 b64_json 格式，本文件做一次解码后向上返回 raw bytes。
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import httpx

from app.config import (
    AZURE_IMAGE_API_KEY,
    AZURE_IMAGE_API_VERSION,
    AZURE_IMAGE_DEPLOYMENT,
    AZURE_IMAGE_ENDPOINT,
)

logger = logging.getLogger(__name__)


# ---- 常量 -----------------------------------------------------------------

# 与 ai_image_tool.html 保持一致的合法尺寸列表（手动选择 + 自动判定的最终落点）
# 留意：Azure 接口对未知 size 会 400，前端需要走白名单
ALLOWED_SIZES = {
    "1024x1024",
    "1280x720", "2048x1152", "2560x1440", "3584x2016",
    "720x1280", "1152x2048", "1440x2560", "2016x3584",
    "1536x1024", "1024x1536",
}

# Azure gpt-image 接受的 quality 取值
ALLOWED_QUALITIES = {"low", "medium", "high", "auto"}

# 默认请求超时：生图较慢，给到 2 分钟
DEFAULT_TIMEOUT = 180.0


# ---- 异常 -----------------------------------------------------------------

class ArtImageConfigError(RuntimeError):
    """配置缺失（endpoint / api_key 等）。"""


class ArtImageAPIError(RuntimeError):
    """Azure 接口返回非 2xx 或缺少图片字段。"""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


# ---- 输入数据结构 ---------------------------------------------------------

@dataclass
class ReferenceImage:
    """参考图：一份待发给 Azure /images/edits 的图片。"""

    filename: str
    data: bytes
    content_type: str = "image/png"


# ---- 公共校验 -------------------------------------------------------------

def _ensure_config() -> None:
    """启动期校验：缺失关键配置时立刻报错，避免 500。"""
    if not AZURE_IMAGE_ENDPOINT or not AZURE_IMAGE_API_KEY:
        raise ArtImageConfigError(
            "Azure 图片生成配置缺失：请检查 .env 中 AZURE_IMAGE_ENDPOINT / AZURE_IMAGE_API_KEY"
        )


def _validate_size(size: str) -> None:
    if size not in ALLOWED_SIZES:
        raise ValueError(
            f"非法尺寸：{size}（合法值见 ALLOWED_SIZES）"
        )


def _validate_quality(quality: str) -> None:
    if quality not in ALLOWED_QUALITIES:
        raise ValueError(
            f"非法质量：{quality}（应为 low / medium / high / auto）"
        )


# ---- 出口：文生图 ---------------------------------------------------------

async def generate(
    *,
    prompt: str,
    size: str,
    quality: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> bytes:
    """无参考图的纯文生图。返回 PNG 字节。"""
    _ensure_config()
    _validate_size(size)
    _validate_quality(quality)
    if not prompt or not prompt.strip():
        raise ValueError("prompt 不能为空")

    url = (
        f"{AZURE_IMAGE_ENDPOINT}/openai/deployments/"
        f"{AZURE_IMAGE_DEPLOYMENT}/images/generations"
        f"?api-version={AZURE_IMAGE_API_VERSION}"
    )
    payload = {
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "output_format": "png",
        "n": 1,
    }
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_IMAGE_API_KEY,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
    return _parse_image_response(resp)


# ---- 出口：参考图编辑 -----------------------------------------------------

async def edit(
    *,
    prompt: str,
    size: str,
    quality: str,
    references: List[ReferenceImage],
    timeout: float = DEFAULT_TIMEOUT,
) -> bytes:
    """带参考图的图片生成（multipart/form-data）。

    references 列表内的顺序就是 Azure 接口里"图1、图2、…"的编号顺序。
    上层应保证 references 非空；空时请走 generate()。
    """
    _ensure_config()
    _validate_size(size)
    _validate_quality(quality)
    if not prompt or not prompt.strip():
        raise ValueError("prompt 不能为空")
    if not references:
        raise ValueError("references 为空时请走 generate()")

    url = (
        f"{AZURE_IMAGE_ENDPOINT}/openai/deployments/"
        f"{AZURE_IMAGE_DEPLOYMENT}/images/edits"
        f"?api-version={AZURE_IMAGE_API_VERSION}"
    )
    headers = {"api-key": AZURE_IMAGE_API_KEY}

    # multipart：与 ai_image_tool.html 的 callEditApi 完全等价
    # prompt 加上"按上传顺序编号为图1、图2..."的前缀，方便用户在描述里指代
    decorated_prompt = (
        "参考图按上传顺序编号为图1、图2、图3……。请严格按照用户描述理解这些编号。"
        f"用户需求：{prompt}"
    )

    files: List[Tuple[str, Tuple[str, bytes, str]]] = []
    data: List[Tuple[str, str]] = [
        ("prompt", decorated_prompt),
        ("size", size),
        ("n", "1"),
        ("quality", quality),
        ("output_format", "png"),
    ]
    for ref in references:
        files.append(
            (
                "image[]",
                (ref.filename, ref.data, ref.content_type or "image/png"),
            )
        )

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, data=data, files=files)
    return _parse_image_response(resp)


# ---- 响应解析 -------------------------------------------------------------

def _parse_image_response(resp: httpx.Response) -> bytes:
    """从 Azure 响应中抽出 b64_json 并解码为字节。"""
    text = resp.text
    try:
        data = resp.json()
    except json.JSONDecodeError:
        data = None

    if resp.status_code >= 400:
        detail = ""
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                detail = str(err.get("message", "")) or str(err)
        if not detail:
            detail = (text or resp.reason_phrase or "未知错误").strip()
        raise ArtImageAPIError(
            f"Azure 接口返回 {resp.status_code}：{detail}",
            status_code=resp.status_code,
        )

    b64 = None
    if isinstance(data, dict):
        items = data.get("data")
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict):
                b64 = first.get("b64_json")
    if not b64:
        raise ArtImageAPIError("Azure 响应未包含 b64_json 字段")

    try:
        return base64.b64decode(b64)
    except (ValueError, TypeError) as e:
        raise ArtImageAPIError(f"图片 base64 解码失败：{e}")
