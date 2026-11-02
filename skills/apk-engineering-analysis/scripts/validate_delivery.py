"""独立核对交付文件、页面链接和压缩包，发现缺失或损坏时返回非零状态。"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import zipfile
from common import local_path, read_json, sha256, write_json


class LocalLinks(HTMLParser):
    """收集静态 HTML 引用；动态资源另由资源清单核对。"""
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                parsed = urlsplit(value)
                if not parsed.scheme and not parsed.netloc and parsed.path:
                    self.targets.append(unquote(parsed.path))


def run(args):
    root = args.workspace.resolve()
    failures = []
    checked = set()

    def check(relative):
        """所有引用限制在交付工作区内，重复路径只检查一次。"""
        if relative in checked:
            return
        checked.add(relative)
        try:
            if not local_path(root, relative).is_file():
                failures.append(f'文件不存在：{relative}')
        except ValueError as error:
            failures.append(str(error))

    for required in ('report.html', 'assets.html', 'package_summary.json', 'file_inventory.json',
                     'browser/resources.json', 'deliverables/manifest.json'):
        check(required)
    for page in ('report.html', 'assets.html'):
        if (root / page).is_file():
            parser = LocalLinks()
            parser.feed((root / page).read_text(encoding='utf-8'))
            for target in parser.targets:
                check(target)
    if (root / 'unity_objects.json').is_file():
        for item in read_json(root / 'unity_objects.json'):
            for relative in item['exports']:
                check(relative)
    if (root / 'browser/resources.json').is_file():
        for item in read_json(root / 'browser/resources.json'):
            check(item['path'])
            if item['thumbnail']:
                check(item['thumbnail'])
    if args.verify_raw:
        for item in read_json(root / 'file_inventory.json'):
            check(item['file'])
            path = local_path(root, item['file'])
            if path.is_file() and sha256(path) != item['sha256']:
                failures.append(f'原始解包文件哈希不匹配：{item["file"]}')
    if args.archives:
        for item in read_json(root / 'deliverables/manifest.json'):
            check(item['file'])
            path = local_path(root, item['file'])
            if not path.is_file():
                continue
            try:
                if path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
                    failures.append(f'压缩包大小或哈希不匹配：{item["file"]}')
                with zipfile.ZipFile(path) as archive:
                    if archive.testzip() or len(archive.infolist()) != item['files']:
                        failures.append(f'压缩包 CRC 或文件数不匹配：{item["file"]}')
            except (OSError, zipfile.BadZipFile) as error:
                failures.append(f'压缩包读取失败：{item["file"]}，{error}')
    result = {'checked_paths': len(checked), 'archives_checked': args.archives,
              'raw_hashes_checked': args.verify_raw, 'failures': failures,
              'status': '通过' if not failures else '失败', 'browser_interaction_checked': False}
    write_json(root / 'verification.json', result)
    print(f'已核对 {len(checked)} 个路径，发现 {len(failures)} 项问题；结果见 verification.json')
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--archives', action='store_true', help='重新核对归档哈希、CRC 和文件数')
    parser.add_argument('--verify-raw', action='store_true', help='逐项重新核对原始解包文件哈希')
    run(parser.parse_args())
