from pathlib import Path
import json,csv,zipfile,collections,re,io,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(r'E:\AIlab\AHAgames')
OUT=ROOT/'reskin_review';OUT.mkdir(exist_ok=True)
rows=list(csv.DictReader((ROOT/'art_manifest.csv').open(encoding='utf-8-sig',newline='')))
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8-sig'))
byid={int(r['id']):r for r in rows}
manifest=[dict(gameId=int(r['id']),apiName=r['name'],dir=r['dir'],sizeBytes=next((ROOT/r['dir']).glob('*.zip')).stat().st_size) for r in rows]
results=[]
for m in manifest:
 r=byid[m['gameId']];p=ROOT/m['dir'];z=zipfile.ZipFile(next(p.glob('*.zip')))
 files=[f for f in z.infolist() if not f.is_dir()];ext=collections.Counter(Path(f.filename).suffix.lower() for f in files)
 names=[f.filename for f in files];joined='\n'.join(names).lower()
 probes=[]
 for f in files:
  if Path(f.filename).suffix.lower() in ('.html','.js','.json') and f.file_size<3000000 and (re.search(r'(index|main|cocos|settings|config|data|language|locale|i18n)',Path(f.filename).name,re.I)):
   probes.append(z.read(f).decode('utf-8',errors='replace'))
   if sum(map(len,probes))>8000000:break
 code='\n'.join(probes)
 engine='待识别'
 for label,pat in [('Unity WebGL',r'UnityLoader|createUnityInstance|\.unityweb|\.data\.br|\.wasm\.br'),('Cocos',r'cc\.Asset|cc\.game|cocos|cclegacy'),('Laya',r'Laya\.|laya\.'),('Construct',r'c3runtime|c2runtime|Construct 3'),('Phaser',r'Phaser\.|phaser'),('Three.js',r'THREE\.|three\.module'),('Egret',r'egret\.')]:
  if re.search(pat,joined+'\n'+code,re.I):engine=label;break
 loc=[n for n in names if re.search(r'(localiz|languages?|locales?|i18n|translations?)',n,re.I)][:12]
 resource=[n for n in names if Path(n).suffix.lower() in ('.png','.jpg','.jpeg','.webp','.atlas','.skel','.fnt','.ttf','.glb','.gltf','.ktx','.ktx2')]
 imgfiles=[f for f in files if Path(f.filename).suffix.lower() in ('.png','.jpg','.jpeg','.webp')]
 hashes={hashlib.sha256(z.read(f)).hexdigest() for f in imgfiles}
 result=dict(id=m['gameId'],name=m['apiName'],dir=m['dir'],engine=engine,zipMB=round(m['sizeBytes']/1048576,2),files=len(files),images=len(imgfiles),uniqueImages=len(hashes),imageHashes=sorted(hashes),ext=dict(ext),localePaths=loc,resourceExamples=resource[:14],description=r['description'],introduction=r['introduction'],category=r['category'])
 results.append(result)
 print(f"{m['gameId']} | {m['apiName']} | {engine} | {result['zipMB']}MB | img {result['images']} | "+str({k:v for k,v in ext.items() if k in ['.atlas','.skel','.glb','.gltf','.bin','.data','.wasm','.fnt','.ttf']})+' | '+r['description'][:140])
(OUT/'package_audit.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
for batch in range(4):
 subset=manifest[batch*20:(batch+1)*20]
 sheet=Image.new('RGB',(1500,((len(subset)+3)//4)*295),'#171d28');d=ImageDraw.Draw(sheet)
 for j,m in enumerate(subset):
  x=(j%4)*375;y=(j//4)*295;p=ROOT/m['dir']/'art'
  d.text((x+8,y+6),str(m['gameId'])+' '+m['apiName'][:30],font=font,fill='white')
  for k,typ in enumerate(['theme','preview']):
   f=next(p.glob(typ+'.*'));im=Image.open(f)
   if typ=='preview':im.seek(min(im.n_frames-1,im.n_frames//2))
   im=ImageOps.contain(im.convert('RGB'),(175,245));sheet.paste(im,(x+8+k*182+(175-im.width)//2,y+34))
 sheet.save(OUT/f'contact_{batch+1}.jpg',quality=90)
