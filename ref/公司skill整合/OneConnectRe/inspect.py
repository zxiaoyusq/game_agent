import json
p=json.load(open('baseline/data.js',encoding='utf-8'))['project']
for l in p[5]:
 print('LAYOUT',l[0]);
 for layer in l[6]:
  print('LAYER',layer[0]);
  for x in layer[14]: print(str(x)[:300])
