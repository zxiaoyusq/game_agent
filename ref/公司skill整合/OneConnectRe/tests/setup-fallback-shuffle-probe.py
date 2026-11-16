"""Controlled deadlock injection into an isolated unconfigured-level copy."""
import json,shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'))
from build_offline_worker_candidate import build
game=root/'analysis'/'fallback_shuffle_candidate'/'game';shutil.copytree(root/'game',game,dirs_exist_ok=True)
fixture=json.loads((root/'tests/fixtures/deadlock-free.json').read_text(encoding='utf8'));board=json.dumps(fixture['levels'][0]['board'],separators=(',',':'))
hook=game/'board-hooks.js';source=hook.read_text(encoding='utf8');needle='    if (!hasBoard && !saved) {'
injected="    if(current===13 && !hasBoard && !saved){var probe="+board+",arr=runtime.types.t0.instances[0],global=runtime.types.t32.instances[0];for(var y=1;y<=6;y++)for(var x=1;x<=12;x++)arr.arr[x][y][0]=probe[y-1][x-1];global.instance_vars[3]=56;}\n"
if needle not in source:raise RuntimeError('board insertion point missing')
hook.write_text(source.replace(needle,injected+needle,1),encoding='utf8');print('controlled fallback candidate',*build(game))
