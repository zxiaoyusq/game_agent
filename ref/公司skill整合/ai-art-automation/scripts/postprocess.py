#!/usr/bin/env python3
"""生图结果后处理（本地 PIL，不消耗 API 额度）。

支持：抠背景(flood fill)、裁剪空白、等比缩放、压缩、贴背景图、透明校验。

用法:
  python postprocess.py --input in.png --output out.png [选项...]

选项:
  --remove-bg          从边缘 flood fill 抠除背景为透明（需 numpy）
  --tol INT            抠背景颜色容差（白底30，深色底60）
  --crop-trim          裁剪透明空白区域
  --fit-max INT        长边不超过 INT 等比缩放
  --height INT         高度= INT 等比缩放
  --width INT          宽度= INT 等比缩放
  --resize WxH         contain 等比缩放到 WxH 范围内（保持比例、不变形）
  --compress           压缩 PNG（P模式+optimize）
  --close-size INT     压缩时自动选最接近此字节数的色板(256/128/64/32)
  --paste-bg PATH      把处理后的透明图等比缩放居中贴到该背景图上
  --flatten COLOR      合成时不透明化背景颜色（如 white/black）
  --check-alpha        仅校验是否真透明（mode/角落alpha/透明像素计数），不写文件

依赖: Pillow（必需）；numpy 仅 --remove-bg 需要。
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 Pillow: python -m pip install pillow")

# Pillow 9 用 Image.LANCZOS；Pillow 10+ 改为 Image.Resampling.LANCZOS
try:
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # 旧版 Pillow 兜底
    LANCZOS = Image.LANCZOS


def floodfill_remove_bg(img: Image.Image, tol: int) -> Image.Image:
    import numpy as np
    from collections import deque

    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape
    seed = tuple(int(v) for v in arr[0, 0])
    visited = np.zeros((h, w), dtype=bool)
    q = deque()
    for y in range(h):
        for x in (0, w - 1):
            q.append((y, x)); visited[y, x] = True
    for x in range(w):
        for y in (0, h - 1):
            q.append((y, x)); visited[y, x] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                d = float(np.sqrt(((arr[ny, nx] - seed) ** 2).sum()))
                if d <= tol:
                    visited[ny, nx] = True
                    q.append((ny, nx))
    rgba = img.convert("RGBA")
    a = np.array(rgba)
    a[visited, 3] = 0
    return Image.fromarray(a, "RGBA")


def compress(img: Image.Image, close_size: int | None) -> Image.Image:
    best = None
    best_size = float("inf")
    for colors in ([256, 128, 64, 32] if close_size else [256]):
        p = img.convert("P", palette=Image.ADAPTIVE, colors=colors)
        buf = io.BytesIO()
        p.save(buf, format="PNG", optimize=True)
        cur = len(buf.getvalue())
        target = close_size if close_size else 0
        if abs(cur - target) < abs(best_size - target):
            best = p
            best_size = cur
    return best


def main():
    ap = argparse.ArgumentParser(description="图片后处理")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=False)
    ap.add_argument("--remove-bg", action="store_true")
    ap.add_argument("--tol", type=int, default=30)
    ap.add_argument("--crop-trim", action="store_true")
    ap.add_argument("--fit-max", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--width", type=int)
    ap.add_argument("--resize", type=str, help="WxH，contain 等比缩放（不变形）")
    ap.add_argument("--compress", action="store_true")
    ap.add_argument("--close-size", type=int)
    ap.add_argument("--paste-bg", type=str)
    ap.add_argument("--flatten", type=str, default=None, help="white/black/hex")
    ap.add_argument("--check-alpha", action="store_true", help="校验是否真透明，不写文件")
    args = ap.parse_args()

    if args.check_alpha:
        img2 = Image.open(args.input)
        if "A" in img2.getbands():
            rgba = img2.convert("RGBA")
            a = rgba.getchannel("A").histogram()
            corners = [(0,0),(rgba.width-1,0),(0,rgba.height-1),(rgba.width-1,rgba.height-1)]
            corner_alpha = [rgba.getpixel(c)[3] for c in corners]
            print(f"mode={img2.mode} size={img2.size}")
            print(f"transparent_px(sum A<128)={sum(a[:128])}  alpha0={a[0]}  alpha255={a[255]}")
            print(f"corners_alpha={corner_alpha}")
        else:
            print(f"mode={img2.mode} size={img2.size}  NO_ALPHA（非透明，需 --remove-bg 或接口不支持透明）")
        return

    src = Path(args.input)
    out = Path(args.output)
    if not src.exists():
        sys.exit(f"输入不存在: {src}")

    img = Image.open(src)
    if args.remove_bg:
        img = floodfill_remove_bg(img, args.tol)
        print(f"[remove-bg] tol={args.tol}")
    if args.crop_trim:
        if img.mode not in ("RGBA", "LA") and "transparency" not in img.info:
            sys.exit("--crop-trim 需要透明通道，请先 --remove-bg 或提供 RGBA")
        img = img.crop(img.getbbox())
        print(f"[crop-trim] -> {img.width}x{img.height}")
    if args.fit_max or args.height or args.width or args.resize:
        w, h = img.size
        if args.resize:
            nw, nh = map(int, args.resize.lower().split("x"))
            scale = min(nw / w, nh / h)
            img = img.resize((round(w * scale), round(h * scale)), LANCZOS)
        else:
            scale = 1.0
            if args.fit_max:
                scale = min(scale, args.fit_max / max(w, h))
            if args.height:
                scale = min(scale, args.height / h)
            if args.width:
                scale = min(scale, args.width / w)
            img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), LANCZOS)
        print(f"[resize] -> {img.width}x{img.height}")
    if args.compress:
        img = compress(img, args.close_size)
        print(f"[compress] mode={img.mode}")

    if args.paste_bg:
        bg = Image.open(args.paste_bg).convert("RGBA")
        fg = img.convert("RGBA")
        bw, bh = bg.size
        scale = bw / fg.width
        fg = fg.resize((round(fg.width * scale), round(fg.height * scale)), LANCZOS)
        bg.alpha_composite(fg, ((bw - fg.width) // 2, (bh - fg.height) // 2))
        img = bg
        print(f"[paste-bg] {args.paste_bg} {bw}x{bh}, fg centered {fg.width}x{fg.height}")

    if args.flatten:
        base = Image.new("RGBA", img.size, args.flatten if len(args.flatten) > 3 else args.flatten)
        base.alpha_composite(img.convert("RGBA"))
        img = base.convert("RGB")
        print(f"[flatten] {args.flatten}")

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"OK  {out}  {img.width}x{img.height}  {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
