#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pkm_to_png.py -- PKM(ETC1) → PNG 完整解码器

实现：
  - PKM 头解析（magic "PKM "、version、dataType、extendedWidth/Height、originalWidth/Height，
    均为大端；数据从偏移 16 开始，可能未对齐）。
  - ETC1_RGB8 完整解码（含 differential/individual 模式、flip、modifier 表），
    与 AOSP opengl/libs/ETC1/etc1.cpp 的 decode 逻辑逐位一致。
  - ETC2 变体（dataType 2..7）本脚本不实现，会给出明确报错与可用工具建议。

用法：
  python pkm_to_png.py --root assets/ --out png_out/
  python pkm_to_png.py --root assets/a.pkm --out out.png
  python pkm_to_png.py --root . --out . --max-size 4096

依赖：pip install pillow
"""
import argparse
import json
import os
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ETC1 modifier 表（与 spec/AOSP 一致）
TABLE = [
    [2, 8, -2, -8],
    [5, 17, -5, -17],
    [9, 29, -9, -29],
    [13, 42, -13, -42],
    [18, 60, -18, -60],
    [24, 80, -24, -80],
    [33, 106, -33, -106],
    [47, 183, -47, -183],
]
LOOKUP = [0, 1, 2, 3, -4, -3, -2, -1]
MAGIC = b"PKM "


def clamp(x):
    return 0 if x < 0 else (255 if x > 255 else x)


def convert4to8(b):
    c = b & 0xF
    return (c << 4) | c


def convert5to8(b):
    c = b & 0x1F
    return (c << 3) | (c >> 2)


def convert_diff(base, diff):
    return convert5to8((0x1F & base) + LOOKUP[0x7 & diff])


def decode_subblock(pix, x0, y0, r, g, b, table, low, second, flipped, w):
    base_x = base_y = 0
    if second:
        if flipped:
            base_y = 2
        else:
            base_x = 2
    for i in range(8):
        if flipped:
            x = base_x + (i >> 1)
            y = base_y + (i & 1)
        else:
            x = base_x + (i >> 2)
            y = base_y + (i & 3)
        k = y + (x * 4)
        off = ((low >> k) & 1) | ((low >> (k + 15)) & 2)
        d = table[off]
        px = x0 + x
        py = y0 + y
        if px < w[0] and py < w[1]:
            idx = (py * w[0] + px) * 3
            pix[idx] = clamp(r + d)
            pix[idx + 1] = clamp(g + d)
            pix[idx + 2] = clamp(b + d)


def decode_block(data, off, pix, x0, y0, w, h):
    b = data[off:off + 8]
    high = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
    low = (b[4] << 24) | (b[5] << 16) | (b[6] << 8) | b[7]
    if high & 2:
        r_base = high >> 27
        g_base = high >> 19
        b_base = high >> 11
        r1 = convert5to8(r_base)
        r2 = convert_diff(r_base, high >> 24)
        g1 = convert5to8(g_base)
        g2 = convert_diff(g_base, high >> 16)
        b1 = convert5to8(b_base)
        b2 = convert_diff(b_base, high >> 8)
    else:
        r1 = convert4to8(high >> 28)
        r2 = convert4to8(high >> 24)
        g1 = convert4to8(high >> 20)
        g2 = convert4to8(high >> 16)
        b1 = convert4to8(high >> 12)
        b2 = convert4to8(high >> 8)
    ta = TABLE[7 & (high >> 5)]
    tb = TABLE[7 & (high >> 2)]
    flipped = (high & 1) != 0
    decode_subblock(pix, x0, y0, r1, g1, b1, ta, low, False, flipped, (w, h))
    decode_subblock(pix, x0, y0, r2, g2, b2, tb, low, True, flipped, (w, h))


def parse_pkm(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 16 or data[:4] != MAGIC:
        raise ValueError("not a PKM file: %s" % path)
    data_type = struct.unpack(">H", data[6:8])[0]
    ext_w = struct.unpack(">H", data[8:10])[0]
    ext_h = struct.unpack(">H", data[10:12])[0]
    orig_w = struct.unpack(">H", data[12:14])[0]
    orig_h = struct.unpack(">H", data[14:16])[0]
    return {"type": data_type, "w": ext_w, "h": ext_h,
            "ow": orig_w, "oh": orig_h, "data": data[16:]}


def decode_etc1(path, out, max_size=0):
    meta = parse_pkm(path)
    if meta["type"] in (2, 3, 4, 5, 6, 7):
        raise NotImplementedError(
            "ETC2 (dataType %d) 未实现；请用 etc2comp / Mali Texture Compression Tool 转换" % meta["type"])
    if meta["type"] not in (0, 1):
        raise NotImplementedError("未知 dataType %d" % meta["type"])
    w, h = meta["w"], meta["h"]
    if max_size and (w > max_size or h > max_size):
        raise ValueError("尺寸 %dx%d 超过 --max-size" % (w, h))
    data = meta["data"]
    # 取第一个 mipmap 层（type=1 时数据含多级，按首层长度跳过其余）
    block_bytes = (w // 4) * (h // 4) * 8
    pix = bytearray(w * h * 3)
    off = 0
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            decode_block(data, off, pix, bx, by, w, h)
            off += 8
    from PIL import Image
    img = Image.frombytes("RGB", (w, h), bytes(pix))
    img.save(out, "PNG")
    return {"src": path, "out": out, "w": w, "h": h, "bytes": len(data)}


def main():
    ap = argparse.ArgumentParser(description="PKM(ETC1)→PNG")
    ap.add_argument("--root", required=True, help="PKM 文件或目录")
    ap.add_argument("--out", required=True, help="输出 PNG 或目录")
    ap.add_argument("--max-size", type=int, default=0)
    args = ap.parse_args()

    files = []
    if os.path.isdir(args.root):
        for base, dirs, names in os.walk(args.root):
            for fn in sorted(names):
                if fn.lower().endswith(".pkm"):
                    files.append(os.path.join(base, fn))
    else:
        files = [args.root]

    if not files:
        print("no pkm files", file=sys.stderr)
        sys.exit(2)

    reports = []
    for path in files:
        if os.path.isdir(args.out):
            os.makedirs(args.out, exist_ok=True)
            out = os.path.join(args.out, os.path.splitext(os.path.basename(path))[0] + ".png")
        else:
            os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
            out = args.out
        try:
            reports.append(decode_etc1(path, out, args.max_size))
        except Exception as exc:
            reports.append({"src": path, "error": "%s" % exc})
    ok = [r for r in reports if r.get("out")]
    bad = [r for r in reports if r.get("error")]
    print(json.dumps({"total": len(reports), "ok": len(ok), "failed": len(bad),
                      "failed_samples": [r["src"] for r in bad[:50]]}, ensure_ascii=False))
    if bad:
        print("[warn] 部分失败，见上；ETC2 请用外部工具", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
