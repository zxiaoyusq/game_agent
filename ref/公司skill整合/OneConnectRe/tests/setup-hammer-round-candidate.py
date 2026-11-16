"""Isolated proof of stable-snapshot evidence; not production transaction code."""
import shutil, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
game=root/'analysis/hammer_round_evidence_candidate/game'
shutil.copytree(root/'game',game,dirs_exist_ok=True)
path=game/'round-save.js';s=path.read_text(encoding='utf8')
old='  pendingDisplay=s;return s;';new="  if(typeof s.hammerOperationId==='string')window.oneConnectPendingHammerTag=s.hammerOperationId;pendingDisplay=s;return s;"
assert old in s;s=s.replace(old,new,1)
old='  if(!window.oneConnectRoundSaveModel.validate(s,entry))return false;';new="  if(typeof window.oneConnectPendingHammerTag==='string')s.hammerOperationId=window.oneConnectPendingHammerTag;\n"+old
assert old in s;s=s.replace(old,new,1);path.write_text(s,encoding='utf8')
print('isolated stable marker experiment',*build(game))
