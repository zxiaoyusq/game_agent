from pathlib import Path
s=Path('tests/natural-clear.cjs').read_text(encoding='utf-8-sig')
s=s.replace('for(let i=0;i<60;i++)','for(let i=0;i<120;i++)')
s=s.replace("if(s.level>1||s.tiles.length===0){console.log('CLEARED',JSON.stringify(s));break}","if(s.level>=3){console.log('REACHED_LEVEL_3',s.level);break}if(s.tiles.length===0){console.log('OPEN_BONUS',s.level);await p.waitForTimeout(3000);await p.mouse.click(640,350);await p.waitForTimeout(6500);continue}")
s=s.replace("await p.screenshot({path:'screenshots/dev_win_result.png'});", "await p.screenshot({path:'screenshots/config_level3.png'});")
Path('tests/natural-three.cjs').write_text(s,encoding='utf-8')
