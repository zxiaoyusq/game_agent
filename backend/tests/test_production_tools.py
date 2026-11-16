"""生产工具边界验证：真实图片字节、资产保护、阶段权限与子进程环境。"""

import asyncio
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from PIL import Image

from app.services import art_image
from app.services.workflow.production_tools import create_production_tools, validation_environment


def image_bytes(format="PNG"):
    """使用实际可解码的小图片替代远程付费服务，保留格式转换的真实行为。"""
    output = io.BytesIO()
    Image.new("RGB", (12, 8), (33, 99, 165)).save(output, format)
    return output.getvalue()


class ProductionToolsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / "project"
        self.workspace.mkdir()
        self.run = {"stage": "art", "attempt": 1}
        self.events = []
        self.tools = {item.name: item for item in create_production_tools(
            self.workspace, self.run, lambda *args: self.events.append(args),
        )}

    async def generate(self, **options):
        return json.loads(await self.tools["generate_art_image"].ainvoke({
            "prompt": "生成原创棋盘背景", "destination": "public/assets/board.png", **options,
        }))

    def write(self, relative, content):
        target = self.workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    async def test_provider_output_is_saved_as_requested_image_with_actual_hash(self):
        for suffix, expected_format in [("png", "PNG"), ("webp", "WEBP")]:
            with self.subTest(format=suffix), patch.object(
                art_image, "generate", autospec=True, return_value=image_bytes(),
            ) as provider, patch.object(art_image, "edit", autospec=True) as edit:
                result = await self.generate(destination=f"public/assets/board.{suffix}")
                target = self.workspace / result["path"]
                content = target.read_bytes()
                with Image.open(target) as saved:
                    saved.load()
                    self.assertEqual(saved.format, expected_format)
                    self.assertEqual(saved.size, (12, 8))
                self.assertEqual(result["size"], len(content))
                self.assertEqual((result["width"], result["height"]), (12, 8))
                self.assertEqual(result["sha256"], hashlib.sha256(content).hexdigest())
                provider.assert_awaited_once_with(prompt="生成原创棋盘背景", size="1536x1024", quality="high")
                edit.assert_not_awaited()
                self.assertEqual(self.events[-1], ("image_generated", "图片API已生成并保存真实资源", result))

    async def test_reference_images_use_real_provider_contract_and_matching_mime_types(self):
        names = ["reference-assets/a.PNG", "reference-assets/b.jpeg", "reference-assets/c.webp", "assets/d.jpeg"]
        formats = ["PNG", "JPEG", "WEBP", "PNG"]
        contents = [image_bytes(format) for format in formats]
        for name, content in zip(names, contents):
            self.write(name, content)
        with patch.object(art_image, "edit", autospec=True, return_value=image_bytes()) as provider, \
                patch.object(art_image, "generate", autospec=True) as generate:
            result = await self.generate(reference_paths=names, size="1024x1024", quality="medium")
        provider.assert_awaited_once()
        generate.assert_not_awaited()
        arguments = provider.call_args.kwargs
        self.assertEqual(arguments["size"], "1024x1024")
        self.assertEqual(arguments["quality"], "medium")
        references = arguments["references"]
        self.assertEqual(len(references), 4)
        for name, content, format, reference in zip(names, contents, formats, references):
            self.assertIsInstance(reference, art_image.ReferenceImage)
            self.assertEqual(reference.filename, Path(name).stem + {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[format])
            self.assertEqual(reference.data, content)
            self.assertEqual(reference.content_type, f"image/{format.lower()}")
        self.assertTrue((self.workspace / result["path"]).is_file())

    async def test_disguised_webp_reference_uses_real_mime_filename_and_unchanged_bytes(self):
        """使用原包同类伪扩展，验证编辑调用实际收到原字节及一致的上传名称和MIME。"""
        image = Image.new("RGBA", (2, 2))
        image.putdata([(255, 0, 0, 255), (0, 255, 0, 128), (0, 0, 255, 64), (12, 34, 56, 0)])
        encoded = io.BytesIO()
        image.save(encoded, "WEBP", lossless=True, exact=True)
        content = encoded.getvalue()
        original = self.write("reference-assets/cocos-atlas.png", content)
        with patch.object(art_image, "edit", autospec=True, return_value=image_bytes()) as edit, \
                patch.object(art_image, "generate", autospec=True) as generate:
            result = await self.generate(reference_paths=["reference-assets/cocos-atlas.png"])
        generate.assert_not_awaited()
        edit.assert_awaited_once()
        reference = edit.call_args.kwargs["references"][0]
        self.assertEqual(reference.filename, "cocos-atlas.webp")
        self.assertEqual(reference.content_type, "image/webp")
        self.assertEqual(reference.data, content)
        self.assertEqual(original.read_bytes(), content)
        with Image.open(io.BytesIO(reference.data)) as uploaded:
            self.assertEqual(uploaded.convert("RGBA").tobytes(), image.tobytes())
        self.assertEqual(result["reference_images"], [{
            "path": "reference-assets/cocos-atlas.png", "sha256": hashlib.sha256(content).hexdigest(),
            "size": len(content), "width": 2, "height": 2, "format": "WEBP",
            "content_type": "image/webp", "upload_filename": "cocos-atlas.webp",
        }])
        self.assertEqual(self.events[0][2]["reference_images"], result["reference_images"])

    async def test_stage_gates_reject_requests_before_external_work(self):
        with patch.object(art_image, "generate", autospec=True) as provider, \
                patch("app.services.workflow.production_tools.asyncio.create_subprocess_exec", new_callable=AsyncMock) as spawn:
            for stage in ["prototype", "code", "test", "publish", None]:
                self.run["stage"] = stage
                with self.subTest(image_stage=stage), self.assertRaisesRegex(ValueError, "美术阶段"):
                    await self.generate()
            for stage in ["prototype", "art", "publish", None]:
                self.run["stage"] = stage
                with self.subTest(runtime_stage=stage), self.assertRaisesRegex(ValueError, "代码或测试阶段"):
                    await self.tools["prepare_web_runtime"].ainvoke({})
        provider.assert_not_awaited()
        spawn.assert_not_awaited()
        self.assertEqual(self.events, [])

    async def test_destination_paths_and_existing_assets_are_protected_before_api_call(self):
        original = self.write("public/assets/existing.png", "已存在的版本".encode())
        internal = self.workspace / "private"
        internal.mkdir()
        (self.workspace / "assets").symlink_to(internal, target_is_directory=True)
        (self.workspace / "public/assets/external").symlink_to(self.root, target_is_directory=True)
        paths = ["outside.png", "public/assets/../../outside.png", "public/assets/../outside.png",
                 "/public/assets/absolute.png", "public/assets/.hidden.png", "public/assets/file.svg",
                 "assets/linked.png", "public/assets/external/outside.png", "public/assets/existing.png"]
        with patch.object(art_image, "generate", autospec=True) as provider:
            for destination in paths:
                with self.subTest(destination=destination), self.assertRaises(ValueError):
                    await self.generate(destination=destination)
        provider.assert_not_awaited()
        self.assertEqual(original.read_bytes(), "已存在的版本".encode())
        self.assertEqual(list(internal.iterdir()), [])
        self.assertEqual(self.events, [])

    async def test_api_wait_cannot_overwrite_a_new_asset(self):
        target = self.workspace / "public/assets/board.png"

        async def provider(**kwargs):
            self.write("public/assets/board.png", "其他工具刚完成的版本".encode())
            return image_bytes()

        with patch.object(art_image, "generate", autospec=True, side_effect=provider):
            with self.assertRaises(FileExistsError):
                await self.generate()
        self.assertEqual(target.read_bytes(), "其他工具刚完成的版本".encode())
        self.assertEqual([event[0] for event in self.events], ["image_generation_started"])

    async def test_api_wait_cannot_redirect_output_through_a_new_symlink(self):
        outside = self.root / "outside"
        outside.mkdir()

        async def provider(**kwargs):
            (self.workspace / "public").mkdir()
            (self.workspace / "public/assets").symlink_to(outside, target_is_directory=True)
            return image_bytes()

        with patch.object(art_image, "generate", autospec=True, side_effect=provider):
            with self.assertRaisesRegex(ValueError, "符号链接"):
                await self.generate()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual([event[0] for event in self.events], ["image_generation_started"])

    async def test_reference_validation_rejects_fake_images_oversize_and_unsafe_paths(self):
        self.write("refs/text.png", b"this is not an image")
        self.write("refs/unsupported.png", image_bytes("BMP"))
        self.write("refs/broken.png", image_bytes("PNG")[:40])
        self.write("refs/vector.svg", b"<svg/>")
        self.write("refs/real.png", image_bytes())
        animated = io.BytesIO()
        Image.new("RGBA", (2, 2), "red").save(animated, "WEBP", save_all=True,
            append_images=[Image.new("RGBA", (2, 2), "blue")], duration=100, loop=0)
        self.write("refs/animated.png", animated.getvalue())
        (self.workspace / "refs/directory.png").mkdir()
        (self.workspace / "refs/linked.png").symlink_to(self.workspace / "refs/real.png")
        oversize = self.workspace / "refs/oversize.png"
        with oversize.open("wb") as file:
            file.truncate(10_000_001)
        paths = ["refs/missing.png", "refs/text.png", "refs/unsupported.png", "refs/broken.png", "refs/animated.png", "refs/vector.svg",
                 "refs/oversize.png", "refs/directory.png", "refs/linked.png", "../outside.png", "/refs/real.png"]
        with patch.object(art_image, "edit", autospec=True) as edit, \
                patch.object(art_image, "generate", autospec=True) as generate:
            for name in paths:
                with self.subTest(reference=name), self.assertRaises(ValueError):
                    await self.generate(reference_paths=[name])
            # 数量先于文件读取校验，避免一次无效请求读取任意多份大文件。
            with self.assertRaisesRegex(ValueError, "最多使用4张"):
                await self.generate(reference_paths=["nonexistent.png"] * 5)
        edit.assert_not_awaited()
        generate.assert_not_awaited()
        self.assertEqual(self.events, [])
        self.assertFalse((self.workspace / "public/assets/board.png").exists())

    async def test_provider_failure_hides_credentials_and_never_reports_a_file(self):
        secret = "测试专用图片服务凭据"
        with patch("app.services.workflow.model_runtime.config.AZURE_IMAGE_API_KEY", secret), \
                patch.object(art_image, "generate", autospec=True, side_effect=RuntimeError(f"上游拒绝 {secret}")):
            with self.assertRaises(RuntimeError) as caught:
                await self.generate()
        self.assertNotIn(secret, str(caught.exception))
        self.assertIn("凭据已隐藏", str(caught.exception))
        self.assertFalse((self.workspace / "public/assets/board.png").exists())
        self.assertEqual([event[0] for event in self.events], ["image_generation_started"])

    async def test_invalid_provider_image_does_not_create_asset_or_success_event(self):
        with patch.object(art_image, "generate", autospec=True, return_value=b"not image bytes"):
            with self.assertRaises(OSError):
                await self.generate()
        self.assertFalse((self.workspace / "public/assets/board.png").exists())
        self.assertEqual([event[0] for event in self.events], ["image_generation_started"])

    def test_subprocess_environment_keeps_runtime_settings_and_excludes_service_credentials(self):
        runtime = {"PATH": "/usr/bin", "HOME": "/tmp/home", "LANG": "zh_CN.UTF-8", "LC_ALL": "C.UTF-8", "TMPDIR": "/tmp"}
        secrets = {name: "测试凭据" for name in [
            "LLM_API_KEY", "AZURE_IMAGE_API_KEY", "AWS_ACCESS_KEY_ID", "AUTHORIZATION", "MCP_HEADERS",
            "DATABASE_URL", "NPM_TOKEN", "npm_config_auth", "NODE_OPTIONS", "LC_SERVICE_SECRET",
        ]}
        with patch.dict(os.environ, {**runtime, **secrets}, clear=True):
            self.assertEqual(validation_environment(), runtime)

    async def test_npm_preparation_is_fixed_and_has_no_service_credentials_or_lifecycle_scripts(self):
        package = self.write("package.json", b'{"scripts":{"check":"node scripts/check.cjs"}}')
        original = package.read_bytes()
        for stage, exit_code in [("code", 0), ("test", 1)]:
            self.run["stage"] = stage
            process = SimpleNamespace(returncode=exit_code, communicate=AsyncMock(return_value=("测试安装输出".encode(), None)))
            with self.subTest(stage=stage), \
                    patch.dict(os.environ, {"PATH": "/usr/bin", "API_KEY": "不可传入", "AWS_ACCESS_KEY_ID": "不可传入"}, clear=True), \
                    patch("app.services.workflow.production_tools.asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=process) as spawn, \
                    patch("app.services.workflow.production_tools.stop_process", new_callable=AsyncMock) as stop:
                result = json.loads(await self.tools["prepare_web_runtime"].ainvoke({}))
                self.assertEqual(result["exit_code"], exit_code)
                self.assertIn("测试安装输出", result["output"])
                arguments = spawn.call_args.args
                self.assertEqual(arguments[0:2], ("npm", "install"))
                self.assertIn("--ignore-scripts", arguments)
                self.assertIn("--save-exact", arguments)
                self.assertEqual(arguments[-1], "playwright@1.63.0")
                self.assertEqual(spawn.call_args.kwargs["cwd"], self.workspace)
                self.assertEqual(spawn.call_args.kwargs["env"], {"PATH": "/usr/bin"})
                self.assertNotIn("shell", spawn.call_args.kwargs)
                stop.assert_awaited_once_with(process)
                self.assertEqual(self.events[-1][2], result)
                self.assertIn("完成" if exit_code == 0 else "失败", self.events[-1][1])
        self.assertEqual(package.read_bytes(), original)

    async def test_npm_requires_valid_project_manifest_and_rejects_symlink_write_targets(self):
        self.run["stage"] = "code"
        with patch("app.services.workflow.production_tools.asyncio.create_subprocess_exec", new_callable=AsyncMock) as spawn:
            with self.assertRaises(ValueError):
                await self.tools["prepare_web_runtime"].ainvoke({})
            package = self.write("package.json", b"[]")
            with self.assertRaises(ValueError):
                await self.tools["prepare_web_runtime"].ainvoke({})
            package.write_text("{}", encoding="utf-8")
            for name in ["package-lock.json", "npm-shrinkwrap.json", "node_modules"]:
                target = self.workspace / name
                target.symlink_to(self.root / "outside")
                try:
                    with self.subTest(path=name), self.assertRaisesRegex(ValueError, "符号链接"):
                        await self.tools["prepare_web_runtime"].ainvoke({})
                finally:
                    target.unlink()
            package.unlink()
            package.symlink_to(self.root / "outside")
            with self.assertRaisesRegex(ValueError, "符号链接"):
                await self.tools["prepare_web_runtime"].ainvoke({})
        spawn.assert_not_awaited()
        self.assertEqual(self.events, [])

    async def test_npm_timeout_always_stops_the_subprocess(self):
        self.run["stage"] = "test"
        self.write("package.json", b"{}")
        process = SimpleNamespace(returncode=None, communicate=AsyncMock(side_effect=asyncio.TimeoutError))
        with patch("app.services.workflow.production_tools.asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=process), \
                patch("app.services.workflow.production_tools.stop_process", new_callable=AsyncMock) as stop:
            with self.assertRaises(asyncio.TimeoutError):
                await self.tools["prepare_web_runtime"].ainvoke({})
        stop.assert_awaited_once_with(process)
        self.assertEqual(self.events, [])
