from pathlib import Path
import json,csv,re,html,hashlib,collections
from selection_data import selections
ROOT=Path(__file__).parent.parent
OUT=ROOT/'reskin_review'
BACKUP=ROOT/'index.before_reskin_20261021.html'
if not BACKUP.exists(): BACKUP.write_bytes((ROOT/'index.html').read_bytes())
original=BACKUP.read_text(encoding='utf-8-sig')
audit=json.loads((OUT/'package_audit.json').read_text(encoding='utf-8'))
byid={r['id']:r for r in audit}
labels={'P0':'首批试点','P1':'第二批 / 替补','P2':'暂缓，成本或内容门槛高','P3':'不适合全量换皮首批'}
ease={1:'很高 / 未拆包',2:'高',3:'中',4:'低—中',5:'低'}
for rank,s in enumerate(selections(),1):
 r=byid[s['id']];r.update(s);r['rank']=rank;r['effort']=ease[s['dimensions'][2]]
ordered=sorted(audit,key=lambda r:r['rank'])
assert len(ordered)==74 and len(byid)==74
def h(t):return html.escape(str(t),quote=True)
def evidence(r):
 ext=r['ext']; extras=[]
 for e,label in [('.atlas','atlas'),('.plist','plist'),('.bin','bin'),('.glb','glb'),('.data','data'),('.wasm','wasm'),('.zip','内嵌zip')]:
  if ext.get(e):extras.append(f'{ext[e]} {label}')
 return f"外层图片 {r['images']} / 按内容去重 {r['uniqueImages']}；"+('、'.join(extras) if extras else '未见上述特殊扩展名')
for r in audit:
 r['evidenceSummary']=evidence(r)
 r['languageEvidence']='；'.join(r['localePaths'][:2]) or ('包内有 build/resources/assets/texts/en-US.txt；加载方式待核实' if r['id']==78388 else '文件名扫描未找到显式语言目录；不代表没有硬编码文案')
(OUT/'reskin_ranking.json').write_text(json.dumps(ordered,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'reskin_ranking.csv').open('w',encoding='utf-8-sig',newline='') as f:
 fields=['排序','ID','游戏','分组','总分','美术收益','文化展示适配','工作量易度','本地化易度','不改代码可行性','工作量','建议方向','推荐或降级理由','替换范围','约束与风险','文化备注','资源证据','语言线索','本地目录']
 w=csv.writer(f);w.writerow(fields)
 for r in ordered:w.writerow([r['rank'],r['id'],r['name'],r['tier'],r['score'],*r['dimensions'],r['effort'],r['theme'],r['reason'],r['scope'],r['caution'],r['culture'],r['evidenceSummary'],r['languageEvidence'],str(ROOT/r['dir'])])
counts=collections.Counter(r['tier'] for r in audit)
common='''本轮为选型初筛：逐个读取74个ZIP的外层文件目录，扫描部分入口/配置的引擎和语言线索；查看74款商店主题图与GIF中间帧；另外查看12款候选的包内大图/图集样本。未逐款通关，未递归展开内嵌ZIP，未证明所有远程资源完整、动态加载路径可达或本地化可用。宣传图与包内样本是两类证据，不能相互替代。'''
method='''五维各1—5分，越高越好：美术重制收益30%、文化展示适配25%、工作量易度25%、多语言易度15%、不改代码可行性5%。总分=6A+5C+5E+3L+F，满分100。均为本轮人工选型判断，并非营收、留存、审核通过率或实测工时报价。文化分评价“可通过美术形成中性表达的空间”，不代表原包可直接上线。排序先按分组，再按总分，同分按ID；分组可因资源封装、主题与机制绑定、同类重复而覆盖分数。工作量按外层资源规模、图集/模型/状态复杂度判断，文件数不是要重画的对象数。'''
languages='''严格“代码一行不动”时，仅能使用原有语言加载、字体、排版和语言选择机制。若原包缺少语言入口、字形塑形、RTL或文本扩展能力，则完整多语言需求存在阻断；所有P0都是“优先取证/试换”，不是已证实零代码完成。Candy Crush存在languages.json、Classic Billiard存在en-US.txt、Flowers Match存在LY06_Language目录，仅证明有线索。建议按实际发行国家配置语言：例如英语/法语/阿拉伯语作为候选基础包；南亚按国家选择印地语、孟加拉语、乌尔都语等，东南亚选择印尼语、泰语、越南语等，东非视国家加入斯瓦希里语。此为规划建议，未核验传音流量国家占比；不把地区、国家与语言一一对应。阿语/乌尔都语检查连写、混排、数字、标点、RTL；泰语等检查字体与断行。玩法棋盘、方向箭头和操控不能随文字方向整体镜像。'''
boundaries='''全量重制范围包含：运行中实际引用的所有美术、图集子图/动画帧、字体与含字图片、加载/菜单/失败/胜利/教程页、商店icon/banner/hotgame/theme/preview。不得用“核心画面换了”代替“全量覆盖”。贴图尺寸、裁切、锚点、UV、透明区、图集rect/rotated/trimmed、碰撞观感与ID映射维持契约；重绘角色不能改变骨骼和玩法轮廓。抽象图形不是一概排除：图案配对牌可换语义，而箭头路径、颜色容量、数字大小本身承担规则时应降级。'''
unknowns='''待确认：①各包运行时真正引用/闲置/远程资源的完整清单；②内嵌ZIP、data/bin/wasm中的实际资源与可回写路径；③源码、可编辑工程、构建工具是否具备；④目标国家、目标语言及字体/RTL现有支持；⑤全帧/全场景替换后是否能保持原玩法与碰撞观感；⑥知名名称/角色/商店图原创化后的残留检查；⑦实际工期、低端传音设备包体/性能、地区内容接受度及市场效果。以上不影响本轮给出初筛，但会影响能否正式进入制作。'''
sources=[('W3C：右至左文字处理','https://www.w3.org/TR/2009/NOTE-i18n-html-tech-bidi-20090908/'),('IGDA：游戏本地化实践','https://igda.org/resources-archive/best-practices-for-game-localization/')]
md=['# AHA Games 美术重制与本地化选型','', '日期：2026-10-21；范围：74款本地H5包。','',f"分组：P0 {counts['P0']}款；P1 {counts['P1']}款；P2 {counts['P2']}款；P3 {counts['P3']}款。",'', '## 首批建议','']
for r in ordered[:counts['P0']]:md += [f"{r['rank']}. **{r['name']}（{r['id']}，{r['score']}分）**：{r['reason']} 替换工作量：{r['effort']}。",'']
md+=['## 方法与边界','',common,'',method,'',boundaries,'','## 多语言与地区方案','',languages,'','## 全量排序','', '|排序|游戏|分组|总分|工作量|理由|','|---|---|---|---:|---|---|']
for r in ordered:md.append(f"|{r['rank']}|{r['name']} ({r['id']})|{r['tier']}|{r['score']}|{r['effort']}|{r['reason']}|")
md+=['','## 每款替换边界与证据','']
for r in ordered:
 md += [f"### {r['rank']}. {r['name']} ({r['id']})",'',f"- 方向：{r['theme']}；五维：{' / '.join(map(str,r['dimensions']))}。",f"- 替换：{r['scope']}",f"- 注意：{r['caution']}",f"- 文化：{r['culture']}",f"- 外层证据：{r['evidenceSummary']}；压缩包 {r['zipMB']} MiB。",f"- 引擎指纹候选：{r['engine']}（未作为运行验收结论）。",f"- 语言线索：{r['languageEvidence']}。",f"- 目录：`{ROOT/r['dir']}`",'']
md+=['## 正式制作前的样板验收','', '每个候选先打通一整局开始→游玩→失败/胜利→重开，替换一组核心元素、一个图集和所有对应状态；核对ID、尺寸、锚点、动画、字体、按钮溢出、阿语连写与混排。通过后再承诺全量工期。优先用One Connect验证配对图标，用Candy Crush验证图集和语言表，用Bubble Shooter GO验证颜色/特效契约。其余首批候选按产能接续；同类泡泡、Ludo、纸牌暂不同时铺开。', '', '## 未知清单','',unknowns,'', '## 资料完整性备注','', '原manifest.json只有37条，而art_manifest.csv、实际游戏目录和HTML均有74款；本轮以三者中完整的74款清单交叉校对，并逐包读取，不依赖旧manifest遗漏第二批。图像去重按完整文件SHA-256，仅识别字节相同文件，不识别裁切重复或内容近似。包内图集有大量对象；内嵌ZIP未递归计数。', '', '## 参考','']
md += [f'- [{label}]({url})' for label,url in sources]
(OUT/'筛选说明.md').write_text('\n'.join(md),encoding='utf-8')
css='''
/* RESKIN_REVIEW_STYLE_BEGIN */
header{position:relative} .review-shell{max-width:1500px;margin:24px auto 0;padding:0 28px}
.review-panel{border:1px solid #334354;background:linear-gradient(135deg,#172533,#171a21 70%);border-radius:16px;padding:24px;margin-bottom:18px}
.review-panel h2{font-size:25px;margin:4px 0 12px}.review-panel h3{font-size:17px;margin:15px 0 8px}
.review-kicker{color:#83d4cb;font-size:12px;letter-spacing:1px}.review-muted{color:#aab6c4;font-size:13px}
.review-metrics{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}.review-metrics span{background:#101820;border:1px solid #334354;border-radius:9px;padding:9px 14px}
.review-top{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.review-pick{padding:16px;background:#121a23;border:1px solid #304656;border-radius:11px}
.review-pick strong{display:block;font-size:16px}.review-pick p{font-size:13px;color:#b5c0cd;margin:7px 0}.review-pick .review-score{float:right;color:#93e2c8;font-size:21px}
.review-table-wrap{overflow-x:auto;border:1px solid #303a47;border-radius:10px;margin-top:14px}
.review-table{border-collapse:collapse;width:100%;font-size:13px;background:#151b23;min-width:1080px}.review-table th,.review-table td{padding:12px;border-bottom:1px solid #2a3440;text-align:left;vertical-align:top}.review-table th{background:#22303c;white-space:nowrap}.review-table td:nth-child(2){min-width:190px}.review-table td:last-child{min-width:300px}.review-table tr:hover{background:#1d2935}
.review-pill{display:inline-block;border-radius:6px;padding:2px 8px;font-size:12px;font-weight:600;background:#303743;color:#c7d0dd;white-space:nowrap}.tier-P0{background:#173e35;color:#8ce0bd}.tier-P1{background:#193652;color:#93c6fa}.tier-P2{background:#453521;color:#eec385}.tier-P3{background:#3c2932;color:#e1a4b3}
.review-note{padding:16px 20px;margin:0 20px 20px;background:#111b24;border-left:3px solid #5289b3;border-radius:6px;font-size:13px}.review-note p{margin:6px 0}.review-note details{margin-top:8px}.review-note summary{cursor:pointer;color:#9fc4e8}.review-note .review-evidence{color:#9daec1;font-size:12px;overflow-wrap:anywhere}
.review-panel details{border-top:1px solid #334354;padding-top:12px;margin-top:14px}.review-panel summary{cursor:pointer;color:#b2d4f5;font-weight:600}.review-panel details p{font-size:13px;color:#bac5d1}
.review-tools{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.review-tools select{min-width:160px}.review-formula{font-variant-numeric:tabular-nums;white-space:nowrap;font-size:12px;color:#95acbe}.card{scroll-margin-top:15px}.review-empty{color:#e3bc82;padding:15px}
.review-tools button{background:#263c50;border:1px solid #4a6880;border-radius:8px;color:#e6f1fa;padding:8px 12px;cursor:pointer;font:inherit;font-size:13px}.review-tools button:hover{background:#34536d}.review-tools button:focus-visible,summary:focus-visible,a:focus-visible{outline:2px solid #91d6ed;outline-offset:3px}
@media(max-width:900px){.review-top{grid-template-columns:repeat(2,minmax(0,1fr))}.review-shell{padding:0 16px}.review-panel{padding:18px}}
@media(max-width:540px){.review-top{grid-template-columns:1fr}.review-panel h2{font-size:21px}.review-note{margin-left:12px;margin-right:12px}.review-tools select{width:100%}}
/* RESKIN_REVIEW_STYLE_END */
'''
top=''.join(f'''<article class="review-pick"><span class="review-score">{r['score']}</span><span class="review-kicker">首批 · {r['rank']:02d}</span><strong><a href="#game-{r['id']}" data-review-jump="{r['id']}">{h(r['name'])}</a></strong><p>{h(r['theme'])} · 工作量 {h(r['effort'])}</p><p>{h(r['reason'])}</p></article>''' for r in ordered if r['tier']=='P0')
trs=[]
for r in ordered:
 a,c,e,l,f=r['dimensions']
 trs.append(f'''<tr class="review-row" data-game="{r['id']}"><td>{r['rank']:02d}</td><td><a href="#game-{r['id']}" data-review-jump="{r['id']}"><b>{h(r['name'])}</b></a><div class="review-muted">{r['id']} · {h(r['theme'])}</div></td><td><span class="review-pill tier-{r['tier']}">{r['tier']}</span><br>{h(labels[r['tier']])}</td><td><b>{r['score']}</b><div class="review-formula">{a} / {c} / {e} / {l} / {f}</div></td><td>{h(r['effort'])}<div class="review-muted">图片 {r['images']} / 去重 {r['uniqueImages']}<br>{r['zipMB']} MiB</div></td><td>{h(r['reason'])}<div class="review-muted">{h(r['caution'])}</div></td></tr>''')
section=f'''<!-- RESKIN_REVIEW_BEGIN -->
<section class="review-shell" id="reskin-review" aria-labelledby="review-heading"><div class="review-panel">
<div class="review-kicker">选型评估 · 2026-10-21 · 玩法与代码保持原样</div><h2 id="review-heading">先做 6 款，保留 {counts['P1']} 款第二批与替补</h2>
<p>优先选择<strong>主题可替换、文化表达灵活、全量工作量可控</strong>的游戏。箭头、数字、纯色块不因包体小而优先；多角色内容库与三维封包也不因封面好看而低估成本。</p>
<div class="review-metrics"><span><b>74</b> 款已初筛</span><span>P0 <b>{counts['P0']}</b> 首批</span><span>P1 <b>{counts['P1']}</b> 第二批 / 替补</span><span>P2 <b>{counts['P2']}</b> 暂缓</span><span>P3 <b>{counts['P3']}</b> 不优先</span></div>
<div class="review-top">{top}</div>
<p class="review-muted">建议先用 One Connect 做完整样板，再验证 Candy Crush 的图集/语言表和 Bubble Shooter GO 的颜色/特效契约。相近泡泡龙、Ludo和纸牌首批不重复铺开。分数是选型判断，未验证营收、地区偏好或实际制作工时。</p>
<details><summary>评估方法、证据深度与评分口径</summary><p>{h(common)}</p><p>{h(method)}</p><p>五维显示顺序：美术收益 / 文化展示适配 / 工作量易度 / 本地化易度 / 不改代码可行性。5分最好，1分最弱。低—中/中/高是相对工作量，不是已报价的人日。引擎仅有静态指纹候选，不作为运行验收。</p><p>原manifest.json仅37条，完整的art_manifest.csv、实际目录和原HTML为74款；本轮逐个包体核对。图片按PNG/JPEG/WebP外层文件计数，去重按SHA-256，不含内嵌ZIP和二进制中的贴图。</p></details>
<details open><summary>“代码不动”与多语言的关键条件</summary><p>{h(languages)}</p></details>
<details><summary>文化表达建议与全量替换范围</summary><p>非洲、南亚、中东和东南亚内部差异很大。本页文化备注是待验证的设计建议，不是地区禁令或受众偏好的已证实结论。建议以水果、自然、原创日用品、家庭桌游和虚构运动品牌作为初始方向；涉及肉类、露肤、恐怖、真实阵营或明显品牌角色时逐项看具体内容。</p><p>{h(boundaries)}</p></details>
<details><summary>正式制作前仍需确认的事项</summary><p>{h(unknowns)}</p><p>每款先验一整局开始→游玩→失败/胜利→重开；核对完整美术映射、原交互尺寸、全部动画状态及目标语言。P0表示优先取证和试换，不能理解为已经验证零代码量产。</p></details>
<p class="review-muted">完整说明：<a href="reskin_review/筛选说明.md">筛选说明</a> · <a href="reskin_review/reskin_ranking.csv">74款评分 CSV</a> · <a href="reskin_review/reskin_ranking.json">评分 JSON</a> · <a href="reskin_review/package_audit.json">包内静态清单</a> · <a href="reskin_review/contact_1.jpg">预览拼图 1</a> / <a href="reskin_review/contact_2.jpg">2</a> / <a href="reskin_review/contact_3.jpg">3</a> / <a href="reskin_review/contact_4.jpg">4</a> · <a href="reskin_review/internal_1.jpg">包内样本 1</a> / <a href="reskin_review/internal_2.jpg">2</a> / <a href="reskin_review/internal_3.jpg">3</a></p>
<p class="review-muted">参考：{' · '.join(f'<a href="{url}" target="_blank" rel="noreferrer">{h(label)}</a>' for label,url in sources)}。链接用于方法参考，具体排名来自本地材料与人工判断。</p>
</div><div class="review-panel"><h3>74 款优先级排序</h3><div class="review-tools">
<label for="priority">分组</label><select id="priority"><option value="">全部分组</option>{''.join(f'<option value="{k}">{k} · {v}</option>' for k,v in labels.items())}</select>
<label for="sort">排序</label><select id="sort"><option value="priority">综合优先级</option><option value="score">总分优先</option><option value="effort">工作量从低到高</option><option value="art">美术收益优先</option><option value="original">原始顺序</option></select>
<button type="button" id="review-reset">重置全部筛选</button><span class="review-muted" id="review-count"></span></div>
<p class="review-muted">与页面顶部搜索、分类联动；下方原卡片也同步筛选/排序。点击游戏名跳到原始素材和逐款备注。表内排序号始终表示综合优先级。</p>
<div class="review-table-wrap"><table class="review-table"><thead><tr><th>排序</th><th>游戏 / 建议方向</th><th>分组</th><th>总分 / 五维</th><th>相对工作量 / 证据</th><th>理由与限制</th></tr></thead><tbody id="review-rows">{''.join(trs)}</tbody></table></div><p id="review-empty" class="review-empty hidden">没有符合条件的游戏，请调整筛选。</p>
</div></section>
<!-- RESKIN_REVIEW_END -->'''
cardpattern=re.compile(r'<section class="card"[^>]*>.*?</section>',re.S)
matches=list(cardpattern.finditer(original));assert len(matches)==74
card_original_ids=[]
def decorate(match):
 block=match.group(0)
 gid=int(re.search(r'class="folder">.*?(\d{5})_',block).group(1));r=byid[gid];card_original_ids.append(gid)
 block=block.replace('<section class="card"',f'<section class="card" id="game-{gid}" data-game="{gid}"',1)
 note=f'''<!-- REVIEW_NOTE_BEGIN --><aside class="review-note" aria-label="换皮筛选备注"><p><span class="review-pill tier-{r['tier']}">{r['tier']} · {h(labels[r['tier']])}</span> <b>综合 #{r['rank']:02d} · {r['score']} / 100</b> · 工作量 {h(r['effort'])} · {h(r['theme'])}</p><p><b>筛选理由：</b>{h(r['reason'])}</p><details><summary>查看替换范围、文化备注与包内证据</summary><p><b>替换范围：</b>{h(r['scope'])}</p><p><b>条件 / 降级原因：</b>{h(r['caution'])}</p><p><b>文化展示：</b>{h(r['culture'])}</p><p class="review-evidence">{h(r['evidenceSummary'])}；{r['zipMB']} MiB；引擎指纹候选：{h(r['engine'])}。<br>语言线索：{h(r['languageEvidence'])}<br>包内资源例：{h('；'.join(r['resourceExamples'][:2]))}</p></details></aside><!-- REVIEW_NOTE_END -->'''
 return block.replace('</section>',note+'</section>')
updated=cardpattern.sub(decorate,original)
updated=updated.replace('搜索游戏名 / 文件夹名 / 分类 / 标签 …','搜索名称 / ID / 换皮方向 / 备注 …',1)
updated=updated.replace('</style>',css+'\n</style>',1)
updated=updated.replace('</header><main id="list">','</header>'+section+'<main id="list">',1)
assert '<!-- RESKIN_REVIEW_BEGIN -->' in updated
script='''
const cards=[...document.querySelectorAll('.card')];
const reviewData=REVIEW_DATA;
const q=document.getElementById('q'),cat=document.getElementById('cat'),cnt=document.getElementById('cnt');
const priority=document.getElementById('priority'),sort=document.getElementById('sort');
const rowMap=new Map([...document.querySelectorAll('.review-row')].map(el=>[el.dataset.game,el]));
const list=document.getElementById('list'),reviewRows=document.getElementById('review-rows');
const originalIndex=new Map(cards.map((el,i)=>[el.dataset.game,i]));
function compareCards(a,b){
 const x=reviewData[a.dataset.game],y=reviewData[b.dataset.game];
 if(sort.value==='original')return originalIndex.get(a.dataset.game)-originalIndex.get(b.dataset.game);
 if(sort.value==='score')return y.score-x.score||x.rank-y.rank;
 if(sort.value==='effort')return y.dimensions[2]-x.dimensions[2]||x.rank-y.rank;
 if(sort.value==='art')return y.dimensions[0]-x.dimensions[0]||x.rank-y.rank;
 return x.rank-y.rank;
}
function apply(){
 const t=q.value.trim().toLowerCase(),c=cat.value,p=priority.value;
 let n=0;
 for(const el of [...cards].sort(compareCards)){
  const r=reviewData[el.dataset.game];
  const searchText=el.dataset.s+' '+el.dataset.game+' '+r.search;
  const show=(!t||searchText.includes(t))&&(!c||el.dataset.cat===c)&&(!p||r.tier===p);
  el.classList.toggle('hidden',!show);
  const row=rowMap.get(el.dataset.game);row.classList.toggle('hidden',!show);
  list.appendChild(el);reviewRows.appendChild(row);
  if(show)n++;
 }
 cnt.textContent=`显示 ${n} / ${cards.length}`;
 document.getElementById('review-count').textContent=`显示 ${n} / ${cards.length} 款`;
 document.getElementById('review-empty').classList.toggle('hidden',n!==0);
}
function resetReview(){q.value='';cat.value='';priority.value='';sort.value='priority';apply();}
q.addEventListener('input',apply);cat.addEventListener('change',apply);priority.addEventListener('change',apply);sort.addEventListener('change',apply);
document.getElementById('review-reset').addEventListener('click',resetReview);
document.querySelectorAll('[data-review-jump]').forEach(link=>link.addEventListener('click',event=>{
 event.preventDefault();const target=document.getElementById('game-'+link.dataset.reviewJump);
 if(target.classList.contains('hidden'))resetReview();
 target.scrollIntoView({behavior:'smooth',block:'start'});
 history.replaceState(null,'','#'+target.id);
}));
apply();
'''
client={str(r['id']):dict(rank=r['rank'],tier=r['tier'],score=r['score'],dimensions=r['dimensions'],search=(' '.join([r['theme'],r['reason'],r['scope'],r['caution'],r['culture']])).lower()) for r in ordered}
script=script.replace('REVIEW_DATA',json.dumps(client,ensure_ascii=False).replace('</','<\\/'))
updated=re.sub(r'<script>.*?</script>',lambda m:'<script>'+script+'</script>',updated,flags=re.S)
(ROOT/'index.html').write_text(updated,encoding='utf-8')
(OUT/'review_script.js').write_text(script,encoding='utf-8')
# Verify preservation by stripping only the exact inserted data and notes.
newcards=cardpattern.findall(updated)
def clean(block):
 block=re.sub(r' id="game-\d+" data-game="\d+"','',block,count=1)
 return re.sub(r'<!-- REVIEW_NOTE_BEGIN -->.*?<!-- REVIEW_NOTE_END -->','',block,flags=re.S)
assert [m.group(0) for m in matches]==[clean(x) for x in newcards], 'Original card content changed'
assert len(re.findall(r'<img\b',updated))==len(re.findall(r'<img\b',original))==370
assert len(re.findall(r'class="review-row"',updated))==74
assert len(re.findall(r'<!-- REVIEW_NOTE_BEGIN -->',updated))==74
verification={'date':'2026-10-21','games':len(ordered),'tiers':dict(counts),'originalCardsPreserved':True,'inlineImagesPreserved':370,'originalHtmlSHA256':hashlib.sha256(BACKUP.read_bytes()).hexdigest(),'modifiedHtmlSHA256':hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest(),'browserVerification':'未执行：浏览器拒绝file协议访问；未绕过该限制','scope':'静态选型初筛；未修改游戏ZIP、玩法、代码或美术资产'}
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(verification,ensure_ascii=False,indent=2))
