"""Build a partial level 13 using decoded board data; bomb behavior is unknown."""
import json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
entry=json.loads((root/'tests/fixtures/level13-expanded.json').read_text(encoding='utf8'))['levels'][0]
entry['generator'].pop('seed',None)
config=json.loads((root/'config/levels.json').read_text(encoding='utf8'))
config['levels']=sorted([e for e in config['levels'] if e['level']!=13]+[entry],key=lambda e:e['level'])
target=root/'analysis/level13_partial_random'
shutil.copytree(root/'game',target/'game',dirs_exist_ok=True)
(target/'levels.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(target/'levels.json'),'--output',str(target/'game/data.js')],cwd=root,check=True)
