"""生成离线资源浏览器、证据报告和校验压缩包；没有人工分析时明确输出库存状态。"""
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import quote
import zipfile
from common import local_path, read_json, sha256, write_json

MEDIA = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.wav', '.ogg', '.mp3', '.ttf', '.otf', '.obj'}
CSS = '''body{margin:0;background:#eef3f8;color:#23334a;font:16px/1.8 system-ui}main{max-width:1180px;margin:28px auto;background:white;padding:32px;border-radius:14px}h1{line-height:1.4}h2{margin-top:38px;border-top:1px solid #dce5ef;padding-top:20px}a{color:#096dba;overflow-wrap:anywhere}table{display:block;overflow:auto;border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #dce5ef;padding:8px;min-width:90px}th{background:#edf4fc}pre{background:#18273c;color:#e7f0ff;padding:18px;overflow:auto;border-radius:8px}.note{background:#edf4fc;padding:15px;border-radius:8px}input,select,button{padding:9px;margin:5px;border:1px solid #aac0d6;border-radius:6px}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px}.card{background:#f0f5fb;padding:12px;overflow:hidden;border-radius:8px}.card img{width:100%;height:150px;object-fit:contain;background:#26374d}.card p{font-size:13px;overflow-wrap:anywhere}audio{width:100%}summary{cursor:pointer}code{overflow-wrap:anywhere}p{overflow-wrap:anywhere}@media(max-width:600px){main{margin:0;padding:16px}}'''


def link(path, label):
    return f'<a href="{quote(str(path), safe="/")}">{html.escape(str(label))}</a>'


def page(title, content):
    return f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style><main>{content}</main></html>'


def grid(headers, rows):
    """表格默认转义，链接由调用方放在独立的段落中。"""
    return '<table><thead><tr>' + ''.join(f'<th>{html.escape(str(value))}</th>' for value in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{html.escape(str(value))}</td>' for value in row) + '</tr>' for row in rows) + '</tbody></table>'


def collect_media(root, objects, inventory):
    """对象导出和 APK 普通媒体分别标注；缩略图失败不丢弃原文件。"""
    from PIL import Image
    files = {}
    for item in objects:
        for relative in item['exports']:
            if Path(relative).suffix.lower() in MEDIA:
                files[relative] = {'name': item.get('name') or Path(relative).name, 'type': item['type'],
                                   'origin': 'Unity 对象', 'source': item['source'], 'path_id': str(item['path_id'])}
    for item in inventory:
        if Path(item['file']).suffix.lower() in MEDIA:
            files.setdefault(item['file'], {'name': Path(item['file']).name, 'type': '包内普通媒体',
                                            'origin': 'Android/其他文件', 'source': item['path'], 'path_id': ''})
    thumbnails = root / 'browser/thumbnails'
    thumbnails.mkdir(parents=True, exist_ok=True)
    resources = []
    for relative, item in files.items():
        source = local_path(root, relative)
        row = {**item, 'path': relative, 'bytes': source.stat().st_size, 'width': '', 'height': '', 'thumbnail': '', 'error': ''}
        if source.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
            try:
                with Image.open(source) as raw:
                    raw.load()
                    image = raw.convert('RGBA')
                    row['width'], row['height'] = image.size
                    image.thumbnail((180, 140))
                    canvas = Image.new('RGBA', (192, 152), '#28384f')
                    canvas.alpha_composite(image, ((192 - image.width) // 2, (152 - image.height) // 2))
                    destination = thumbnails / (hashlib.sha256(relative.encode()).hexdigest()[:24] + '.jpg')
                    canvas.convert('RGB').save(destination, quality=80)
                    row['thumbnail'] = destination.relative_to(root).as_posix()
            except Exception as error:
                row['error'] = str(error)[:300]
        resources.append(row)
    write_json(root / 'browser/resources.json', resources)
    with (root / 'analysis/art_resources.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        fields = ['name', 'type', 'origin', 'source', 'path_id', 'path', 'bytes', 'width', 'height', 'thumbnail', 'error']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(resources)
    return resources


def build_gallery(root, resources):
    """内嵌索引支持直接双击打开，分页和懒加载避免一次渲染所有切图。"""
    body = '''<h1>APK 提取资源浏览器</h1><p><a href="report.html">返回报告</a> · <a href="analysis/art_resources.csv">资源 CSV</a></p><p>原图集与切图可能包含重复像素；包内普通媒体可能来自 SDK，不能自动等同于主玩法素材。</p><input id="query" placeholder="搜索资源名"><select id="kind"><option value="">全部类型</option></select><p id="status"></p><div id="grid"></div><button id="more">继续加载</button>'''
    script = r'''<script id="data" type="application/json">__DATA__</script><script>
// 索引由本地解析结果产生；名称仅作为文本显示，不执行包内脚本。
const rows=JSON.parse(document.getElementById('data').textContent),grid=document.getElementById('grid');let shown=0,selected=[];
const url=s=>s.split('/').map(encodeURIComponent).join('/');
for(const value of [...new Set(rows.map(r=>r.type))].sort()){const option=document.createElement('option');option.value=value;option.textContent=value;document.getElementById('kind').append(option)}
function add(){for(const row of selected.slice(shown,shown+80)){const card=document.createElement('article');card.className='card';const download=document.createElement('a');download.href=url(row.path);download.download='';download.textContent='下载原文件';if(row.thumbnail){const anchor=document.createElement('a');anchor.href=url(row.path);anchor.target='_blank';const image=document.createElement('img');image.loading='lazy';image.src=url(row.thumbnail);image.alt=row.name;anchor.append(image);card.append(anchor)}else if(/\.(wav|ogg|mp3)$/i.test(row.path)){const audio=document.createElement('audio');audio.controls=true;audio.preload='none';audio.src=url(row.path);card.append(audio)}const name=document.createElement('p');name.textContent=row.name;const meta=document.createElement('p');meta.textContent=`${row.type} · ${row.origin} · ${row.width?row.width+' × '+row.height:''} ${(row.bytes/1024).toFixed(1)} KiB`;const details=document.createElement('details'),summary=document.createElement('summary'),source=document.createElement('p');summary.textContent='来源与对象编号';source.textContent=row.source+' / '+row.path_id;details.append(summary,source);card.append(name,meta,download,details);grid.append(card)}shown=Math.min(shown+80,selected.length);document.getElementById('status').textContent=`共 ${selected.length} 个匹配文件，已显示 ${shown} 个`;document.getElementById('more').hidden=shown>=selected.length}
function filter(){const query=document.getElementById('query').value.toLowerCase(),kind=document.getElementById('kind').value;selected=rows.filter(row=>(!kind||row.type===kind)&&row.name.toLowerCase().includes(query));shown=0;grid.replaceChildren();add()}
document.getElementById('query').addEventListener('input',filter);document.getElementById('kind').addEventListener('input',filter);document.getElementById('more').addEventListener('click',add);filter();
</script>'''
    script = script.replace('__DATA__', json.dumps(resources, ensure_ascii=False).replace('<', '\\u003c'))
    (root / 'assets.html').write_text(page('APK 资源浏览器', body + script), encoding='utf-8')


def pack(root, destination, relative_paths):
    """压缩包仅取规范清单，防止重跑遗留文件被误当成最新成功产物。"""
    paths = sorted(set(relative_paths))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        for relative in paths:
            source = local_path(root, relative)
            mode = zipfile.ZIP_STORED if source.suffix.lower() in ('.png', '.jpg', '.webp', '.ogg', '.mp3') else zipfile.ZIP_DEFLATED
            archive.write(source, relative, compress_type=mode)
    with zipfile.ZipFile(destination) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f'压缩包 CRC 校验失败：{bad}')
    return {'file': destination.relative_to(root).as_posix(), 'files': len(paths), 'bytes': destination.stat().st_size,
            'sha256': sha256(destination), 'crc_check': '通过'}


def build_report(root, package, unity, findings, manifests):
    """事实分析由 Agent 提供；脚本仅渲染证据，不根据名称生成貌似已验证的结论。"""
    title = findings.get('title') if findings else 'APK 包内容清单（尚未完成工程分析）'
    body = f'<h1>{html.escape(title or "APK 工程分析")}</h1>'
    body += '<p>' + link('assets.html', '浏览资源') + ' · ' + link('package_summary.json', '来源与包信息') + ' · ' + link('file_inventory.json', '带哈希的完整文件清单') + '</p>'
    body += '<p class="note">本次输出以静态文件证据为基础。恢复声明和占位 DLL 不等于原始实现；代码和资源中的功能不一定对所有玩家实际启用。</p>'
    if findings:
        body += '<p>' + html.escape(findings.get('scope', '静态拆解，运行验证情况见各项证据。')) + '</p>'
    else:
        body += '<p class="note">尚未提供核心代码阅读与业务分析，目前只有自动库存。不可把此页面作为完整工程拆解报告交付。</p>'
    body += '<h2>安装包与工程线索</h2>'
    body += grid(['包名', '版本', '分包标识', 'min/target API'], [[item['android'].get('package', '未解码'), item['android'].get('version_name', ''), item['android'].get('split', ''), f"{item['android'].get('min_sdk', '')}/{item['android'].get('target_sdk', '')}"] for item in package['archives']])
    body += '<p>引擎线索：' + html.escape(', '.join(package['engines'])) + f'；APK 文件总量：{package["file_count"]}；解压数据：{package["uncompressed_bytes"]/1048576:.1f} MiB。</p>'
    if unity:
        body += '<h2>Unity 资源统计</h2>' + grid(['对象类型', '打包对象数'], sorted(unity['type_counts'].items()))
        body += '<p>解码失败分布：' + html.escape(json.dumps(unity['decode_failure_counts'], ensure_ascii=False)) + '。失败字节和原始文件仍保留。</p>'
    allowed = {'包内证据', '指令验证', '结构推断', '重建建议', '待验证'}
    for section in (findings or {}).get('sections', []):
        confidence = section.get('basis')
        if confidence not in allowed:
            raise ValueError(f'分析章节必须注明有效证据类型：{section.get("title")}')
        body += '<h2>' + html.escape(section['title']) + '</h2><p class="note">证据类型：' + confidence + '</p>'
        for paragraph in section.get('paragraphs', []):
            body += '<p>' + html.escape(paragraph) + '</p>'
        for value in section.get('tables', []):
            body += grid(value['headers'], value['rows'])
        for code in section.get('code', []):
            body += '<p>' + html.escape(code['label']) + '</p><pre><code>' + html.escape(code['text']) + '</code></pre>'
        for item in section.get('evidence', []):
            target = local_path(root, item['path'])
            if not target.is_file():
                raise FileNotFoundError(f'报告引用的证据不存在：{item["path"]}')
            body += '<p>' + link(item['path'], item['label']) + '</p>'
    body += '<h2>产物与校验</h2>'
    for item in manifests:
        body += '<p>' + link(item['file'], Path(item['file']).name) + f' · {item["bytes"]/1048576:.1f} MiB · {item["files"]} 个文件 · CRC 通过</p>'
    body += '<p>' + link('deliverables/manifest.json', '压缩包 SHA-256 校验清单') + '</p>'
    for relative, label in [('analysis/config_index.json', '配置字段索引'), ('analysis/resource_links.json', '对象引用关系'), ('analysis/node_hierarchy.txt', '节点层级'), ('analysis/decode_failures.json', '解码失败清单'), ('code/types.json', '代码类型索引'), ('code/native_core/index.json', '关键原生方法')]:
        if (root / relative).is_file():
            body += '<p>' + link(relative, label) + '</p>'
    for limitation in (findings or {}).get('limitations', []):
        body += '<p class="note">' + html.escape(limitation) + '</p>'
    (root / 'report.html').write_text(page(title or 'APK 工程分析', body), encoding='utf-8')


def run(args):
    root = args.workspace.resolve()
    package = read_json(root / 'package_summary.json')
    inventory = read_json(root / 'file_inventory.json')
    objects = read_json(root / 'unity_objects.json') if (root / 'unity_objects.json').exists() else []
    unity = read_json(root / 'unity_summary.json') if (root / 'unity_summary.json').exists() else None
    findings = read_json(args.findings) if args.findings else None
    if findings is not None and not findings.get('sections'):
        raise ValueError('分析文件没有章节，不能标记为已完成的工程报告')
    (root / 'analysis').mkdir(exist_ok=True)
    resources = collect_media(root, objects, inventory)
    build_gallery(root, resources)
    resource_paths = [name for item in objects for name in item['exports']]
    resource_paths.extend(item['path'] for item in resources)
    resource_paths.extend(path.relative_to(root).as_posix() for path in (root / 'analysis').rglob('*') if path.is_file())
    resource_paths.extend(path.relative_to(root).as_posix() for path in (root / 'recovered').rglob('*') if path.is_file())
    resource_paths.extend(name for name in ['package_summary.json', 'file_inventory.json', 'unity_objects.json', 'unity_summary.json', 'browser/resources.json'] if (root / name).is_file())
    manifests = [pack(root, root / 'deliverables/resources.zip', resource_paths)]
    code_paths = [path.relative_to(root).as_posix() for directory in ['code/il2cpp', 'code/gameplay', 'code/native_core'] for path in (root / directory).rglob('*') if path.is_file()]
    code_paths.extend(name for name in ['code/types.json', 'code/assemblies.json'] if (root / name).is_file())
    if code_paths:
        manifests.append(pack(root, root / 'deliverables/core_code.zip', code_paths))
    write_json(root / 'deliverables/manifest.json', manifests)
    if findings is not None:
        write_json(root / 'findings.json', findings)
    build_report(root, package, unity, findings, manifests)
    write_json(root / 'delivery_validation.json', {'canonical_exports': sum(len(item['exports']) for item in objects),
               'media_files': len(resources), 'thumbnail_failures': sum(bool(item['error']) for item in resources),
               'archive_crc': '全部通过', 'report_state': '包含人工分析，结论需按证据复核' if findings else '仅库存，工程分析尚未完成'})
    print(f'已生成报告、资源浏览器和 {len(manifests)} 个压缩包；媒体文件 {len(resources)} 个，CRC 全部通过')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--findings', type=Path, help='Agent 阅读证据后编写的结构化分析，不提供时明确标记为库存')
    run(parser.parse_args())
