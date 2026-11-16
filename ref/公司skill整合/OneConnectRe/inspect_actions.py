import json,re
p=json.load(open('baseline/data.js',encoding='utf8'))['project'];s=open('baseline/c2runtime.js',encoding='utf8').read().split('cr.getObjectRefTable=function(){return[')[1].split(']}')[0].split(',')
game=next(x for x in p[6] if x[0]=='gameEvent')
def walk(e,path):
 if not isinstance(e,list):return
 if len(e)>6 and e[0]==0 and isinstance(e[5],list) and isinstance(e[6],list):
  for a in e[6]:
   if isinstance(a,list) and len(a)>5 and any('"'+z+'"' in json.dumps(a[5],separators=(',',':')) for z in ['tip','shuffle']):
    print(path,'conditions',json.dumps(e[5],separators=(',',':')),'action',s[a[1]].split('prototype.')[-1],json.dumps(a,separators=(',',':')))
 for i,x in enumerate(e):walk(x,path+[i])
walk(game[1],[])
