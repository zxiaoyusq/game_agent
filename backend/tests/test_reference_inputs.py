"""远程参考输入回归：流式大小边界、ZIP校验、客户端隔离和持久重试。"""

import asyncio
import hashlib
import io
import json
import stat
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app.services.workflow import reference_inputs


class ReferenceInputTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "ref").mkdir()

    async def upload(self, name, content, client="mac-one", request_id="upload-001"):
        async def chunks():
            for offset in range(0, len(content), 17):
                yield content[offset:offset + 17]
        return await reference_inputs.upload_reference(self.root, client, name, request_id, chunks())

    def archive(self, files):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files:
                archive.writestr(name, content)
        return stream.getvalue()

    def uploaded_files(self):
        return list((self.root / "ref" / reference_inputs.UPLOAD_DIRECTORY).rglob("*"))

    async def test_text_upload_is_readable_reference_and_retries_persist_without_overwrite(self):
        content = "# 棋盘说明\n使用红绿黄蓝四营地。".encode()
        first = await self.upload("需求.md", content)
        self.assertEqual(first["bytes"], len(content))
        self.assertEqual(first["sha256"], hashlib.sha256(content).hexdigest())
        path = self.root / "ref" / first["reference_path"]
        self.assertEqual(path.read_bytes(), content)
        modified = path.stat().st_mtime_ns
        second = await self.upload("需求.md", content)
        self.assertEqual(first, second)
        self.assertEqual(path.stat().st_mtime_ns, modified)
        self.assertEqual(reference_inputs.validate_references(self.root, "mac-one", ["ref/" + first["reference_path"]]),
                         [first["reference_path"]])
        with self.assertRaisesRegex(ValueError, "不同文件内容"):
            await self.upload("需求.md", "改动后的内容".encode())
        with self.assertRaisesRegex(ValueError, "不同文件内容"):
            await self.upload("另一份.md", content)
        self.assertEqual(path.read_bytes(), content)
        duplicate = await self.upload("需求.md", content, request_id="upload-002")
        self.assertEqual(duplicate["reference_path"], first["reference_path"])
        self.assertEqual(len([p for p in self.uploaded_files() if p.is_file()]), 1)

    async def test_client_namespaces_and_parent_directories_do_not_leak_uploads(self):
        first = await self.upload("private.md", "第一位用户的资料".encode())
        second = await self.upload("private.md", "第二位用户的资料".encode(), client="mac-two")
        for value in [first["reference_path"], "mcp-inputs", "ref/mcp-inputs/", "mcp-inputs/mac-one"]:
            with self.subTest(path=value), self.assertRaises(PermissionError):
                reference_inputs.validate_references(self.root, "mac-two", [value])
        visible = reference_inputs.list_references(self.root, "mac-two")
        paths = [item["reference_path"] for item in visible["items"]]
        self.assertEqual(paths, [second["reference_path"]])
        self.assertNotIn("mac-one", json.dumps(visible))

    def test_company_case_documents_are_discoverable_by_remote_agents(self):
        """远程目录与网页采用同一案例来源，找到的单篇路径可以直接通过引用校验。"""
        case = self.root / "ref/公司skill整合/OneConnectRe"
        case.mkdir(parents=True)
        (case / "开发说明.md").write_text("# 案例说明\n保留原码验证，不冒充宿主验收。", encoding="utf-8")
        (case / "game.js").write_text("throw new Error('不执行来源脚本')")
        result = reference_inputs.list_references(self.root, "mac-one", query="OneConnectRe")
        self.assertEqual(result["total"], 2)
        paths = [item["reference_path"] for item in result["items"]]
        self.assertEqual(reference_inputs.validate_references(self.root, "mac-one", paths), paths)
        self.assertIn("公司skill整合/OneConnectRe/开发说明.md", paths)
        self.assertFalse(any(path.endswith(".js") for path in paths))

    async def test_zip_is_validated_without_extracting_or_running_its_code(self):
        content = self.archive([("game/config.json", '{"board":15}'), ("game/main.js", "throw new Error('不得执行');")])
        result = await self.upload("reference.zip", content)
        self.assertEqual(result["validation"]["kind"], "zip")
        self.assertEqual(result["validation"]["entries"], 2)
        files = [item for item in self.uploaded_files() if item.is_file()]
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].suffix, ".zip")
        self.assertFalse((self.root / "game").exists())
        self.assertEqual(list((self.root / "backend/data/workflow/reference_uploads/staging").iterdir()), [])

    async def test_zip_rejects_traversal_links_duplicates_bombs_and_corrupt_crc(self):
        link = zipfile.ZipInfo("link.txt")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        samples = [
            b"not-a-zip", self.archive([]), self.archive([("../outside.txt", "不能越界")]),
            self.archive([(link, "/outside")]), self.archive([("big.txt", "x" * 500_000)]),
        ]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            samples.append(self.archive([("duplicate.txt", "one"), ("duplicate.txt", "two")]))
        # 修改已存储文件的字节而保留原 CRC，目录可读但完整性校验必须失败。
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_STORED) as archive:
            archive.writestr("entry.txt", b"crc-content")
        samples.append(stream.getvalue().replace(b"crc-content", b"CRC-content", 1))
        for index, content in enumerate(samples):
            with self.subTest(index=index), self.assertRaises(ValueError):
                await self.upload("bad.zip", content, request_id=f"bad-{index}")
        self.assertEqual(self.uploaded_files(), [])
        self.assertEqual(list((self.root / "backend/data/workflow/reference_uploads/staging").iterdir()), [])

    async def test_size_is_enforced_during_stream_and_total_quota_counts_unique_files(self):
        with patch.object(reference_inputs, "MAX_UPLOAD_BYTES", 4), self.assertRaisesRegex(ValueError, "64MB"):
            await self.upload("large.txt", b"12345")
        self.assertEqual(self.uploaded_files(), [])
        with patch.object(reference_inputs, "MAX_CLIENT_BYTES", 5):
            first = await self.upload("small.txt", b"12345")
            again = await self.upload("small.txt", b"12345", request_id="same-content-new-request")
            self.assertEqual(first["reference_path"], again["reference_path"])
            with self.assertRaisesRegex(ValueError, "总量"):
                await self.upload("extra.txt", b"x", request_id="quota-overflow")
        self.assertEqual(len([p for p in self.uploaded_files() if p.is_file()]), 1)

    async def test_empty_invalid_text_type_and_filename_never_commit(self):
        for name, content in [("empty.txt", b""), ("bad.txt", b"\xff\xfe"), ("null.txt", b"\x00"),
                              ("invalid.json", b"not-json"), ("tool.exe", b"MZ"), ("../escape.txt", b"bad"),
                              ("a/b.txt", b"bad"), (".env", b"secret"), ("C:\\input.txt", b"bad"),
                              ("长" * 100 + ".txt", b"long-name")]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                await self.upload(name, content)
        with patch.object(reference_inputs, "MAX_TEXT_BYTES", 3), self.assertRaisesRegex(ValueError, "文本"):
            await self.upload("large.txt", b"1234")
        self.assertEqual(self.uploaded_files(), [])

    async def test_images_must_decode_and_match_the_extension(self):
        stream = io.BytesIO()
        Image.new("RGB", (4, 5), "red").save(stream, format="PNG")
        content = stream.getvalue()
        result = await self.upload("board.png", content)
        self.assertEqual(result["validation"], {"kind": "image", "width": 4, "height": 5, "format": "PNG"})
        with self.assertRaisesRegex(ValueError, "后缀"):
            await self.upload("board.webp", content, request_id="wrong-format")
        with self.assertRaisesRegex(ValueError, "损坏"):
            await self.upload("bad.png", b"not-an-image", request_id="bad-image")

    async def test_reference_and_upload_directory_symlinks_are_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "guide.md").write_text("不能跟随链接")
        (self.root / "ref" / "alias").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            reference_inputs.validate_references(self.root, "mac-one", ["alias/guide.md"])
        (self.root / "ref" / reference_inputs.UPLOAD_DIRECTORY).symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            await self.upload("guide.md", b"reference")
        self.assertFalse((outside / "mac-one").exists())

    async def test_staging_symlink_is_rejected_before_receiving_the_body(self):
        directory = self.root / "backend/data/workflow/reference_uploads"
        directory.mkdir(parents=True)
        outside = self.root / "outside"
        outside.mkdir()
        (directory / "staging").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            await self.upload("guide.md", b"reference")
        self.assertEqual(list(outside.iterdir()), [])

    async def test_private_directory_ancestor_symlink_is_rejected(self):
        (self.root / "backend").mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "backend/data").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            await self.upload("guide.md", b"reference")
        self.assertEqual(list(outside.iterdir()), [])

    async def test_cancelled_stream_discards_partial_private_input(self):
        async def interrupted_chunks():
            yield b"unfinished"
            raise asyncio.CancelledError()

        with self.assertRaises(asyncio.CancelledError):
            await reference_inputs.upload_reference(self.root, "mac-one", "guide.md", "cancelled", interrupted_chunks())
        self.assertEqual(self.uploaded_files(), [])
        self.assertEqual(list((self.root / "backend/data/workflow/reference_uploads/staging").iterdir()), [])

    async def test_library_index_search_pagination_and_directory_references(self):
        library = self.root / "ref" / "公司skill整合/AHAgames"
        game = library / "94034_Ludo_Superstar"
        game.mkdir(parents=True)
        (game / "gameInfo.json").write_text(json.dumps({"gameId": 94034, "apiName": "Ludo Superstar"}))
        (game / "Ludo.zip").write_bytes("存在性索引，不在列表时读取包体".encode())
        (self.root / "ref" / "说明.md").write_text("已有的参考资料")
        with patch("app.services.reference_games._research_summary", side_effect=AssertionError("不应递归研究目录")):
            result = reference_inputs.list_references(self.root, "mac-one", query="LUDO", limit=1)
        self.assertEqual(result["total"], 1)
        item = result["items"][0]
        self.assertEqual(item["name"], "Ludo Superstar")
        self.assertEqual(item["package_paths"], ["公司skill整合/AHAgames/94034_Ludo_Superstar/Ludo.zip"])
        self.assertEqual(reference_inputs.validate_references(self.root, "mac-one", [item["reference_path"]]), [item["reference_path"]])
        first = reference_inputs.list_references(self.root, "mac-one", limit=1)
        second = reference_inputs.list_references(self.root, "mac-one", limit=1, offset=first["next_offset"])
        self.assertTrue(first["has_more"])
        self.assertNotEqual(first["items"][0]["reference_path"], second["items"][0]["reference_path"])
        self.assertNotIn(str(self.root), json.dumps(first, ensure_ascii=False))

    async def test_tampered_uploaded_file_cannot_reuse_a_receipt(self):
        result = await self.upload("guide.txt", b"reference")
        (self.root / "ref" / result["reference_path"]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "内容变化"):
            await self.upload("guide.txt", b"reference")

    async def test_failed_receipt_write_rolls_back_new_content_and_cleans_private_files(self):
        with patch.object(reference_inputs.json, "dump", side_effect=OSError("模拟磁盘写入失败")):
            with self.assertRaisesRegex(OSError, "模拟磁盘"):
                await self.upload("guide.md", b"reference")
        self.assertEqual([item for item in self.uploaded_files() if item.is_file()], [])
        private = self.root / "backend/data/workflow/reference_uploads"
        self.assertEqual(list(private.rglob("*.tmp")), [])
        self.assertEqual(list(private.rglob("*.json")), [])
        first = await self.upload("guide.md", b"reference")
        # 复用已有内容时收据失败，不能误删先前成功上传的文件。
        with patch.object(reference_inputs.json, "dump", side_effect=OSError("模拟磁盘写入失败")):
            with self.assertRaises(OSError):
                await self.upload("guide.md", b"reference", request_id="retry-new-id")
        self.assertEqual((self.root / "ref" / first["reference_path"]).read_bytes(), b"reference")

    async def test_concurrent_same_request_returns_one_result_and_conflicts_never_overwrite(self):
        # 使用两个线程的独立事件循环模拟并发提交，验证共享业务锁的收据边界。
        async def request(content):
            return await asyncio.to_thread(lambda: asyncio.run(self.upload("guide.md", content)))

        first, repeated = await asyncio.gather(request(b"reference"), request(b"reference"))
        self.assertEqual(first, repeated)
        self.assertEqual(len(list((self.root / "backend/data/workflow/reference_uploads/receipts").rglob("*.json"))), 1)
        results = await asyncio.gather(request(b"reference"), request(b"different"), return_exceptions=True)
        self.assertEqual(results[0], first)
        self.assertIsInstance(results[1], ValueError)
        self.assertEqual((self.root / "ref" / first["reference_path"]).read_bytes(), b"reference")

    async def test_non_regular_existing_target_and_linked_receipt_are_rejected(self):
        content = b"reference"
        digest = hashlib.sha256(content).hexdigest()
        target = self.root / "ref/mcp-inputs/mac-one" / digest / "guide.md"
        target.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "普通文件"):
            await self.upload("guide.md", content)
        target.rmdir()
        first = await self.upload("guide.md", content)
        receipt = next((self.root / "backend/data/workflow/reference_uploads/receipts").rglob("*.json"))
        receipt.unlink()
        outside = self.root / "private.json"
        outside.write_text("{}")
        receipt.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            await self.upload("guide.md", content)
        self.assertEqual(outside.read_text(), "{}")
        self.assertTrue((self.root / "ref" / first["reference_path"]).is_file())


if __name__ == "__main__":
    unittest.main()
