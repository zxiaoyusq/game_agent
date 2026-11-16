from pathlib import Path
p=Path('tests/natural-clear.cjs');s=p.read_text(encoding='utf-8-sig');s=s.replace("await p.waitForTimeout(6000);await p.screenshot({path:'screenshots/dev_win_result.png'});", "await p.waitForTimeout(6000);await p.screenshot({path:'screenshots/dev_win_result.png'});await p.mouse.click(640,350);await p.waitForTimeout(6500);await p.screenshot({path:'screenshots/dev_bonus_open.png'});await p.mouse.click(640,350);await p.waitForTimeout(6500);await p.screenshot({path:'screenshots/dev_bonus_next.png'});")
Path('tests/natural-progress.cjs').write_text(s,encoding='utf-8')
