from pathlib import Path
import argparse,hashlib,json,zipfile,shutil,subprocess,sys,tempfile
from build_offline_worker import build as build_offline
ROOT=Path(__file__).resolve().parent.parent

def create(game,out,expected_config=None,allow_lossless_effect_reencoding=False):
 game=Path(game);out=Path(out)
 if out.exists():raise FileExistsError('output exists: '+str(out))
 if expected_config is not None:
  source=json.loads(Path(expected_config).read_text(encoding='utf-8-sig'))
  try:
   text=(game/'level-config.js').read_text(encoding='utf-8-sig').strip()
   prefix='window.oneConnectLevels='
   if not text.startswith(prefix) or not text.endswith(';'):raise ValueError('unexpected wrapper')
   compiled=json.loads(text[len(prefix):-1])
  except (OSError,ValueError) as exc:raise ValueError('invalid generated level configuration') from exc
  if compiled!=source:raise ValueError('level configuration mismatch: apply the level configuration before packaging')
  # Regenerate in a disposable copy so validating a package never modifies its
  # input. This includes the existing compressed-asset and reserve-frame mapping.
  with tempfile.TemporaryDirectory(prefix='oc-package-check-') as tmp:
   candidate=Path(tmp)/'game';shutil.copytree(game,candidate)
   (candidate/'offline-worker.js').unlink(missing_ok=True)
   result=subprocess.run([sys.executable,str(ROOT/'tools/compile_levels.py'),'--config',str(Path(expected_config).resolve()),'--output',str(candidate/'data.js')],capture_output=True,text=True,encoding='utf8',errors='replace')
   if result.returncode:raise ValueError('level compile validation failed: '+result.stderr.strip())
   if json.loads((candidate/'data.js').read_text(encoding='utf8'))!=json.loads((game/'data.js').read_text(encoding='utf8')):raise ValueError('Construct data mismatch: apply the level configuration before packaging')
 data=json.loads((game/'data.js').read_text(encoding='utf8')); refs=set()
 def scan(x):
  if isinstance(x,list):
   for v in x:scan(v)
  elif isinstance(x,dict):
   for v in x.values():scan(v)
  elif isinstance(x,str) and x.startswith('images/'):refs.add(x)
 scan(data);missing=sorted(x for x in refs if not (game/x).is_file())
 if missing:raise ValueError('missing Construct assets: '+str(missing))
 for name in ['dots-sheet0.png','line-sheet0.png','popfx-sheet0.png','popfx-sheet1.png']:
  candidate=game/'images'/name;original=ROOT/'baseline/images'/name
  if candidate.read_bytes()!=original.read_bytes():
   if not allow_lossless_effect_reencoding:raise ValueError('original effect mismatch: '+name)
   from PIL import Image
   with Image.open(candidate) as a,Image.open(original) as b:
    if a.size!=b.size or a.convert('RGBA').tobytes()!=b.convert('RGBA').tobytes():raise ValueError('original effect pixel mismatch: '+name)
 baseline=json.loads((ROOT/'baseline/data.js').read_text(encoding='utf8'))
 def effect_definition(project,name):
  try:
   types=project['project'][3]
   matches=[item for item in types if isinstance(item,list) and item and item[0]==name]
  except (KeyError,IndexError,TypeError):raise ValueError('original effect definition mismatch: '+name)
  if len(matches)!=1:raise ValueError('original effect definition mismatch: '+name)
  return matches[0]
 for name in ('t7','t8','t48'):
  actual=effect_definition(data,name);original=effect_definition(baseline,name)
  if allow_lossless_effect_reencoding:
   import copy
   actual=copy.deepcopy(actual);original=copy.deepcopy(original)
   for definition in (actual,original):
    for animation in definition[7]:
     for frame in animation[7]:frame[1]=0
  if actual!=original:raise ValueError('original effect definition mismatch: '+name)
 if (game/'offline-worker.js').exists():build_offline(game)
 files=sorted(p for p in game.rglob('*') if p.is_file());out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for f in files:z.write(f,f.relative_to(game).as_posix())
 with zipfile.ZipFile(out) as z:
  if z.testzip():raise ValueError('ZIP integrity check failed')
  for f in files:
   if z.read(f.relative_to(game).as_posix())!=f.read_bytes():raise ValueError('ZIP content mismatch: '+str(f))
 return len(files),out.stat().st_size,hashlib.sha256(out.read_bytes()).hexdigest()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--game-dir',default=str(ROOT/'game'));p.add_argument('--config',help='source level configuration to compare before packaging');p.add_argument('--output',required=True);p.add_argument('--allow-lossless-effect-reencoding',action='store_true',help='allow reencoded original effects only if RGBA pixels match');a=p.parse_args();expected=a.config or (ROOT/'config/levels.json' if Path(a.game_dir).resolve()==(ROOT/'game').resolve() else None);n,size,digest=create(a.game_dir,a.output,expected_config=expected,allow_lossless_effect_reencoding=a.allow_lossless_effect_reencoding);print('files',n,'bytes',size,'sha256',digest)
