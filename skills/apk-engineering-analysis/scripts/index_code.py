"""按程序集索引 IL2CPP 声明，输出选定业务程序集的结构，不把空方法体称为源码。"""
import argparse
import bisect
from collections import Counter
from pathlib import Path
import re
from common import write_json


def run(args):
    text = args.dump.read_text(encoding='utf-8')
    images = sorted((int(start), name) for name, start in re.findall(r'^// Image \d+: (.*?) - (\d+)$', text, re.M))
    if not images:
        raise ValueError('未识别程序集表，请确认输入是 Il2CppDumper 的 dump.cs')
    starts = [item[0] for item in images]
    # 类型声明前可能存在多行属性，不能假设 Namespace 后紧接 class。
    matches = list(re.finditer(r'^// Namespace: (.*?)\n([\s\S]*?) // TypeDefIndex: (\d+)\n', text, re.M))
    types, previous_offset, line_number = [], 0, 1
    for index, match in enumerate(matches):
        type_index = int(match.group(3))
        image_index = bisect.bisect_right(starts, type_index) - 1
        if image_index < 0:
            raise ValueError('类型索引早于首个程序集，不能可靠定位类型归属')
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        line_number += text.count('\n', previous_offset, match.start())
        previous_offset = match.start()
        types.append({'namespace': match.group(1), 'declaration': match.group(2).splitlines()[-1],
                      'type_index': type_index, 'assembly': images[image_index][1], 'line': line_number,
                      'body': text[match.start():end]})
    if not types:
        raise ValueError('程序集表存在但未识别任何类型，请检查 dump.cs 格式')
    counts = Counter(item['assembly'] for item in types)
    selected = [item for item in types if item['assembly'] in args.assembly]
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / 'types.json', [{k: v for k, v in item.items() if k != 'body'} for item in types])
    write_json(args.output / 'assemblies.json', [{'name': name, 'first_type_index': start, 'types': counts[name]} for start, name in images])
    write_json(args.output / 'gameplay/types_with_members.json', selected)
    (args.output / 'gameplay/declarations.cs').write_text('// 以下为恢复的声明和偏移，空方法体不是原始实现。\n' + '\n'.join(item['body'] for item in selected), encoding='utf-8')
    print(f'已索引 {len(types)} 个类型，选定程序集 {len(selected)} 个类型')
    if not selected:
        print('选定程序集没有匹配类型，请查看 assemblies.json 后使用 --assembly 指定实际业务程序集')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dump', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='建议使用工作区/code')
    parser.add_argument('--assembly', action='append', help='可多次指定；默认 Assembly-CSharp.dll')
    args = parser.parse_args()
    args.assembly = args.assembly or ['Assembly-CSharp.dll']
    run(args)
