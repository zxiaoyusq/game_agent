from pathlib import Path
p=Path('natural_win.cjs');s=p.read_text(encoding='utf-8-sig');s=s.replace("let arr=[];for(let yy=20", "let ix=((85+y*101+10)*info.width+89+x*101)*3;if(data[ix]+data[ix+1]+data[ix+2]<250)continue;let arr=[];for(let yy=20")
s=s.replace("for(let step=0;step<36;step++){let pair=null;", "for(let step=0;step<60;step++){grid=await classify();let remain=grid.flat().filter(x=>x!==-1).length;if(!remain){console.log('BOARD CLEAR');break}let pair=null;")
s=s.replace("if(!pair){console.log('NO_PAIR step',step);break}","if(!pair){console.log('NO_PAIR shuffle',step);await p.mouse.click(1010,48);await p.waitForTimeout(5500);continue}")
s=s.replace("await p.waitForTimeout(200);console.log('pair',step+1)","await p.waitForTimeout(600);console.log('pair',step+1)")
s=s.replace("natural_win.cjs", "natural_win2.cjs")
Path('natural_win2.cjs').write_text(s,encoding='utf-8')
