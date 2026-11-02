#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_vendor_isolation.py -- 隔离验收三段门禁（静态提示 / 三层网络 / Seed 完整性）

用途：Phase 7 一键汇总：
  1. 静态：按 isolation-config.json 的 static_markers 统计被禁 SDK 标记是否仍存在。
     —— 存在只记 WARN（字符串残留 ≠ 联网），不存在才加分。
  2. 网络：用 capture_network_evidence.py 的结果（evidence.json）核对 blocked 域族
     在 DNS QUERY / TLS SNI / HTTP HOST 三层是否 0 命中；任一 >0 → FAIL。
     同时核对 allowed 域族是否至少有一个成功请求（--allow-missing-allowed 可降级 WARN）。
  3. Seed：把 seed 目录交给 prepare_offline_seed.py --check-only，missing/unmapped/
     hash_conflict 任一 >0 → FAIL。

用法：
  python verify_vendor_isolation.py --apk-dir <decoded> \
      --isolation-config isolation-config.json --network-evidence network_evidence.csv \
      --seed-dir <apk-project>/assets/remote_seed --manifest <...>/project.manifest \
      --out verification.json

退出码：0 = 无 FAIL；1 = 存在 FAIL（--no-fail 时不因 FAIL 退出）。
"""
import argparse
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def import_network_evidence(path):
    """接受 evidence.json（capture 产物）或其原始 CSV，内部转调 capture 脚本。"""
    here = os.path.dirname(os.path.abspath(__file__))
    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    tmp = os.path.join(os.path.dirname(path) or ".", "_tmp_evidence.json")
    subprocess.run([sys.executable, os.path.join(here, "capture_network_evidence.py"),
                    "--input", path, "--out", tmp], check=True)
    with open(tmp, "r", encoding="utf-8") as fh:
        return json.load(fh)


def check_network(evidence, blocked, allowed, allow_missing_allowed):
    checks = []
    fam = evidence.get("families", {}) or {}
    summary = evidence.get("summary", {}) or {}
    for name, _patterns in (blocked or {}).items():
        counts = summary.get(name, {})
        hits = {t: counts.get(t, 0) for t in ("QUERY", "TLS", "HOST")}
        total = sum(hits.values())
        checks.append({
            "kind": "blocked", "family": name, "hits": hits, "total": total,
            "status": "FAIL" if total > 0 else "PASS",
            "samples": fam.get(name, {}),
        })
    for name, _patterns in (allowed or {}).items():
        counts = summary.get(name, {})
        ok = counts.get("HOST", 0) > 0 or counts.get("TLS", 0) > 0
        status = "PASS" if ok else ("WARN" if allow_missing_allowed else "FAIL")
        checks.append({
            "kind": "allowed", "family": name, "hits": {t: counts.get(t, 0) for t in ("QUERY", "TLS", "HOST")},
            "status": status,
            "note": "目标渠道至少需要 HOST/TLS 成功证据" if not ok else "",
        })
    return checks


def check_static(apk_dir, static_markers):
    warnings = []
    if not os.path.isdir(apk_dir) or not static_markers:
        return warnings
    # 复用 scan 脚本做关键字统计
    here = os.path.dirname(os.path.abspath(__file__))
    cfg_tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_static_cfg.json")
    with open(cfg_tmp, "w", encoding="utf-8") as fh:
        json.dump({"static_markers": static_markers}, fh)
    out_tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_surfaces.json")
    subprocess.run([sys.executable, os.path.join(here, "scan_original_sdk_surfaces.py"),
                    "--apk-dir", apk_dir, "--config", cfg_tmp, "--out", out_tmp,
                    "--no-urls"], check=True)
    with open(out_tmp, "r", encoding="utf-8") as fh:
        surfaces = json.load(fh)
    for marker, hits in surfaces.get("keywords", {}).items():
        if hits:
            warnings.append({"marker": marker, "hits": len(hits),
                             "files": sorted({h["file"] for h in hits})[:20]})
    for p in (cfg_tmp, out_tmp):
        try:
            os.remove(p)
        except OSError:
            pass
    return warnings


def check_seed(seed_dir, manifest, report_only):
    here = os.path.dirname(os.path.abspath(__file__))
    args = [sys.executable, os.path.join(here, "prepare_offline_seed.py"),
            "--seed-out", seed_dir, "--check-only", "--report-only"]
    if manifest:
        args += ["--manifest", manifest]
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    raw = proc.stdout.strip()
    report = None
    candidates = [raw, raw.splitlines()[-1] if raw else ""]
    if "{" in raw and "}" in raw:
        candidates.append(raw[raw.find("{"):raw.rfind("}")+1])
    for candidate in candidates:
        try:
            report = json.loads(candidate)
            break
        except (ValueError, TypeError):
            continue
    if report is None:
        report = {"raw_stdout": proc.stdout, "raw_stderr": proc.stderr, "parse_failed": True}
    if proc.returncode != 0:
        report.setdefault("fatal", True)
        report.setdefault("stderr", proc.stderr)
    bad = (report.get("missing") or 0) + (report.get("unmapped") or 0) + (report.get("hash_conflict") or 0)
    if report.get("parse_failed") or report.get("fatal"):
        bad = bad + 1
    return {"status": "FAIL" if bad else "PASS", "report": report}


def main():
    ap = argparse.ArgumentParser(description="隔离验收三段门禁")
    ap.add_argument("--apk-dir", required=True, help="解码后的 APK 目录")
    ap.add_argument("--isolation-config", required=True)
    ap.add_argument("--network-evidence", required=True, help="evidence.json 或原始 CSV")
    ap.add_argument("--seed-dir", default="", help="Seed 目录（assets/remote_seed）")
    ap.add_argument("--manifest", default="", help="project.manifest 路径")
    ap.add_argument("--out", default="verification.json")
    ap.add_argument("--allow-missing-allowed", action="store_true")
    ap.add_argument("--no-fail", action="store_true")
    args = ap.parse_args()

    with open(args.isolation_config, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    blocked = cfg.get("blocked_domain_families", {})
    allowed = cfg.get("allowed_domain_families", {})
    static_markers = cfg.get("static_markers", {})

    evidence = import_network_evidence(args.network_evidence)
    net_checks = check_network(evidence, blocked, allowed, args.allow_missing_allowed)
    static_warnings = check_static(args.apk_dir, static_markers)
    seed_check = check_seed(args.seed_dir, args.manifest, report_only=True) if args.seed_dir else None

    statuses = [c["status"] for c in net_checks]
    if seed_check:
        statuses.append(seed_check["status"])
    has_fail = "FAIL" in statuses
    result = {
        "summary": {"status": "FAIL" if has_fail else "PASS",
                     "network": {c["family"]: c["status"] for c in net_checks if c["kind"] == "blocked"},
                     "allowed": {c["family"]: c["status"] for c in net_checks if c["kind"] == "allowed"},
                     "seed": seed_check["status"] if seed_check else "not-run",
                     "static_warnings": len(static_warnings)},
        "network_checks": net_checks,
        "static_warnings": static_warnings,
        "seed_check": seed_check,
        "note": "WARN = 静态字符串残留/目标渠道缺证据；判定 PASS 以网络层 + Seed 门禁为准。",
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    if has_fail and not args.no_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
