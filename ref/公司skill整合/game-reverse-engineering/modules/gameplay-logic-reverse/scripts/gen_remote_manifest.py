#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_remote_manifest.py -- 从 Cocos settings.js / _CCSettings 生成远程资源清单

用途：解析构建产物里的远程 Bundle 名单（remoteBundles）与版本表（bundleVers），
      按 URL 模板拼出每个远程 bundle 的完整拉取地址（config.json / 资源文件），
      作为 download_remote_trait_bundles.py 的输入，也是离线内置的基础清单。

用法：
  python gen_remote_manifest.py --settings assets/main/index.js --url-template "https://cdn.example.com/{bundle}/{version}/config.json" --out remote_manifest_full.json
  python gen_remote_manifest.py --settings-dir assets --url-template "https://cdn.example.com/{bundle}/{version}/" --out remote_manifest_full.json

说明：
  - 只解析"远程名单+版本"，不解析资源内容；URL 模板的 {bundle}/{version} 占位符
    必须保留，脚本会按 bundleVers 逐个展开。
  - 若项目把远程配置写在别的键（如 serverUrl / assetRoot），用 --server-regex 覆盖。
"""
import argparse
import glob
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# _CCSettings 常见字段
REMOTE_RE = re.compile(r"""(?is)["']?(?:remotes|remoteBundles|remote_bundles)["']?\s*:\s*\[([^\]]*)\]""")
VERSIONS_RE = re.compile(r"""(?is)["']?(?:bundleVers|bundle_vers|versions)["']?\s*:\s*\{([^}]*)\}""")
SERVER_RE = re.compile(r"""(?is)["'](?:server|cdn|assetRoot|asset_root)["']\s*:\s*["']([^"']+)["']""")
NAME_RE = re.compile(r"""(?is)["'](?:name|bundle|id)["']\s*:\s*["']([^"']+)["']""")


def parse_settings_text(text, url_template, server_regex):
    result = {"bundles": [], "server": None, "warnings": []}
    m = REMOTE_RE.search(text)
    if not m:
        result["warnings"].append("未找到 remoteBundles 数组（可能全部内置或字段名不同）")
    remote_names = []
    if m:
        content = m.group(1)
        for nm in re.finditer(r'["\']([^"\']+)["\']', content):
            name = nm.group(1)
            if name not in remote_names:
                remote_names.append(name)

    vers = {}
    mv = VERSIONS_RE.search(text)
    if mv:
        for pair in re.finditer(r'["\']([^"\']+)["\']\s*:\s*["\']([^"\']+)["\']', mv.group(1)):
            vers[pair.group(1)] = pair.group(2)
    if not vers:
        result["warnings"].append("未找到 bundleVers 版本表，将用 'latest' 兜底并标 WARN")

    server = None
    ms = SERVER_RE.search(text) if not server_regex else server_regex.search(text)
    if ms:
        server = ms.group(1)
    result["server"] = server

    for name in remote_names:
        version = vers.get(name) or vers.get(name + "_bundle") or "latest"
        url = url_template.replace("{bundle}", name).replace("{version}", version)
        if url.lower().endswith(".json"):
            config_url = url
            base_url = url[: url.rfind("/")]
        else:
            config_url = url.rstrip("/") + "/config.json"
            base_url = url.rstrip("/")
        result["bundles"].append({"name": name, "version": version, "url": base_url,
                                  "config_url": config_url,
                                  "deps": None, "unresolved": version == "latest"})
    if not remote_names:
        result["warnings"].append("remoteBundles 为空，输出仅含元信息")
    return result


def main():
    ap = argparse.ArgumentParser(description="生成远程 Bundle 清单")
    ap.add_argument("--settings", default="", help="settings.js 文件路径")
    ap.add_argument("--settings-dir", default="", help="扫描目录（找 index.js/settings*.js/src/…）")
    ap.add_argument("--url-template", required=True,
                    help="如 https://cdn.example.com/{bundle}/{version}/config.json")
    ap.add_argument("--out", default="remote_manifest_full.json")
    ap.add_argument("--server-regex", default="", help="覆盖 server/cdn 字段正则")
    args = ap.parse_args()

    files = []
    if args.settings:
        files = [args.settings]
    elif args.settings_dir:
        for pat in ("**/index.js", "**/settings*.js", "**/project.manifest"):
            files += glob.glob(os.path.join(args.settings_dir, pat), recursive=True)
    if not files:
        print("未找到 settings 文件", file=sys.stderr)
        sys.exit(2)

    texts = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                texts.append((f, fh.read()))
        except OSError:
            continue
    if not texts:
        print("settings 文件不可读", file=sys.stderr)
        sys.exit(2)

    server_regex = None
    if args.server_regex:
        server_regex = re.compile(args.server_regex, re.I)
    merged = {"bundles": [], "server": None, "warnings": [], "sources": [f for f, _ in texts]}
    by_name = {}
    for f, text in texts:
        part = parse_settings_text(text, args.url_template, server_regex)
        for b in part["bundles"]:
            if b["name"] not in by_name:
                by_name[b["name"]] = b
        for w in part["warnings"]:
            merged["warnings"].append("%s: %s" % (f, w))
        if merged["server"] is None:
            merged["server"] = part["server"]
    merged["bundles"] = [by_name[k] for k in sorted(by_name)]
    merged["bundle_count"] = len(merged["bundles"])

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"sources": merged["sources"], "bundles": merged["bundle_count"],
                      "server": merged["server"], "warnings": merged["warnings"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
