#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
decrypt_jsc.py -- XXTEA 解密 Cocos .jsc 脚本（完整文件缓冲，无头部剥离）

算法与 cc-reverse / xxtea-node 保持一致：
  1) key 按 JS toBytes 规则得到字节串（ASCII 直接取 charCode & 0xFF，
     非 ASCII 走 UTF-8；项目常用 16 字符 ASCII key，如 "--xxxx--" 或十六进制串）；
  2) data 整文件字节 → 按小端组装 uint32 words；
  3) XXTEA 解密（delta=0x9E3779B9，q=6+52/n）；
  4) 末尾 word 存放原始长度，按 includeLength 还原字节；
  5) 若结果以 1f 8b 开头 → gzip 解压；0x78 + zlib 头 → zlib 解压；
  6) 否则须像文本（可打印字符占比 ≥ 0.85），否则标记二进制（.atlas/.plist 等用 --allow-binary）。

用法：
  python decrypt_jsc.py --src assets/main.js --dst main.dec.js --key "yourkey"
  python decrypt_jsc.py --src assets/ --dst assets_dec/ --key-file key.txt --recursive
  python decrypt_jsc.py --src a.jsc --dst a.js --key-hex 2d2d68756e... --allow-binary

说明：key 的位置因引擎版本而异（2.x main.js 内嵌 / 3.x libcocos2djs.so 内找
      SCRIPT_XXTEAKEY / Android 壳常量），先用 projects 侧搜索再解；
      本脚本不含任何项目私有 key 默认值。
"""
import argparse
import gzip
import json
import os
import re
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DELTA = 0x9E3779B9
MASK = 0xFFFFFFFF


def to_bytes(text):
    """JS toBytes：单码位 <0x80 取 charCode，>=0x800 走 UTF-8（等价 str.encode('utf-8')）。"""
    if isinstance(text, bytes):
        return text
    return text.encode("utf-8")


def to_uint32_array(data):
    n = (len(data) + 3) >> 2
    v = [0] * n
    for i, b in enumerate(data):
        v[i >> 2] |= b << ((i & 3) << 3)
    return v


def mx(sum_, y, z, p, e, k):
    # JS 语义：全部按 32 位环绕；Python 需要显式 & MASK
    a = ((z >> 5) ^ ((y << 2) & MASK)) & MASK
    b = ((y >> 3) ^ ((z << 4) & MASK)) & MASK
    c = (a + b) & MASK
    d = (((sum_ ^ y) & MASK) + ((k[(p & 3) ^ e] ^ z) & MASK)) & MASK
    return (c ^ d) & MASK


def fixk(k):
    if len(k) < 16:
        k = bytes(k) + bytes(16 - len(k))
    return k


def decrypt_uint32_array(v, k):
    length = len(v)
    n = length - 1
    y = v[0]
    q = (6 + 52 // length) if length else 0
    sum_ = (q * DELTA) & MASK
    while sum_ != 0:
        e = (sum_ >> 2) & 3
        # JS for(l = n; l > 0; --l) 结束后 l == 0，最后一次 mx 用的是 p=0
        for p in range(n, 0, -1):
            z = v[p - 1]
            y = v[p] = (v[p] - mx(sum_, y, z, p, e, k)) & MASK
        z = v[n]
        y = v[0] = (v[0] - mx(sum_, y, z, 0, e, k)) & MASK
        sum_ = (sum_ - DELTA) & MASK
    return v


def to_uint8_array(v, include_length):
    length = len(v)
    n = length << 2
    m = v[length - 1]
    if include_length:
        n -= 4
        if m < n - 3 or m > n:
            return None
        n = m
    out = bytearray(n)
    for i in range(n):
        out[i] = (v[i >> 2] >> ((i & 3) << 3)) & 0xFF
    return bytes(out)


def decrypt(data, key):
    k = to_uint32_array(fixk(to_bytes(key)))
    v = to_uint32_array(data)
    dec = decrypt_uint32_array(v, k)
    return to_uint8_array(dec, True)


def printable_ratio(b):
    if not b:
        return 0.0
    good = sum(1 for x in b[:8192] if x in (9, 10, 13) or 0x20 <= x < 0x7F or x >= 0x80)
    return good / len(b[:8192])


def decode_file(src, dst, key, allow_binary):
    with open(src, "rb") as fh:
        raw = fh.read()
    try:
        out = decrypt(raw, key)
    except Exception as exc:
        raise RuntimeError("xxtea decrypt failed: %s" % exc)
    if out is None:
        raise RuntimeError("output length check failed (bad key?)")
    mime = None
    if out[:2] == b"\x1f\x8b":
        out = gzip.decompress(out)
        mime = "gzip"
    elif len(out) > 2 and out[0] == 0x78 and (out[1] & 0x0F) == 0x08:
        out = zlib.decompress(out)
        mime = "zlib"
    if allow_binary:
        ok = True
    else:
        ok = printable_ratio(out) >= 0.85
    with open(dst, "wb") as fh:
        fh.write(out)
    return {"src": src, "dst": dst, "size": len(out), "mime": mime or "plain", "ok_text": ok}


def main():
    ap = argparse.ArgumentParser(description="XXTEA 解密 .jsc")
    ap.add_argument("--src", required=True, help="文件或目录")
    ap.add_argument("--dst", required=True, help="文件或目录")
    ap.add_argument("--key", default="", help="字符串 key")
    ap.add_argument("--key-hex", default="", help="十六进制 key（优先于 --key）")
    ap.add_argument("--key-file", default="", help="从文件读 key（去除换行）")
    ap.add_argument("--recursive", action="store_true", default=True)
    ap.add_argument("--allow-binary", action="store_true", help="接受非文本输出")
    ap.add_argument("--summary", default="", help="输出 JSON 摘要到此文件")
    args = ap.parse_args()

    if args.key_hex:
        key = bytes.fromhex(args.key_hex.replace(" ", ""))
    elif args.key_file:
        key = open(args.key_file, "rb").read().strip()
    else:
        key = args.key
    if not key:
        print("[fatal] 需要 --key/--key-hex/--key-file", file=sys.stderr)
        sys.exit(2)

    reports = []
    if os.path.isdir(args.src):
        os.makedirs(args.dst, exist_ok=True)
        for base, dirs, files in os.walk(args.src):
            for fn in sorted(files):
                if not fn.lower().endswith(".jsc"):
                    continue
                rel = os.path.relpath(os.path.join(base, fn), args.src)
                src = os.path.join(base, fn)
                dst = os.path.join(args.dst, os.path.splitext(rel)[0] + ".js")
                os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
                try:
                    reports.append(decode_file(src, dst, key, args.allow_binary))
                except Exception as exc:
                    reports.append({"src": src, "error": "%s" % exc})
    else:
        dst = args.dst if not args.dst.lower().endswith(".js") else args.dst
        if not dst.lower().endswith(".js"):
            dst = os.path.splitext(args.dst)[0] + ".js"
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        reports.append(decode_file(args.src, dst, key, args.allow_binary))

    ok = sum(1 for r in reports if r.get("ok_text"))
    bad = [r for r in reports if r.get("error") or not r.get("ok_text")]
    print(json.dumps({"files": len(reports), "ok_text": ok, "issues": len(bad),
                      "bad": [r.get("src") for r in bad[:50]]}, ensure_ascii=False))
    if args.summary:
        with open(args.summary, "w", encoding="utf-8") as fh:
            json.dump(reports, fh, ensure_ascii=False, indent=2)
    if bad:
        print("[warn] %d 个文件非文本或失败（可能是 key 不对或本就不是 .jsc）" % len(bad), file=sys.stderr)


if __name__ == "__main__":
    main()
