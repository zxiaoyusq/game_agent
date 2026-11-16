import json
p=json.load(open('baseline/data.js',encoding='utf-8'))['project']
for sheet in p[6]:
 print('\nSHEET',sheet[0])
 def walk(x,path):
  if not isinstance(x,list):return
  if len(x)>=6 and x[0]==1 and isinstance(x[1],str): print('VAR',path,x[:6])
  for i,v in enumerate(x):walk(v,path+[i])
 walk(sheet[1],[])
