#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_original_sdk_surfaces.py -- 静态盘点 APK 中原厂/第三方 SDK 相关表面

用途：在反编译/解码后的 APK 目录中扫描 Manifest、XML、JSON、JS、smali、Java/Kotlin、
      文本资源中出现的 SDK 关键字、URL、appId 特征、自动初始化组件，供 Phase 1 使用。
      结果仅作为"线索"，不作为网络是否已切断的证据。

用法：
  python scan_original_sdk_surfaces.py --apk-dir <decoded> --out surfaces.json
  python scan_original_sdk_surfaces.py --apk-dir <decoded> --config isolation-config.json --out surfaces.json

--config 可选：isolation-config.json 里的 static_markers 字段可覆盖关键字：
  {
    "static_markers": {
      "vendor-a": ["com/vendor/a", "vendor_a_sdk", "vendor-a.example.com"],
      "vendor-b": ["com/vendor/b"]
    }
  }
没有配置时使用内置通用 SDK 常见关键字（仅作示例，名单不表示任何具体项目）。

输出 fields：
  keywords: {keyword: [{file, line, context}]}
  urls: {url: [{file, line}]}
  manifest_components: [{name, type, file}]
  suspicious_files: [{file, size, reason}]
"""
import argparse
import fnmatch
import json
import os
import re
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 仅内置一套通用示例关键字；真实项目务必用 --config 覆盖。
DEFAULT_KEYWORDS = [
    "bugsnag", "crashlytics", "firebase", "admob", "applovin", "unityads",
    "ironsource", "appsflyer", "adjust", "facebook", "sentry", "datadog",
    "braze", "kochava", "talkingdata", "umeng", "taobao", "alipay",
    "weixin", "googleads", "play-services", "gaid", "androidid", "idfa",
]

URL_RE = re.compile(r"https?://[A-Za-z0-9._~:/?#[]@!$&'()*+,;=%-]+", re.I)
APPID_RE = re.compile(r"(?i)(apps*id|appid|clients*id|clientid|apis*key|trackings*id)[\"'=s:]+([A-Za-z0-9_-]{16,})")

TEXT_EXTS = {".xml", ".json", ".js", ".txt", ".smali", ".java", ".kt", ".properties", ".plist", ".cfg", ".ini", ".html"}
# 不扫描的二进制/大文件
SKIP_DIRS = {"res/drawable", "res/mipmap", "lib", "META-INF", "assets/audio", "assets/video"}


def iter_text_files(root):
    for base, dirs, files in os.walk(root):
        rel = os.path.relpath(base, root).replace("\\", "/")
        dirs[:] = [d for d in dirs if not any(part in rel + "/" + d for part in SKIP_DIRS)]
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in TEXT_EXTS:
                continue
            path = os.path.join(base, fn)
            try:
                if os.path.getsize(path) > 30 * 1024 * 1024:
                    continue
            except OSError:
                continue
            yield path, rel + "/" + fn


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def line_no(text, pos):
    return text.count("\n", 0, pos) + 1


def scan_keywords(root, keywords, limit_per_kw):
    hits = defaultdict(list)
    for path, rel in iter_text_files(root):
        try:
            text = read_text(path)
        except Exception:
            continue
        lines = text.splitlines()
        for kw in keywords:
            if kw not in text:
                continue
            low = kw.lower()
            for i, line in enumerate(lines, 1):
                if low in line.lower():
                    hits[kw].append({"file": rel, "line": i, "context": line[:240].strip()})
                    if len(hits[kw]) >= limit_per_kw:
                        break
    return dict(hits)


def scan_urls(root, limit=2000):
    hits = defaultdict(list)
    seen_urls = 0
    for path, rel in iter_text_files(root):
        text = read_text(path)
        for m in URL_RE.finditer(text):
            url = m.group(0)
            line = line_no(text, m.start())
            hits[url].append({"file": rel, "line": line})
            seen_urls += 1
            if seen_urls >= limit:
                return dict(hits)
    return dict(hits)


def scan_appids(root, limit=1000):
    hits = []
    for path, rel in iter_text_files(root):
        text = read_text(path)
        for m in APPID_RE.finditer(text):
            hits.append({"file": rel, "line": line_no(text, m.start()),
                         "label": m.group(1), "value": m.group(2)[:40]})
            if len(hits) >= limit:
                return hits
    return hits


def scan_manifest_components(root):
    comps = []
    manifest = os.path.join(root, "AndroidManifest.xml")
    if not os.path.exists(manifest):
        return comps
    text = read_text(manifest)
    for tag in ("provider", "activity", "service", "receiver", "meta-data"):
        for m in re.finditer(r"<%s\b[^>]*>" % tag, text, re.I):
            comps.append({"type": tag, "tag": m.group(0)[:300]})
    return comps


def main():
    ap = argparse.ArgumentParser(description="扫描 APK 中 SDK 表面")
    ap.add_argument("--apk-dir", required=True, help="解码后的 APK 目录")
    ap.add_argument("--config", default="", help="isolation-config.json")
    ap.add_argument("--out", default="surfaces.json")
    ap.add_argument("--limit-per-keyword", type=int, default=50)
    ap.add_argument("--no-urls", action="store_true")
    args = ap.parse_args()

    keywords = list(DEFAULT_KEYWORDS)
    if args.config and os.path.exists(args.config):
        with open(args.config, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
        extra = cfg.get("static_markers", {})
        for name, markers in extra.items():
            for m in markers:
                if m not in keywords:
                    keywords.append(m)

    root = args.apk_dir
    result = {
        "root": root,
        "keywords": scan_keywords(root, keywords, args.limit_per_keyword),
        "urls": {} if args.no_urls else scan_urls(root),
        "appids": scan_appids(root),
        "manifest_components": scan_manifest_components(root),
        "notice": "静态字符串只作线索；必须用 Phase 8 真机 DNS/TLS/HOST 三层抓包证明连接已断。",
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    kw_counts = {k: len(v) for k, v in result["keywords"].items()}
    print(json.dumps({"keywords": kw_counts,
                      "url_count": len(result["urls"]),
                      "appid_count": len(result["appids"])},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
