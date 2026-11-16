# -*- coding: utf-8 -*-
"""美术差异复核 · 报告回写（非破坏）：向既有评审 HTML 注入复核横幅与逐屏状态标签。

模式（2026-10-19 DADAPET 实测）：
  - <h1> 后插入复核横幅（日期/方式/工程版本/采集语言/结论速览/新截图目录）
  - 给已复核屏的 <h2> 追加状态标签徽标（✔绿 ✗红 🔄蓝 ⚠橙）
  - 原始问题条目一字不动；不内嵌新截图（引用目录）

用法:
    py -X utf8 artdiff_reaudit_html.py --report 当前美术差异.html \
        --h1 "DADAPET · 美术与交互评审" \
        --banner-file banner.html \
        --chips-json chips.json
chips.json:
  [
    {"anchor": "<h2>清洁界面</h2>", "level": "mixed",  "text": "⚠ 主角✔ 底板✔ / 昵称缺失✗"},
    {"anchor": "<h2>商城界面</h2>", "level": "fail",   "text": "✗ 烧鸡图标仍缺失"}
  ]
level ∈ fixed(绿) fail(红) rebuild(蓝) mixed/partial/warn(橙)
"""
import argparse
import json
from pathlib import Path

COLORS = {
    "fixed":   ("#16a34a", "#ecfdf5"),
    "fail":    ("#dc2626", "#fef2f2"),
    "rebuild": ("#2563eb", "#eff6ff"),
    "mixed":   ("#d97706", "#fffbeb"),
    "partial": ("#d97706", "#fffbeb"),
    "warn":    ("#d97706", "#fffbeb"),
}
STYLE = ("display:inline-block;margin-left:10px;padding:2px 10px;border-radius:999px;"
         "font-size:13px;font-weight:700;vertical-align:middle;")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--h1", required=True, help="横幅插入锚点（通常是整个 <h1>…</h1>）")
    ap.add_argument("--banner-file", required=True, help="横幅 HTML 片段文件")
    ap.add_argument("--chips-json", required=True, help="状态标签清单 JSON")
    a = ap.parse_args()

    p = Path(a.report)
    html = p.read_text(encoding="utf-8")
    assert a.h1 in html, "锚点 h1 不在报告中"
    assert a.h1 not in html.replace(a.h1, "", 1) or html.count(a.h1) == 1, "锚点不唯一，先确认"

    banner = Path(a.banner_file).read_text(encoding="utf-8")
    html = html.replace(a.h1, a.h1 + banner, 1)

    chips = json.load(open(a.chips_json, encoding="utf-8"))
    matched, missed = 0, []
    for c in chips:
        anchor = c["anchor"]
        if anchor not in html:
            missed.append(anchor)
            continue
        color, bg = COLORS.get(c["level"], COLORS["warn"])
        chip = f'<span style="{STYLE}background:{bg};color:{color};">{c["text"]}</span>'
        html = html.replace(anchor, anchor + chip, 1)
        matched += 1

    p.write_text(html, encoding="utf-8")
    print(f"横幅已插入；状态标签 {matched}/{len(chips)}")
    for m in missed:
        print("未匹配（检查措辞/编号是否与报告一致）:", m)


if __name__ == "__main__":
    main()
