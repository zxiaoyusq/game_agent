import os,html
from PIL import Image
root=os.path.dirname(os.path.abspath(__file__))
imgdir=os.path.join(root,'baseline','images')
groups={'玩法牌面图集':[],'背景与底板':[],'字体':[],'按钮与状态变体':[],'弹窗、反馈与特效':[],'其他独立图片':[]}
for name in sorted(os.listdir(imgdir)):
 if not name.endswith('.png'):continue
 n=name.lower()
 if n.startswith('tiles-sheet'): group='玩法牌面图集'
 elif 'font' in n:group='字体'
 elif any(x in n for x in ['gametilebg','tileempty','tilepurple','tilestar','gradient','sunray','9patch']):group='背景与底板'
 elif any(x in n for x in ['button','pause-sheet','themebutton']):group='按钮与状态变体'
 elif any(x in n for x in ['popup','bonus','shine','spark','popfx','autoshuffle','nomatch','timesup','mark','line','dots','tutorial']):group='弹窗、反馈与特效'
 else:group='其他独立图片'
 with Image.open(os.path.join(imgdir,name)) as im: size=f'{im.width} × {im.height}'
 groups[group].append((name,size))
head='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>One Connect 原版截图与资源</title><style>body{margin:0;background:#0e1328;color:#e9ecfa;font:16px/1.6 system-ui}header,main{max-width:1400px;margin:auto;padding:24px}h1{font-size:30px}h2{border-bottom:1px solid #45506c;padding:15px 0}p{color:#c3cbe1}a{color:#8ac8ff}nav{display:flex;gap:20px;flex-wrap:wrap;position:sticky;top:0;background:#18223d;padding:10px 24px;z-index:2} .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:18px}.card{background:#1b2641;border-radius:12px;padding:14px}.card img{width:100%;height:auto;border-radius:6px}.assets{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}.asset{background:#1b2641;padding:10px;border-radius:8px;overflow-wrap:anywhere}.asset img{height:150px;width:100%;object-fit:contain;background:repeating-conic-gradient(#46516a 0 25%,#27334d 0 50%) 0/20px 20px}.note{background:#263654;padding:15px;border-radius:8px}.small{font-size:13px;color:#bdc9df}</style><header><h1>One Connect 原版截图与资源</h1><p>2026-10-29 · Chrome 桌面浏览器 1280×720 · 本地原版副本的自然点击截图。游戏界面与资源均来自原包；分类按文件名和静态拆解推断，未证明所有状态的用途。</p></header><nav><a href="#screens">运行截图</a><a href="#experiments">修改验证</a><a href="#assets">美术资源</a><a href="#unknown">未到达与注意事项</a></nav><main><h2 id="screens">原版运行截图</h2><div class="grid">'''
shots=[('menu.png','主菜单','直接打开原版 game.html，等待加载。'),('theme.png','主题选择','主菜单点击开始按钮。'),('board.png','对局：甜点','点击甜点主题后进入第 1 关。'),('pair_before.png','对局：动物，配对前','选择动物主题，观察随机棋盘。'),('pair_after.png','自然配对后','点击棋盘中相邻且图案相同的两张牌；两张消失，得分由 0 变为 100。'),('pause2.png','暂停','对局中点击右上角暂停。截图记录本次浏览器实际画面。'),('resumed.png','恢复对局','暂停界面点击三角播放按钮。'),('failure.png','原版超时结算','完成一次配对后等待原版 5 分钟倒计时归零；缺少宿主 showAd 报错，此画面未出现主页按钮。')]
for f,title,desc in shots:
 if os.path.exists(os.path.join(root,'screenshots',f)):head+=f'<article class="card"><h3>{title}</h3><img loading="lazy" src="screenshots/{f}"><p>{desc}</p></article>'
head+='</div><h2 id="experiments">独立副本修改验证</h2><p>仅用于验证可修改性，不是美术方向：标题图集调色，开始按钮右移 80 像素，初始计时从 300 秒改为 60 秒。</p><div class="grid">'
for f,title,desc in [('experiment_menu.png','实验菜单','可见标题变色及开始按钮右移；点击右移后的按钮进入主题选择。'),('experiment_theme.png','实验主题选择','通过右移按钮自然进入主题页。'),('experiment_board.png','实验计时','选择动物主题后显示约 0:58，验证初始 60 秒生效。'),('experiment_timeout.png','实验版超时结算','将初始计时改为 60 秒，等待倒计时自然归零；本次以本地模拟宿主接口运行。'),('quick_home.png','实验版返回菜单','10 秒实验版计时结束后点击结算页的主页按钮。'),('quick_restart.png','实验版重新开始','返回菜单后重新点击开始并选择主题，进入新一局。')]:head+=f'<article class="card"><h3>{title}</h3><img loading="lazy" src="screenshots/{f}"><p>{desc}</p></article>'
head+='</div><h2>后续自然推进截图 · 开发副本</h2><p>采用原版玩法并增加本地宿主适配；通过实际点击完成配对和奖励，没有跳关。第 3 关示例还使用了独立固定棋盘配置，不代表原版随机结果。</p><div class="grid">'
for f,title,desc in [('dev_win_result.png','第 1 关清盘奖励','完成 36 对配对后出现奖励箱。'),('dev_bonus_open.png','第 2 关','打开奖励箱后自然进入开发副本的第 2 关。'),('board_level3.png','第 3 关：固定棋盘实验','第 2 关自然完成后加载指定的固定棋盘与 180 秒时间。')]:
 if os.path.exists(os.path.join(root,'screenshots',f)):head+=f'<article class="card"><h3>{title}</h3><img loading="lazy" src="screenshots/{f}"><p>{desc}</p></article>'
head+='</div><h2 id="assets">原版美术资源</h2><p>点击图片可查看原文件。sheet 后缀表示导出贴图页，文件不一定一页对应一个 UI 状态；同名前缀的 sheet0、sheet1 等作为可能的状态或图集变体并列展示。透明区域以棋盘格显示。</p>'
for group,files in groups.items():
 head+=f'<h3>{group} · {len(files)}</h3><div class="assets">'
 for name,size in files:
  h=html.escape(name);head+=f'<div class="asset"><a href="baseline/images/{h}"><img loading="lazy" src="baseline/images/{h}" alt="{h}"></a><div>{h}</div><div class="small">{size}</div></div>'
 head+='</div>'
head+='''<h2 id="unknown">未到达与注意事项</h2><div class="note"><p>已在开发副本自然完成前两关并进入第 3 关；原版裸页面的完整过关流程仍需验证。原版超时结算可见，但缺少宿主接口时未出现主页按钮，原版完整重开未通过；不以调试跳转冒充自然解锁。直接打开游戏会出现缺少宿主 h5_sdk 的错误；真实广告和宿主回调尚未验证。</p><p>暂停页面在当前 Chrome 无头运行中呈黑底白色图标，是否与正式宿主表现一致尚待比对。测试资源颜色只是技术验证，不代表选定风格。</p></div></main></html>'''
open(os.path.join(root,'原版截图与资源.html'),'w',encoding='utf-8').write(head)
print({k:len(v) for k,v in groups.items()})
