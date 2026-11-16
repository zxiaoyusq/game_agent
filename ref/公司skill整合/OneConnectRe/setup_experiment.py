import json
from PIL import Image,ImageOps
p='experiment/data.js'
d=json.load(open(p,encoding='utf-8'))
for sheet in d['project'][6]:
 def walk(o):
  if isinstance(o,list):
   if len(o)>4 and o[0]==1 and o[1]=='timerInit' and o[3]==300: o[3]=60
   for x in o: walk(x)
 walk(sheet)
for layout in d['project'][5]:
 if layout[0]=='menu':
  for layer in layout[6]:
   for inst in layer[14]:
    if inst[1]==18 and inst[2]==23: inst[0][0]=720
open(p,'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))
p='experiment/images/title-sheet0.png'
im=Image.open(p).convert('RGBA'); r,g,b,a=im.split(); Image.merge('RGBA',(b,r,g,a)).save(p)
