from pathlib import Path
from PIL import Image
import shutil,zipfile,hashlib
root=Path(__file__).resolve().parent.parent
source=root/'game'; candidates=root/'analysis/lossless_png_20261029'; stage=root/'analysis/无损压缩运行副本'; out=root/'analysis/OneConnect_无损压缩验证.zip'
if stage.exists() or out.exists(): raise SystemExit('output already exists; preserve existing files and choose a new destination')
shutil.copytree(source,stage)
changed=[]
for candidate in candidates.glob('*.png'):
 original=source/'images'/candidate.name
 if not original.is_file(): raise SystemExit('missing source: '+candidate.name)
 with Image.open(original) as a, Image.open(candidate) as b:
  if a.size!=b.size or a.convert('RGBA').tobytes()!=b.convert('RGBA').tobytes(): raise SystemExit('pixel mismatch: '+candidate.name)
 if candidate.stat().st_size < original.stat().st_size:
  shutil.copy2(candidate,stage/'images'/candidate.name);changed.append(candidate.name)
files=sorted(x for x in stage.rglob('*') if x.is_file())
with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in files:z.write(f,f.relative_to(stage).as_posix())
with zipfile.ZipFile(out) as z:
 if z.testzip() is not None:raise SystemExit('ZIP integrity failure')
 if len(z.namelist())!=len(files):raise SystemExit('ZIP file count mismatch')
 for f in files:
  if z.read(f.relative_to(stage).as_posix())!=f.read_bytes():raise SystemExit('ZIP file mismatch')
print('images replaced:',len(changed),'files:',len(files),'zip bytes:',out.stat().st_size,'sha256:',hashlib.sha256(out.read_bytes()).hexdigest())
