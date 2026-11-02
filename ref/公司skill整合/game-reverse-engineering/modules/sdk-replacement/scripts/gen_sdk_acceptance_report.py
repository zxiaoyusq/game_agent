#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_sdk_acceptance_report.py -- 生成"完全替换 SDK"验收报告 Markdown

用途：把 Phase 7/8 的 evidence.json + verification.json（+ 可选 acceptance_contract.md、
      baseline.json）汇总成可交付的中文验收报告；报告不会自动给结论，最终判定
      以真机 DNS/TLS/HOST 三层证据 + 业务回归为准。

用法：
  python gen_sdk_acceptance_report.py --evidence network_evidence.json \
      --verification verification.json --out 验收报告.md
  python gen_sdk_acceptance_report.py --evidence evidence.json --verification verification.json \
      --contract acceptance_contract.md --baseline baseline.json --apk-info apk.json --out 验收报告.md
"""
import argparse
import datetime
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def load(path, default=None):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return default


def fmt_hits(obj):
    parts = []
    for t in ("QUERY", "TLS", "HOST"):
        parts.append("%s=%s" % (t, obj.get(t, 0)))
    return ", ".join(parts)


def main():
    ap = argparse.ArgumentParser(description="生成验收报告")
    ap.add_argument("--evidence", required=True, help="capture_network_evidence.py 产物")
    ap.add_argument("--verification", required=True, help="verify_vendor_isolation.py 产物")
    ap.add_argument("--contract", default="", help="acceptance_contract.md")
    ap.add_argument("--baseline", default="", help="baseline.json")
    ap.add_argument("--apk-info", default="", help="apk.json（sha256/签名/是否断网复验等字段）")
    ap.add_argument("--out", default="验收报告.md")
    ap.add_argument("--title", default="完全替换 SDK 验收报告")
    args = ap.parse_args()

    ev = load(args.evidence, {})
    ver = load(args.verification, {})
    base = load(args.baseline, {})
    apk = load(args.apk_info, {})
    contract_text = ""
    if args.contract and os.path.exists(args.contract):
        with open(args.contract, "r", encoding="utf-8") as fh:
            contract_text = fh.read()

    lines = []
    lines.append("# %s" % args.title)
    lines.append("")
    lines.append("- 生成时间：%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if base:
        lines.append("- 基线：`%s`（APK SHA-256 `%s`）" % (base.get("name", "-"), base.get("apk_sha256", "-")))
    if apk:
        lines.append("- 交付 APK：`%s`（SHA-256 `%s`，证书 `%s`）" %
                     (apk.get("name", "-"), apk.get("sha256", "-"), apk.get("cert_sha256", "-")))
    lines.append("")
    lines.append("## 1. 结论摘要")
    lines.append("")
    summ = ver.get("summary", {}) or {}
    lines.append("- 门禁总体：**%s**" % summ.get("status", "?"))
    lines.append("- 被禁域族各层命中：%s" % json.dumps(summ.get("network", {}), ensure_ascii=False))
    lines.append("- 目标渠道：%s" % json.dumps(summ.get("allowed", {}), ensure_ascii=False))
    lines.append("- Seed 门禁：**%s**（%s）" % (summ.get("seed", "?"), (ver.get("seed_check") or {}).get("report", {}).get("missing", "?")))
    lines.append("- 静态残留 WARN 数：%d" % summ.get("static_warnings", 0))
    lines.append("")

    lines.append("## 2. 目标渠道（新 SDK）联网证据")
    lines.append("")
    fam = ev.get("families", {}) or {}
    summ_map = ev.get("summary", {}) or {}
    allowed_names = [c["family"] for c in ver.get("network_checks", []) if c["kind"] == "allowed"]
    for name in allowed_names:
        lines.append("### %s" % name)
        lines.append("")
        hits = summ_map.get(name, {})
        lines.append("- 三层命中：%s" % fmt_hits(hits))
        lines.append("- 样本：%d 条（详见 evidence.json）" % sum(len(fam.get(name, {}).get(t, [])) for t in ("QUERY", "TLS", "HOST")))
        lines.append("")
    if not allowed_names:
        lines.append("（配置中无 allowed 域族）")
        lines.append("")

    lines.append("## 3. 被禁域族三层核查")
    lines.append("")
    lines.append("| 域族 | QUERY | TLS | HOST | 判定 |")
    lines.append("|---|---|---|---|---|")
    for c in ver.get("network_checks", []):
        if c["kind"] == "blocked":
            lines.append("| %s | %s | %s | %s | %s |" %
                         (c["family"], c["hits"].get("QUERY", 0), c["hits"].get("TLS", 0),
                          c["hits"].get("HOST", 0), c["status"]))
    lines.append("")
    lines.append("结论：被禁域族三层命中均为 0 才代表原厂连接已断；若某个域族 UNCLASSIFIED 样本出现，需人工复核归类后再下结论。")
    lines.append("")

    lines.append("## 4. Seed 离线内置门禁")
    lines.append("")
    seed = ver.get("seed_check") or {}
    rep = seed.get("report", {}) or {}
    lines.append("- 状态：**%s**" % seed.get("status", "not-run"))
    lines.append("- missing=%s unmapped=%s hash_conflict=%s（expected=%s seed_files=%s）" %
                 (rep.get("missing", "?"), rep.get("unmapped", "?"), rep.get("hash_conflict", "?"),
                  rep.get("expected_files", "?"), rep.get("seed_files", "?")))
    if rep.get("missing_samples"):
        lines.append("- missing 样例：`%s`" % "`, `".join(rep["missing_samples"][:30]))
    if rep.get("unmapped_samples"):
        lines.append("- unmapped 样例：`%s`" % "`, `".join(rep["unmapped_samples"][:30]))
    lines.append("")

    lines.append("## 5. 静态残留（只读提示）")
    lines.append("")
    if ver.get("static_warnings"):
        lines.append("| 标记 | 命中数 | 文件样例 |")
        lines.append("|---|---|---|")
        for w in ver["static_warnings"]:
            files = "`, `".join(w.get("files", [])[:5])
            lines.append("| `%s` | %d | `%s` |" % (w["marker"], w["hits"], files))
    else:
        lines.append("无（或未配置 static_markers）。")
    lines.append("")
    lines.append("> 注意：静态字符串/类残留不作为已断网的依据；网络层 0 命中才是。")
    lines.append("")

    lines.append("## 6. 验收契约")
    lines.append("")
    if contract_text:
        lines.append("```text")
        lines.append(contract_text.strip())
        lines.append("```")
    else:
        lines.append("（未提供 acceptance_contract.md，请人工按 Phase 2 契约逐条对照。）")
    lines.append("")

    lines.append("## 7. 未尽事项与下一步")
    lines.append("")
    lines.append("- [ ] 联网冷启动 ×3 与断网冷启动 ×3 记录（截图/录屏/业务事件）")
    lines.append("- [ ] 目标渠道平台后台核对（展示/埋点/转化）")
    lines.append("- [ ] 模拟器结论已复核为真机结论（本报告不替代真机 QA）")
    lines.append("- [ ] 若 Phase 6 执行过：静态扫描被摘除 SDK 标记为 0 的证据")
    lines.append("")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("report written:", os.path.abspath(args.out), "lines:", len(lines))


if __name__ == "__main__":
    main()
