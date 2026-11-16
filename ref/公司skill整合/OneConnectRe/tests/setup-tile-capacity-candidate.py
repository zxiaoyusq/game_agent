from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys
from PIL import Image
root=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--full',action='store_true');p.add_argument('--gravity',action='store_true');p.add_argument('--deadlock',action='store_true');a=p.parse_args()
out=Path(a.output).resolve();allowed=(root/'analysis').resolve()
if allowed not in out.parents or out.exists():raise SystemExit('output must be a new directory under analysis')
source=root/'美术换皮准备/20261029_四主题换皮/斋月_三处修正版_96px'
manifest=json.loads((root/'美术换皮准备/20261029_四主题换皮/斋月_备用切片清单.json').read_text(encoding='utf8'))
shutil.copytree(root/'game',out/'game');d=out/'game';atlas=Image.new('RGBA',(512,256),(0,0,0,0))
for i in range(10):
 path=source/f'斋月_{i+1:02}.png';expected=manifest['tiles'][i]
 assert expected['file']==path.name and hashlib.sha256(path.read_bytes()).hexdigest()==expected['sha256']
 im=Image.open(path).convert('RGBA');assert im.size==(96,96)
 atlas.paste(im,(1+(i%5)*98,1+(i//5)*98))
p=d/'images/tiles-reserve-test.png';atlas.save(p,optimize=True)
path=d/'data.js';data=json.loads(path.read_text(encoding='utf8'));anims=data['project'][3][5][7]
assert len(anims)==3 and len({len(anim[7]) for anim in anims})==1
frame_count=len(anims[0][7])
if frame_count==20:
 for anim in anims:
  for i in range(10):anim[7].append(['images/tiles-reserve-test.png',p.stat().st_size,1+(i%5)*98,1+(i//5)*98,96,96,1,0.5,0.5,[],[],0])
elif frame_count!=30 or any(anim[7][29][0]!='images/tiles-reserve-test.png' for anim in anims):raise ValueError('unexpected tile animation layout')
path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')
for name,old,new in [('board-hooks.js','v > 20','v > 30'),('round-save-model.js','v>20','v>30'),('board-generator.js','types>20','types>30')]:
 path=d/name;s=path.read_text(encoding='utf8')
 if old in s:s=s.replace(old,new)
 elif new not in s:raise ValueError('unexpected '+name)
 path.write_text(s,encoding='utf8')
if 'n>30' not in (d/'gravity-generator.js').read_text(encoding='utf8'):shutil.copyfile(root/'tests/fixtures/gravity-generator-30-candidate.js',d/'gravity-generator.js')
board=[[0]*12 for _ in range(6)]
if a.full:
 for i in range(10):
  row=2+i//5;col=1+2*(i%5);board[row][col]=board[row][col+1]=21+i
else:board[2][4]=board[2][5]=21;board[3][4]=board[3][5]=22
entry={'level':13,'seconds':180,'movement':'static','board':board}
if a.gravity:
 mask=[[int(i<6)]*10 for i in range(8)]
 entry={'level':13,'seconds':3600,'movement':'gravity_down','boardSize':{'rows':8,'cols':10,'itemSize':75,'spacing':5,'offsetX':240,'offsetY':35},'gravity':{'top':0,'left':0,'rows':10,'cols':6},'generator':{'mask':mask,'typeCount':30,'seed':1234}}
if a.deadlock:
 entry=json.loads((root/'tests/fixtures/deadlock-expanded-tiles.json').read_text(encoding='utf8'))['levels'][0]
(d/'level-config.js').write_text('window.oneConnectLevels='+json.dumps({'levels':[entry]},separators=(',',':'))+';',encoding='utf8')
subprocess.run([sys.executable,str(root/'tools/build_offline_worker.py'),'--game-dir',str(d)],check=True)
print('isolated candidate',out,'atlas bytes',p.stat().st_size)
