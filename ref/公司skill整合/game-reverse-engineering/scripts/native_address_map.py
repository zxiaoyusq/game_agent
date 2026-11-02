"""Read-only ELF/PE static address mapping; never executes the input.

Usage: python native_address_map.py target.so --file-offset 0x1200
       python native_address_map.py target.dll --static-va 0x140001200
Output includes SHA-256 and all candidate mappings; runtime load bias is not guessed.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path


def unpack(data, fmt, offset):
    size = struct.calcsize(fmt)
    if offset < 0 or offset + size > len(data):
        raise ValueError("truncated structure")
    return struct.unpack_from(fmt, data, offset)


def region(name, offset, va, raw_size, mem_size, data_len, bits):
    if va + mem_size > (1 << bits):
        raise ValueError("region exceeds address width: " + name)
    if raw_size and offset + raw_size > data_len:
        raise ValueError("file-backed region exceeds input: " + name)
    return dict(name=name, file_offset=offset, static_va=va,
                file_size=raw_size, memory_size=mem_size)


def parse(data):
    if data[:4] == b"\x7fELF":
        if len(data) < 16 or data[4] not in (1, 2) or data[5] not in (1, 2):
            raise ValueError("invalid ELF identification")
        bits = 32 if data[4] == 1 else 64
        endian = "<" if data[5] == 1 else ">"
        fmt = endian + ("HHIIIIIHHHHHH" if bits == 32 else "HHIQQQIHHHHHH")
        h = unpack(data, fmt, 16)
        if data[6] != 1 or h[2] != 1:
            raise ValueError("unsupported ELF version")
        phoff, entsize, count = h[4], h[8], h[9]
        phfmt = endian + ("IIIIIIII" if bits == 32 else "IIQQQQQQ")
        if count == 0xFFFF:
            raise ValueError("extended ELF program-header count unsupported")
        if count and (entsize < struct.calcsize(phfmt) or phoff + entsize * count > len(data)):
            raise ValueError("invalid ELF program-header table")
        regions = []
        for i in range(count):
            ph = unpack(data, phfmt, phoff + i * entsize)
            if ph[0] != 1:
                continue
            off, va, raw, mem = (ph[1], ph[2], ph[4], ph[5]) if bits == 32 else (ph[2], ph[3], ph[5], ph[6])
            if raw > mem:
                raise ValueError("ELF filesz exceeds memsz")
            align = ph[7]
            if align > 1 and ((align & (align - 1)) or off % align != va % align):
                raise ValueError("invalid ELF segment alignment")
            regions.append(region("PT_LOAD[{}]".format(i), off, va, raw, mem, len(data), bits))
        return dict(format="ELF", bits=bits, endian="little" if endian == "<" else "big",
                    machine=h[1], static_address_kind="link_va", regions=regions)
    if data[:2] == b"MZ":
        pe = unpack(data, "<I", 0x3C)[0]
        if data[pe:pe + 4] != b"PE\0\0":
            raise ValueError("invalid PE signature")
        machine, count, _, _, _, optsize, _ = unpack(data, "<HHIIIHH", pe + 4)
        opt = pe + 24
        if opt + optsize > len(data):
            raise ValueError("truncated PE optional header")
        magic = unpack(data, "<H", opt)[0]
        if magic not in (0x10B, 0x20B) or optsize < (96 if magic == 0x10B else 112):
            raise ValueError("unsupported PE optional header")
        bits = 32 if magic == 0x10B else 64
        base = unpack(data, "<I" if bits == 32 else "<Q", opt + (28 if bits == 32 else 24))[0]
        header_size = unpack(data, "<I", opt + 60)[0]
        section_table = opt + optsize
        if section_table + count * 40 > len(data) or header_size < section_table + count * 40:
            raise ValueError("invalid PE section table/headers")
        regions = [region("headers", 0, base, header_size, header_size, len(data), bits)]
        for i in range(count):
            pos = section_table + i * 40
            name = data[pos:pos + 8].split(b"\0", 1)[0].decode("ascii", errors="backslashreplace")
            mem, rva, raw, off = unpack(data, "<IIII", pos + 8)
            # Raw section alignment padding is not claimed as mapped virtual data.
            backed = min(raw, mem) if mem else raw
            if raw and off + raw > len(data):
                raise ValueError("PE raw section exceeds input")
            if rva + (mem or raw) > (1 << 32):
                raise ValueError("PE region exceeds RVA width")
            regions.append(region(name, off, base + rva, backed, mem or raw, len(data), bits))
        return dict(format="PE", bits=bits, endian="little", machine=machine,
                    image_base=base, static_address_kind="preferred_va", regions=regions)
    raise ValueError("unsupported input (expected ELF or PE)")


def mappings(info, kind, value):
    if value < 0:
        raise ValueError("address must be nonnegative")
    found = []
    for r in info["regions"]:
        start = r["file_offset"] if kind == "file_offset" else r["static_va"]
        span = r["file_size"] if kind == "file_offset" else r["memory_size"]
        delta = value - start
        if not 0 <= delta < span:
            continue
        va = r["static_va"] + delta
        row = dict(region=r["name"], static_va=hex(va),
                   file_offset=hex(r["file_offset"] + delta) if delta < r["file_size"] else None,
                   file_backed=delta < r["file_size"])
        if info["format"] == "PE":
            row["rva"] = hex(va - info["image_base"])
        found.append(row)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    args = ap.add_mutually_exclusive_group()
    args.add_argument("--file-offset", type=lambda s: int(s, 0))
    args.add_argument("--static-va", type=lambda s: int(s, 0))
    opts = ap.parse_args()
    try:
        data = opts.input.read_bytes()
        info = parse(data)
        result = dict(path=str(opts.input.resolve()), sha256=hashlib.sha256(data).hexdigest(),
                      size=len(data), **info)
        if opts.file_offset is not None or opts.static_va is not None:
            kind = "file_offset" if opts.file_offset is not None else "static_va"
            value = opts.file_offset if opts.file_offset is not None else opts.static_va
            result["query"] = dict(kind=kind, value=hex(value))
            result["matches"] = mappings(info, kind, value)
            result["status"] = "ambiguous" if len(result["matches"]) > 1 else "mapped" if result["matches"] else "unmapped"
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, struct.error) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
