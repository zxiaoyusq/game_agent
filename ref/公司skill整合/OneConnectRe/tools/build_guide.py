from pathlib import Path
import html, markdown
root=Path(__file__).resolve().parent.parent
pages=[('总览','迭代接口总览.md'),('广告与宿主','迭代接口文档/01_广告与宿主接口.md'),('美术与 UI','迭代接口文档/02_美术资源替换.md'),('关卡','迭代接口文档/03_关卡配置与编辑.md'),('埋点','迭代接口文档/04_本地埋点与事件.md'),('构建与回归','迭代接口文档/05_构建运行与回归.md'),('SDK 模板','迭代接口文档/06_CombiMons模板SDK接入.md'),('激励广告','迭代接口文档/07_激励广告生命周期.md'),('竞品关卡参考','迭代接口文档/06_TileConnect关卡拆解参考.md')]
nav=''.join(f'<a href="#section{i}">{html.escape(title)}</a>' for i,(title,_) in enumerate(pages))
parts=[]
for i,(title,rel) in enumerate(pages):
 text=(root/rel).read_text(encoding='utf-8-sig')
 content=markdown.markdown(text,extensions=['tables','fenced_code'])
 if i == 0:
  for j,(_, target) in enumerate(pages[1:],start=1): content=content.replace('href="'+target+'"','href="#section'+str(j)+'"')
 parts.append(f'<section id="section{i}">{content}</section>')
out='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>One Connect 迭代接口手册</title><style>body{margin:0;background:#10182b;color:#eaf0ff;font:16px/1.75 system-ui}header,main{max-width:1250px;margin:auto;padding:24px}header p{color:#c1cde2}nav{position:sticky;top:0;z-index:1;background:#1d2a44;padding:12px;display:flex;gap:18px;flex-wrap:wrap}a{color:#9cd6ff}section{scroll-margin-top:70px;background:#1b2740;border-radius:12px;padding:25px;margin:18px 0;overflow:auto}h1{font-size:26px}h2{font-size:21px;border-bottom:1px solid #53627c;padding-bottom:8px}table{width:100%;border-collapse:collapse}th,td{border:1px solid #50617e;text-align:left;vertical-align:top;padding:8px}th{background:#293b59}code{background:#101b30;padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}pre{background:#101b30;padding:15px;overflow:auto}pre code{padding:0}blockquote{border-left:4px solid #79bdf3;padding-left:16px}strong{color:#fff}li{margin:5px 0}</style></head><body><header><h1>One Connect 迭代接口手册</h1><p>广告、美术、关卡、埋点及构建回归的实际入口和操作说明。手册由项目内 Markdown 文档生成。</p></header><nav>'''+nav+'</nav><main>'+''.join(parts)+'</main></body></html>'
(root/'迭代接口手册.html').write_text(out,encoding='utf8')
print('Built',len(pages),'sections')
