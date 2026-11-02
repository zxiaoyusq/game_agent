#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_transsion_sdk_pack.py -- 从"已接入传音 SDK 的成品 APK"中抽取可复用素材包

用途：传音（Transsion）体系 SDK（Hisavana 广告聚合 / Athena 埋点 / AhaPush / PalmUpdate 等）
      不以公开 AAR 形式分发，通常只能从已跑通的成品包里回收。本脚本把成品 APK 中
      与传音体系相关的 dex、native so、Manifest 声明抽成结构化素材包，供其它项目 sidecar 注入时复用。

设计原则（与 sdk-replacement / SKILL.md 一致）：
  * 抽出来的是**素材**，不是官方 SDK 发布物；包名、appId、密钥、证书一律 DO_NOT_COPY_LITERAL_VALUES。
  * 默认**不复制**任何可能含密钥的配置文件（google-services.json / strings.xml / mediation.json），
    需要时用 --include-config 显式开启，脚本会同时输出 REDACTION-REPORT.md 列出被抹掉的字段。
  * 只做静态回收；是否完整以"官方包 vs 出货包逐类比对"为准（脚本给出类计数，比对方法见 references/）。

用法：
  # 1) 只看成品包里有哪些候选 dex / so（不落盘）
  python scripts/extract_transsion_sdk_pack.py --apk shipped.apk --out pack --dry-run

  # 2) 抽 dex + so（so 默认只取传音/广告链路常用集）
  python scripts/extract_transsion_sdk_pack.py --apk shipped.apk --out pack --abi arm64-v8a

  # 3) 同时抽 Manifest 声明（需要 apktool 解码目录）
  python scripts/extract_transsion_sdk_pack.py --apk shipped.apk --out pack \
      --decoded <apktool-project-dir>

  # 4) 需要配置样例时（会抹密钥）
  python scripts/extract_transsion_sdk_pack.py --apk shipped.apk --out pack --include-config

产物：
  pack/dex/*.dex                 候选 dex（按类分布命名，保留原 classesN 名于 manifest）
  pack/lib/<abi>/*.so            native 依赖
  pack/manifest/AndroidManifest.fragment.xml   （--decoded 时）
  pack/config/*                  （--include-config 时，已抹密钥）
  pack/PACK_MANIFEST.json        sha256 / 类数 / 来源 APK sha256 / 抽取时间
  pack/REDACTION-REPORT.md       （有抹除动作时）
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import struct
import sys
import zipfile

# ---------------------------------------------------------------------------
# 传音体系识别标记（类前缀  归属组件）
# ---------------------------------------------------------------------------
SUITE_MARKERS = {
    "hisavana": ["com/cloud/hisavana", "com/hisavana/"],
    "transsion": ["com/transsion/"],
    "ahapush": ["net/bat/"],
    "palm_update": ["com/transsion/upgradesdk"],
    "adx": ["com/hs/adx"],
    "hsdata": ["cn/hsdata/"],
}
# 弱标记：命中不足以判定该 dex 属于传音体系（如仅引用一两个回调类的宿主 dex）
WEAK_MARKERS = {"hsdata"}
# 广告链路常见的 native 依赖（按需增删）
DEFAULT_SO = [
    "libpglarmor.so", "libbuffer_pgl.so", "libfile_lock_pgl.so", "libtobEmbedPagEncrypt.so",
    "libtt_ugen_layout.so", "libnms.so", "libmmkv.so", "libapminsighta.so", "libapminsightb.so",
]
# 需要抹除的敏感字段模式（用于 --include-config 与 Manifest 片段）
SECRET_PATTERNS = [
    (re.compile(r'(com\.hs\.ads\.APP_KEY"[^>]*android:value=")([^"]+)(")'), r"\1REDACTED\3"),
    (re.compile(r'("client_id"\s*:\s*")([^"]+)(")'), r"\1REDACTED\3"),
    (re.compile(r'("api_key"\s*:\s*\[\s*\{\s*"current_key"\s*:\s*")([^"]+)(")'), r"\1REDACTED\3"),
    (re.compile(r'("project_number"\s*:\s*")([^"]+)(")'), r"\1REDACTED\3"),
    (re.compile(r'("mobilesdk_app_id"\s*:\s*")([^"]+)(")'), r"\1REDACTED\3"),
    (re.compile(r'("appId"\s*:\s*")([^"]{6,})(")'), r"\1REDACTED\3"),
    (re.compile(r'("app_id"\s*:\s*")([^"]{6,})(")'), r"\1REDACTED\3"),
]


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------- 极简 DEX 解析（无第三方依赖） ---------------------------
def _uleb128(buf: bytes, i: int):
    result = shift = 0
    while True:
        byte = buf[i]
        i += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return result, i


class MiniDex:
    """只解析 string_ids / type_ids / class_defs，足够做归属判定与类计数。"""

    def __init__(self, path: str):
        self.path = path
        self.data = open(path, "rb").read()
        d = self.data
        if d[:4] != b"dex\n":
            raise ValueError(f"not a dex file: {path}")
        self.n_str = struct.unpack_from("<I", d, 0x38)[0]
        self.o_str = struct.unpack_from("<I", d, 0x3C)[0]
        self.n_type = struct.unpack_from("<I", d, 0x40)[0]
        self.o_type = struct.unpack_from("<I", d, 0x44)[0]
        self.n_class = struct.unpack_from("<I", d, 0x60)[0]
        self.o_class = struct.unpack_from("<I", d, 0x64)[0]

    def string(self, idx: int) -> str:
        p = struct.unpack_from("<I", self.data, self.o_str + 4 * idx)[0]
        _, q = _uleb128(self.data, p)
        end = self.data.index(b"\x00", q)
        return self.data[q:end].decode("utf-8", "replace")

    def class_names(self) -> list:
        out = []
        for k in range(self.n_class):
            tidx = struct.unpack_from("<I", self.data, self.o_class + 32 * k)[0]
            if tidx >= self.n_type:
                continue
            sidx = struct.unpack_from("<I", self.data, self.o_type + 4 * tidx)[0]
            if sidx < self.n_str:
                desc = self.string(sidx)
                if desc.startswith("L") and desc.endswith(";"):
                    out.append(desc[1:-1])
        return out


def classify(names):
    hit = {}
    for component, prefixes in SUITE_MARKERS.items():
        hit[component] = sum(1 for n in names if n.startswith(tuple(prefixes)))
    core = sum(v for k, v in hit.items() if k not in WEAK_MARKERS)
    return hit, core


# ---------------------------------------------------------------------------
def extract_dex(zf: zipfile.ZipFile, out_dir: str, tmp_dir: str, dry: bool, min_hits: int):
    entries = [n for n in zf.namelist() if re.match(r"^classes\d*\.dex$", n)]
    entries.sort(key=lambda n: (len(n), n))
    results = []
    os.makedirs(tmp_dir, exist_ok=True)
    for name in entries:
        tmp = os.path.join(tmp_dir, name)
        with open(tmp, "wb") as fh:
            fh.write(zf.read(name))
        try:
            dex = MiniDex(tmp)
            names = dex.class_names()
            hit, core_hits = classify(names)
        except Exception as exc:  # noqa: BLE001
            results.append({"entry": name, "error": str(exc)})
            continue
        total_hits = sum(hit.values())
        record = {"entry": name, "classes": len(names), "suite_hits": hit,
                  "suite_total": total_hits, "core_total": core_hits,
                  "labels": [k for k, v in hit.items() if v > 0],
                  "recommended": core_hits >= min_hits}
        if core_hits >= min_hits and not dry:
            dst = os.path.join(out_dir, "dex", name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(tmp, "rb") as src:
                payload = src.read()
            with open(dst, "wb") as fh:
                fh.write(payload)
            record["sha256"] = sha256_file(dst)
            record["size"] = os.path.getsize(dst)
        results.append(record)
        os.remove(tmp)
    return results


def extract_so(zf: zipfile.ZipFile, out_dir: str, abi: str, want: list, dry: bool):
    out = []
    for name in zf.namelist():
        if not name.startswith(f"lib/{abi}/") or not name.endswith(".so"):
            continue
        base = os.path.basename(name)
        if want and base not in want:
            continue
        record = {"entry": name, "size": zf.getinfo(name).file_size}
        if not dry:
            dst = os.path.join(out_dir, "lib", abi, base)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as fh:
                fh.write(zf.read(name))
            record["sha256"] = sha256_file(dst)
        out.append(record)
    return out


def extract_manifest(decoded: str, out_dir: str):
    """从 apktool 解码目录抽传音相关 Manifest 声明（含密钥抹除）。"""
    import xml.etree.ElementTree as ET
    manifest = os.path.join(decoded, "AndroidManifest.xml")
    if not os.path.isfile(manifest):
        return {"error": "AndroidManifest.xml not found in --decoded dir"}
    ns = "http://schemas.android.com/apk/res/android"
    ET.register_namespace("android", ns)
    keywords = ("transsion", "hisavana", "hs.ads", "hsdata", "athena", "palm", "ahapush",
                "galileo", "cloud.sdk", "pgl", "vungle", "bytedance", "pangle", "safedk")
    root = ET.parse(manifest).getroot()
    out = ET.Element("manifest", {"package": "com.<target>.app", "fragment": "transsion-suite"})
    kept = 0

    def blob(elem):
        return " ".join(f"{k} {v}" for k, v in elem.attrib.items()).lower()

    for child in root:
        tag = child.tag.split("}")[-1]
        if tag in ("uses-permission", "permission") and any(k in blob(child) for k in keywords):
            out.append(child); kept += 1
        elif tag == "application":
            app = ET.SubElement(out, "application")
            for sub in child:
                st = sub.tag.split("}")[-1]
                if st in ("activity", "service", "provider", "receiver", "meta-data", "uses-library",
                          "activity-alias") and any(k in blob(sub) for k in keywords):
                    app.append(sub); kept += 1
        elif tag == "queries":
            q = ET.SubElement(out, "queries")
            for sub in child:
                if any(k in ET.tostring(sub, encoding="unicode").lower() for k in keywords):
                    q.append(sub); kept += 1
    text = ET.tostring(out, encoding="unicode")
    redactions = []
    for pattern, repl in SECRET_PATTERNS:
        text, n = pattern.subn(repl, text)
        if n:
            redactions.append(f"{pattern.pattern[:40]}... x{n}")
    os.makedirs(os.path.join(out_dir, "manifest"), exist_ok=True)
    path = os.path.join(out_dir, "manifest", "AndroidManifest.fragment.xml")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"<!-- 抽取自 {decoded}；entries={kept}；密钥类字段已抹除 -->\n")
        fh.write(text.replace("><", ">\n<"))
    return {"entries": kept, "path": os.path.relpath(path, out_dir), "redactions": redactions,
            "sha256": sha256_file(path)}


def extract_config(zf: zipfile.ZipFile, out_dir: str):
    """复制配置样例并抹除密钥。默认关闭，需 --include-config。"""
    wanted = ["assets/mediation.json", "res/values/strings.xml", "google-services.json"]
    copied, redactions = [], []
    for name in wanted:
        try:
            raw = zf.read(name)
        except KeyError:
            continue
        text = raw.decode("utf-8", "replace")
        for pattern, repl in SECRET_PATTERNS:
            text, n = pattern.subn(repl, text)
            if n:
                redactions.append(f"{name}: {pattern.pattern[:40]}... x{n}")
        dst = os.path.join(out_dir, "config", os.path.basename(name))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        copied.append({"path": os.path.relpath(dst, out_dir), "sha256": sha256_file(dst),
                       "source_entry": name})
    return copied, redactions


def main() -> int:
    ap = argparse.ArgumentParser(description="从成品 APK 抽取传音体系 SDK 素材包")
    ap.add_argument("--apk", required=True, help="已接入传音 SDK 的成品 APK")
    ap.add_argument("--out", required=True, help="输出素材包目录")
    ap.add_argument("--abi", default="arm64-v8a", help="native 库 ABI（默认 arm64-v8a）")
    ap.add_argument("--so", default=",".join(DEFAULT_SO),
                    help="要抽取的 .so 文件名（逗号分隔；传空串=全部）")
    ap.add_argument("--decoded", default="", help="apktool 解码目录（用于抽 Manifest 声明）")
    ap.add_argument("--include-config", action="store_true",
                    help="同时抽配置样例（会抹除密钥，仍建议人工复核）")
    ap.add_argument("--min-hits", type=int, default=5,
                    help="命中多少个『核心』传音类才视为素材 dex（默认 5；弱标记如 cn/hsdata 不计入）")
    ap.add_argument("--dry-run", action="store_true", help="只分析不落盘")
    args = ap.parse_args()

    if not os.path.isfile(args.apk):
        print(f"ERROR: APK not found: {args.apk}", file=sys.stderr)
        return 2
    so_want = [s.strip() for s in args.so.split(",") if s.strip()]

    tmp_dir = os.path.join(args.out, "_tmp") if not args.dry_run else os.path.join(
        os.environ.get("TEMP", "/tmp"), "_transsion_pack_tmp")
    pack = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "source_apk": os.path.basename(args.apk),
        "source_apk_sha256": sha256_file(args.apk),
        "abi": args.abi,
        "dry_run": args.dry_run,
        "notice": "素材包=注入态回收物，不是官方 SDK 发布物；包名/appId/密钥/证书均为 DO_NOT_COPY_LITERAL_VALUES",
    }
    with zipfile.ZipFile(args.apk) as zf:
        pack["dex"] = extract_dex(zf, args.out, tmp_dir, args.dry_run, args.min_hits)
        pack["native"] = extract_so(zf, args.out, args.abi, so_want, args.dry_run)
        redactions = []
        if args.include_config and not args.dry_run:
            pack["config"], cfg_red = extract_config(zf, args.out)
            redactions += cfg_red
        else:
            pack["config"] = []

    if args.decoded and not args.dry_run:
        man = extract_manifest(args.decoded, args.out)
        pack["manifest"] = man
        redactions += man.get("redactions", [])
    if not args.dry_run:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "PACK_MANIFEST.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(pack, fh, ensure_ascii=False, indent=2)
        if redactions:
            with open(os.path.join(args.out, "REDACTION-REPORT.md"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("# 密钥抹除报告\n\n抽取时对以下字段做了 REDACTED 替换，提交/共享前请人工复核：\n\n")
                for item in redactions:
                    fh.write(f"- {item}\n")
        try:
            os.rmdir(tmp_dir)
        except OSError:
            pass

    print(json.dumps({
        "source": pack["source_apk"], "sha256": pack["source_apk_sha256"][:16] + "...",
        "dex_candidates": [{k: d.get(k) for k in ("entry", "classes", "suite_total", "core_total", "labels", "recommended")}
                           for d in pack["dex"]],
        "native": len(pack["native"]), "config": len(pack["config"]),
        "manifest": pack.get("manifest", {}).get("entries") if isinstance(pack.get("manifest"), dict) else None,
        "out": args.out, "dry_run": args.dry_run,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
