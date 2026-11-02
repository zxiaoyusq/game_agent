"""把已完成的竞品研究 Markdown 渲染为阅读版，内嵌本地图片并核对页面引用。"""
import argparse
import base64
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

import markdown


class ReportParser(HTMLParser):
    """检查渲染结果中的图片与链接，保留 Markdown 生成的 HTML 结构。"""
    def __init__(self, root):
        super().__init__(convert_charrefs=False)
        self.root = root
        self.chunks = []
        self.embedded = []
        self.remote = []
        self.links = []
        self.ids = set()
        self.chapters = 0

    def image_uri(self, source):
        """仅内嵌真实可识别的本地位图，不联网下载，不按扩展名猜 MIME。"""
        parsed = urlsplit(source)
        if parsed.scheme in ('http', 'https') and parsed.netloc:
            self.remote.append(source)
            return source
        if parsed.scheme or parsed.netloc:
            raise ValueError(f'图片引用须为本地相对路径或 HTTP(S) 地址：{source}')
        path = (self.root / unquote(parsed.path)).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f'图片路径越出报告目录：{source}')
        data = path.read_bytes()
        if data.startswith(b'\x89PNG\r\n\x1a\n'):
            mime = 'image/png'
        elif data.startswith(b'\xff\xd8\xff'):
            mime = 'image/jpeg'
        elif data[:6] in (b'GIF87a', b'GIF89a'):
            mime = 'image/gif'
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            mime = 'image/webp'
        else:
            raise ValueError(f'不支持或无法识别的图片格式：{source}')
        self.embedded.append({'path': path.relative_to(self.root).as_posix(), 'mime': mime, 'bytes': len(data)})
        return f'data:{mime};base64,' + base64.b64encode(data).decode('ascii')

    def start(self, tag, attrs, closing):
        """图片重新生成经过转义的属性，其余标签保留渲染器原有格式。"""
        values = dict(attrs)
        if values.get('id'):
            self.ids.add(values['id'])
        if tag == 'h2':
            self.chapters += 1
        if tag == 'a' and values.get('href'):
            self.links.append(values['href'])
        if tag != 'img':
            self.chunks.append(self.get_starttag_text())
            return
        if not values.get('src'):
            raise ValueError('图片缺少 src')
        values['src'] = self.image_uri(values['src'])
        rendered = ' '.join(f'{key}="{escape(value, quote=True)}"' if value is not None else key for key, value in values.items())
        self.chunks.append('<img ' + rendered + (' />' if closing else '>'))

    def handle_starttag(self, tag, attrs):
        self.start(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self.start(tag, attrs, True)

    def handle_endtag(self, tag):
        self.chunks.append(f'</{tag}>')

    def handle_data(self, data):
        self.chunks.append(data)

    def handle_entityref(self, name):
        self.chunks.append(f'&{name};')

    def handle_charref(self, name):
        self.chunks.append(f'&#{name};')

    def handle_comment(self, data):
        self.chunks.append(f'<!--{data}-->')

    def broken_links(self):
        """远程网页由研究过程核实，这里只检查本地文件和文内锚点。"""
        missing = []
        for href in self.links:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc:
                continue
            if parsed.path:
                if not (self.root / unquote(parsed.path)).exists():
                    missing.append(href)
            elif parsed.fragment and unquote(parsed.fragment) not in self.ids:
                missing.append(href)
        return sorted(set(missing))


CSS = '''
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f1f5f7;color:#203542;font:16px/1.85 system-ui,sans-serif}a{color:#087f82;overflow-wrap:anywhere}header{background:#173c4b;color:white;padding:18px 28px}header button{float:right;padding:7px 14px;cursor:pointer}.layout{display:grid;grid-template-columns:260px minmax(0,1fr);gap:24px;max-width:1500px;margin:auto;padding:24px}aside{position:sticky;top:20px;align-self:start;max-height:90vh;overflow:auto;background:white;padding:18px;font-size:13px;border-radius:10px}aside ul{padding-left:18px}aside ul ul ul{display:none}article{min-width:0;background:white;border-radius:10px;padding:32px 40px}h1{line-height:1.4}h2{border-top:1px solid #dce5ea;padding-top:24px;margin-top:40px}h1,h2,h3{scroll-margin-top:20px}img{display:block;max-width:100%;height:auto;margin:20px auto}.table-scroll{overflow:auto;max-width:100%;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #dce5ea;text-align:left;vertical-align:top;padding:10px;min-width:100px}th{background:#edf6f6}pre{overflow:auto;background:#edf2f5;padding:16px}code{overflow-wrap:anywhere}blockquote{border-left:4px solid #8fc3c3;padding-left:16px;color:#49616b}.mobile-toc{display:none}footer{color:#647780;border-top:1px solid #dce5ea;margin-top:30px;padding-top:14px;font-size:13px}
@media(max-width:760px){.layout{display:block;padding:10px}aside{display:none}article{padding:20px 16px}h1{font-size:27px}.mobile-toc{display:block;background:#edf6f6;padding:12px}.mobile-toc ul{padding-left:20px}.mobile-toc ul ul ul{display:none}}
@media print{body{background:white;font-size:11px}header,aside,.mobile-toc{display:none}.layout{display:block;padding:0}article{padding:0}.table-scroll{overflow:visible}th,td{min-width:0;padding:5px}table{font-size:10px}h2,h3{break-after:avoid}tr,img{break-inside:avoid}img{max-height:650px;object-fit:contain}}
'''


def render(args):
    """对可信研究源稿做展示转换，研究真伪和完整性仍由 Agent 核验。"""
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if source.parent != output.parent or source == output:
        raise ValueError('HTML 与 Markdown 必须为同目录的不同文件，以保持相对链接正确')
    content = source.read_text(encoding='utf-8')
    if not content.strip() or '[TODO' in content:
        raise ValueError('源稿为空或仍含初始化占位符，不能交付')
    converter = markdown.Markdown(extensions=['tables', 'toc', 'fenced_code'], extension_configs={'toc': {'toc_depth': '2-3'}})
    body = converter.convert(content)
    parser = ReportParser(source.parent)
    parser.feed(body + converter.toc)
    # 目录一并参与锚点核验；正文单独解析，避免重复追加目录。
    body_parser = ReportParser(source.parent)
    body_parser.feed(body)
    body = ''.join(body_parser.chunks)
    body = re.sub(r'(<table>.*?</table>)', r'<div class="table-scroll">\1</div>', body, flags=re.S)
    manifest = {'source': source.name, 'output': output.name, 'chapters': body_parser.chapters,
                'embedded_images': body_parser.embedded, 'remote_images': body_parser.remote,
                'missing_local_links': parser.broken_links(), 'research_verified': False,
                'note': '此清单仅检查渲染结构；图像是否实际查看、事实是否核实需另行验收。'}
    (source.parent / 'render_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    title = escape(args.title)
    rendered = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><header>{title}<button onclick="window.print()">打印 / 保存 PDF</button></header><div class="layout"><aside aria-label="报告目录">{converter.toc}</aside><article><details class="mobile-toc"><summary>展开报告目录</summary>{converter.toc}</details>{body}<footer>图片与资料用于竞品研究；事实、观察、反馈和建议的证据范围以正文为准。</footer></article></div></body></html>'''
    output.write_text(rendered, encoding='utf-8')
    print(f'已生成报告：{output}；二级章节 {manifest["chapters"]} 个，本地图像 {len(body_parser.embedded)} 个，远程图像 {len(body_parser.remote)} 个')
    if manifest['missing_local_links']:
        print('存在缺失本地引用，详见 render_manifest.json；请修复后再交付')
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='已经完成并核实的研究 Markdown')
    parser.add_argument('--output', type=Path, required=True, help='与源稿同目录的 HTML 文件')
    parser.add_argument('--title', required=True, help='实际游戏或玩法主题的报告标题')
    render(parser.parse_args())
