"""gpt-image 接口冒烟脚本。

目的：在不起 FastAPI 的情况下，直接调 services/art_image.generate() 验证
Azure gpt-image 端点 + .env 中的 key/endpoint/deployment 是否能正常出图。

用法（在 backend/ 目录下，conda activate 313 后）：
    python -m tests.smoke_gpt_image

成功时把 PNG 字节大小打印出来，并把图保存到 backend/data/_smoke_gpt_image.png。
失败时把异常类型 + 关键信息打印出来便于定位。
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path

# 显式加载 .env，否则 services/art_image 拿不到 key（.env 默认在 backend/ 下）
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# 把 service 层的 retry 日志打到 stderr，方便观察重试过程
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ↑ load_dotenv 必须在 import services 之前；下面再 import
from app.services import art_image as art_service  # noqa: E402
from app.services.art_image import (  # noqa: E402
    ArtImageAPIError,
    ArtImageConfigError,
)


# 测试参数：用最小尺寸 + low 质量，最快返回结果
PROMPT = "a red apple on a white background"
SIZE = "1024x1024"
QUALITY = "low"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "_smoke_gpt_image.png"


async def main() -> int:
    print("==== gpt-image 冒烟测试 ====")
    print(f"prompt:  {PROMPT}")
    print(f"size:    {SIZE}")
    print(f"quality: {QUALITY}")

    t0 = time.time()
    try:
        png = await art_service.generate(
            prompt=PROMPT,
            size=SIZE,
            quality=QUALITY,
        )
    except ArtImageConfigError as e:
        print(f"[FAIL][config] {e}")
        return 2
    except ArtImageAPIError as e:
        print(f"[FAIL][azure {e.status_code}] {e}")
        return 3
    except Exception as e:  # noqa: BLE001 —— 顶层兜底，方便看到任意异常
        print(f"[FAIL][{type(e).__name__}] {e}")
        return 4

    cost = time.time() - t0
    if not png or len(png) < 1024:
        print(f"[FAIL] 返回字节数过小：{len(png) if png else 0}")
        return 5

    # PNG 文件头校验：89 50 4E 47
    if png[:4] != b"\x89PNG":
        print(f"[FAIL] 返回内容前 4 字节不是 PNG header：{png[:4]!r}")
        return 6

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_bytes(png)

    print(f"[OK] {len(png)} bytes，耗时 {cost:.1f}s，保存到 {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
