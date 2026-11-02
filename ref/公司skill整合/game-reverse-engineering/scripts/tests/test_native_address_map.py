"""Synthetic offline tests for address provenance and malformed inputs."""
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "native_address_map.py"
spec = importlib.util.spec_from_file_location("native_address_map", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def elf(bits=64, endian="<", duplicate=False):
    data = bytearray(0x300)
    data[:16] = b"\x7fELF" + bytes([1 if bits == 32 else 2, 1 if endian == "<" else 2, 1]) + bytes(9)
    hfmt = "HHIIIIIHHHHHH" if bits == 32 else "HHIQQQIHHHHHH"
    phfmt = "IIIIIIII" if bits == 32 else "IIQQQQQQ"
    hsize = 52 if bits == 32 else 64
    phsize = struct.calcsize(endian + phfmt)
    struct.pack_into(endian + hfmt, data, 16, 3, 40 if bits == 32 else 183, 1,
                     0x4100, hsize, 0, 0, hsize, phsize, 2 if duplicate else 1, 0, 0, 0)
    for i in range(2 if duplicate else 1):
        vals = (1, 0x100, 0x4100 + i * 0x1000, 0, 0x40, 0x80, 5, 0x1000) if bits == 32 else (1, 5, 0x100, 0x4100 + i * 0x1000, 0, 0x40, 0x80, 0x1000)
        struct.pack_into(endian + phfmt, data, hsize + i * phsize, *vals)
    return bytes(data)


def pe(bits=64):
    data = bytearray(0x400)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    optsize = 0xE0 if bits == 32 else 0xF0
    struct.pack_into("<HHIIIHH", data, 0x84, 0x14C if bits == 32 else 0x8664, 1, 0, 0, 0, optsize, 0)
    opt = 0x98
    struct.pack_into("<H", data, opt, 0x10B if bits == 32 else 0x20B)
    struct.pack_into("<I" if bits == 32 else "<Q", data, opt + (28 if bits == 32 else 24), 0x400000 if bits == 32 else 0x140000000)
    struct.pack_into("<I", data, opt + 60, 0x200)
    pos = opt + optsize
    data[pos:pos + 8] = b".data\0\0\0"
    struct.pack_into("<IIII", data, pos + 8, 0x180, 0x1000, 0x100, 0x200)
    return bytes(data)


class AddressTests(unittest.TestCase):
    def test_elf_architecture_and_endian_matrix(self):
        for bits in (32, 64):
            for endian in ("<", ">"):
                with self.subTest(bits=bits, endian=endian):
                    info = mod.parse(elf(bits, endian))
                    self.assertEqual(info["bits"], bits)
                    self.assertEqual(mod.mappings(info, "file_offset", 0x120)[0]["static_va"], "0x4120")
                    self.assertEqual(mod.mappings(info, "static_va", 0x4120)[0]["file_offset"], "0x120")

    def test_bss_and_half_open_boundary(self):
        info = mod.parse(elf())
        row = mod.mappings(info, "static_va", 0x4140)[0]
        self.assertIsNone(row["file_offset"])
        self.assertFalse(row["file_backed"])
        self.assertEqual(mod.mappings(info, "static_va", 0x4180), [])
        self.assertEqual(mod.mappings(info, "file_offset", 0x140), [])

    def test_overlapping_file_ranges_are_not_silently_resolved(self):
        self.assertEqual(len(mod.mappings(mod.parse(elf(duplicate=True)), "file_offset", 0x120)), 2)

    def test_pe_32_and_64_rva_and_header(self):
        for bits, base in [(32, 0x400000), (64, 0x140000000)]:
            info = mod.parse(pe(bits))
            row = mod.mappings(info, "file_offset", 0x210)[0]
            self.assertEqual(row["static_va"], hex(base + 0x1010))
            self.assertEqual(row["rva"], "0x1010")
            self.assertEqual(mod.mappings(info, "static_va", base + 0x1010)[0]["file_offset"], "0x210")
            self.assertEqual(mod.mappings(info, "file_offset", 0x40)[0]["rva"], "0x40")
            self.assertIsNone(mod.mappings(info, "static_va", base + 0x1100)[0]["file_offset"])
            self.assertEqual(mod.mappings(info, "file_offset", 0x350), [])

    def test_truncated_or_unsupported_inputs(self):
        for data in [b"", b"MZ", b"\x7fELF", elf()[:80], pe()[:300], b"not an executable"]:
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                mod.parse(data)

    def test_invalid_segment_or_table(self):
        for field_offset, value in [(64 + 32, 0x400), (64 + 40, 0x20), (56, 0xFFFF)]:
            data = bytearray(elf())
            struct.pack_into("<H" if field_offset == 56 else "<Q", data, field_offset, value)
            with self.assertRaises(ValueError):
                mod.parse(data)

    def test_negative_address(self):
        with self.assertRaises(ValueError):
            mod.mappings(mod.parse(elf()), "static_va", -1)

    def test_elf_address_width_overflow(self):
        data = bytearray(elf(32))
        struct.pack_into("<I", data, 52 + 8, 0xFFFFFFF0)
        struct.pack_into("<I", data, 52 + 28, 1)
        with self.assertRaisesRegex(ValueError, "address width"):
            mod.parse(data)

    def test_elf_invalid_alignment(self):
        for offset, value in [(64 + 16, 0x4101), (64 + 48, 3)]:
            data = bytearray(elf())
            struct.pack_into("<Q", data, offset, value)
            with self.assertRaisesRegex(ValueError, "alignment"):
                mod.parse(data)

    def test_cli_provenance_read_only_and_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.so"
            data = elf()
            path.write_bytes(data)
            done = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path), "--file-offset", "0x120"], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            output = json.loads(done.stdout)
            self.assertEqual(output["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(output["status"], "mapped")
            self.assertEqual(path.read_bytes(), data)
            done = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path), "--file-offset", "-1"], capture_output=True, text=True)
            self.assertEqual(done.returncode, 1)
            self.assertIn("error", json.loads(done.stderr))


if __name__ == "__main__":
    unittest.main()
