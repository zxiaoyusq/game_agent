"""Build isolated 8x10 generated-board candidates without changing shipping config."""
import json,shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker_candidate import build
source=json.loads((root/'config/levels.json').read_text(encoding='utf8'))
for direction in ('up','right'):
    target=root/'analysis'/('expanded_8x10_'+direction)/'game'
    shutil.copytree(root/'game',target,dirs_exist_ok=True)
    candidate=json.loads(json.dumps(source))
    entry=next(x for x in candidate['levels'] if x['level']==17)
    entry['movement']='gravity_'+direction
    entry['generator']=dict(entry['generator'],seed=42)
    (target/'level-config.js').write_text('window.oneConnectLevels='+json.dumps(candidate,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
    print(direction,*build(target))
