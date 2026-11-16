from pathlib import Path
s=Path('tests/board-first.cjs').read_text(encoding='utf-8-sig');s=s.replace("await p.mouse.click(425,460);", "await p.mouse.click(Number(process.env.THEME_X||425),460);");Path('tests/board-first.cjs').write_text(s,encoding='utf8')
