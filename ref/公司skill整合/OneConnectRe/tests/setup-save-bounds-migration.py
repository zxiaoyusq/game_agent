"""Build isolated old/new copies for a real pre-change gravity save migration."""
import json, shutil, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
for name in ('save_bounds_old','save_bounds_new'):
    target=root/'analysis'/name/'game'
    shutil.copytree(root/'game',target,dirs_exist_ok=True)
    if name.endswith('old'):
        (target/'round-save-model.js').write_bytes(subprocess.check_output(['git','show','af758ca:game/round-save-model.js'],cwd=root))
        path=target/'level-config.js';config=json.loads(path.read_text(encoding='utf8').split('=',1)[1].strip().removesuffix(';'))
        next(e for e in config['levels'] if e['level']==17).pop('autoShuffle',None)
        path.write_text('window.oneConnectLevels='+json.dumps(config,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
    print(name,*build(target))
