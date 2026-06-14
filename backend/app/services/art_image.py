"""美术 Agent - AI 图片生成业务核心。

封装 Azure OpenAI gpt-image 的两个端点：
- generate(prompt, size, quality)            → 文生图
- edit(prompt, size, quality, references=[]) → 参考图编辑（多参考图）

数据流：上层只关心 (prompt, size, quality, references) → 拿到 PNG bytes。
本文件不感知 HTTP 框架，路由层负责请求/响应包装。

Azure 网关返回 b64_json 格式，本文件做一次解码后向上返回 raw bytes。
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import random
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

# 上游遇到 429 / 5xx 时的退避重试参数。
# Azure gpt-image-2 当前会高频出现"429 限流"和"500 上游 OpenAI 错误"，
# 单次调用成功率很低；不重试的话用户在 UI 上几乎一次都点不通。
RETRY_MAX_ATTEMPTS = 3            # 总共最多尝试 3 次（首次 + 2 次重试）
RETRY_BASE_DELAY = 2.0            # 第一次重试等待 ~2s，之后指数级翻倍
RETRY_MAX_DELAY = 12.0            # 单次等待上限，避免堆叠到几十秒
RETRY_RETRYABLE_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}


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

    resp = await _post_with_retry(
        url,
        timeout=timeout,
        json=payload,
        headers=headers,
        op="generate",
    )
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

    # 注意：httpx 0.28+ 在 AsyncClient 上同时使用 data=list[tuple] + files= 时，
    # 内部 multipart 编码会落到同步流路径，触发
    # "Attempted to send an sync request with an AsyncClient instance."
    # 这里所有字段名都是唯一的，用 dict 即可绕开该路径。
    data: dict = {
        "prompt": decorated_prompt,
        "size": size,
        "n": "1",
        "quality": quality,
        "output_format": "png",
    }
    files: List[Tuple[str, Tuple[str, bytes, str]]] = []
    for ref in references:
        files.append(
            (
                "image[]",
                (ref.filename, ref.data, ref.content_type or "image/png"),
            )
        )

    # 注意：files 是包含 bytes 的内存对象，可以重复使用——httpx 不会在第一次请求里
    # 消费掉 bytes（与文件句柄不同），这让我们能安全地把整个 (data, files) 一起重试。
    resp = await _post_with_retry(
        url,
        timeout=timeout,
        headers=headers,
        data=data,
        files=files,
        op="edit",
    )
    return _parse_image_response(resp)


# ---- 公共：带退避重试的 POST ----------------------------------------------

async def _post_with_retry(
    url: str,
    *,
    timeout: float,
    op: str,
    headers: Optional[dict] = None,
    json: Optional[dict] = None,
    # data 用 dict 而不是 list[tuple]：见 edit() 里的注释，
    # 后者会在 httpx 0.28+ 上触发 "sync request with AsyncClient" 错误。
    data: Optional[dict] = None,
    files: Optional[List[Tuple[str, Tuple[str, bytes, str]]]] = None,
) -> httpx.Response:
    """带退避重试的 httpx POST。

    重试触发条件：
      1) 网络层错误（httpx.TransportError、ReadTimeout 等）
      2) 上游返回 429 / 5xx（详见 RETRY_RETRYABLE_STATUSES）
    其它情况一律不重试，直接把响应交给上层做错误透传。
    """
    last_exc: Optional[BaseException] = None
    last_resp: Optional[httpx.Response] = None

    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json=json,
                    data=data,
                    files=files,
                )
        except (httpx.TransportError, httpx.TimeoutException) as e:
            # 网络抖动 / 超时：明确属于可重试范畴
            last_exc = e
            last_resp = None
            logger.warning(
                "art_image[%s] attempt %d/%d transport error: %r",
                op, attempt, RETRY_MAX_ATTEMPTS, e,
            )
        else:
            # 拿到响应：成功或非可重试错误就立刻返回
            if resp.status_code < 400 or resp.status_code not in RETRY_RETRYABLE_STATUSES:
                return resp
            last_resp = resp
            logger.warning(
                "art_image[%s] attempt %d/%d upstream %d: %s",
                op, attempt, RETRY_MAX_ATTEMPTS, resp.status_code,
                _short_error_text(resp),
            )

        # 走到这里说明本次失败但允许重试；如果已经是最后一次就跳出
        if attempt >= RETRY_MAX_ATTEMPTS:
            break

        # 指数退避 + 抖动，避开"齐步走"的雪崩重试
        delay = min(RETRY_MAX_DELAY, RETRY_BASE_DELAY * (2 ** (attempt - 1)))
        delay += random.uniform(0, 0.5)
        await asyncio.sleep(delay)

    # 所有尝试都失败：优先把最后一次的 HTTP 响应抛回给上层（保留 status/detail）
    if last_resp is not None:
        return last_resp
    # 全程网络层失败：把异常包成 ArtImageAPIError 让路由层走 502 分支
    raise ArtImageAPIError(
        f"调用 Azure 失败（{op}）：{last_exc!r}",
        status_code=None,
    )


def _short_error_text(resp: httpx.Response) -> str:
    """截短上游响应正文用于日志，避免 500 错误页污染日志文件。"""
    try:
        text = resp.text or ""
    except Exception:  # noqa: BLE001 —— 仅用于日志兜底
        return "<unreadable>"
    return (text[:160] + "…") if len(text) > 160 else text


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
