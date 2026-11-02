import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SKILL_DIR = Path(__file__).resolve().parents[1]
EXPORTER = SKILL_DIR / "scripts" / "spine_export.py"
PREVIEWER = SKILL_DIR / "scripts" / "make_preview.py"
CHROMA_REMOVER = SKILL_DIR / "scripts" / "remove_chroma_key.py"
EDGE_DECONTAMINATOR = SKILL_DIR / "scripts" / "decontaminate_alpha_edges.py"
PYTHON = sys.executable


class SpineExportCliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="spine-imagegen-test-"))
        self.parts_dir = self.temp_dir / "parts"
        self.parts_dir.mkdir()
        self.out_dir = self.temp_dir / "out"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def write_rgba_part(self, name, opaque=True):
        image = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
        if opaque:
            for x in range(2, 10):
                for y in range(2, 10):
                    image.putpixel((x, y), (220, 160, 90, 255))
        else:
            image = Image.new("RGBA", (12, 12), (220, 160, 90, 255))
        path = self.parts_dir / name
        image.save(path)
        return path

    def write_layout(self, parts):
        layout = {
            "name": "fixture",
            "canvas": {"width": 64, "height": 64},
            "idle": {"duration": 2.4},
            "parts": parts,
        }
        layout_path = self.temp_dir / "layout.json"
        layout_path.write_text(json.dumps(layout), encoding="utf-8")
        return layout_path

    def run_exporter(self, layout_path):
        return subprocess.run(
            [PYTHON, str(EXPORTER), "--layout", str(layout_path), "--out", str(self.out_dir)],
            text=True,
            capture_output=True,
            check=False,
        )

    def run_previewer(self, layout_path):
        return subprocess.run(
            [PYTHON, str(PREVIEWER), "--layout", str(layout_path), "--out", str(self.out_dir)],
            text=True,
            capture_output=True,
            check=False,
        )

    def run_chroma_remover(self, source_path, output_path):
        return subprocess.run(
            [PYTHON, str(CHROMA_REMOVER), "--input", str(source_path), "--output", str(output_path)],
            text=True,
            capture_output=True,
            check=False,
        )

    def run_edge_decontaminator(self, source_path, output_path):
        return subprocess.run(
            [PYTHON, str(EDGE_DECONTAMINATOR), "--input", str(source_path), "--output", str(output_path)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_exports_two_transparent_parts_to_spine_package_with_idle(self):
        tail = self.write_rgba_part("tail.png")
        body = self.write_rgba_part("body.png")
        layout_path = self.write_layout([
            {"name": "tail", "file": str(tail), "bone": "tail", "slot": "tail", "x": -8, "y": -4, "draw_order": 0, "idle_rotate": 7},
            {"name": "body", "file": str(body), "bone": "body", "slot": "body", "x": 0, "y": 0, "draw_order": 1, "idle_scale_y": 0.02},
        ])

        result = self.run_exporter(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.out_dir / "fixture.png").is_file())
        self.assertTrue((self.out_dir / "fixture.atlas").is_file())
        self.assertTrue((self.out_dir / "fixture.json").is_file())
        self.assertTrue((self.out_dir / "manifest.json").is_file())
        self.assertIn("tail", (self.out_dir / "fixture.atlas").read_text(encoding="utf-8"))
        self.assertIn("body", (self.out_dir / "fixture.atlas").read_text(encoding="utf-8"))
        skeleton = json.loads((self.out_dir / "fixture.json").read_text(encoding="utf-8"))
        self.assertIn("idle", skeleton["animations"])
        attachments = skeleton["skins"][0]["attachments"]
        self.assertIn("tail", attachments)
        self.assertIn("body", attachments)

    def test_writes_editor_images_for_spine_import_and_points_metadata_to_them(self):
        body = self.write_rgba_part("body.png")
        layout_path = self.write_layout([
            {"name": "body", "file": str(body), "bone": "body", "slot": "body", "x": 0, "y": 0, "draw_order": 0},
        ])

        result = self.run_exporter(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.out_dir / "images" / "body.png").is_file())
        skeleton = json.loads((self.out_dir / "fixture.json").read_text(encoding="utf-8"))
        self.assertEqual(skeleton["skeleton"]["images"], "images/")

    def test_orders_parent_bones_before_lower_draw_order_children(self):
        tail = self.write_rgba_part("tail.png")
        body = self.write_rgba_part("body.png")
        layout_path = self.write_layout([
            {"name": "tail", "file": str(tail), "bone": "tail", "parent": "body", "slot": "tail", "x": -8, "y": -4, "draw_order": 0},
            {"name": "body", "file": str(body), "bone": "body", "slot": "body", "x": 0, "y": 0, "draw_order": 1},
        ])

        result = self.run_exporter(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        skeleton = json.loads((self.out_dir / "fixture.json").read_text(encoding="utf-8"))
        self.assertEqual([bone["name"] for bone in skeleton["bones"]], ["root", "body", "tail"])

    def test_exports_named_extra_control_bones_with_length(self):
        body = self.write_rgba_part("body.png")
        layout_path = self.write_layout([
            {"name": "body", "file": str(body), "bone": "body", "parent": "pelvis", "slot": "body", "x": 0, "y": 0, "draw_order": 0},
        ])
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        layout["extra_bones"] = [
            {"name": "pelvis", "parent": "root", "x": -10, "y": -4, "length": 80},
            {"name": "neck", "parent": "pelvis", "x": 12, "y": 24, "length": 60},
        ]
        layout_path.write_text(json.dumps(layout), encoding="utf-8")

        result = self.run_exporter(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        skeleton = json.loads((self.out_dir / "fixture.json").read_text(encoding="utf-8"))
        bones = {bone["name"]: bone for bone in skeleton["bones"]}
        self.assertEqual(bones["pelvis"]["parent"], "root")
        self.assertEqual(bones["pelvis"]["length"], 80)
        self.assertEqual(bones["neck"]["parent"], "pelvis")
        self.assertEqual(bones["body"]["parent"], "pelvis")

    def test_rejects_part_without_any_transparent_pixels(self):
        opaque_body = self.write_rgba_part("opaque_body.png", opaque=False)
        layout_path = self.write_layout([
            {"name": "body", "file": str(opaque_body), "bone": "body", "slot": "body", "x": 0, "y": 0, "draw_order": 0},
        ])

        result = self.run_exporter(layout_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must contain both transparent and opaque pixels", result.stderr)

    def test_scales_a_trimmed_part_before_packing_when_layout_requests_it(self):
        body = self.write_rgba_part("body.png")
        layout_path = self.write_layout([
            {"name": "body", "file": str(body), "bone": "body", "slot": "body", "x": 0, "y": 0, "draw_order": 0, "image_scale": 2.0},
        ])

        result = self.run_exporter(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        skeleton = json.loads((self.out_dir / "fixture.json").read_text(encoding="utf-8"))
        attachment = skeleton["skins"][0]["attachments"]["body"]["body"]
        self.assertEqual(attachment["width"], 16)
        self.assertEqual(attachment["height"], 16)
        with Image.open(self.out_dir / "preview_parts" / "body.png") as normalized:
            self.assertEqual(normalized.size, (16, 16))

    def test_can_remove_disconnected_atlas_artifacts_when_layout_requests_cleanup(self):
        image = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
        image.putpixel((0, 0), (220, 160, 90, 255))
        for x in range(2, 10):
            for y in range(2, 10):
                image.putpixel((x, y), (220, 160, 90, 255))
        body = self.parts_dir / "body_with_artifact.png"
        image.save(body)
        layout_path = self.write_layout([
            {"name": "body", "file": str(body), "bone": "body", "slot": "body", "x": 0, "y": 0, "draw_order": 0, "keep_largest_component": True},
        ])

        result = self.run_exporter(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.out_dir / "preview_parts" / "body.png") as normalized:
            self.assertEqual(normalized.size, (8, 8))
            self.assertEqual(normalized.getpixel((0, 0)), (220, 160, 90, 255))

    def test_uses_the_requested_target_spine_version_in_export_metadata(self):
        body = self.write_rgba_part("body.png")
        layout_path = self.write_layout([
            {"name": "body", "file": str(body), "bone": "body", "slot": "body", "x": 0, "y": 0, "draw_order": 0},
        ])
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        layout["spine_version"] = "4.3.26"
        layout_path.write_text(json.dumps(layout), encoding="utf-8")

        result = self.run_exporter(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        skeleton = json.loads((self.out_dir / "fixture.json").read_text(encoding="utf-8"))
        self.assertEqual(skeleton["skeleton"]["spine"], "4.3.26")

    def test_emits_spine_38_skins_and_rotation_timeline_in_38_format(self):
        body = self.write_rgba_part("body.png")
        layout_path = self.write_layout([
            {"name": "body", "file": str(body), "bone": "body", "slot": "body", "x": 0, "y": 0, "draw_order": 0, "idle_rotate": 5},
        ])
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        layout["spine_version"] = "3.8.99"
        layout_path.write_text(json.dumps(layout), encoding="utf-8")

        result = self.run_exporter(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        skeleton = json.loads((self.out_dir / "fixture.json").read_text(encoding="utf-8"))
        self.assertIsInstance(skeleton["skins"], list)
        self.assertEqual(skeleton["skins"][0]["name"], "default")
        rotate = skeleton["animations"]["idle"]["bones"]["body"]["rotate"]
        self.assertIn("angle", rotate[1])
        self.assertNotIn("value", rotate[1])

    def test_builds_local_preview_for_every_exported_part(self):
        tail = self.write_rgba_part("tail.png")
        body = self.write_rgba_part("body.png")
        layout_path = self.write_layout([
            {"name": "tail", "file": str(tail), "bone": "tail", "slot": "tail", "x": -8, "y": -4, "draw_order": 0},
            {"name": "body", "file": str(body), "bone": "body", "slot": "body", "x": 0, "y": 0, "draw_order": 1},
        ])
        self.assertEqual(self.run_exporter(layout_path).returncode, 0)

        result = self.run_previewer(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        preview = self.out_dir / "preview.html"
        self.assertTrue(preview.is_file())
        markup = preview.read_text(encoding="utf-8")
        self.assertIn("preview_parts/tail.png", markup)
        self.assertIn("preview_parts/body.png", markup)
        self.assertIn("@keyframes", markup)

    def test_preview_preserves_parented_part_world_position(self):
        tail = self.write_rgba_part("tail.png")
        body = self.write_rgba_part("body.png")
        layout_path = self.write_layout([
            {"name": "body", "file": str(body), "bone": "body", "slot": "body", "x": 10, "y": 0, "draw_order": 0},
            {"name": "tail", "file": str(tail), "bone": "tail", "parent": "body", "slot": "tail", "x": 10, "y": 0, "draw_order": 1},
        ])
        self.assertEqual(self.run_exporter(layout_path).returncode, 0)

        result = self.run_previewer(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.out_dir / "preview.png") as preview:
            self.assertEqual(preview.getpixel((50, 32)), (220, 160, 90, 255))

    def test_removes_flat_green_background_without_erasing_character_color(self):
        source = Image.new("RGB", (4, 4), (0, 255, 0))
        source.putpixel((2, 2), (220, 160, 90))
        source_path = self.temp_dir / "green_screen.png"
        output_path = self.temp_dir / "cutout.png"
        source.save(source_path)

        result = self.run_chroma_remover(source_path, output_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(output_path) as cutout:
            self.assertEqual(cutout.mode, "RGBA")
            self.assertEqual(cutout.getpixel((0, 0))[3], 0)
            self.assertEqual(cutout.getpixel((2, 2)), (220, 160, 90, 255))

    def test_decontaminates_white_matte_on_soft_and_opaque_outer_edges(self):
        source = Image.new("RGBA", (7, 7), (0, 0, 0, 0))
        for y in range(1, 6):
            for x in range(1, 6):
                source.putpixel((x, y), (255, 250, 239, 255))
        for y in range(2, 5):
            for x in range(2, 5):
                source.putpixel((x, y), (220, 160, 90, 255))
        source.putpixel((1, 3), (255, 250, 239, 128))
        source_path = self.temp_dir / "white_matte.png"
        output_path = self.temp_dir / "decontaminated.png"
        source.save(source_path)

        result = self.run_edge_decontaminator(source_path, output_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(output_path) as cleaned:
            self.assertEqual(cleaned.getpixel((1, 3)), (220, 160, 90, 128))
            self.assertEqual(cleaned.getpixel((1, 2)), (220, 160, 90, 255))

    def test_decontamination_preserves_unrelated_opaque_white_details(self):
        source = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
        for y in range(1, 8):
            for x in range(1, 8):
                source.putpixel((x, y), (220, 160, 90, 255))
        source.putpixel((4, 4), (255, 255, 255, 255))
        source_path = self.temp_dir / "white_detail.png"
        output_path = self.temp_dir / "white_detail_clean.png"
        source.save(source_path)

        result = self.run_edge_decontaminator(source_path, output_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(output_path) as cleaned:
            self.assertEqual(cleaned.getpixel((4, 4)), (255, 255, 255, 255))

    def test_exporter_can_decontaminate_trimmed_editor_images_without_touching_sources(self):
        source = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
        for y in range(2, 7):
            for x in range(2, 7):
                source.putpixel((x, y), (255, 250, 239, 255))
        for y in range(3, 6):
            for x in range(3, 6):
                source.putpixel((x, y), (220, 160, 90, 255))
        source_path = self.parts_dir / "matte_body.png"
        source.save(source_path)
        layout_path = self.write_layout([
            {
                "name": "body",
                "file": str(source_path),
                "bone": "body",
                "slot": "body",
                "x": 0,
                "y": 0,
                "draw_order": 0,
            },
        ])
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        layout["decontaminate_edges"] = True
        layout_path.write_text(json.dumps(layout), encoding="utf-8")

        result = self.run_exporter(layout_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.out_dir / "images" / "body.png") as cleaned:
            self.assertEqual(cleaned.getpixel((0, 1)), (220, 160, 90, 255))
        with Image.open(source_path) as original:
            self.assertEqual(original.getpixel((2, 3)), (255, 250, 239, 255))


if __name__ == "__main__":
    unittest.main()
