"""Isolated fixed deadlock with an explicitly reversible shuffle-failure injection."""
import json, shutil, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
target=root/'analysis/exhaustion_restart_candidate/game'
shutil.copytree(root/'game',target,dirs_exist_ok=True)
config=json.loads((root/'tests/fixtures/deadlock-free.json').read_text(encoding='utf8'))
(target/'level-config.js').write_text('window.oneConnectLevels='+json.dumps(config,separators=(',',':'))+';\n',encoding='utf8')
p=target/'auto-shuffle.js';s=p.read_text(encoding='utf8');needle='      var runtime=this.runtime;'
assert needle in s
s=s.replace(needle,needle+"\n      if(this.sid===742793113326854 && window.__forceShuffleFailure) return;",1)
p.write_text(s,encoding='utf8')
print('isolated controlled deadlock',*build(target))
