import json,re
p=json.load(open('baseline/data.js',encoding='utf8'))['project'];runtime=open('baseline/c2runtime.js',encoding='utf8').read();refs=runtime.split('cr.getObjectRefTable=function(){return[')[1].split(']}')[0].split(',')
core=next(s for s in p[6] if s[0]=='core');e=core[1][0][7][8][7][0]
def walk(x,depth=0):
 if not isinstance(x,list) or len(x)<7 or x[0]!=0:return
 def fmt(a):
  return ' '.join((refs[z[1]].split('prototype.')[-1] if isinstance(z,list) and len(z)>1 and isinstance(z[1],int) and 0<=z[1]<len(refs) else '?')+':'+json.dumps(z[-1],separators=(',',':')) for z in a)
 print(' '*depth,'C',fmt(x[5]),'A',fmt(x[6]))
 if len(x)>7:
  for sub in x[7]:walk(sub,depth+1)
walk(e)
