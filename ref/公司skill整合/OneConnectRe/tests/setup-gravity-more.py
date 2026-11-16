from pathlib import Path
import argparse,json,shutil,subprocess,sys
root=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--direction',choices=['up','left']);p.add_argument('--generated',action='store_true');p.add_argument('--tools',action='store_true');a=p.parse_args()
target=Path(a.output).resolve()
if (root/'analysis').resolve() not in target.parents or target.exists():raise SystemExit('output must be a new directory under analysis')
shutil.copytree(root/'game',target/'game');game=target/'game'
for name in ['board-gravity.js','gravity-runtime.js','board-hooks.js','gravity-generator.js']:shutil.copyfile(root/'tests/fixtures/gravity-more'/name,game/name)
if a.direction:
 screen=[[1,1,0,0],[0,2,3,0],[2,0,3,0],[0,0,0,0]];board=[[0]*12 for _ in range(6)]
 for r in range(4):
  for c in range(4):board[1+c][11-(3+r)]=screen[r][c]
 entry={'level':13,'seconds':180,'movement':'gravity_'+a.direction,'gravity':{'top':3,'left':1,'rows':4,'cols':4},'board':board}
 if a.generated:
  mask=[[int(1<=y<5 and 5<=x<9) for x in range(12)] for y in range(6)]
  entry={'level':13,'seconds':180,'movement':'gravity_'+a.direction,'gravity':{'top':3,'left':1,'rows':4,'cols':4},'generator':{'mask':mask,'typeCount':8,'seed':42}}
 (game/'level-config.js').write_text('window.oneConnectLevels='+json.dumps({'levels':[entry]},separators=(',',':'))+';',encoding='utf8')
if a.tools:
 tools=target/'tools';tools.mkdir()
 for name in ['board_solver.js','compile_levels.py']:shutil.copyfile(root/'tests/fixtures/gravity-more'/name,tools/name)
 shutil.copyfile(root/'tools/build_offline_worker.py',tools/'build_offline_worker.py')
 shutil.copyfile(root/'tests/fixtures/gravity-more/关卡编辑.html',target/'关卡编辑.html')
subprocess.run([sys.executable,str(root/'tools/build_offline_worker.py'),'--game-dir',str(game)],check=True)
print('isolated gravity candidate',target)
