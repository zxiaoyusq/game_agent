"""带参考图（edit 端点）的 gpt-image 冒烟脚本。

复现 / 验证：知识库引用图片时，前端报错
    'RuntimeError: Attempted to send an sync request with an AsyncClient instance.'

修复点见 services/art_image.py::edit —— 把 data 从 list[tuple] 改成 dict，
否则 httpx 0.28+ 在 AsyncClient 上同时给 data + files 时会落到同步流路径报错。

用法（在 backend/ 目录下，conda activate 313 后）：
    python -m tests.smoke_kb_refs

依赖：本地 data/knowledge/art/images 至少有 1 张 PNG。
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from app.services import art_image as art_service  # noqa: E402
from app.services.art_image import (  # noqa: E402
    ArtImageAPIError,
    ArtImageConfigError,
    ReferenceImage,
)


PROMPT = "保持参考图1的整体配色与风格，画一个圆润的小图标"
SIZE = "1024x1024"
QUALITY = "low"


def _pick_one_png() -> Path | None:
    """挑一张 art/images 下的 PNG 作为参考图。"""
    root = Path(__file__).resolve().parent.parent / "data" / "knowledge" / "art" / "images"
    if not root.exists():
        return None
    for p in root.rglob("*.png"):
        return p
    return None


async def main() -> int:
    ref_path = _pick_one_png()
    if ref_path is None:
        print("[SKIP] 未找到任何 PNG 参考图，请先在知识库 art/images 下放一张")
        return 0

    print("==== gpt-image edit（kb_refs）冒烟测试 ====")
    print(f"reference: {ref_path}")
    print(f"prompt:    {PROMPT}")

    ref = ReferenceImage(
        filename=ref_path.name,
        data=ref_path.read_bytes(),
        content_type="image/png",
    )

    t0 = time.time()
    try:
        png = await art_service.edit(
            prompt=PROMPT,
            size=SIZE,
            quality=QUALITY,
            references=[ref],
        )
    except ArtImageConfigError as e:
        print(f"[FAIL][config] {e}")
        return 2
    except ArtImageAPIError as e:
        print(f"[FAIL][azure {e.status_code}] {e}")
        return 3
    except Exception as e:  # noqa: BLE001 —— 顶层兜底
        print(f"[FAIL][{type(e).__name__}] {e}")
        return 4

    cost = time.time() - t0
    if not png or png[:4] != b"\x89PNG":
        head = png[:4] if png else None
        print(f"[FAIL] 返回的不是 PNG（前 4 字节={head!r}）")
        return 5

    out = Path(__file__).resolve().parent.parent / "data" / "_smoke_kb_refs.png"
    out.write_bytes(png)
    print(f"[OK] {len(png)} bytes，耗时 {cost:.1f}s，保存到 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
