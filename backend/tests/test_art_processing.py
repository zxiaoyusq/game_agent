"""确定性美术后处理：真实像素、透明边缘、文件来源与工作区边界。"""

import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app.services.workflow import art_processing
from app.services.workflow.production_tools import create_production_tools


def encode(image, format="PNG", **options):
    """以真实编码图片构造测试输入，不使用图片解码替身。"""
    output = io.BytesIO()
    image.save(output, format, **options)
    return output.getvalue()


class ArtProcessingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / "project"
        self.workspace.mkdir()
        self.run = {"stage": "art"}
        self.events = []
        self.tools = {tool.name: tool for tool in create_production_tools(
            self.workspace, self.run, lambda *event: self.events.append(event))}
        # 同时含不透明、半透明和透明像素，能发现重复alpha混合及错误裁切。
        self.image = Image.new("RGBA", (4, 2))
        self.image.putdata([(240, 10, 20, 255), (30, 40, 50, 128), (60, 70, 80, 0), (90, 100, 110, 255),
                            (120, 130, 140, 64), (150, 160, 170, 255), (180, 190, 200, 192), (210, 220, 230, 0)])
        self.original = encode(self.image)
        self.source = self.write("reference-assets/atlas.png", self.original)

    def write(self, relative, content):
        path = self.workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def process(self, **options):
        return json.loads(self.tools["process_art_image"].invoke({
            "source_path": "reference-assets/atlas.png", "destination": "public/assets/piece.png", **options}))

    def test_crop_preserves_exact_rgba_and_records_input_output_evidence(self):
        result = self.process(crop=[1, 0, 2, 2])
        target = self.workspace / result["path"]
        with Image.open(target) as actual:
            self.assertEqual(actual.size, (2, 2))
            self.assertEqual(actual.convert("RGBA").tobytes(), self.image.crop((1, 0, 3, 2)).tobytes())
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(result["source_sha256"], hashlib.sha256(self.original).hexdigest())
        self.assertEqual(result["sha256"], hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual(result["alpha"]["transparent_pixels"], 1)
        self.assertEqual(result["alpha"]["opaque_pixels"], 1)
        self.assertEqual(result["alpha"]["semitransparent_pixels"], 2)
        self.assertEqual(result["resize_mode"], "none")
        self.assertEqual(result["provenance"], "deterministic_image_processing")
        self.assertEqual(self.events[0], ("image_processed", "图片已按明确矩形和尺寸处理并保存", result))
        self.assertEqual([event[0] for event in self.events], ["image_processed"])

    def test_contain_centers_without_stretch_or_squared_alpha(self):
        result = self.process(target_size=[4, 4])
        self.assertEqual(result["content_size"], [4, 2])
        self.assertEqual(result["offset"], [0, 1])
        with Image.open(self.workspace / result["path"]) as actual:
            self.assertEqual(actual.size, (4, 4))
            self.assertEqual(actual.crop((0, 1, 4, 3)).tobytes(), self.image.tobytes())
            self.assertEqual(actual.getpixel((1, 1)), (30, 40, 50, 128))
            self.assertEqual(actual.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(result["alpha"]["transparent_pixels"], 10)

    def test_resize_uses_real_lanczos_and_webp_is_lossless(self):
        result = self.process(target_size=[8, 8], destination="public/assets/piece.webp")
        self.assertEqual(result["content_size"], [8, 4])
        self.assertEqual(result["offset"], [0, 2])
        expected = self.image.resize((8, 4), Image.Resampling.LANCZOS)
        with Image.open(self.workspace / result["path"]) as actual:
            self.assertEqual(actual.format, "WEBP")
            self.assertEqual(actual.convert("RGBA").crop((0, 2, 8, 6)).tobytes(), expected.tobytes())
        self.assertGreater(result["alpha"]["semitransparent_pixels"], 0)

    def test_jpeg_input_gets_opaque_alpha_without_guessing_background(self):
        content = encode(Image.new("RGB", (3, 2), (250, 250, 250)), "JPEG")
        self.write("reference-assets/white.jpg", content)
        result = self.process(source_path="reference-assets/white.jpg")
        self.assertEqual(result["alpha"]["opaque_pixels"], 6)
        self.assertEqual(result["alpha"]["transparent_pixels"], 0)

    def test_supported_real_formats_override_source_extensions_and_keep_alpha(self):
        """Cocos伪扩展只改变文件名；精确裁切仍保留真实解码RGBA及来源字节。"""
        for index, (name, format) in enumerate([("cocos.png", "WEBP"), ("named-jpeg.jpg", "PNG")]):
            content = encode(self.image, format, **({"lossless": True, "exact": True} if format == "WEBP" else {}))
            source = self.write(f"reference-assets/{name}", content)
            result = self.process(source_path=f"reference-assets/{name}", crop=[1, 0, 2, 2],
                                  destination=f"public/assets/decoded-{index}.png")
            expected = self.image.crop((1, 0, 3, 2))
            with Image.open(self.workspace / result["path"]) as actual:
                self.assertEqual(actual.format, "PNG")
                self.assertEqual(actual.convert("RGBA").tobytes(), expected.tobytes())
            self.assertEqual(result["input_format"], format)
            self.assertEqual(result["alpha"]["sha256"], hashlib.sha256(expected.getchannel("A").tobytes()).hexdigest())
            self.assertEqual(result["source_sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(source.read_bytes(), content)

    def test_stage_and_strict_coordinate_validation_fail_without_writes(self):
        for stage in ["prototype", "code", "test", None]:
            self.run["stage"] = stage
            with self.subTest(stage=stage), self.assertRaisesRegex(ValueError, "美术阶段"):
                self.process()
        self.run["stage"] = "art"
        for options in [
            {"crop": [0, 0, 1]}, {"crop": [-1, 0, 1, 1]}, {"crop": [0, 0, 0, 1]},
            {"crop": [3, 0, 2, 2]}, {"crop": [0, 1, 2, 2]}, {"crop": [False, 0, 1, 1]},
            {"crop": [0.5, 0, 1, 1]}, {"crop": ["0", 0, 1, 1]},
            {"target_size": []}, {"target_size": [0, 1]}, {"target_size": [8193, 1]},
            {"target_size": [8192, 8192]}, {"target_size": [True, 1]},
        ]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.process(**options)
        self.assertFalse((self.workspace / "public").exists())
        self.assertEqual(self.events, [])

    def test_paths_symlinks_and_existing_candidates_are_protected(self):
        self.write("public/assets/existing.png", "已有候选".encode())
        (self.workspace / "reference-assets/linked.png").symlink_to(self.source)
        (self.workspace / "public/assets/external").symlink_to(self.root, target_is_directory=True)
        for path in ["../atlas.png", "/atlas.png", "reference-assets/.hidden.png", "reference-assets/linked.png",
                     "reference-assets/./atlas.png", "reference-assets//atlas.png", "reference-assets\\atlas.png"]:
            with self.subTest(source=path), self.assertRaises(ValueError):
                self.process(source_path=path)
        for path in ["assets/out.png", "public/assets/../out.png", "public/assets/out.jpg", "public/assets/existing.png",
                     "public/assets/external/out.png", "public/assets/.hidden.png", "public/assets/out.png\n"]:
            with self.subTest(destination=path), self.assertRaises(ValueError):
                self.process(destination=path)
        self.assertEqual((self.workspace / "public/assets/existing.png").read_bytes(), "已有候选".encode())
        self.assertFalse((self.root / "out.png").exists())
        self.assertEqual(self.events, [])

    def test_file_types_size_pixels_and_multiple_frames_are_rejected(self):
        self.write("reference-assets/fake.png", b"not-image")
        self.write("reference-assets/unsupported.png", encode(self.image, "BMP"))
        self.write("reference-assets/broken.png", self.original[:40])
        oversized = self.workspace / "reference-assets/large.png"
        with oversized.open("wb") as file:
            file.truncate(10_000_001)
        self.write("reference-assets/wide.png", encode(Image.new("RGB", (8193, 1))))
        animated = encode(Image.new("RGBA", (2, 2), (255, 0, 0, 255)), "WEBP", save_all=True,
                          append_images=[Image.new("RGBA", (2, 2), (0, 0, 255, 255))], duration=100, loop=0)
        self.write("reference-assets/animated.webp", animated)
        for name in ["fake.png", "unsupported.png", "broken.png", "large.png", "wide.png", "animated.webp", "missing.png"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.process(source_path=f"reference-assets/{name}")
        with patch.object(art_processing, "MAX_IMAGE_PIXELS", 7), self.assertRaisesRegex(ValueError, "像素限制"):
            self.process()
        self.assertFalse((self.workspace / "public").exists())
        self.assertEqual(self.events, [])

    def test_processing_cannot_overwrite_or_follow_a_new_output_link(self):
        real_process = art_processing.process_image_bytes

        def create_candidate(*args, **kwargs):
            self.write("public/assets/piece.png", "并发候选".encode())
            return real_process(*args, **kwargs)

        with patch.object(art_processing, "process_image_bytes", side_effect=create_candidate), self.assertRaises(FileExistsError):
            self.process()
        self.assertEqual((self.workspace / "public/assets/piece.png").read_bytes(), "并发候选".encode())
        self.assertEqual(self.events, [])

        def create_link(*args, **kwargs):
            (self.workspace / "public/assets/link").symlink_to(self.root, target_is_directory=True)
            return real_process(*args, **kwargs)

        with patch.object(art_processing, "process_image_bytes", side_effect=create_link), self.assertRaisesRegex(ValueError, "符号链接"):
            self.process(destination="public/assets/link/out.png")
        self.assertFalse((self.root / "out.png").exists())
        self.assertEqual(self.events, [])


if __name__ == "__main__":
    unittest.main()
