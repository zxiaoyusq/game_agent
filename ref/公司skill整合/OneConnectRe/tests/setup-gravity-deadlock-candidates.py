"""Build isolated controlled gravity/deadlock fixtures for device testing."""
import json, shutil, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker_candidate import build
for level in (17,22,24):
    target=root/'analysis'/f'gravity_deadlock_{level}'/'game'
    shutil.copytree(root/'game',target,dirs_exist_ok=True)
    fixture=json.loads((root/'tests'/'fixtures'/f'level{level}-gravity-deadlock.json').read_text(encoding='utf8'))
    (target/'level-config.js').write_text('window.oneConnectLevels='+json.dumps(fixture,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
    print(level,*build(target))
for name in ('gravity_policy_old','gravity_policy_new'):
    target=root/'analysis'/name/'game'
    shutil.copytree(root/'game',target,dirs_exist_ok=True)
    config_file=target/'level-config.js'
    config=json.loads(config_file.read_text(encoding='utf8').split('=',1)[1].strip().removesuffix(';'))
    if name.endswith('old'):
        for entry in config['levels']:
            if entry['level'] in (17,22,24): entry.pop('autoShuffle',None)
    config_file.write_text('window.oneConnectLevels='+json.dumps(config,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
    print(name,*build(target))
