import json
p=json.load(open('baseline/data.js',encoding='utf8'))['project'];core=next(s for s in p[6] if s[0]=='core');e=core[1][0][7][8][7][0][7][0];print(json.dumps(e[6],separators=(',',':')))
