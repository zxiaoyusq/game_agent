from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import shutil,json,zipfile,io,hashlib
root=Path.cwd();src=root/'game';dst=root/'analysis'/'lossless_webp_stage_20261030';out=root/'analysis'/'lossless_webp_files_20261030';
if dst.exists() or out.exists():raise SystemExit('output exists')
shutil.copytree(src,dst);out.mkdir(); txt=(src/'data.js').read_text(encoding='utf8'); protected={'dots-sheet0.png','line-sheet0.png','popfx-sheet0.png','popfx-sheet1.png','credits-sheet0.png'}
files=[p for p in (src/'images').glob('*.png') if p.name not in protected and 'images/'+p.name in txt]
def run(p):
 q=out/(p.stem+'.webp')
 with Image.open(p) as im:
  im=im.convert('RGBA');im.save(q,'WEBP',lossless=True,quality=100,method=6,exact=True)
  with Image.open(q) as decoded:
   if decoded.convert('RGBA').tobytes()!=im.tobytes():raise RuntimeError('RGBA mismatch '+p.name)
 return (p.name,q.name,p.stat().st_size,q.stat().st_size)
with ThreadPoolExecutor(max_workers=4) as ex: rows=list(ex.map(run,files))
data=(dst/'data.js').read_text(encoding='utf8'); accepted=[]
for orig,new,a,b in rows:
 if b>=a:continue
 shutil.copy2(out/new,dst/'images'/new);(dst/'images'/orig).unlink();data=data.replace('images/'+orig,'images/'+new);accepted.append([orig,new,a,b])
(dst/'data.js').write_text(data,encoding='utf8');fs=sorted(p for p in dst.rglob('*') if p.is_file());buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in fs:z.write(f,f.relative_to(dst).as_posix())
manifest={'files':accepted,'compressed_zip_bytes':len(buf.getvalue()),'raw_bytes':sum(p.stat().st_size for p in fs)};(out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print('tested',len(rows),'accepted',len(accepted),'zip bytes',len(buf.getvalue()),'raw bytes',manifest['raw_bytes'],flush=True)
