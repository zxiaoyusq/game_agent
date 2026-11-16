"""ZIP 研究与按件取材的真实文件、来源记录和边界回归。"""

import hashlib
import json
import stat
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

from app.services.workflow import reference_tools


class ReferenceToolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.ref = self.root / "ref"
        self.ref.mkdir()
        self.workspace = self.root / "games" / "new-game"
        self.workspace.mkdir(parents=True)
        self.events = []
        self.tools = {item.name: item for item in reference_tools.create_reference_tools(
            self.root, self.workspace, lambda *event: self.events.append(event))}

    def archive(self, entries, name="sample.zip"):
        target = self.ref / name
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
                for entry, content in entries:
                    archive.writestr(entry, content)
        return target

    def invoke(self, name, **arguments):
        return json.loads(self.tools[name].invoke(arguments))

    def test_pagination_and_text_slices_bind_to_archive_and_member_hashes(self):
        text = "const 规则 = '六点出营';\n" * 8
        archive = self.archive([("assets/config.json", '{"safe":[0,13]}'), ("src/main.js", text)])
        listing = self.invoke("list_reference_archive", path="ref/sample.zip", limit=1)
        self.assertEqual(listing["total_entries"], 2)
        self.assertTrue(listing["has_more"])
        self.assertEqual(listing["archive_sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
        second = self.invoke("list_reference_archive", path="sample.zip", offset=1, limit=1)
        self.assertEqual(second["entries"][0]["path"], "src/main.js")
        self.assertFalse(second["has_more"])
        read = self.invoke("read_reference_archive", path="sample.zip", member="src/main.js", offset=5, limit=13)
        self.assertEqual(read["content"], text[5:18])
        self.assertEqual(read["total_chars"], len(text))
        self.assertEqual(read["sha256"], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(self.events[-1][0], "reference_archive_read")
        self.assertEqual(self.events[-1][2]["archive_sha256"], listing["archive_sha256"])
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_text_limit_binary_and_invalid_utf8_are_explicit(self):
        text = "四季商路" * 30000
        self.archive([("long.js", text), ("image.png", b"\x89PNG\x00\xff"), ("bad.js", b"\xff\xfe")])
        # 高重复文本需要单独放宽此测试的压缩比，文本分页本身仍按正式上限运行。
        with patch.object(reference_tools, "MAX_COMPRESSION_RATIO", 10000):
            read = self.invoke("read_reference_archive", path="sample.zip", member="long.js", limit=1000000)
            self.assertEqual(len(read["content"]), 60000)
            for member in ("image.png", "bad.js"):
                with self.subTest(member=member), self.assertRaises(ValueError):
                    self.invoke("read_reference_archive", path="sample.zip", member=member)

    def test_search_paginates_matches_without_losing_archive_counts(self):
        self.archive([("loading/config.123ab.json", "{}"), ("scripts/config.456cd.json", "{}"),
                      ("scripts/main.js", "const dice = 6;")])
        first = self.invoke("list_reference_archive", path="sample.zip", query="CONFIG.", limit=1)
        self.assertEqual(first["total_entries"], 3)
        self.assertEqual(first["matched_entries"], 2)
        self.assertEqual(first["entries"][0]["path"], "loading/config.123ab.json")
        self.assertEqual(first["next_offset"], 1)
        second = self.invoke("list_reference_archive", path="sample.zip", query="CONFIG.", offset=first["next_offset"], limit=1)
        self.assertEqual(second["entries"][0]["path"], "scripts/config.456cd.json")
        self.assertFalse(second["has_more"])
        self.assertIsNone(second["next_offset"])
        missing = self.invoke("list_reference_archive", path="sample.zip", query="absent", offset=10)
        self.assertEqual(missing["matched_entries"], 0)
        self.assertEqual(missing["entries"], [])
        self.assertEqual(missing["offset"], 0)

    def test_missing_member_suggests_real_paths_without_reading_a_substitute(self):
        actual = "game/loading/assets/resources/config.0bf53.json"
        self.archive([(actual, '{"真实配置":true}'), ("game/other.json", "{}")])
        for member in ("game/assets/resources/config.0bf53.json", "game/assets/resources/config.f931b.json"):
            with self.subTest(member=member), self.assertRaises(ValueError) as caught:
                self.invoke("read_reference_archive", path="sample.zip", member=member)
            message = str(caught.exception)
            self.assertIn(member, message)
            self.assertIn(actual, message)
            self.assertIn("尚未读取", message)
            self.assertIn("list_reference_archive", message)
        self.assertEqual(self.events, [])
        self.assertEqual(list(self.workspace.iterdir()), [])
        found = self.invoke("list_reference_archive", path="sample.zip", query="config.")
        result = self.invoke("read_reference_archive", path="sample.zip", member=found["entries"][0]["path"])
        self.assertEqual(result["content"], '{"真实配置":true}')

    def test_directory_and_absent_resource_have_distinct_recovery_messages(self):
        self.archive([("explicit/", ""), ("explicit/a.json", "{}"), ("implicit/a.json", "{}")])
        for member in ("explicit/", "implicit", "implicit/"):
            with self.subTest(member=member), self.assertRaisesRegex(ValueError, "指定条目是目录"):
                self.invoke("read_reference_archive", path="sample.zip", member=member)
        with self.assertRaisesRegex(ValueError, "没有同名候选") as caught:
            self.invoke("read_reference_archive", path="sample.zip", member="resources/import/absent-uuid.123ab.json")
        self.assertIn("不要重复猜路径", str(caught.exception))
        self.assertEqual(self.events, [])

    def test_actual_failed_ludo_paths_can_be_located_or_confirmed_absent(self):
        """重放真实任务的三次失败，纠错仅使用原包目录，不制造兼容文件。"""
        root = Path(__file__).resolve().parents[2]
        archive = "公司skill整合/AHAgames/94034_Ludo_Superstar/Ludo_Superstar.zip"
        if not (root / "ref" / archive).is_file():
            self.skipTest("当前环境未提供 Ludo Superstar 原包")
        tools = {item.name: item for item in reference_tools.create_reference_tools(
            root, self.workspace, lambda *event: self.events.append(event))}
        prefix = "www.hnyigegame.com/Ludo_Superstar/game/"
        corrections = [
            ("assets/resources/config.f931b.json", "loading/assets/resources/config.0bf53.json", "resources/config."),
            ("assets/resources/import/0c/0c67ce8ea.b217e.json",
             "loading/assets/resources/import/0c/0c67ce8ea.b217e.json", "0c67ce8ea.b217e.json"),
        ]
        for wrong, expected, query in corrections:
            with self.subTest(member=wrong):
                with self.assertRaises(ValueError) as caught:
                    tools["read_reference_archive"].invoke({"path": archive, "member": prefix + wrong})
                self.assertIn(prefix + expected, str(caught.exception))
                listing = json.loads(tools["list_reference_archive"].invoke({"path": archive, "query": query}))
                entry = next(item for item in listing["entries"] if item["path"] == prefix + expected)
                result = json.loads(tools["read_reference_archive"].invoke({"path": archive, "member": entry["path"], "limit": 200}))
                self.assertEqual(result["sha256"], entry["sha256"])
                self.assertTrue(result["content"])
        # 美术阶段同样不能统一加 loading/ 前缀；部分素材确实在 game/assets 下。
        filename = "c0e17be1-c9df-45e2-89b3-18f681954af2.5ad39.png"
        actual = prefix + "assets/resources/native/c0/" + filename
        with self.assertRaises(ValueError) as caught:
            tools["extract_reference_asset"].invoke({
                "path": archive, "member": prefix + "loading/assets/resources/native/c0/" + filename,
                "destination": "public/assets/info-green.png"})
        self.assertIn(actual, str(caught.exception))
        missing = "f69238d7-5752-4765-818a-01966727ed9a"
        with self.assertRaisesRegex(ValueError, "没有同名候选"):
            tools["read_reference_archive"].invoke({"path": archive, "member": prefix + f"loading/assets/resources/import/f6/{missing}.df05c.json"})
        listing = json.loads(tools["list_reference_archive"].invoke({"path": archive, "query": missing}))
        self.assertEqual(listing["matched_entries"], 0)
        self.assertEqual(sum(event[0] == "reference_archive_read" for event in self.events), 2)
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_zip_paths_duplicates_links_and_parent_collisions_are_rejected(self):
        link = zipfile.ZipInfo("linked.png")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        cases = [
            [("../secret.txt", "no")], [("/absolute.txt", "no")], [("C:\\private.txt", "no")],
            [("a/./b.js", "no")], [("same.js", "one"), ("same.js", "two")],
            [(link, "/outside.png")], [("folder", "file"), ("folder/child.js", "no")],
        ]
        for index, entries in enumerate(cases):
            self.archive(entries, f"bad{index}.zip")
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.invoke("list_reference_archive", path=f"bad{index}.zip")
        self.assertEqual(self.events, [])
        self.assertFalse((self.root / "secret.txt").exists())

    def test_damaged_zip_and_bomb_limits(self):
        (self.ref / "broken.zip").write_text("这不是压缩包")
        with self.assertRaisesRegex(ValueError, "损坏"):
            self.invoke("list_reference_archive", path="broken.zip")
        self.archive([("bomb.json", b"0" * 1000000)], "bomb.zip")
        with self.assertRaisesRegex(ValueError, "压缩比"):
            self.invoke("list_reference_archive", path="bomb.zip")
        self.archive([("one.js", "first"), ("two.js", "second")])
        with patch.object(reference_tools, "MAX_EXPANDED_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "展开总大小"):
                self.invoke("list_reference_archive", path="sample.zip")
        with patch.object(reference_tools, "MAX_ENTRIES", 1):
            with self.assertRaisesRegex(ValueError, "文件数"):
                self.invoke("list_reference_archive", path="sample.zip")

    def test_reference_root_and_symlink_escape_are_rejected(self):
        real = self.archive([("main.js", "console.log('来源')")])
        (self.ref / "alias.zip").symlink_to(real)
        (self.ref / "linked").symlink_to(self.ref, target_is_directory=True)
        for name in ("../sample.zip", str(real), "alias.zip", "linked/sample.zip"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.invoke("list_reference_archive", path=name)

    def test_asset_copy_is_exact_records_provenance_and_never_overwrites_edits(self):
        pixels = b"\x89PNG\r\nfixture"
        self.archive([("art/piece.png", pixels), ("main.js", "const dice = 6;")])
        result = self.invoke("extract_reference_asset", path="sample.zip", member="art/piece.png", destination="public/assets/piece.png")
        target = self.workspace / "public/assets/piece.png"
        self.assertEqual(target.read_bytes(), pixels)
        self.assertEqual(result["sha256"], hashlib.sha256(pixels).hexdigest())
        self.assertEqual(result["purpose"], "reference_asset")
        self.assertEqual(self.events[-1][0], "reference_asset_copied")
        repeated = self.invoke("extract_reference_asset", path="sample.zip", member="art/piece.png", destination="public/assets/piece.png")
        self.assertTrue(repeated["reused"])
        target.write_bytes("用户已经换皮".encode())
        with self.assertRaisesRegex(ValueError, "不能覆盖"):
            self.invoke("extract_reference_asset", path="sample.zip", member="art/piece.png", destination="public/assets/piece.png")
        self.assertEqual(target.read_bytes(), "用户已经换皮".encode())
        code = self.invoke("extract_reference_asset", path="sample.zip", member="main.js", destination="reference-inputs/main.js")
        self.assertEqual(code["purpose"], "reference_only")
        self.assertEqual((self.workspace / "reference-inputs/main.js").read_text(), "const dice = 6;")

    def test_copy_cannot_write_game_sources_or_disguise_executable_files(self):
        self.archive([("piece.png", b"image"), ("main.js", "const code = 1;"), ("tool.exe", b"MZ")])
        for member, destination in [("piece.png", "../piece.png"), ("piece.png", "src/piece.png"),
                                    ("piece.png", "workflow/piece.png"), ("piece.png", "public/assets/.secret.png"),
                                    ("main.js", "public/assets/main.js"), ("main.js", "public/assets/main.png"),
                                    ("tool.exe", "reference-inputs/tool.exe")]:
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                self.invoke("extract_reference_asset", path="sample.zip", member=member, destination=destination)
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_extract_keeps_original_bytes_and_explains_actual_format_conversion(self):
        self.archive([("piece.png", b"original-png-bytes")])
        with self.assertRaises(ValueError) as caught:
            self.invoke("extract_reference_asset", path="sample.zip", member="piece.png", destination="public/assets/piece.webp")
        self.assertIn("destination=public/assets/piece.png", str(caught.exception))
        self.assertIn("process_art_image", str(caught.exception))
        self.assertEqual(list(self.workspace.iterdir()), [])
        self.assertEqual(self.events, [])

    def test_copy_rejects_symlink_targets_and_budget_overflow(self):
        self.archive([("piece.png", b"image-bytes")])
        outside = self.root / "outside"
        outside.mkdir()
        (self.workspace / "reference-assets").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            self.invoke("extract_reference_asset", path="sample.zip", member="piece.png", destination="reference-assets/piece.png")
        self.assertEqual(list(outside.iterdir()), [])
        (self.workspace / "reference-assets").unlink()
        with patch.object(reference_tools, "MAX_EXTRACTED_BYTES", 3):
            with self.assertRaisesRegex(ValueError, "取材目录总量"):
                self.invoke("extract_reference_asset", path="sample.zip", member="piece.png", destination="reference-assets/piece.png")
        self.assertFalse((self.workspace / "reference-assets/piece.png").exists())

    def test_actual_ludo_archives_are_read_without_extracting_old_games(self):
        project_root = Path(__file__).resolve().parents[2]
        inputs = [
            ("公司skill整合/AHAgames/82251_Just_Ludo/Just_Ludo.zip", "www.volcanoh5game.com/Just_Ludo/assets/main/index.js", "canWalk"),
            ("公司skill整合/AHAgames/94034_Ludo_Superstar/Ludo_Superstar.zip", "www.hnyigegame.com/Ludo_Superstar/game/scripts/assets/main/index.a298e.js", "GameScene"),
        ]
        if not all((project_root / "ref" / name).is_file() for name, _, _ in inputs):
            self.skipTest("当前环境未提供两份Ludo原包")
        actual = {item.name: item for item in reference_tools.create_reference_tools(project_root, self.workspace, lambda *event: self.events.append(event))}
        for archive, member, marker in inputs:
            with self.subTest(archive=archive):
                listing = json.loads(actual["list_reference_archive"].invoke({"path": archive, "limit": 2}))
                self.assertGreater(listing["total_entries"], 100)
                self.assertEqual(len(listing["archive_sha256"]), 64)
                read = json.loads(actual["read_reference_archive"].invoke({"path": archive, "member": member, "limit": 60000}))
                self.assertGreater(read["total_chars"], 10000)
                # 真实业务代码的第一页可以识别Cocos模块，不从预先写好的分析报告取结果。
                self.assertTrue("cc." in read["content"] or "window.__require" in read["content"])
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_native_web_board_profile_exposes_its_real_knowledge_files(self):
        from app.services.production_library import SOURCE, resolve_profile
        profile = resolve_profile("board-games", "native-web")
        self.assertIn("SVG", profile["framework"]["instructions"])
        self.assertEqual(profile["framework"]["required_validations"], ["npm run build", "npm test", "npm run check"])
        self.assertEqual(profile["framework"]["preview_entry"], "dist/index.html")
        for name in profile["knowledge_paths"]:
            module, _, filename = name.split("/")
            self.assertTrue((SOURCE / module / filename).read_text(encoding="utf-8").strip())


if __name__ == "__main__":
    unittest.main()
