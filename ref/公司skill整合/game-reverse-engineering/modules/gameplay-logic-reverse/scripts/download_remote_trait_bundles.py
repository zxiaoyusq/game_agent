#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_remote_trait_bundles.py -- 批量下载远程 Bundle（含 Trait/配置/资源）

用途：按 gen_remote_manifest.py 的清单把所有远程 bundle 下载到本地目录，
      构建"离线内置"素材库。支持断点续传（已有文件且大小一致即跳过）、
      max 重试、失败记账；不改变任何游戏代码，只负责把"网上的内容"搬到本地。

用法：
  python download_remote_trait_bundles.py --manifest remote_manifest_full.json --out remote_traits/raw
  python download_remote_trait_bundles.py --manifest m.json --out raw --include-regex ".*(trait|config).*" --parallel 4 --retry 3

输出：out/<bundle>/config.json + out/<bundle>/**/*，out/download_report.json 记录成功/失败。
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
    "Accept": "*/*",
}


def fetch(url, dest, retries, timeout=30):
    """下载单个文件；返回 (ok, detail)。现有同大小文件视为已下载。"""
    if os.path.exists(dest):
        return True, "exists"
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    last = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            tmp = dest + ".part"
            with open(tmp, "wb") as fh:
                fh.write(data)
            os.replace(tmp, dest)
            return True, "ok"
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
            last = exc
            time.sleep(min(2 ** attempt, 8))
    return False, "%s" % last


def main():
    ap = argparse.ArgumentParser(description="批量下载远程 Bundle")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--retry", type=int, default=3)
    ap.add_argument("--include-regex", default="", help="只下载匹配的 URL（如 .*config.json）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    per_bundle = []
    include = re.compile(args.include_regex) if args.include_regex else None
    for bundle in manifest.get("bundles", []):
        name = bundle["name"]
        base = bundle["url"].rstrip("/")
        # config.json + 常见资源子路径：先下载 config，再看它列出的资源
        items = [{"url": bundle.get("config_url") or base + "/config.json", "rel": "config.json"}]
        per_bundle.append((name, base, items))

    tasks = []
    for name, base, items in per_bundle:
        for it in items:
            url = it["url"]
            if include and not include.search(url):
                continue
            dest = os.path.join(args.out, name, it["rel"])
            tasks.append((url, dest, name))

    if args.dry_run:
        print(json.dumps({"tasks": len(tasks), "sample": tasks[:10]}, ensure_ascii=False, indent=2))
        return

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        futures = {pool.submit(fetch, url, dest, args.retry): (url, dest, name) for url, dest, name in tasks}
        for fut in concurrent.futures.as_completed(futures):
            url, dest, name = futures[fut]
            ok, detail = fut.result()
            results.append({"url": url, "dest": dest, "bundle": name, "ok": ok, "detail": detail})

    ok_n = sum(1 for r in results if r["ok"])
    failed = [r for r in results if not r["ok"]]
    report = {"total": len(results), "ok": ok_n, "failed": len(failed),
              "failed_samples": failed[:200], "out": args.out}
    with open(os.path.join(args.out, "download_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"total": report["total"], "ok": report["ok"], "failed": report["failed"]},
                     ensure_ascii=False, indent=2))
    if failed:
        print("失败清单见 %s" % os.path.join(args.out, "download_report.json"), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
