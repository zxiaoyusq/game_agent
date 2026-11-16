from pathlib import Path
import zipfile,json,io
from PIL import Image,ImageOps,ImageDraw,ImageFont
p=Path(__file__).parent.parent
a=json.loads((p/'reskin_review/package_audit.json').read_text(encoding='utf-8'))
ids=[77413,77924,87138,94215,95486,88881,78388,90848,82251,90189,93876,95173]
f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
for start in range(0,len(ids),4):
 sheet=Image.new('RGB',(1400,4*310),'#242936');d=ImageDraw.Draw(sheet)
 for row,gid in enumerate(ids[start:start+4]):
  r=next(x for x in a if x['id']==gid);z=zipfile.ZipFile(next((p/r['dir']).glob('*.zip')))
  imgs=[]
  for entry in z.infolist():
   if Path(entry.filename).suffix.lower() in ['.png','.jpg','.webp'] and not any(t in entry.filename.lower() for t in ['splash','loading','logo','banner']):
    try:
     im=Image.open(io.BytesIO(z.read(entry)))
     if im.width*im.height>15000:imgs.append((im.width*im.height,entry.filename,im.copy()))
    except Exception: pass
  imgs.sort(key=lambda x:x[0],reverse=True)
  d.text((10,row*310+3),str(gid)+' '+r['name'],font=f,fill='white')
  selected=imgs[:5]
  for j,(_,name,im) in enumerate(selected):
   im=ImageOps.contain(im.convert('RGBA'),(265,252));bg=Image.new('RGBA',im.size,'#777777');bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(j*280,row*310+25))
   d.text((j*280,row*310+280),Path(name).name[:32],font=f,fill='white')
 sheet.save(p/f'reskin_review/internal_{start//4+1}.jpg')
 for row,gid in enumerate(ids[start:start+4]):
  r=next(x for x in a if x['id']==gid);z=zipfile.ZipFile(next((p/r['dir']).glob('*.zip')))
  models=[n for n in z.namelist() if Path(n).suffix.lower() in ['.lh','.lm','.lmat','.ls','.glb','.gltf','.atlas','.plist','.fnt']]
  print(gid,models[:8])
