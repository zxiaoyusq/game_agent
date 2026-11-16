"""本地公司游戏参考目录回归；全部夹具在临时目录，不访问网络。"""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.reference_games import router
from app.services import reference_games as reference


class ReferenceGamesTests(unittest.TestCase):
    """验证当前文件状态、BOM 文本和受限图片边界，不运行第三方游戏。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "AHAgames"
        self.root.mkdir()
        self.override = patch.object(reference, "REFERENCE_GAMES_ROOT", self.root)
        self.override.start()

    def tearDown(self):
        self.override.stop()
        self.temp.cleanup()

    def make_game(self, identifier, name="参考游戏", package=False):
        """保留失效的 Windows 路径，确保服务只使用当前同目录文件。"""
        directory = self.root / f"{identifier}_Game"
        directory.mkdir()
        info = {"gameId": identifier, "apiName": name, "category": "Puzzle", "source": "来源声明",
                "localFile": "E:\\archive\\old_game.zip", "verifiedAt": "历史成功", "localBytes": 9999}
        (directory / "gameInfo.json").write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8-sig")
        art = directory / "art"
        art.mkdir()
        (art / "icon.webp").write_bytes(b"local image fixture")
        (art / "preview.gif").write_bytes(b"local gif fixture")
        if package:
            (directory / "actual.zip").write_bytes(b"local package fixture")
        return directory

    def write_csv(self, name, fields, rows):
        with (self.root / name).open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_actual_files_override_historical_success_and_manifest_counts(self):
        self.make_game(100, package=True)
        self.make_game("200")
        (self.root / "manifest.json").write_text('[{"gameId":100}]', encoding="utf-8-sig")
        self.write_csv("manifest.csv", ["gameId", "status"], [{"gameId": 100, "status": "OK"}, {"gameId": 200, "status": "OK"}])
        self.write_csv("art_manifest.csv", ["id", "description"], [{"id": 100, "description": "本地介绍，含逗号"}, {"id": 200, "description": "第二款"}])
        result = reference.list_reference_games()
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["summary"]["local_package_games"], 1)
        self.assertEqual(result["summary"]["missing_package_games"], 1)
        self.assertEqual(result["summary"]["manifest_json_records"], 1)
        self.assertEqual(result["summary"]["manifest_csv_records"], 2)
        self.assertTrue(any("数量不一致" in item for item in result["summary"]["warnings"]))
        first, second = result["items"]
        self.assertEqual(first["description"], "本地介绍，含逗号")
        self.assertEqual(first["package"]["name"], "actual.zip")
        self.assertEqual(second["package_status"], "missing")
        self.assertIsNone(second["package"])
        self.assertNotIn("E:\\archive", json.dumps(result))
        self.assertEqual(first["reference_path"], "公司skill整合/AHAgames/100_Game/gameInfo.json")
        self.assertEqual(reference.reference_game_asset("100", "icon.webp").read_bytes(), b"local image fixture")

    def test_asset_access_rejects_traversal_scripts_packages_and_unknown_games(self):
        directory = self.make_game(100, package=True)
        (directory / "art" / "index.html").write_text("<script>throw new Error('不会执行')</script>")
        (directory / "art" / "icon.js").write_text("throw new Error('不会执行')")
        (directory / "art" / "extra.png").write_bytes(b"not a store role")
        game = reference.get_reference_game("100")
        self.assertEqual({asset["name"] for asset in game["assets"]}, {"icon.webp", "preview.gif"})
        self.assertTrue(all(asset["url"].startswith("/api/workflow/reference-games/100/assets/") for asset in game["assets"]))
        for path in ["../gameInfo.json", "..\\gameInfo.json", "/tmp/icon.webp", "x\x00.png"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                reference.reference_game_asset("100", path)
        for path in ["index.html", "icon.js", "actual.zip", "extra.png", "unknown.png"]:
            with self.subTest(path=path), self.assertRaises(FileNotFoundError):
                reference.reference_game_asset("100", path)
        with self.assertRaises(FileNotFoundError):
            reference.get_reference_game("unknown")
        with self.assertRaises(ValueError):
            reference.get_reference_game("../100")

    def test_symlink_files_and_parent_directories_are_never_exposed(self):
        directory = self.make_game(100)
        image = directory / "art" / "icon.webp"
        outside = Path(self.temp.name) / "private.webp"
        outside.write_bytes(b"outside")
        image.unlink()
        image.symlink_to(outside)
        with self.assertRaises(FileNotFoundError):
            reference.reference_game_asset("100", "icon.webp")
        (directory / "art" / "preview.gif").unlink()
        image.unlink()
        (directory / "art").rmdir()
        (directory / "art").symlink_to(outside.parent, target_is_directory=True)
        self.assertEqual(reference.get_reference_game("100")["assets"], [])
        with self.assertRaises(FileNotFoundError):
            reference.reference_game_asset("100", "private.webp")
        alias = Path(self.temp.name) / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with patch.object(reference, "REFERENCE_GAMES_ROOT", alias), self.assertRaises(ValueError):
            reference.list_reference_games()
        parent_alias = Path(self.temp.name) / "parent-link"
        parent_alias.symlink_to(self.root.parent, target_is_directory=True)
        with patch.object(reference, "REFERENCE_GAMES_ROOT", parent_alias / self.root.name), self.assertRaises(ValueError):
            reference.list_reference_games()

    def test_duplicate_ids_and_bad_metadata_are_reported_without_ambiguous_lookup(self):
        first = self.make_game(100)
        second = self.make_game(200)
        (second / "gameInfo.json").write_text((first / "gameInfo.json").read_text(encoding="utf-8-sig"))
        bad = self.root / "bad"
        bad.mkdir()
        (bad / "gameInfo.json").write_text("broken JSON")
        result = reference.list_reference_games()
        self.assertEqual(result["total"], 0)
        self.assertTrue(any("重复" in item for item in result["summary"]["warnings"]))
        self.assertTrue(any("bad" in item for item in result["summary"]["warnings"]))
        with self.assertRaises(FileNotFoundError):
            reference.get_reference_game("100")

    def test_research_is_counted_without_copying_or_following_links(self):
        self.make_game(100)
        research = self.root / "art_direction"
        research.mkdir()
        (research / "设计.md").write_text("# 设计说明", encoding="utf-8")
        (research / "unsafe").symlink_to(Path(self.temp.name), target_is_directory=True)
        result = reference.list_reference_games()
        record = next(item for item in result["summary"]["research"] if item["name"] == "art_direction")
        self.assertEqual(record["file_count"], 1)
        self.assertEqual(record["reference_path"], "公司skill整合/AHAgames/art_direction")
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ["100_Game", "art_direction"])

    def test_missing_reference_directory_has_explicit_empty_state(self):
        self.root.rmdir()
        result = reference.list_reference_games()
        self.assertEqual(result["total"], 0)
        self.assertTrue(result["summary"]["warnings"])
        with self.assertRaises(FileNotFoundError):
            reference.get_reference_game("100")

    def test_case_documents_are_readable_and_selectable_without_importing_project_files(self):
        """OneConnect 案例独立于游戏清单，文档可按原路径传给已有参考读取工具。"""
        case = self.root.parent / "OneConnectRe"
        case.mkdir()
        document = case / "开发说明.md"
        content = "# 来源案例\n<script>window.caseExecuted = true</script>\n真实宿主未验收。"
        document.write_text(content, encoding="utf-8-sig")
        (case / "game.js").write_text("throw new Error('不执行')")
        (case / "review.html").write_text("<script>不执行</script>")
        (case / ".private.md").write_text("隐藏内容")
        (case / "too-large.md").write_bytes(b"a" * (reference.MAX_DOCUMENT_BYTES + 1))
        result = reference.list_reference_games()
        self.assertEqual(result["total"], 0)
        source = next(item for item in result["summary"]["research"] if item["name"] == "OneConnectRe")
        self.assertEqual([item["name"] for item in source["documents"]], ["开发说明"])
        selected = source["documents"][0]["reference_path"]
        self.assertEqual(selected, "公司skill整合/OneConnectRe/开发说明.md")
        app = FastAPI()
        app.include_router(router, prefix="/api")
        with TestClient(app) as client:
            response = client.get("/api/workflow/reference-games/research-document", params={"path": selected})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["content"], content)
            self.assertEqual(response.headers["content-type"], "application/json")
            self.assertEqual(len(response.json()["sha256"]), 64)
            for path in ["../private.md", "公司skill整合/OneConnectRe/../开发说明.md",
                         "公司skill整合/OneConnectRe/.private.md", "公司skill整合/OneConnectRe/game.js",
                         "公司skill整合/OneConnectRe/review.html", "公司skill整合/OneConnectRe/too-large.md"]:
                with self.subTest(path=path):
                    self.assertEqual(client.get("/api/workflow/reference-games/research-document", params={"path": path}).status_code, 404)

    def test_research_document_links_deleted_files_and_invalid_text_are_rejected(self):
        case = self.root.parent / "OneConnectRe"
        case.mkdir()
        outside = self.root.parent / "outside.md"
        outside.write_text("私有文本")
        (case / "link.md").symlink_to(outside)
        path = "公司skill整合/OneConnectRe/link.md"
        with self.assertRaises(FileNotFoundError):
            reference.read_research_document(path)
        (case / "bad.md").write_bytes(b"\xff\x00")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            reference.read_research_document("公司skill整合/OneConnectRe/bad.md")
        (case / "bad.md").unlink()
        with self.assertRaises(FileNotFoundError):
            reference.read_research_document("公司skill整合/OneConnectRe/bad.md")

    def test_routes_return_local_data_images_and_reject_invalid_paths(self):
        """仅挂载真实路由，避免主应用启动流程触及运行服务和持久资料。"""
        self.make_game(100)
        app = FastAPI()
        app.include_router(router, prefix="/api")
        base = "/api/workflow/reference-games"
        with TestClient(app) as client:
            response = client.get(base)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["total"], 1)
            detail = client.get(f"{base}/100")
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(detail.json()["package_status"], "missing")
            for filename, content_type in [("icon.webp", "image/webp"), ("preview.gif", "image/gif")]:
                image = client.get(f"{base}/100/assets/{filename}")
                self.assertEqual(image.status_code, 200)
                self.assertEqual(image.headers["content-type"], content_type)
                self.assertEqual(image.headers["x-content-type-options"], "nosniff")
                self.assertEqual(image.content, reference.reference_game_asset("100", filename).read_bytes())
            for path in ["unknown", "100/assets/unknown.png", "100/assets/gameInfo.json", "100/assets/index.html"]:
                self.assertEqual(client.get(f"{base}/{path}").status_code, 404)
            # 编码后的反斜杠进入参数校验，斜杠穿越无法匹配资源路由。
            self.assertEqual(client.get(f"{base}/100/assets/%2E%2E%5CgameInfo.json").status_code, 400)
            self.assertEqual(client.get(f"{base}/100/assets/%2E%2E%2FgameInfo.json").status_code, 404)
            self.assertEqual(client.get(f"{base}/%2E%2E%5C100").status_code, 400)


if __name__ == "__main__":
    unittest.main()
