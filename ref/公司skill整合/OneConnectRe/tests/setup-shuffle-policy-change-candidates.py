"""Build isolated free-to-original policy migration copies."""
import json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for policy in ('free','original'):
    base=root/'analysis'/('shuffle_policy_'+policy);game=base/'game'
    shutil.copytree(root/'game',game,dirs_exist_ok=True)
    config=json.loads((root/'config/levels.json').read_text(encoding='utf8'))
    next(e for e in config['levels'] if e['level']==29)['autoShuffle']=policy
    config_path=base/'levels.json';config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf8')
    subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(config_path),'--output',str(game/'data.js')],cwd=root,check=True)
