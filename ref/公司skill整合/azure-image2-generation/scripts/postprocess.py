#!/usr/bin/env python3
"""生图结果后处理（本地 PIL，不消耗 API 额度）。

透明背景请优先用 gpt_image.py（或旧版 azure_image2.py）--background transparent 由模型直接生成；
本脚本的角色是 **校验 alpha** 与 **兜底抠图**，不再是一般流程里的必经步骤。

支持：校验透明通道、抠背景(flood fill 兜底)、裁剪空白、等比缩放、压缩、贴背景图。

用法:
  python postprocess.py --input in.png --check-alpha          # 只校验，不写文件
  python postprocess.py --input in.png --output out.png [选项...]

选项:
  --check-alpha        只校验透明通道（mode/尺寸/角落 alpha/透明像素占比），不写文件
  --alpha-floor INT    把 alpha >= INT 置为 255（模型直出主体 alpha 上限常为 253-254）
  --sharpen INT        放大后 UnsharpMask 找回锐度（percent，建议 40-70）
  --pad-canvas INT     把结果居中贴到 NxN 透明画布（做固定规格母版，如 4096x4096）
  --remove-bg          兜底：从边缘 flood fill 抠除背景为透明（仅当接口没给出真 alpha 时用）
  --tol INT            抠背景颜色容差（白底30，深色底60）
  --crop-trim          裁剪透明空白区域
  --fit-max INT        长边不超过 INT 等比缩放
  --height INT         高度= INT 等比缩放
  --width INT          宽度= INT 等比缩放
  --resize WxH         强制尺寸（可能变形）
  --compress           压缩 PNG（P模式+optimize）
  --close-size INT     压缩时自动选最接近此字节数的色板(256/128/64/32)
  --paste-bg PATH      把处理后的透明图等比缩放居中贴到该背景图上
  --flatten COLOR      合成时不透明化背景颜色（如 white/black）
"""
import argparse
import io
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 Pillow: pip install pillow")


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
    ap.add_argument("--resize", type=str, help="WxH")
    ap.add_argument("--compress", action="store_true")
    ap.add_argument("--close-size", type=int)
    ap.add_argument("--paste-bg", type=str)
    ap.add_argument("--flatten", type=str, default=None, help="white/black/hex")
    ap.add_argument("--check-alpha", action="store_true", help="校验是否真透明：打印 mode/尺寸/角落alpha/透明像素计数，不写文件")
    ap.add_argument("--sharpen", type=int, default=0,
                    help="放大后做 UnsharpMask 找回锐度（percent，建议 40-70；0=关闭）")
    ap.add_argument("--pad-canvas", type=int, default=None,
                    help="把结果居中贴到 NxN 的透明画布上（做「4096 母版」这类固定规格时用）")
    ap.add_argument("--alpha-floor", type=int, default=None,
                    help="把 alpha >= INT 的像素置为 255。模型直出的主体 alpha 上限通常是 253-254（A==255 的像素为 0），"
                         "下游若按 A==255 判不透明会整张误判，用本参数归一化")
    args = ap.parse_args()

    if args.check_alpha:
        img2 = Image.open(args.input)
        if "A" in Image.open(args.input).getbands():
            rgba = img2.convert("RGBA")
            a = rgba.getchannel("A").histogram()
            corners = [(0,0),(rgba.width-1,0),(0,rgba.height-1),(rgba.width-1,rgba.height-1)]
            corner_alpha = [rgba.getpixel(c)[3] for c in corners]
            total = float(rgba.width * rgba.height) or 1.0
            print(f"mode={img2.mode} size={img2.size}")
            print(f"transparent_px(sum A<128)={sum(a[:128])}  alpha0={a[0]}  alpha255={a[255]}")
            print(f"transparent_pct={a[0] / total * 100:.2f}%")
            print(f"corners_alpha={corner_alpha}")
            ok = img2.mode in ("RGBA", "LA") and a[0] > 0 and all(c == 0 for c in corner_alpha)
            print("VERDICT: " + ("真透明 OK" if ok
                                 else "不合格 —— 四角未全透明或缺少 alpha 通道，请用 --remove-bg 兜底"))
        else:
            print(f"mode={img2.mode} size={img2.size}  NO_ALPHA（非透明，需 --remove-bg 或接口不支持透明）")
        return

    src = Path(args.input)
    out = Path(args.output)
    if not src.exists():
        sys.exit(f"输入不存在: {src}")

    img = Image.open(src)
    if args.alpha_floor is not None:
        if "A" not in img.getbands() and "transparency" not in img.info:
            sys.exit("--alpha-floor 需要带 alpha 通道的图（本文档模型直出为 RGBA）")
        img = img.convert("RGBA")
        img.putalpha(img.getchannel("A").point(lambda v: 255 if v >= args.alpha_floor else v))
        print(f"[alpha-floor] alpha >= {args.alpha_floor} -> 255")
    if args.remove_bg:
        img = floodfill_remove_bg(img, args.tol)
        print(f"[remove-bg] tol={args.tol}")
    if args.crop_trim:
        if img.mode not in ("RGBA", "LA") and "transparency" not in img.info:
            sys.exit("--crop-trim 需要透明通道，请先 --remove-bg 或提供 RGBA")
        rgba = img.convert("RGBA")
        # 必须按 alpha 通道取 bbox：模型直出的透明 PNG 里，背景像素常是「RGB 有值 + A=0」
        # （实测 (29,24,16,0) 这类），而 Image.getbbox() 看的是全部通道，会返回整幅画布 -> 裁不掉。
        bbox = rgba.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if bbox is None:
            sys.exit("--crop-trim: alpha 全透明，没有可裁的主体")
        img = rgba.crop(bbox)
        print(f"[crop-trim] -> {img.width}x{img.height} (按 alpha 通道)")
    if args.fit_max or args.height or args.width or args.resize:
        w, h = img.size
        if args.resize:
            nw, nh = map(int, args.resize.lower().split("x"))
            scale = min(nw / w, nh / h)
            img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
        else:
            scale = 1.0
            if args.fit_max:
                scale = min(scale, args.fit_max / max(w, h))
            if args.height:
                scale = min(scale, args.height / h)
            if args.width:
                scale = min(scale, args.width / w)
            img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        print(f"[resize] -> {img.width}x{img.height}")
    if args.sharpen > 0:
        from PIL import ImageFilter
        rgb = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.4, percent=args.sharpen, threshold=3))
        if "A" in img.getbands():
            img = Image.merge("RGBA", (*rgb.split(), img.getchannel("A")))
        else:
            img = rgb
        print(f"[sharpen] UnsharpMask percent={args.sharpen}")
    if args.compress:
        img = compress(img, args.close_size)
        print(f"[compress] mode={img.mode}")

    if args.paste_bg:
        bg = Image.open(args.paste_bg).convert("RGBA")
        fg = img.convert("RGBA")
        bw, bh = bg.size
        scale = bw / fg.width
        fg = fg.resize((round(fg.width * scale), round(fg.height * scale)), Image.LANCZOS)
        bg.alpha_composite(fg, ((bw - fg.width) // 2, (bh - fg.height) // 2))
        img = bg
        print(f"[paste-bg] {args.paste_bg} {bw}x{bh}, fg centered {fg.width}x{fg.height}")

    if args.flatten:
        base = Image.new("RGBA", img.size, args.flatten if len(args.flatten) > 3 else args.flatten)
        base.alpha_composite(img.convert("RGBA"))
        img = base.convert("RGB")
        print(f"[flatten] {args.flatten}")

    if args.pad_canvas:
        n = args.pad_canvas
        fg = img.convert("RGBA")
        if max(fg.width, fg.height) > n:
            sys.exit(f"--pad-canvas {n} 小于图像尺寸 {fg.width}x{fg.height}，先 --fit-max 缩小")
        base = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        base.alpha_composite(fg, ((n - fg.width) // 2, (n - fg.height) // 2))
        img = base
        print(f"[pad-canvas] -> {n}x{n}, 主体 {fg.width}x{fg.height} 居中")

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"OK  {out}  {img.width}x{img.height}  {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
