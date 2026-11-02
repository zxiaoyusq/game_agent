# -*- coding: utf-8 -*-
"""md2book_template.py — 通用 md→单文件HTML全书 注入器（模板）

用法：
  1. 复制本脚本到拆解工作目录 tools\ 下
  2. 修改 MAPPING（md 文件 -> 目标 section id -> 面板标题）
  3. 修改 BOOK / DOCS 路径
  4. 直接运行（幂等，可反复执行）
依赖：仅 Python 3.8+ 标准库。目标 HTML 需包含 .tbl/.acc 等 CSS（见
  skill: game-reverse-engineering/modules/deliverable-book-template/SKILL.md 第三节）。
"""
import os, re, html

# ============ 配置区（换游戏只改这里） ============
WORK = r"E:\Gameprogram\<Game>_APK_work"
BOOK = os.path.join(WORK, "<Game>_设计解析全书.html")
DOCS = os.path.join(WORK, "docs")
MAPPING = [
    # (md 文件名, section id, 面板标题)
    ("_EVIDENCE_INDEX.md", "s0", "证据包索引 · 拆解现场规范"),
    ("01_局内合并玩法系统.md", "s4", "深度原文：01_局内合并玩法系统.md（含全部证据行号）"),
    # ... 按目标游戏系统增删
]
# =================================================

ACC_CLS = "acc deep"
MARK = "<!--MDDEEP-->"


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`([^`]+?)`", r"<code>\1</code>", s)
    return s


def md_to_html(md):
    lines = md.splitlines()
    out, i, n = [], 0, len(lines)
    in_code, code_buf = False, []
    list_open = ""

    def close_list():
        nonlocal list_open
        if list_open:
            out.append(f"</{list_open}>")
            list_open = ""

    while i < n:
        ln = lines[i]
        if ln.strip().startswith("```"):
            close_list()
            if in_code:
                out.append('<pre class="code">' + html.escape("\n".join(code_buf)) + "</pre>")
                in_code = False
            else:
                in_code, code_buf = True, []
            i += 1
            continue
        if in_code:
            code_buf.append(ln)
            i += 1
            continue
        s = ln.strip()
        if re.match(r"^(---+|\*\*\*+)$", s):
            close_list(); out.append("<hr class='mdhr'>"); i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            close_list()
            lv = len(m.group(1))
            tag = "h3" if lv == 1 else "h4" if lv == 2 else "h5"
            out.append(f"<{tag} class='mdh'>{inline(m.group(2))}</{tag}>")
            i += 1; continue
        if s.startswith(">"):
            close_list()
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append("<div class='mdquote'>" + "<br>".join(inline(b) for b in buf if b) + "</div>")
            continue
        if s.startswith("|") and i + 1 < n and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
            close_list()
            hdr = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            body = []
            while i < n and lines[i].strip().startswith("|"):
                body.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<div class='tblwrap'><table class='tbl'><thead><tr>" +
                       "".join(f"<th>{inline(h)}</th>" for h in hdr) + "</tr></thead><tbody>" +
                       "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in body) +
                       "</tbody></table></div>")
            continue
        m = re.match(r"^(\d+)[.、]\s+(.*)$", s)
        if m:
            if list_open != "ol":
                close_list(); out.append("<ol>"); list_open = "ol"
            out.append(f"<li>{inline(m.group(2))}</li>"); i += 1; continue
        if re.match(r"^[-*+]\s+", s):
            if list_open != "ul":
                close_list(); out.append("<ul>"); list_open = "ul"
            item = re.sub(r"^[-*+]\s+", "", s)
            out.append(f"<li>{inline(item)}</li>"); i += 1; continue
        close_list()
        if s == "":
            i += 1; continue
        out.append(f"<p class='mdp'>{inline(s)}</p>")
        i += 1
    close_list()
    if in_code:
        out.append('<pre class="code">' + html.escape("\n".join(code_buf)) + "</pre>")
    return "\n".join(out)


STYLE = """
<style>
details.acc.deep{border-left:4px solid var(--acc2,#7c6cff)}
details.acc.deep summary{color:#b9a6ff}
details.acc.deep .bd{font-size:13px;background:#141824}
.mdh{color:#c9b6ff!important}
h3.mdh{font-size:16px;margin:22px 0 8px;border-left:3px solid #4d3a78;padding-left:10px}
h5.mdh{color:#8fd0d6!important;font-size:13.5px}
.mdp{margin:7px 0}
pre.code{background:#0d1017;border:1px solid #2a3142;border-radius:8px;padding:12px 14px;overflow-x:auto;
 font-family:Consolas,monospace;font-size:12px;color:#9ecbff;margin:10px 0;line-height:1.5}
.mdquote{border-left:3px solid #4d3a78;background:#1c1830;padding:8px 14px;margin:10px 0;border-radius:0 8px 8px 0;font-size:12.5px;color:#c5b8e8}
hr.mdhr{border:none;border-top:1px dashed #3a4560;margin:18px 0}
.mdnote{font-size:11px;color:var(--tx3,#66718a);margin:6px 0 2px}
</style>
"""


def main():
    book = open(BOOK, encoding="utf-8").read()
    for md_name, sec_id, title in MAPPING:
        p = os.path.join(DOCS, md_name)
        if not os.path.exists(p):
            print("!! missing", md_name)
            continue
        md = open(p, encoding="utf-8").read()
        body = md_to_html(md)
        panel = (f'<details class="{ACC_CLS}"><summary>📄 {title}</summary>'
                 f'<div class="bd"><p class="mdnote">以下为 {md_name} 全文（自动转换；证据行号/文件路径保持原样）</p>'
                 f"{body}</div></details>")
        m = re.search(r'<section id="' + sec_id + r'">', book)
        if not m:
            print("!! section not found", sec_id)
            continue
        end = book.index("</section>", m.end())
        seg = book[m.start():end]
        seg = re.sub(r"(?:<!--MDDEEP-->.*?</details>\s*)+", "", seg, flags=re.S)  # 幂等清除
        book = book[:m.start()] + seg + panel + book[end:]
        print("injected:", md_name, "->", sec_id, f"({len(body)//1024}KB)")
    if "details.acc.deep" not in book:
        book = book.replace("</head>", STYLE + "</head>")
    open(BOOK, "w", encoding="utf-8").write(book)
    print("book size:", os.path.getsize(BOOK))


if __name__ == "__main__":
    main()
