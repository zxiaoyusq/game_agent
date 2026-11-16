from pathlib import Path
from collections import Counter
import csv,hashlib,html,json
from PIL import Image
root=Path(__file__).resolve().parent.parent; out=root/'美术换皮准备';out.mkdir(exist_ok=True)
source=root/'baseline'; extensions={'.png','.jpg','.svg','.ogg','.m4a','.ttf','.otf','.woff','.woff2'}
files=sorted(f for f in source.rglob('*') if f.is_file() and f.suffix.lower() in extensions)
known={'tiles-sheet0.png':'玩法牌：动物主题','tiles-sheet1.png':'玩法牌：甜点主题','tiles-sheet2.png':'玩法牌：水果主题','title-sheet0.png':'主菜单标题','startbutton-sheet0.png':'开始按钮','gamefont.png':'局内位图字体','menufont.png':'菜单位图字体','popup-sheet0.png':'结算弹窗候选','homebutton-sheet0.png':'返回按钮候选','pause-sheet0.png':'暂停入口候选'}
def cat(f):
 n=f.name.lower()
 if f.suffix.lower() in {'.ogg','.m4a'}:return '音频'
 if f.parent.name!='images':return '宿主包装图'
 if 'font' in n:return '位图字体'
 if n.startswith('tiles-sheet'):return '三主题牌面图集'
 if any(w in n for w in ['gradient','sunray','gametilebg','tileempty','tilepurple','9patch']):return '背景与底板候选'
 if any(w in n for w in ['popfx','spark','shine','line','dots','mark']):return '连线与特效候选'
 if any(w in n for w in ['button','pause','popup','bonus','timesup','nomatch','tutorial','uisymbols','cupsymbol','credits','title']):return '界面及状态候选'
 return '其他图片待确认'
rows=[]
for f in files:
 rel=f.relative_to(source).as_posix(); target=root/'game'/rel; digest=hashlib.sha256(f.read_bytes()).hexdigest(); info={'asset':rel,'group':cat(f),'bytes':f.stat().st_size,'sha256':digest,'game_match':'一致' if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==digest else '差异或缺失','meaning':known.get(f.name,'文件名分类，具体用途待运行核实'),'confidence':'部分有运行或静态定位，见接口文档' if f.name in known else '候选，待核实','target':'待用户确定','candidate':'','qa':'未开始'}
 if f.suffix.lower() in {'.png','.jpg'}:
  with Image.open(f) as im:info.update(width=im.width,height=im.height,mode=im.mode)
 else:info.update(width='',height='',mode='')
 rows.append(info)
with (out/'原版资源轻索引.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
(out/'原版资源轻索引.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
esc=html.escape
screens=[('竖屏主菜单','portrait_audit_baseline_menu.png','原版 baseline/game.html；390×844 浏览器；打开后等待加载。'),('竖屏主题选择','portrait_audit_baseline_theme.png','同一原版浏览器会话；点击开始。'),('竖屏对局','portrait_audit_baseline_after.png','同一原版浏览器会话；选择动物主题。'),('横屏暂停','pause2.png','原版桌面 Chrome；自然点击暂停，画面为黑底白图标，宿主表现待核对。'),('横屏失败','failure.png','原版桌面 Chrome；自然倒计时失败，缺少宿主广告接口。')]
scr=''.join(f'<article><h3>{esc(n)}</h3><img class="shot" loading="lazy" src="../screenshots/{esc(fn)}" alt="{esc(n)}"><p>{esc(note)}</p></article>' for n,fn,note in screens)
assets=[]
for x in rows:
 rel=x['asset']; ext=Path(rel).suffix.lower(); src='../baseline/'+rel
 if ext in ('.png','.jpg','.svg'):media=f'<img loading="lazy" src="{esc(src)}" alt="{esc(rel)}">'
 elif ext in ('.ogg','.m4a'):media=f'<audio controls preload="none" src="{esc(src)}"></audio>'
 else:media='<p>字体文件</p>'
 size=f"{x['width']}×{x['height']} · {x['mode']}" if x['width'] else '音频/其他文件'
 assets.append(f'<article class="asset" data-group="{esc(x["group"])}" data-name="{esc(rel.lower())}">{media}<b>{esc(Path(rel).name)}</b><p>{esc(x["meaning"])}<br>{esc(size)} · {x["bytes"]:,} 字节<br>用途：{esc(x["confidence"])}</p><small>{esc(rel)}</small></article>')
groups=sorted(set(x['group'] for x in rows));options=''.join(f'<option>{esc(g)}</option>' for g in groups)
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>One Connect 换皮准备</title><style>body{margin:0;background:#111a2d;color:#e9efff;font:16px/1.65 system-ui}header,main{max-width:1400px;margin:auto;padding:24px}nav{position:sticky;top:0;background:#253754;padding:12px;display:flex;gap:20px;flex-wrap:wrap;z-index:2}a{color:#8dd7ff}section{padding:10px 0 25px}h2{border-bottom:1px solid #50617b;padding-bottom:10px}.note{background:#263b55;padding:16px;border-radius:10px}.screens{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}article{background:#1f304b;border-radius:10px;padding:12px;overflow-wrap:anywhere}.shot{width:100%;height:350px;object-fit:contain;background:#0f172a}.assets{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}.asset img{width:100%;height:150px;object-fit:contain;background:repeating-conic-gradient(#54617a 0 25%,#26364b 0 50%) 0/16px 16px}.asset p,small{font-size:12px;color:#c4d2e6}audio{width:100%}input,select{padding:8px;font:inherit}li{margin:6px 0}h3{margin:3px 0}</style></head><body><header><h1>One Connect 美术换皮准备</h1><p>查看原版竖屏与资源，确定美术方向后再生产代表样。当前没有新风格或换皮成品。</p></header><nav><a href="#screens">原版画面</a><a href="#plan">换皮范围</a><a href="#assets">全部资源</a><a href="#next">确认事项</a></nav><main><section id="screens"><h2>原版画面与来源</h2><div class="note">竖屏为原版 baseline 在本地浏览器的自然操作截图；横屏为既有桌面证据。它们不是 AHA 真机截图。原包的 1280×720 为设计尺寸，竖屏实际对局显示 6 列 × 12 行。</div><div class="screens">'''+scr+'''</div></section><section id="plan"><h2>建议拆分的美术范围</h2><ul><li><b>核心玩法：</b>三套主题牌面、棋盘底板与连线，重点检查牌型辨识、状态和图集帧顺序。</li><li><b>菜单与界面：</b>标题、开始、主题选择、局内按钮、暂停、结算及其状态；同族资源统一规划，避免重复生产。</li><li><b>背景及反馈：</b>底板、闪光、粒子和奖励效果；当前部分用途仅由文件名推断，回填前需核对真实使用关系。</li><li><b>文字与音频：</b>位图字体和原音频单列；是否替换、文字语言及命名待确认。</li></ul><p>优先代表样：竖屏对局（牌面、背景、局内 UI）与主菜单；确认后再按同族批量生产、集中回填和整屏回归。图集尺寸、帧矩形、挂点与点击区域须按实际数据核对。</p></section><section id="assets"><h2>原版资源轻索引</h2><p>共 '''+str(len(rows))+''' 个图片、音频与字体文件。按文件名初步分类，未见运行证据的用途均为候选；不等同已拆分图集帧或已确认替换清单。 <a href="原版资源轻索引.csv">下载 CSV</a> · <a href="原版资源轻索引.json">JSON</a></p><label>分类 <select id="group"><option value="">全部</option>'''+options+'''</select></label> <label>搜索 <input id="q" placeholder="文件名或路径"></label><div id="list" class="assets">'''+''.join(assets)+'''</div></section><section id="next"><h2>待你确定</h2><div class="note"><p>请选择或提供美术方向与参考图；可说明题材、画风、色彩、需要保留的元素，以及是否先做对局代表屏。此前报告中的配色或题材只是建议，不代表已批准。</p><p>待核实：全部帧的用途与锚点、特殊状态、竖屏暂停与结算、AHA 宿主实际画面。新美术的效果图、候选、替换和真实运行验收均尚未开始。</p></div><p><a href="../原版截图与资源.html">查看原始截图与资源页面</a> · <a href="../迭代接口手册.html">查看资源替换接口手册</a></p></section></main><script>const group=document.querySelector('#group'),q=document.querySelector('#q');function filter(){for(const e of document.querySelectorAll('.asset'))e.hidden=!!((group.value&&group.value!==e.dataset.group)||(q.value&&!e.dataset.name.includes(q.value.toLowerCase())))}group.onchange=filter;q.oninput=filter;</script></body></html>'''
(out/'换皮方向参考.html').write_text(page,encoding='utf8')
print('files',len(rows),'groups',dict(Counter(x['group'] for x in rows)),'dev_differences',sum(x['game_match']!='一致' for x in rows))
