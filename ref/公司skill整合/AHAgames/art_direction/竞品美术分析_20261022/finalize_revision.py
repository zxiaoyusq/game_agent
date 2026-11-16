from pathlib import Path
import json
R=Path(__file__).parent
p=R/'style_notes.json';ns=json.loads(p.read_text(encoding='utf-8'))
fix={'粗白字':'高明度粗字','小白圆按钮':'小型高明度圆按钮','白按钮':'高明度按钮','暖色留白':'低干扰底色留白','高明度色圆按钮':'高明度圆按钮','高明度色圆角':'高明度圆角','高明度色顶面':'高明度顶面','高明度色缝隙':'高明度缝隙','低明度色描边':'低明度描边'}
for n in ns:
 for k,v in list(n.items()):
  if isinstance(v,str):
   for a,b in fix.items():v=v.replace(a,b)
   n[k]=v
p.write_text(json.dumps(ns,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'build_report.py';c=p.read_text(encoding='utf-8')
for a,b in fix.items():c=c.replace(a,b)
if '风格母版文档' not in c:
 c=c.replace('## 风格总览','[风格母版文档：7种母版与地区适配规则](7种美术风格母版_地区配色独立版.md)\n\n## 风格总览')
 c=c.replace('<a href="screenshot_sources.json">来源记录</a>','<a href="screenshot_sources.json">来源记录</a> · <a href="7种美术风格母版_地区配色独立版.md">7种风格母版</a>')
p.write_text(c,encoding='utf-8')
print('Final wording and template navigation updated.')
