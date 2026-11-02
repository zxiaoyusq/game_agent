"""按明确的方法名前缀导出原生指令，架构来自 ELF，地址边界明确标注为估算。"""
import argparse
import bisect
from pathlib import Path
import re
from common import read_json, safe_name, write_json
import capstone
from elftools.elf.elffile import ELFFile


def run(args):
    if args.max_bytes <= 0:
        raise ValueError('方法最大读取字节数必须大于零')
    methods = [item for item in read_json(args.script)['ScriptMethod'] if item['Address'] > 0]
    with args.library.open('rb') as stream:
        elf = ELFFile(stream)
        architecture = elf.header['e_machine']
        segments = [dict(segment.header) for segment in elf.iter_segments() if segment['p_type'] == 'PT_LOAD']
    if architecture not in ('EM_AARCH64', 'EM_ARM', 'EM_X86_64', 'EM_386'):
        raise ValueError(f'当前脚本不支持该 ELF 架构：{architecture}')
    # ARM32 的函数指针最低位通常标记 Thumb；允许按实测指令覆盖，不能凭产品名猜 ABI。
    canonical = lambda address: address & ~1 if architecture == 'EM_ARM' else address
    names = {}
    for item in methods:
        names.setdefault(canonical(item['Address']), []).append(item['Name'])
    addresses = sorted(names)
    data = args.library.read_bytes()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    records = []
    selected = [item for item in methods if any(item['Name'].startswith(prefix) for prefix in args.prefix)]
    if not selected:
        raise ValueError('没有匹配方法；先从 script.json 确认完整命名空间和方法前缀')
    for number, method in enumerate(selected):
        original_address = method['Address']
        address = canonical(original_address)
        if architecture == 'EM_ARM':
            thumb = args.arm_mode == 'thumb' or (args.arm_mode == 'auto' and original_address & 1)
            engine = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB if thumb else capstone.CS_MODE_ARM)
        elif architecture == 'EM_AARCH64':
            engine = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
        else:
            engine = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64 if architecture == 'EM_X86_64' else capstone.CS_MODE_32)
        segment = next((item for item in segments if item['p_vaddr'] <= address < item['p_vaddr'] + item['p_filesz']), None)
        if segment is None:
            records.append({**method, 'error': '地址不在 ELF 文件加载段内'})
            continue
        next_index = bisect.bisect_right(addresses, address)
        next_address = addresses[next_index] if next_index < len(addresses) else address + args.max_bytes
        offset = segment['p_offset'] + address - segment['p_vaddr']
        size = min(next_address - address, args.max_bytes, segment['p_offset'] + segment['p_filesz'] - offset)
        lines = [f'; 方法：{method["Name"]}', f'; 声明：{method.get("Signature", "")}',
                 f'; 虚拟地址：0x{address:x}；文件偏移：0x{offset:x}；架构：{architecture}',
                 '; 边界取下一已知方法，可能含填充或辅助代码；不是原始源码。', '']
        calls = set()
        for instruction in engine.disasm(data[offset:offset + size], address):
            annotation = ''
            if instruction.mnemonic in ('bl', 'blx', 'b', 'b.w', 'call', 'jmp'):
                match = re.fullmatch(r'#?(0x[0-9a-f]+)', instruction.op_str)
                if match and canonical(int(match.group(1), 16)) in names:
                    targets = names[canonical(int(match.group(1), 16))][:4]
                    calls.update(targets)
                    annotation = ' ; 已知目标：' + ' | '.join(targets)
            lines.append(f'0x{instruction.address:x}: {instruction.mnemonic:<9} {instruction.op_str}{annotation}')
        filename = f'{address:08x}_{number:05d}_{safe_name(method["Name"])}.asm'
        (output / filename).write_text('\n'.join(lines), encoding='utf-8')
        records.append({**method, 'architecture': architecture, 'file_offset': offset, 'estimated_bytes': size,
                        'instruction_count': len(lines) - 5, 'direct_calls': sorted(calls), 'assembly_file': filename})
    write_json(output / 'index.json', records)
    print(f'已处理 {len(records)} 个方法，成功导出 {sum("assembly_file" in item for item in records)} 个指令文件')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', required=True, type=Path)
    parser.add_argument('--script', required=True, type=Path, help='Il2CppDumper 的 script.json')
    parser.add_argument('--prefix', required=True, action='append', help='完整方法名前缀，可多次指定')
    parser.add_argument('--output', required=True, type=Path, help='建议使用工作区/code/native_core')
    parser.add_argument('--arm-mode', choices=['auto', 'arm', 'thumb'], default='auto')
    parser.add_argument('--max-bytes', type=int, default=32768)
    run(parser.parse_args())
