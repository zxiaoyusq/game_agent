from pathlib import Path
import json,shutil,hashlib,html
from PIL import Image,ImageOps,ImageDraw,ImageFont
R=Path(__file__).parent
sources=json.loads((R/'screenshot_sources.json').read_text(encoding='utf-8'))
notes=json.loads((R/'style_notes.json').read_text(encoding='utf-8'))
bundle=Path('C:/Users/NENGHO~1.ZHA/AppData/Local/Temp/browser-use/assets/a17e7029-2e3b-4108-8fc0-ac58db2688ab/manifest.json')
b=json.loads(bundle.read_text(encoding='utf-8'))
muscle={'key':'muscle_morph','name':'Muscle Morph','artist':'AbbaYosua.Design','store':'https://play.google.com/store/apps/details?hl=en_US&id=com.muscle.morph.lean.run','screens':[]}
for i,a in enumerate(b['assets'],1):
 p=R/'screens'/'muscle_morph'/f'{i:02d}.img';p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a['path'],p)
 im=Image.open(p)
 muscle['screens'].append(dict(index=i,path=str(p),url=a['url'],size=list(im.size),format=im.format,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
sources=[s for s in sources if s['key']!='muscle_morph']+[muscle]
(R/'screenshot_sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
bykey={s['key']:s for s in sources}
# Keep source bytes, and create standard .jpg previews that every local browser can open.
for s in sources:
 for sc in s['screens']:
  out=Path(sc['path']).with_suffix('.jpg')
  Image.open(sc['path']).convert('RGB').save(out,quality=94)
  sc['preview']=out.relative_to(R).as_posix()
intro='''# 19款休闲游戏：游戏画面与美术风格分析

查看日期：2026-10-22。范围为上一轮全球及目标市场榜单所列游戏，去重后19款，不是最早选中的6个本地H5原包。

本报告逐张查看官方商店提供的游戏画面，讨论配色、UI、轮廓、造型、渲染与构图，不把物件题材本身当成风格。18款各5张，Muscle Morph为4张，共94张；另补看Tile Explorer的Android大图。原图、来源URL与哈希见screenshot_sources.json。

证据边界：商店截图可能经过放大、合成或增加文案和手势。分析只描述可见的视觉语言；宣传图与常规局内画面分开判断。本次没有安装实机试玩，不据静态图推定实际引擎、着色器、光照算法或制作管线。多数iOS图为商店缩略尺寸，适合判断轮廓、配色和整体质感，不足以可靠判断微小笔触与材质纹理；涉及这些细节的描述采用保守口径。本修订去掉具体色相和固定配色，只描述饱和度、明度、对比与功能分组；地区配色另行指定。

这些是产品样本，不是某国用户审美偏好的因果证据。排行或流行度不能证明某种美术风格在该国表现最好。

[风格母版文档：7种母版与地区适配规则](7种美术风格母版_地区配色独立版.md)

## 风格总览

|游戏|主要风格|对当前换皮的参考位置|
|---|---|---|
'''
md=[intro]
for n in notes:md.append(f"|{n['title']}|{n['style']}|{n['takeaway']}|\n")
md.append('\n## 逐款观察\n')
labels=[('color','饱和度、明度与对比倾向'),('ui','UI造型与文字'),('shape','轮廓与形体'),('art','原画与造型语言'),('render','渲染、光影与材质'),('composition','构图与细节密度'),('boundary','画面证据与限制'),('takeaway','对本次换皮的启示'),('tags','可复用的风格关键词')]
cards=[]
for idx,n in enumerate(notes,1):
 s=bykey[n['key']]
 md.append(f"\n## {idx:02d}. {n['title']}\n\n**风格定位：{n['style']}。**\n\n[官方商店与截图来源]({s['store']}) · 发布者：{s['artist']}\n\n")
 md.append(f"本地截图：screens/{n['key']}/，共{len(s['screens'])}张。对照页可点击放大。\n\n")
 for k,label in labels:md.append(f"- **{label}：** {n[k]}\n")
 imgs=''.join(f'<a href="{sc["preview"]}" target="_blank"><img loading="lazy" src="{sc["preview"]}" alt="{html.escape(n["title"])} screenshot {sc["index"]}"><span>图{sc["index"]:02d} · {sc["size"][0]}×{sc["size"][1]}</span></a>' for sc in s['screens'])
 paragraphs=''.join(f'<p><b>{label}</b>{html.escape(n[k])}</p>' for k,label in labels)
 cards.append(f'<section id="{n["key"]}" data-search="{html.escape(n["title"]+n["style"])}"><h2>{idx:02d} · {html.escape(n["title"])}</h2><div class="style">{html.escape(n["style"])}</div><p><a href="{html.escape(s["store"])}" target="_blank">官方商店来源</a> · {html.escape(s["artist"])}</p><div class="shots">{imgs}</div><div class="notes">{paragraphs}</div></section>')
md.append('''
## 针对当前项目的采用建议

你要的是“圆润、轻量简约、休闲手绘或3D动画电影观感”。建议分别建立两个完整母版，不把所有产品的材质混成一套。

### A. 轻插画与浅立体母版

主要参考Tile Explorer的厚片和小插画，借用Meowdoku的高明度留白与轻UI。棋子轮廓圆润但完整，内部细节少；统一一个受光方向、少量柔影和可控的高光。背景的边缘、饱和度和细节密度都弱于棋子。避免将Meowdoku完全平面的格子与Candy Crush强亮面棋子直接混拼，造成材质不统一。

### B. 轻量3D动画母版

主要参考Bus Fever的简单玩具体积；有角色时参考My Talking Tom 2的大头、短身、清楚表情与宽面明暗。奖励页和重点道具可参考Magic Sort活动图的柔光和饱满曲面，但主棋盘减少亮面装饰色镜面、背景细节和光效数量。使用静态渲染图也可追求这种观感，不要求改变现有游戏代码与玩法。

### 统一的生产原则

- 圆润来自连续的大曲面、合适的倒角和简化内结构，不等于给所有图标套同一个圆角框。
- 手绘感来自形体概括、轮廓节奏和局部绘制方式，不必添加纸纹、旧化和杂乱笔触。
- 3D动画感来自比例、表情、统一光源与干净明暗，不必增加真实皮肤、复杂毛发和金属反射。
- 文化元素决定“画什么”，美术母版决定“怎么画”。三个地区可共享同一母版的造型、阴影、材质和UI，只调整经过当地核对的图案、外观与少量点缀色。
- 主玩法先维护识别：不同棋子要有不同剪影或明显内部图形，颜色不能成为唯一线索。地方纹样优先放在大面积非操作部位，并降低对比。
- 如玩法依赖颜色配对，不要为配合地区主色统一改成相近颜色；地区配色优先作用于界面与背景。

### 优先看哪些

|参考目标|首看|补看|不适合直接照搬的点|
|---|---|---|---|
|圆润消除棋子|Candy Crush|Tile Explorer|过强镜面、特效满屏|
|轻手绘本地化换皮|Tile Explorer|Meowdoku|高对比风景和过细图案|
|圆润轻3D|Bus Fever|My Talking Tom 2|过多角色与场景细节|
|高完成度奖励原画|Magic Sort活动图|Candy Crush|将活动图的华丽度搬入主棋盘|
|低成本场景|Pizza Ready|Mob Control|简化人形不等于动画电影品质|
|桌游UI与颜色规则|Ludo King|Awesome Games部分子游戏|厚高对比装饰框和密集入口|

## 文件与来源说明

- `截图与风格对照.html`：离线对照页，含94张截图、每款完整观察与官方商店链接，可按名称搜索。
- `screens/`：原始商店图（.img，保留下载字节）及通用JPEG预览；JPEG仅用于查看，不作为源图哈希证据。
- `screenshot_sources.json`：每张图的原始URL、发布者、分辨率与SHA-256。
- `contact_01.jpg`—`contact_09.jpg`：18款的双行总览；`contact_10.jpg`：Muscle Morph单独总览。
- 官方游戏画面版权属于各权利人，本地收集用于竞品观察；不是可直接投入换皮生产的素材。
''')
(R/'19款游戏_美术风格详细分析.md').write_text(''.join(md),encoding='utf-8')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>19款休闲游戏 · 截图与风格对照</title><style>
*{box-sizing:border-box}body{margin:0;background:#eff1f4;color:#26313c;font:16px/1.8 "Microsoft YaHei",sans-serif}header,main{max-width:1480px;margin:auto;padding:28px}h1{font-size:30px;margin:0}header p{max-width:1050px}input{width:100%;padding:14px;border:1px solid #c4ccd5;border-radius:10px;font:inherit}section{background:white;border-radius:16px;padding:26px;margin:0 0 28px;box-shadow:0 4px 18px #2738460b}h2{margin:0}.style{color:#316175;font-weight:bold}a{color:#156c94}.shots{display:flex;gap:14px;overflow:auto;padding:12px 0 20px}.shots a{display:flex;flex:none;flex-direction:column;width:210px;text-decoration:none;font-size:12px;color:#63717c}.shots img{width:210px;height:455px;object-fit:contain;background:#f1f2f4;border-radius:6px}.notes{display:grid;grid-template-columns:1fr 1fr;gap:10px 26px}.notes p{margin:0;padding:12px 0;border-top:1px solid #edf0f3}.notes b{display:block;color:#285267;font-size:14px}footer{padding:20px;text-align:center}@media(max-width:800px){header,main{padding:15px}.notes{grid-template-columns:1fr}section{padding:18px}.shots a,.shots img{width:180px}.shots img{height:390px}}
</style><header><h1>19款休闲游戏 · 截图与美术风格对照</h1><p>查看日期：2026-10-22。18款各5张，Muscle Morph为4张，共94张官方商店图。点击图片可查看本地单图。分析关注配色、UI、轮廓、造型与渲染；商店文案、手机外框和手势不计入固定游戏UI。本次未实机试玩，不能据此判断实际技术管线或各地区审美偏好。多数截图为商店缩略尺寸，微观笔触与材质判断有限。</p><p><a href="19款游戏_美术风格详细分析.md">详细Markdown报告</a> · <a href="screenshot_sources.json">来源记录</a> · <a href="7种美术风格母版_地区配色独立版.md">7种风格母版</a></p><input id="search" placeholder="按游戏名或风格词筛选，例如：圆润、3D、极简"></header><main>'''+''.join(cards)+'''</main><footer>仅用于竞品观察 · 原始画面版权属于各游戏权利人</footer><script>document.querySelector('#search').addEventListener('input',e=>{const q=e.target.value.toLowerCase().trim();document.querySelectorAll('section').forEach(s=>s.hidden=!s.dataset.search.toLowerCase().includes(q))})</script></html>'''
(R/'截图与风格对照.html').write_text(page,encoding='utf-8')
sheet=Image.new('RGB',(1440,760),'#e7e9ed');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
d.text((15,10),'Muscle Morph | Official Google Play promotional screenshots',font=font,fill='#26313c')
for i,sc in enumerate(muscle['screens']):
 im=ImageOps.contain(Image.open(sc['path']).convert('RGB'),(340,680));sheet.paste(im,(i*360+(360-im.width)//2,50))
sheet.save(R/'contact_10.jpg',quality=94)
assert len(notes)==19 and len(sources)==19
assert sum(len(s['screens']) for s in sources)==94
for s in sources:
 for sc in s['screens']:
  assert (R/sc['preview']).exists()
  assert hashlib.sha256(Path(sc['path']).read_bytes()).hexdigest()==sc['sha256']
assert page.count('<section ')==19 and page.count('<img ')==94
print(json.dumps({'games':19,'screenshots':94,'report_characters':len(''.join(md)),'html_sections':19,'image_paths_and_source_hashes':'PASS','report':str(R/'19款游戏_美术风格详细分析.md'),'html':str(R/'截图与风格对照.html')},ensure_ascii=False))
