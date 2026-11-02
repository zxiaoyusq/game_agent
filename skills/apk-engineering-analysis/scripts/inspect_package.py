"""接收 APK、XAPK/APKS 或一个产品的分包目录，保存原文件树并识别工程线索。"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import zipfile
from common import read_json, safe_name, sha256, write_json


def extract_archive(source, destination, budget):
    """拒绝越界、符号链接和重复路径；每个 APK 使用独立目录，绝不合并覆盖。"""
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        budget[0] -= sum(item.file_size for item in archive.infolist())
        if budget[0] < 0:
            raise ValueError('解压数据超过设定上限，请检查输入后调整 --max-unpacked-gib')
        names = set()
        for item in archive.infolist():
            name = item.filename.replace('\\', '/')
            parts = PurePosixPath(name)
            if not parts.parts or parts.is_absolute() or '..' in parts.parts or ':' in parts.parts[0]:
                raise ValueError(f'压缩包中存在越界路径：{name}')
            if stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError(f'压缩包中存在符号链接：{name}')
            target = (destination / name).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError(f'压缩包中存在越界路径：{name}')
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if target in names or target.exists():
                raise ValueError(f'压缩包中存在重复文件：{name}')
            names.add(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(item) as incoming, target.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing, length=1024 * 1024)


def android_info(apk, output):
    """清单读取失败时仍保留包与文件清单，不猜测包名或把证书提取当成签名验证。"""
    try:
        from loguru import logger
        logger.disable('androguard')
        from androguard.core.apk import APK
        android = APK(str(apk))
        manifest = android.get_android_manifest_xml()
        if manifest is None:
            raise ValueError('未能解析 AndroidManifest')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(android.get_android_manifest_axml().get_xml())
        info = {'package': android.get_package(), 'version_name': android.get_androidversion_name(),
                'version_code': android.get_androidversion_code(), 'split': manifest.get('split', ''),
                'main_activity': android.get_main_activity(), 'min_sdk': android.get_min_sdk_version(),
                'target_sdk': android.get_target_sdk_version(), 'permissions': android.get_permissions(),
                'activities': android.get_activities(), 'services': android.get_services(),
                'providers': android.get_providers(), 'receivers': android.get_receivers(),
                'signature_verification': '未验证签名完整性或官方签名一致性'}
        # 证书解析失败不能抹掉已成功读取的 Manifest。
        try:
            info['certificate_sha256'] = [cert.sha256_fingerprint.replace(' ', '') for cert in android.get_certificates()]
        except Exception as error:
            info['certificate_parse_error'] = str(error)[:300]
        return info
    except Exception as error:
        return {'parse_error': str(error)[:500]}


def inspect(args):
    """一个输出工作区对应一个包名和版本，多产品输入由调用方分别执行。"""
    output = args.output.expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('输出目录非空，请选择新的工作区，避免混入旧产物')
    output.mkdir(parents=True, exist_ok=True)
    inputs = []
    for source in args.inputs:
        source = source.expanduser().resolve()
        if source.is_dir():
            inputs.extend(sorted(source.rglob('*.apk')))
        elif source.is_file():
            inputs.append(source)
        else:
            raise FileNotFoundError(f'输入不存在：{source}')
    inputs = list(dict.fromkeys(inputs))
    if not inputs:
        raise ValueError('没有找到输入 APK')
    for source in inputs:
        if source.is_relative_to(output):
            raise ValueError('输入必须位于输出工作区之外')
    budget = [int(args.max_unpacked_gib * 1024 ** 3)]
    sources = []
    apk_files = []
    for index, source in enumerate(inputs):
        sources.append({'path': str(source), 'bytes': source.stat().st_size, 'sha256': sha256(source),
                        'source_label': args.source_label, 'source_url': args.source_url})
        if source.suffix.lower() == '.apk':
            apk_files.append(source)
        else:
            container = output / 'containers' / f'{index:03d}_{safe_name(source.stem)}'
            extract_archive(source, container, budget)
            apk_files.extend(sorted(container.rglob('*.apk')))
    if not apk_files:
        raise ValueError('容器中没有 APK；原始容器内容已保留，请检查格式')
    inventory, archives, libraries = [], [], []
    for index, apk in enumerate(apk_files):
        archive_id = f'{index:03d}_{safe_name(apk.stem)}'
        destination = output / 'raw' / archive_id
        extract_archive(apk, destination, budget)
        android = android_info(apk, output / 'manifests' / f'{archive_id}.xml')
        archives.append({'id': archive_id, 'input_path': str(apk), 'sha256': sha256(apk),
                         'bytes': apk.stat().st_size, 'raw_root': destination.relative_to(output).as_posix(), 'android': android})
        for path in sorted(destination.rglob('*')):
            if not path.is_file():
                continue
            relative = path.relative_to(destination).as_posix()
            inventory.append({'archive_id': archive_id, 'path': relative,
                              'file': path.relative_to(output).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha256(path)})
            if path.suffix == '.so':
                entry = {'file': path.relative_to(output).as_posix(), 'name': path.name, 'bytes': path.stat().st_size}
                try:
                    from elftools.elf.elffile import ELFFile
                    with path.open('rb') as stream:
                        elf = ELFFile(stream)
                        entry.update(architecture=elf.header['e_machine'], elf_class=elf.elfclass)
                except Exception as error:
                    entry['parse_error'] = str(error)[:200]
                libraries.append(entry)
    names = [item['path'].lower() for item in inventory]
    def matched(predicate):
        return [item['file'] for item in inventory if predicate(item['path'].lower())]
    engines = []
    if any('libunity.so' in name or 'assets/bin/data/' in name for name in names): engines.append('Unity')
    if any('libue4.so' in name or 'libunreal.so' in name or name.endswith('.pak') for name in names): engines.append('Unreal 线索')
    if any('libcocos' in name or name.endswith('.jsc') for name in names): engines.append('Cocos/JavaScript 线索')
    if any('libflutter.so' in name or 'flutter_assets/' in name for name in names): engines.append('Flutter 线索')
    metadata = []
    for relative in matched(lambda name: name.endswith('global-metadata.dat')):
        with (output / relative).open('rb') as stream:
            header = stream.read(8)
        magic, version = struct.unpack('<II', header) if len(header) == 8 else (None, None)
        metadata.append({'file': relative, 'magic': hex(magic) if magic is not None else None,
                         'standard_magic': magic == 0xfab11baf, 'metadata_version': version})
    package_versions = sorted({(item['android']['package'], str(item['android'].get('version_code') or '')) for item in archives if item['android'].get('package')})
    summary = {'created_at': datetime.now(timezone.utc).isoformat(), 'sources': sources, 'archives': archives,
               'package_versions': package_versions, 'engines': engines or ['未识别：继续检查 Java、原生代码或其他资源格式'],
               'libraries': libraries, 'metadata': metadata,
               'dex_files': matched(lambda name: name.endswith('.dex')),
               'file_count': len(inventory), 'uncompressed_bytes': sum(item['bytes'] for item in inventory),
               'signature_note': '记录证书不等于已验证 APK 签名，也未与 Google Play 官方包比对'}
    write_json(output / 'package_summary.json', summary)
    write_json(output / 'file_inventory.json', inventory)
    if len(package_versions) > 1:
        raise ValueError('发现不同包名或版本，请按产品与版本拆分工作区；已保存输入证据')
    print(f'已保留 {len(archives)} 个 APK、{len(inventory)} 个文件；引擎线索：{", ".join(summary["engines"])}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='+', type=Path, help='APK、XAPK/APKS 或分包目录')
    parser.add_argument('--output', required=True, type=Path, help='新的产品工作区')
    parser.add_argument('--source-label', default='用户提供的本地文件，分发来源未验证')
    parser.add_argument('--source-url', default='')
    parser.add_argument('--max-unpacked-gib', type=float, default=20)
    inspect(parser.parse_args())
