from pathlib import Path
import argparse,shutil,subprocess,sys
root=Path(__file__).resolve().parent.parent;p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--legacy',action='store_true');a=p.parse_args();dest=Path(a.output).resolve()
if (root/'analysis').resolve() not in dest.parents or dest.exists():raise SystemExit('output must be a new directory under analysis')
shutil.copytree(root/'game',dest/'game')
if a.legacy:shutil.copyfile(root/'tests/fixtures/expanded-existing-before/board-hooks.js',dest/'game/board-hooks.js')
subprocess.run([sys.executable,str(root/'tools/build_offline_worker.py'),'--game-dir',str(dest/'game')],check=True)
print('isolated compact geometry test',dest,'legacy' if a.legacy else 'current')
