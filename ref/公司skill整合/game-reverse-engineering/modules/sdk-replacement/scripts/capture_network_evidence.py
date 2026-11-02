#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
capture_network_evidence.py -- 通用三层网络证据分类器（DNS QUERY / TLS SNI / HTTP HOST）

用途：把真机抓包导出的 CSV（PCAPdroid 导出 / mitmproxy 导出转换 / 手工整理的
      ts,direction,type,domain,ip,path,status 行）按 isolation-config.json 中
      blocked / allowed 域族归类，并统计每个域族在三个协议层的命中次数。

输入 CSV 列（顺序不敏感，按表头识别，缺列时按位置 0..6）：
  ts,direction,type,domain,ip,path,status
  type 取值：QUERY（DNS query）、TLS（TLS SNI）、HOST（HTTP Host）；大小写不敏感。

用法：
  python capture_network_evidence.py --input net1.csv,net2.csv --config isolation-config.json --out evidence.json
  python capture_network_evidence.py --input all.csv --families-only vendor-a,vendor-b --out evidence.json

说明：--families-only 用于没有 isolation-config.json 的快速归类；域族条目支持
  "*.a.com"（后缀匹配）、"a.com"（精确+子域）、正则 if 形如 "~regex"。
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def load_families(config_path, families_only):
    families = {}
    if config_path:
        with open(config_path, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
        for name, patterns in cfg.get("blocked_domain_families", {}).items():
            families.setdefault("blocked", {})[name] = list(patterns)
        for name, patterns in cfg.get("allowed_domain_families", {}).items():
            families.setdefault("allowed", {})[name] = list(patterns)
    if families_only:
        for name in families_only.split(","):
            name = name.strip()
            if name:
                families.setdefault("blocked", {})[name] = []
    return families


def compile_matcher(patterns):
    exact = []
    suffix = []
    regex = []
    for p in patterns or []:
        p = p.strip().lower()
        if not p:
            continue
        if p.startswith("~"):
            regex.append(re.compile("(?i)" + p[1:]))
        elif p.startswith("*."):
            suffix.append(p[2:])
        else:
            exact.append(p)
    return exact, suffix, regex


def match_family(domain, entries):
    """entries: list of (family_name, exact, suffix, regex). Return first family name or None."""
    d = (domain or "").strip().lower().rstrip(".")
    if not d:
        return None
    for name, exact, suffix, regex in entries:
        if d in exact:
            return name
        for suf in suffix:
            if d == suf or d.endswith("." + suf):
                return name
        for rx in regex:
            if rx.search(d):
                return name
    return None


def classify(rows, families):
    """rows: list of dict with type/domain. Returns {family: {type: [samples]}}."""
    entries = []
    for bucket in ("blocked", "allowed"):
        for name, patterns in families.get(bucket, {}).items():
            exact, suffix, regex = compile_matcher(patterns)
            entries.append((bucket + ":" + name, exact, suffix, regex))
    out = defaultdict(lambda: defaultdict(list))
    unclassified = []
    for row in rows:
        t = (row.get("type") or "UNKNOWN").strip().upper()
        d = row.get("domain") or ""
        family = match_family(d, entries)
        if family is None:
            if t in ("QUERY", "TLS", "HOST"):
                unclassified.append({k: row.get(k) for k in ("ts", "type", "domain", "ip", "path", "status")})
            continue
        sample = {k: row.get(k) for k in ("ts", "type", "domain", "ip", "path", "status")}
        key = family.split(":", 1)[1]
        out[key][t].append(sample)
        # 控制列表长度，避免超大 JSON
        if len(out[key][t]) > 500:
            del out[key][t][:100]
        row["_family"] = family
    return out, unclassified, entries


def main():
    ap = argparse.ArgumentParser(description="三层网络证据分类器")
    ap.add_argument("--input", required=True, help="CSV 文件，逗号分隔多个")
    ap.add_argument("--config", default="", help="isolation-config.json（blocked/allowed 域族）")
    ap.add_argument("--families-only", default="", help="无 config 时的快速域族名（逗号分隔，归 blocked）")
    ap.add_argument("--out", default="evidence.json")
    ap.add_argument("--dedupe", action="store_true", help="按 (type,domain,ip,path) 去重后计数")
    args = ap.parse_args()

    files = [f.strip() for f in args.input.split(",") if f.strip()]
    rows = []
    for fn in files:
        with open(fn, "r", encoding="utf-8-sig", errors="replace") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                continue
            # 规范化列名
            name_map = {}
            for col in reader.fieldnames:
                c = col.strip().lower().replace(" ", "").replace("_", "")
                if c in ("ts", "time", "timestamp"):
                    name_map[col] = "ts"
                elif c in ("direction", "dir"):
                    name_map[col] = "direction"
                elif c in ("type", "kind"):
                    name_map[col] = "type"
                elif c in ("domain", "host", "servername"):
                    name_map[col] = "domain"
                elif c in ("ip", "destip"):
                    name_map[col] = "ip"
                elif c in ("path", "url"):
                    name_map[col] = "path"
                elif c in ("status", "code"):
                    name_map[col] = "status"
                else:
                    name_map[col] = c
            for raw in reader:
                row = {}
                for k, v in raw.items():
                    row[name_map.get(k, k)] = (v or "").strip()
                rows.append(row)

    if args.dedupe:
        seen = set()
        deduped = []
        for r in rows:
            key = (r.get("type", "").upper(), r.get("domain", ""), r.get("ip", ""), r.get("path", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)
        del rows
        rows = deduped

    families = load_families(args.config, args.families_only)
    out, unclassified, entries = classify(rows, families)
    summary = {}
    for name, types in sorted(out.items()):
        summary[name] = {t: len(v) for t, v in sorted(types.items())}

    result = {
        "input_files": files,
        "rows_total": len(rows),
        "families": {k: dict(v) for k, v in out.items()},
        "summary": summary,
        "unclassified_count": len(unclassified),
        "unclassified_samples": unclassified[:200],
        "note": "type=QUERY(DNS)/TLS(SNI)/HOST(HTTP Host)；blocked 各层计数必须为 0 才通过 Phase 8。",
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"rows": len(rows), "summary": summary,
                      "unclassified": len(unclassified)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
