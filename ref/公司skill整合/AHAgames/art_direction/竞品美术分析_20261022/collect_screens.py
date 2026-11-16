from pathlib import Path
import json,urllib.request,concurrent.futures,hashlib,io
from PIL import Image,ImageOps,ImageDraw,ImageFont
ROOT=Path(__file__).parent
IDS={'block_blast':1617391485,'pizza_ready':6450917563,'ludo_king':993090598,'subway_surfers':512939461,'tile_explorer':6498883328,'mob_control':1562817072,'block_out':6752672568,'magic_sort':6499209744,'meowdoku':6761760135,'arrows_escape':6748397500,'arrows_go':6758326278,'awesome_games':6796405274,'brain_puzzle_3':6756482832,'offline_games':6448104157,'candy_crush':553834731,'perfect_makeover':6754549880,'bus_fever':6746743297,'talking_tom_2':1337578317}
records=[];tasks=[]
for key,ident in IDS.items():
 data=json.loads((ROOT/f'{key}_search.json').read_text(encoding='utf-8'))
 app=next(x for x in data['results'] if x['trackId']==ident)
 record=dict(key=key,id=ident,name=app['trackName'],artist=app.get('artistName'),seller=app.get('sellerName'),store=app['trackViewUrl'],version=app.get('version'),screens=[])
 (ROOT/'screens'/key).mkdir(parents=True,exist_ok=True)
 for i,url in enumerate(app.get('screenshotUrls',[])[:5]):tasks.append((record,i,url))
 records.append(record)
def download(task):
 r,i,url=task;p=ROOT/'screens'/r['key']/f'{i+1:02d}.img'
 try:
  if not p.exists():
   with urllib.request.urlopen(url,timeout=40) as f:raw=f.read()
   p.write_bytes(raw)
  im=Image.open(p);im.load()
  r['screens'].append(dict(index=i+1,path=str(p),url=url,size=list(im.size),format=im.format,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 except Exception as e:print('FAIL',r['key'],i,str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(download,tasks))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
for r in records:r['screens'].sort(key=lambda x:x['index'])
(ROOT/'screenshot_sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
for start in range(0,len(records),2):
 sheet=Image.new('RGB',(1500,1450),'#e7e9ed');d=ImageDraw.Draw(sheet)
 for row,r in enumerate(records[start:start+2]):
  y=row*725;d.text((12,y+8),r['key']+' | '+r['name'],font=font,fill='#192535')
  for col,s in enumerate(r['screens']):
   im=ImageOps.contain(Image.open(s['path']).convert('RGB'),(286,660))
   sheet.paste(im,(col*300+(300-im.width)//2,y+38))
   d.text((col*300+10,y+700),f"{s['index']:02d} {s['size']}",font=small,fill='#192535')
 sheet.save(ROOT/f'contact_{start//2+1:02d}.jpg',quality=92)
print('Games',len(records),'Screens',sum(len(r['screens']) for r in records))
