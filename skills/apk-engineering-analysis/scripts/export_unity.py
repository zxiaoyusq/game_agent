"""批量导出 Unity 美术、音频、文本及序列化配置，并逐对象记录成功和失败。"""

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import argparse
import base64
from common import read_json, write_json
from unity_support import load_environment, fixed_header

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator



def safe_name(value):
    """保留便于识别的资源名，清除路径分隔符，避免导出越界。"""
    return re.sub(r'[^\w.\-一-龥]+', '_', str(value))[:90] or '未命名'


def encode_json(value):
    """少量非 JSON 值使用可追踪的文本表示，原始对象字节另行保留。"""
    if isinstance(value, bytes):
        return {'encoding': 'base64', 'data': base64.b64encode(value).decode('ascii')}
    return str(value)


def main(args):
    """遍历整个产品的可读 Unity 对象，脚本字段树按匹配程序集补齐。"""
    output = args.workspace.expanduser().resolve()
    environment, objects, files, loaded = load_environment(output, args.asset_path)
    versions = sorted({str(asset.unity_version) for asset in files.values() if str(asset.unity_version) != '0.0.0'})
    # 资源包可能由旧版编辑器构建，主程序版本优先取 globalgamemanagers。
    player_versions = sorted({str(asset.unity_version) for name, asset in files.items()
                              if Path(name).name == 'globalgamemanagers' and str(asset.unity_version) != '0.0.0'})
    version = args.unity_version or (player_versions[0] if len(player_versions) == 1 else (versions[0] if len(versions) == 1 else ''))
    dll_folder = args.dummy_dlls or output / 'code/il2cpp/DummyDll'
    print(f'已加载 {len(objects)} 个对象，Unity 版本候选：{versions}', flush=True)
    corrections = []
    try:
        if not version or not dll_folder.is_dir():
            raise ValueError('缺少明确的主程序 Unity 版本或匹配的 DummyDll；已有类型树仍可继续读取')
        generator = TypeTreeGenerator(re.sub(r'c\d+$', '', version))
        for dll in dll_folder.glob('*.dll'):
            generator.load_dll(dll.read_bytes())
        environment.typetree_generator = generator
        print('脚本字段生成器已就绪', flush=True)
    except Exception as error:
        print(f'字段生成器不可用，读取已有类型树或保留原始字节：{error}', flush=True)

    objects = sorted(objects, key=lambda item: (item.assets_file.name, item.path_id))
    records = []
    counts = Counter()
    failures = Counter()
    started = time.time()
    for number, obj in enumerate(objects):
        kind = obj.type.name
        counts[kind] += 1
        source = obj.assets_file.name
        source_key = hashlib.sha1(source.encode()).hexdigest()[:10]
        record = {'source': source, 'path_id': obj.path_id, 'type': kind,
                  'byte_offset': obj.byte_start, 'byte_size': obj.byte_size,
                  'container': getattr(obj, 'container', None), 'exports': []}
        stem = f'{source_key}__{obj.path_id}'
        try:
            # MonoBehaviour 的名称探测会触发完整字段解析，先跳过，以便失败时仍保留脚本身份。
            name = '' if kind == 'MonoBehaviour' else (obj.peek_name() or '')
            if name:
                record['name'] = name
                stem += '__' + safe_name(name)

            def save_bytes(category, suffix, content):
                destination = output / 'exports' / category / (stem + suffix)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                record['exports'].append(str(destination.relative_to(output)))
                return destination

            def save_json(category, value):
                return save_bytes(category, '.json', json.dumps(value, ensure_ascii=False, indent=2, default=encode_json).encode('utf-8', errors='backslashreplace'))

            if kind in ('Texture2D', 'Sprite'):
                data = obj.parse_as_object()
                record['name'] = data.m_Name
                image = data.image
                record['width'], record['height'] = image.size
                if kind == 'Texture2D':
                    record['texture_format'] = int(data.m_TextureFormat)
                destination = output / 'exports' / kind / (stem + '.png')
                destination.parent.mkdir(parents=True, exist_ok=True)
                image.save(destination)
                record['exports'].append(str(destination.relative_to(output)))
                # 图集矩形、旋转、原点、像素密度和贴图引用共同保存，便于研究切图方案。
                if kind == 'Sprite':
                    save_json('sprite_config', obj.parse_as_dict())
            elif kind == 'AudioClip':
                data = obj.parse_as_object()
                record.update({'name': data.m_Name, 'channels': data.m_Channels, 'frequency': data.m_Frequency, 'duration_seconds': data.m_Length, 'compression_format': int(data.m_CompressionFormat)})
                for sample_name, content in data.samples.items():
                    extension = Path(sample_name).suffix or '.wav'
                    save_bytes('AudioClip', '__' + safe_name(Path(sample_name).stem) + extension, content)
            elif kind == 'TextAsset':
                data = obj.parse_as_object()
                content = data.m_Script.encode('utf-8', errors='surrogateescape')
                record['name'] = data.m_Name
                suffix = '.bytes'
                try:
                    text = content.decode('utf-8')
                    suffix = '.txt'
                    try:
                        json.loads(text)
                        suffix = '.json'
                    except (ValueError, TypeError):
                        pass
                except UnicodeError:
                    pass
                save_bytes('TextAsset', suffix, content)
            elif kind == 'Font':
                data = obj.parse_as_object()
                if data.m_FontData:
                    content = bytes(data.m_FontData)
                    save_bytes('Font', '.otf' if content[:4] == b'OTTO' else '.ttf', content)
                else:
                    record['note'] = '无内嵌字体字节，原对象与字形配置保留'
                    save_json('Font', obj.parse_as_dict())
            elif kind == 'Mesh':
                save_bytes('Mesh', '.obj', obj.parse_as_object().export().encode('utf-8'))
            elif kind == 'Shader':
                save_bytes('Shader', '.txt', obj.parse_as_object().export().encode('utf-8'))
            elif kind == 'MonoBehaviour':
                # 先读取固定头和脚本引用，字段树缺失时仍能识别该配置所属功能模块。
                head = obj.parse_monobehaviour_head()
                record['name'] = head.m_Name
                if head.m_Script.m_PathID:
                    try:
                        script = head.m_Script.deref_parse_as_object()
                        record.update({'script_type': f'{script.m_Namespace}.{script.m_ClassName}'.strip('.'), 'script_assembly': script.m_AssemblyName})
                    except Exception as error:
                        record['script_identity_error'] = str(error)[:300]
                data = obj.parse_as_dict()
                header = fixed_header(head)
                diff = {key: {'before': data.get(key), 'after': value} for key, value in header.items() if data.get(key) != value}
                if diff:
                    corrections.append({'source': source, 'path_id': obj.path_id, 'changes': diff})
                data.update(header)
                save_json('MonoBehaviour', data)
            else:
                # 其余对象尽量完整转为 JSON，包括节点、材质、动画、图集和粒子系统。
                save_json(kind, obj.parse_as_dict())
            record['status'] = '已导出' if record['exports'] else '无可独立导出的数据'
        except Exception as error:
            failures[kind] += 1
            record['status'] = '保留原始对象字节'
            record['error'] = str(error)[:800]
            try:
                save_bytes('unparsed/' + kind, '.bin', obj.get_raw_data())
            except Exception as raw_error:
                record['raw_export_error'] = str(raw_error)[:300]
        records.append(record)
        if number % 500 == 0:
            print(f'已处理 {number + 1}/{len(objects)} 个对象', flush=True)
    write_json(output / 'unity_objects.json', records)
    summary = {'unity_version': version, 'version_candidates': versions, 'player_version_candidates': player_versions, 'unitypy_version': UnityPy.__version__,
               'objects': len(records), 'type_counts': dict(counts), 'decode_failure_counts': dict(failures),
               'export_files': sum(len(item['exports']) for item in records),
               'loaded_inputs': loaded, 'elapsed_seconds': round(time.time() - started, 1)}
    write_json(output / 'unity_summary.json', summary)
    write_json(output / 'analysis/header_corrections.json', corrections)
    write_json(output / 'analysis/decode_failures.json', [item for item in records if 'error' in item])
    write_json(output / 'analysis/serialized_files.json', {name: [str(ext.path) for ext in asset.externals] for name, asset in files.items()})
    print(json.dumps({key: value for key, value in summary.items() if key != 'loaded_inputs'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--dummy-dlls', type=Path, help='与当前版本匹配的占位程序集目录')
    parser.add_argument('--unity-version', help='多版本候选时按包内证据明确指定')
    parser.add_argument('--asset-path', type=Path, action='append', help='额外已解包资产目录或资源文件，可多次指定')
    main(parser.parse_args())
