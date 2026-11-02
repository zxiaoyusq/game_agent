#!/usr/bin/env python3
"""Decrypt Cocos 'HEK:' v03 resources: XOR keystream + optional gzip.

Usage:
  python decrypt_v03_resources.py --src <extracted> --dst <decrypted> \
      [--key 65485d8a-8161-4c] [--header HEK:]
"""
import argparse
import collections
import gzip
import hashlib
import json
import os
import sys


def keystream(key, n):
    return (key * (n // len(key) + 1))[:n]


def decrypt(data, key, header):
    if not data.startswith(header.encode()):
        return data, False
    body = data[len(header) + 4:]  # skip 4-byte version marker
    ks = keystream(key, len(body))
    return bytes(a ^ b for a, b in zip(body, ks)), True


def maybe_gunzip(data):
    if data[:2] != b"\x1f\x8b":
        return data, False
    try:
        return gzip.decompress(data), True
    except Exception:
        return data, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--key", default="65485d8a-8161-4c")
    ap.add_argument("--header", default="HEK:")
    a = ap.parse_args()
    key = a.key.encode()
    stats = collections.Counter()
    manifest = []
    errors = []
    os.makedirs(a.dst, exist_ok=True)
    for root, _dirs, files in os.walk(a.src):
        for fn in files:
            src_path = os.path.join(root, fn)
            rel = os.path.relpath(src_path, a.src)
            dst_path = os.path.join(a.dst, rel)
            try:
                raw = open(src_path, "rb").read()
            except OSError as e:
                errors.append((rel, str(e)))
                continue
            pt, was_hek = decrypt(raw, key, a.header)
            pt, was_gz = maybe_gunzip(pt)
            stats[os.path.splitext(fn)[1].lower()] += 1
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            open(dst_path, "wb").write(pt)
            manifest.append({
                "path": rel.replace("\\", "/"),
                "size_in": len(raw),
                "size_out": len(pt),
                "hek": was_hek,
                "gzip": was_gz,
                "sha1": hashlib.sha1(pt).hexdigest(),
            })
    report = {
        "src": a.src, "dst": a.dst, "key": a.key,
        "total_files": sum(stats.values()), "by_ext": dict(stats),
        "errors": errors[:200],
    }
    with open(os.path.join(a.dst, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

