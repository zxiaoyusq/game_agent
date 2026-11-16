from pathlib import Path
import argparse,shutil
root=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);a=p.parse_args();dest=Path(a.candidate).resolve()
if (root/'analysis').resolve() not in dest.parents or not (dest/'game/images/tiles-reserve-test.png').is_file():raise SystemExit('candidate must be an existing isolated capacity candidate under analysis')
tools=dest/'tools';tools.mkdir(exist_ok=True);shutil.copyfile(root/'tools/board_solver.js',tools/'board_solver.js');shutil.copyfile(root/'tools/build_offline_worker.py',tools/'build_offline_worker.py')
s=(root/'tools/compile_levels.py').read_text(encoding='utf8').replace('ROOT=Path(__file__).resolve().parent.parent','ROOT=Path(__file__).resolve().parent.parent.parent.parent')
if 'min(20,cells//2)' in s:
 for old,new in [('min(20,cells//2)','min(30,cells//2)'),('0<=v<=20','0<=v<=30'),('integers from 0 to 20','integers from 0 to 30')]:assert old in s;s=s.replace(old,new)
 needle="    jsdest=dest.with_name('level-config.js')"
 insert="""    extra=dest.parent/'images/tiles-reserve-test.png'
    if not extra.is_file(): raise ValueError('missing reserve atlas')
    animations=output['project'][3][5][7]
    if len(animations)!=3 or any(len(a[7])!=20 for a in animations): raise ValueError('unexpected tile animation layout')
    for anim in animations:
        for i in range(10): anim[7].append(['images/tiles-reserve-test.png',extra.stat().st_size,1+(i%5)*98,1+(i//5)*98,96,96,1,0.5,0.5,[],[],0])
"""
 assert needle in s;s=s.replace(needle,insert+needle)
(tools/'compile_levels.py').write_text(s,encoding='utf8')
s=(root/'关卡编辑.html').read_text(encoding='utf8')
if 'max="20"' in s:
 for old,new in [('max="20"','max="30"'),('id<=20','id<=30'),('Array(20).fill(0)','Array(30).fill(0)'),('Math.min(20,n/2)','Math.min(30,n/2)'),('v>20','v>30')]:assert old in s;s=s.replace(old,new)
 old="button.title='牌型 '+id;button.style.backgroundPosition=`${-(0.5+((id-1)%5)*49)}px ${-(0.5+Math.floor((id-1)/5)*49)}px`;"
 new="button.title='牌型 '+id;let originalId=id;if(id>20){button.style.backgroundImage=\"url('game/images/tiles-reserve-test.png')\";button.style.backgroundSize='256px 128px';id-=20}button.style.backgroundPosition=`${-(0.5+((id-1)%5)*49)}px ${-(0.5+Math.floor((id-1)/5)*49)}px`;"
 assert old in s;s=s.replace(old,new);s=s.replace("button.setAttribute('aria-label','牌型 '+id)","button.setAttribute('aria-label','牌型 '+originalId)");
(dest/'关卡编辑.html').write_text(s,encoding='utf8')
print('isolated editor and compiler prepared',dest)
