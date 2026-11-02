#!/usr/bin/env python3
"""构建 Trait 目录验收 JSON：对齐 本地目录 / 远程清单 / 堆证据 三套口径。

用法:
  python build_trait_acceptance.py \
      --local-dir <本地资产根目录> \
      --catalog <trait 目录名清单.txt> \
      --manifest <remote_manifest_full.json> \
      --evidence <trait_dir_evidence.json> \
      --remote-dec <remote_traits/dec> \
      --out <trait_dir_acceptance.json>

每目录产出: remote_bundle / remote_config / remote_403 / remote_asset_count /
            local_file_count / heap_occurrences / status
"""
import argparse
import collections
import glob
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-dir", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--remote-dec", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    names = [l.strip() for l in open(args.catalog, encoding="utf-8") if l.strip()]
    manifest = json.load(open(args.manifest, encoding="utf-8"))
    evidence = json.load(open(args.evidence, encoding="utf-8"))
    # 兼容两种字段命名：occurrences/classIdRegistered 或 heap_occurrences/heap_classIdRegistered
    def norm_ev(r):
        return {
            "heap_occurrences": r.get("heap_occurrences", r.get("occurrences", 0)),
            "heap_classIdRegistered": r.get("heap_classIdRegistered", r.get("classIdRegistered", False)),
        }
    ev_rows = {r["dir"]: norm_ev(r) for r in evidence.get("rows", [])}

    # 本地资产文件按目录 basename 聚合
    local_files = collections.defaultdict(list)
    for root, _dirs, files in os.walk(args.local_dir):
        for fn in files:
            local_files.setdefault(os.path.basename(root), []).append(fn)

    def remote_assets(bundle):
        exts = collections.Counter()
        for p in glob.glob(os.path.join(args.remote_dec, bundle, "**", "*.*"), recursive=True):
            if os.path.isfile(p):
                exts[os.path.splitext(p)[1]] += 1
        return sum(exts.values()), dict(exts)

    rows = []
    for d in names:
        if d not in manifest.get("bundleVers", {}) and ("Remote_" + d) not in manifest.get("bundleVers", {}):
            remote_name = None
        else:
            remote_name = d if d in manifest["bundleVers"] else "Remote_" + d
        local = local_files.get(d, [])
        n_assets, a_exts = remote_assets(remote_name) if remote_name else (0, {})
        ev = ev_rows.get(d, {})
        status = []
        if remote_name:
            if glob.glob(os.path.join(args.remote_dec, remote_name, "config.*.json")):
                status.append("remote-config-ok")
            else:
                status.append("remote-403")
        if n_assets:
            status.append("remote-assets-ok")
        if local:
            status.append("local-files")
        if ev.get("heap_classIdRegistered"):
            status.append("heap-classid")
        if ev.get("heap_occurrences", 0) > 0:
            status.append("heap-evidence")
        rows.append({
            "dir": d,
            "remote_bundle": remote_name,
            "remote_config": bool(remote_name and glob.glob(os.path.join(args.remote_dec, remote_name, "config.*.json"))),
            "remote_403": bool(remote_name and not glob.glob(os.path.join(args.remote_dec, remote_name, "config.*.json"))),
            "remote_asset_count": n_assets,
            "remote_asset_exts": a_exts,
            "local_file_count": len(local),
            "local_exts": dict(collections.Counter(os.path.splitext(f)[1] for f in local)),
            "heap_occurrences": ev.get("heap_occurrences", 0),
            "heap_classIdRegistered": ev.get("heap_classIdRegistered", False),
            "status": ";".join(status),
        })

    unique = sorted({r["dir"] for r in rows})
    summary = {
        "user_count_262": len(rows),
        "unique_dirs": len(unique),
        "local_with_files": sum(1 for r in rows if r["local_file_count"] > 0),
        "remote_bundle_exists": sum(1 for r in rows if r["remote_bundle"]),
        "remote_config_downloaded": sum(1 for r in rows if r["remote_config"]),
        "remote_403": sum(1 for r in rows if r["remote_403"]),
        "heap_evidence": sum(1 for r in rows if r["heap_occurrences"] > 0),
        "heap_classid": sum(1 for r in rows if r["heap_classIdRegistered"]),
        "full_trait_bundles_remote_manifest": manifest.get("trait_bundle_count"),
    }
    out = {"summary": summary, "unique_dirs": unique, "all_rows": rows}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
