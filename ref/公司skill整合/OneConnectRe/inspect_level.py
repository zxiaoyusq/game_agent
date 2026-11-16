import json
p=json.load(open('baseline/data.js',encoding='utf-8'))['project']
for name,events in p[6]:
 def walk(e,path):
  if not isinstance(e,list):return
  if len(e)>6 and e[0]==0 and isinstance(e[5],list) and isinstance(e[6],list):
   text=json.dumps(e[5:7],ensure_ascii=False,separators=(',',':'))
   if '"level"' in text or '"timerInit"' in text: print(name,path,text[:1800])
  for i,v in enumerate(e):walk(v,path+[i])
 walk(events,[])
