#!/usr/bin/env python3
"""离线只读复核；本轮未执行。用法：python3 native-recheck.py chunks.zip evidence.zip > result.json"""
import hashlib
import json
import struct
import sys
import zipfile

EXPECTED = '4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4'
ARCHIVES = ['0d79feb7b5157fcabda15fb105581acd9fceddad0a9c331cb61cec047863b7aa', 'ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1']
CHECKS = {0x18b09f8:'f30308aa', 0x18b0a64:'e1c8ff90', 0x18b0f90:'601200fd', 0x18b0fa4:'601600fd', 0x18b3374:'98f5ff97', 0x18b339c:'8ef5ff97', 0x1aa30b0:'ea000094', 0x1aa36fc:'e9024092', 0x1aa3708:'61bcfff0', 0x1aa3744:'498c3194', 0x18bc618:'280440f9', 0x18bc62c:'40019f9a', 0x18bc818:'280440f9', 0x18bc8bc:'280440f9', 0x18bca50:'280440f9', 0x18bcccc:'280440f9'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    require(len(sys.argv) == 3, '需要分块ZIP和证据ZIP两个路径')
    for path, expected in zip(sys.argv[1:], ARCHIVES):
        with open(path, 'rb') as source:
            require(hashlib.file_digest(source, 'sha256').hexdigest() == expected, '参考包哈希不符：' + path)
    parts = []
    records = []
    with zipfile.ZipFile(sys.argv[1]) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        require(manifest['original_sha256'] == EXPECTED, 'manifest完整哈希不符')
        require([p['name'] for p in manifest['parts']] == ['parts/arm64.part%03d' % i for i in range(6)], '分块顺序不符')
        for item in manifest['parts']:
            block = archive.read(item['name'])
            digest = sha(block)
            require(len(block) == item['bytes'] and digest == item['sha256'], '分块校验失败：' + item['name'])
            records.append({'path':item['name'], 'bytes':len(block), 'sha256':digest})
            parts.append(block)
    data = b''.join(parts)
    require(len(data) == 48998992, '完整长度不符')
    require(sha(data) == EXPECTED, '完整库哈希不符')
    require(data[:6] == b'\x7fELF\x02\x01', '要求小端ELF64')
    header = struct.unpack_from('<HHIQQQIHHHHHH', data, 16)
    kind, machine, _, _, phoff, shoff, _, _, phsize, phnum, shsize, shnum, _ = header
    require(kind == 3 and machine == 183, '要求AArch64 ET_DYN')
    require(phsize >= 56 and shsize >= 64, 'ELF表项尺寸异常')
    loads = []
    for i in range(phnum):
        p = struct.unpack_from('<IIQQQQQQ', data, phoff+i*phsize)
        if p[0] == 1:
            loads.append({'offset':p[2], 'va':p[3], 'filesz':p[5], 'memsz':p[6], 'flags':p[1]})
    def read_va(va, count):
        for p in loads:
            if p['va'] <= va and va+count <= p['va']+p['filesz']:
                offset = p['offset']+va-p['va']
                require(offset+count <= len(data), 'PT_LOAD越界')
                return data[offset:offset+count]
        raise ValueError('地址不在文件支持的PT_LOAD内：' + hex(va))
    instructions = []
    for va, expected in CHECKS.items():
        actual = read_va(va, 4).hex()
        require(actual == expected, '指令字节不符：' + hex(va))
        instructions.append({'va':hex(va), 'bytes':actual, 'matched':True})
    slots = [0x27a2660,0x27a26e0,0x27a2760,0x27a27e0,0x27a2860]
    names = [0x12eb4d8,0x12eb586,0x12eb63b,0x12eb6ed,0x12eb795]
    relocations = []
    for i in range(shnum):
        s = struct.unpack_from('<IIQQQQIIQQ', data, shoff+i*shsize)
        if s[1] != 4:
            continue
        offset, size, entry = s[4], s[5], s[9]
        require(entry >= 24 and size % entry == 0 and offset+size <= len(data), 'RELA表异常')
        for pos in range(offset, offset+size, entry):
            location, info, addend = struct.unpack_from('<QQq', data, pos)
            if any(abs(location-slot) <= 64 for slot in slots) or addend in names or any(abs(addend-slot) <= 24 for slot in slots):
                relocations.append({'location':hex(location), 'type':info & 0xffffffff, 'symbol_index':info >> 32, 'addend':hex(addend)})
    symbols_member = 'analysis/native_elf_符号.json'
    with zipfile.ZipFile(sys.argv[2]) as archive:
        raw = archive.read(symbols_member)
        require(sha(raw) == 'd4d1f06dc49bb5878b8119779ef6a937d8e0e30a795a1b4955712c431f8011cc', '符号证据哈希不符')
        symbols = json.loads(raw)
    matches = [s for s in symbols['symbols'] if 'MatchShotSolver' in s.get('name','')]
    print(json.dumps({'parts':records, 'library_bytes':len(data), 'library_sha256':sha(data), 'pt_load':loads, 'instruction_checks':instructions, 'candidate_relocations':relocations, 'solver_symbol_matches':matches, 'limits':['未执行竞品','未解码新函数','未验证FDE和vtable语义','符号表检索来自参考JSON']}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('复核失败：' + str(error), file=sys.stderr)
        sys.exit(1)
