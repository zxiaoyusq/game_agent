"""补充导出 Android 原生 XML 和资源表，区别于 Unity 玩法美术配置。"""
import json
from pathlib import Path
import re
import sys
import argparse
from common import read_json, write_json, local_path, safe_name
from loguru import logger
logger.disable('androguard')
from androguard.core.axml import AXMLPrinter, ARSCParser
def run(root, archive_root, archive_id):
    output = root / 'analysis/android_resources' / archive_id
    results = []
    for path in (archive_root / 'res').rglob('*.xml'):
        destination = output / path.relative_to(archive_root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            raw = path.read_bytes()
            data = raw if raw.lstrip().startswith(b'<') else AXMLPrinter(raw).get_xml()
            if not data:
                raise ValueError('未生成 XML 内容')
            destination.write_bytes(data)
            results.append({'source': path.relative_to(root).as_posix(), 'export': destination.relative_to(root).as_posix(), 'status': '已导出'})
        except Exception as error:
            results.append({'source': path.relative_to(root).as_posix(), 'status': '保留原文件', 'error': str(error)[:300]})
    resource_table = archive_root / 'resources.arsc'
    if not resource_table.exists():
        return results
    parser = ARSCParser(resource_table.read_bytes())
    for package in parser.get_packages_names():
        locales = parser.get_locales(package)
        for locale in locales:
            suffix = re.sub(r'[^\w.-]+', '_', locale) or 'default'
            for kind in ('string', 'color', 'dimen', 'integer', 'bool', 'id'):
                try:
                    data = getattr(parser, f'get_{kind}_resources')(package, locale)
                    if data:
                        path = output / 'values' / safe_name(package) / suffix / f'{kind}.xml'
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(data)
                except Exception as error:
                    results.append({'resource_type': kind, 'locale': repr(locale), 'status': '未能导出资源表分组', 'error': str(error)[:300]})
        path = output / f'{safe_name(package)}_public.xml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(parser.get_public_resources(package))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    root = args.workspace.resolve()
    results = []
    for archive in read_json(root / 'package_summary.json')['archives']:
        try:
            results.extend(run(root, local_path(root, archive['raw_root']), archive['id']))
        except Exception as error:
            results.append({'archive_id': archive['id'], 'status': '解析失败，原文件保留', 'error': str(error)[:500]})
    write_json(root / 'analysis/android_resource_summary.json', results)
    print(f'已导出 {sum(item.get("status") == "已导出" for item in results)} 个原生 XML，资源表分组另存')
