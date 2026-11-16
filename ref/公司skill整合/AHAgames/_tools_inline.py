# -*- coding: utf-8 -*-
"""AHAgames 门户页：全部美术资源压缩并内化到 index.html。
- 预览 GIF（动图）→ 动画 WebP（q60，帧率/尺寸保持）
- 静态 webp/jpg/png → WebP q78 重压缩（长边上限 1080）
- 全部转 base64 data URI 内化；原 index.html 备份为 index.backup.html
- 带缓存断点续跑（中断重跑只补缺）
"""
import base64, io, json, re, sys, time
from pathlib import Path

from PIL import Image, ImageSequence

ROOT = Path(r"E:\AIlab\AHAgames")
HTML = ROOT / "index.html"
BACKUP = ROOT / "index.backup.html"
CACHE = ROOT / "_inlined_cache"
CACHE.mkdir(exist_ok=True)

MAX_DIM = 1080
Q_ANIM = 60
Q_STATIC = 78


def gif_to_webp_bytes(src: Path) -> bytes:
    im = Image.open(src)
    frames, durations = [], []
    base = im.convert("RGBA")
    try:
        idx = 0
        while True:
            im.seek(idx)
            frames.append(im.convert("RGBA"))
            durations.append(im.info.get("duration", 100))
            idx += 1
    except EOFError:
        pass
    buf = io.BytesIO()
    frames[0].save(buf, format="WEBP", save_all=True, append_images=frames[1:],
                   duration=durations, loop=im.info.get("loop", 0),
                   quality=Q_ANIM, method=4)
    return buf.getvalue()


def static_to_webp_bytes(src: Path, q: int = Q_STATIC) -> bytes:
    im = Image.open(src)
    im = im.convert("RGBA" if "A" in im.getbands() or src.suffix.lower() == ".png" else "RGB")
    w, h = im.size
    if max(w, h) > MAX_DIM:
        r = MAX_DIM / max(w, h)
        im = im.resize((round(w * r), round(h * r)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=q, method=4)
    return buf.getvalue()


def convert(ref: str) -> tuple[str, int, int]:
    """返回 (mime, 压缩前字节, 压缩后字节)。带缓存。"""
    src = ROOT / ref.replace("/", os.sep)
    key = re.sub(r"[^A-Za-z0-9_.-]", "_", ref) + ".webp"
    cache_file = CACHE / key
    if cache_file.exists():
        data = cache_file.read_bytes()
        return "image/webp", src.stat().st_size, data
    t0 = time.time()
    if src.suffix.lower() == ".gif":
        im = Image.open(src)
        if getattr(im, "n_frames", 1) > 1:
            data = gif_to_webp_bytes(src)
        else:
            data = static_to_webp_bytes(src)
    else:
        data = static_to_webp_bytes(src)
    cache_file.write_bytes(data)
    return "image/webp", src.stat().st_size, data


def main():
    html = HTML.read_text(encoding="utf-8", errors="replace")
    refs = sorted(set(re.findall(r'src="([^"]+?\.(?:webp|gif|png|jpe?g|svg))"', html)))
    print(f"待处理资源 {len(refs)} 个")
    if not BACKUP.exists():
        shutil.copy2(HTML, BACKUP)
        print("已备份原文件 → index.backup.html")

    total_before = total_after = 0
    t0 = time.time()
    for i, ref in enumerate(refs, 1):
        mime, before, after = convert(ref)
        total_before += before
        total_after += len(after)
        b64 = base64.b64encode(after).decode("ascii")
        html = html.replace(f'src="{ref}"', f'src="data:{mime};base64,{b64}"', 1)
        if i % 10 == 0 or i == len(refs):
            print(f"  [{i}/{len(refs)}] 累计 {total_before/1048576:.1f}MB → {total_after/1048576:.1f}MB "
                  f"| 已用 {time.time()-t0:.0f}s", flush=True)

    HTML.write_text(html, encoding="utf-8", newline="\n")
    print("=" * 50)
    print(f"完成：图片 {total_before/1048576:.1f}MB → {total_after/1048576:.1f}MB "
          f"(+33% base64 后 ≈ {total_after*1.33/1048576:.1f}MB)")
    print(f"index.html 最终大小: {HTML.stat().st_size/1048576:.1f}MB")


import os, shutil
if __name__ == "__main__":
    main()
