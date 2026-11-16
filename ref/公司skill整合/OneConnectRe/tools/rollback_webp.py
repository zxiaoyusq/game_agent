from pathlib import Path
import argparse,hashlib,json,shutil
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--game-dir',type=Path,default=ROOT/'game');parser.add_argument('--backup-dir',type=Path,default=ROOT/'backups/webp_integration_20261030');parser.add_argument('--apply',action='store_true');args=parser.parse_args(); game=args.game_dir;back=args.backup_dir
rows=json.loads((back/'manifest.json').read_text(encoding='utf8'));mapping=json.loads((game/'asset-formats.json').read_text(encoding='utf8'))
assert mapping=={x['original']:x['webp'] for x in rows},'asset mapping changed'
for x in rows:
 assert hashlib.sha256((game/x['webp']).read_bytes()).hexdigest()==x['webp_sha256'],'compressed asset changed: '+x['webp']
 assert hashlib.sha256((back/x['original']).read_bytes()).hexdigest()==x['source_sha256'],'backup changed: '+x['original']
 assert not (game/x['original']).exists(),'original path already exists'
old=(back/'data.js').read_text(encoding='utf8');expected=old
for x in rows:expected=expected.replace(x['original'],x['webp'])
assert (game/'data.js').read_text(encoding='utf8')==expected,'data.js changed since integration; manual merge needed'
if args.apply:
 for x in rows:shutil.copy2(back/x['original'],game/x['original'])
 shutil.copy2(back/'data.js',game/'data.js')
 for x in rows:(game/x['webp']).unlink()
 (game/'asset-formats.json').unlink()
 print('restored',len(rows),'PNG assets and data.js')
else:print('rollback preflight passed:',len(rows),'assets; add --apply to restore')
