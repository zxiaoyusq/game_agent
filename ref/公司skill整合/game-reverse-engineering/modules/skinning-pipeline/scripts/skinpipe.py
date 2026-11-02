#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""game-skinning-pipeline unified CLI.

Subcommands: manifest | atlas-extract | atlas-rebuild | map | apply | rollback |
             diff | verify | fixtures | selftest

Exit codes: 0=ok, 1=execution failure, 2=warning with --fail-on-warning,
            3=invalid input, 4=ambiguous requiring manual confirmation.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path

from common import (
    EXIT_FAIL, EXIT_INVALID, EXIT_OK, SCRIPT_VERSION, Logger, image_info,
    now_iso, write_json, write_utf8,
)


def write_png(path: Path, width: int, height: int, rgba: tuple) -> None:
    """Minimal dependency-free PNG writer (RGBA, 8-bit) for fixtures."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(b"\x00" + bytes(rgba) * width for _ in range(height))
    def chunk(typ: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    path.write_bytes(png)


def cmd_fixtures(args, logger) -> int:
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)

    # --- tiny Cocos project with special filenames ---
    proj = root / "cocos-mini-project"
    ui = proj / "assets" / "resources" / "UI"
    names = ["btn_play", "Sprite 中文 测试 (括号)", "emoji\U0001F3A8icon"]
    for i, name in enumerate(names):
        write_png(ui / (name + ".png"), 32, 32, (40 + i * 40, 90, 200, 255))
        meta = {
            "ver": "2.3.7", "uuid": "aaaaaaaa-0000-0000-0000-00000000000%d" % i,
            "importer": "texture", "type": "sprite", "packable": True,
            "width": 32, "height": 32,
            "subMetas": {
                name: {
                    "ver": "1.0.6",
                    "uuid": "bbbbbbbb-0000-0000-0000-00000000000%d" % i,
                    "importer": "sprite-frame",
                    "rawTextureUuid": "aaaaaaaa-0000-0000-0000-00000000000%d" % i,
                    "rotated": False, "width": 32, "height": 32,
                    "rawWidth": 32, "rawHeight": 32,
                }
            },
        }
        write_json(ui / (name + ".png.meta"), meta)
    write_json(proj / "project.json", {"version": "2.4.13", "name": "mini-fixture"})
    write_json(proj / "assets" / "Main.fire",
               [{"__type__": "cc.SceneAsset", "_name": "Main"}])

    # --- synthetic Cocos atlas + index ---
    atlas_dir = root / "cocos-atlas"
    atlas_dir.mkdir(parents=True, exist_ok=True)
    atlas_png = atlas_dir / "ui_atlas_1.png"
    rects = {"sprite_a": (0, 0, 64, 64), "sprite_b": (128, 0, 64, 64),
             "sprite_c": (0, 128, 64, 64), "sprite_d": (128, 128, 64, 64)}
    img = [[(0, 0, 0, 0)] * 192 for _ in range(192)]
    colors = {"sprite_a": (255, 0, 0, 255), "sprite_b": (0, 255, 0, 255),
              "sprite_c": (0, 0, 255, 255), "sprite_d": (255, 255, 0, 255)}
    for name, (x, y, w, h) in rects.items():
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                img[yy][xx] = colors[name]
    raw = b"".join(b"\x00" + b"".join(bytes(px) for px in row) for row in img)
    def chunk(typ: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", 192, 192, 8, 6, 0, 0, 0)
    atlas_png.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                          + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

    meta = {"ver": "2.3.7", "uuid": "cccccccc-0000-0000-0000-000000000000",
            "importer": "texture", "type": "sprite", "packable": True,
            "subMetas": {}}
    index_sprites = []
    for name, (x, y, w, h) in sorted(rects.items()):
        sub = "dddddddd-0000-0000-0000-%012d" % (len(meta["subMetas"]) + 1)
        meta["subMetas"][name] = {
            "ver": "1.0.6", "uuid": sub, "importer": "sprite-frame",
            "rawTextureUuid": meta["uuid"], "rotated": False,
            "width": w, "height": h, "rawWidth": w, "rawHeight": h,
            "borderTop": 0, "borderBottom": 0, "borderLeft": 0, "borderRight": 0,
        }
        index_sprites.append({
            "asset_id": sub, "name": name, "type": "SpriteFrame",
            "src": "ui_atlas_1/%s.png" % name, "atlas": "ui_atlas_1",
            "atlas_rect": {"x": x, "y": y, "w": w, "h": h},
            "sprite_meta": {"rotated": False, "trimmed": False,
                            "source_size": [w, h], "offset": [0, 0],
                            "pivot": [0.5, 0.5], "border": [0, 0, 0, 0],
                            "pixels_per_unit": 100},
            "uuid": meta["uuid"], "sub_uuid": sub,
            "needs_manual_review": False, "review_reason": [],
            "output": "sprites/%s.png" % sub,
        })
    write_json(atlas_dir / "ui_atlas_1.png.meta", meta)
    write_json(atlas_dir / "atlas_extract" / "index.json", {
        "schema_version": "1.0", "manifest": "asset_manifest.json",
        "generated_at": now_iso(), "sprites": index_sprites,
        "atlases": [{"name": "ui_atlas_1", "file": "ui_atlas_1.png",
                     "sprite_count": 4,
                     "sprites": [s["asset_id"] for s in index_sprites],
                     "rects_known": True, "note": None}],
        "warnings": [],
    })

    # --- new art for atlas rebuild + mapping tests ---
    new_art = root / "new_art"
    write_png(new_art / "sprite_a.png", 64, 64, (200, 30, 30, 255))
    write_png(new_art / "sprite_b.png", 64, 64, (30, 200, 30, 255))
    write_png(new_art / "sprite_b_big.png", 96, 96, (30, 200, 30, 255))
    write_png(new_art / "unused_icon.png", 16, 16, (100, 100, 100, 255))
    write_png(new_art / "Sprite 中文 测试 (括号).png", 32, 32, (10, 10, 200, 255))
    write_png(new_art / "emoji\U0001F3A8icon.png", 32, 32, (200, 10, 10, 255))
    # rotated/trimmed test fixtures
    rot = atlas_dir / "atlas_extract" / "rotated_child.json"
    write_json(rot, {
        "schema_version": "1.0", "generated_at": now_iso(),
        "sprites": [{
            "asset_id": "eeeeeeee-0000-0000-0000-000000000001",
            "name": "rot_child", "type": "SpriteFrame", "src": "rot.png",
            "atlas": "ui_atlas_1",
            "atlas_rect": {"x": 64, "y": 0, "w": 64, "h": 64},
            "sprite_meta": {"rotated": True, "trimmed": True,
                            "source_size": [64, 64], "offset": [0, 0],
                            "pivot": [0.5, 0.5], "border": [0, 0, 0, 0]},
            "uuid": "cccccccc-0000-0000-0000-000000000000",
            "sub_uuid": "eeeeeeee-0000-0000-0000-000000000001",
            "needs_manual_review": True, "review_reason": ["rotated", "trimmed"],
            "output": "sprites/rot.png",
        }],
        "atlases": [],
        "warnings": [],
    })

    logger.info("fixtures 写入: %s" % root)
    logger.info("  cocos-mini-project: 特殊文件名(中文/空格/括号/emoji) + meta")
    logger.info("  cocos-atlas: ui_atlas_1.png + meta + atlas_extract/index.json")
    logger.info("  new_art: sprite_a/sprite_b/尺寸不一致/unused/特殊文件名")
    return EXIT_OK


def cmd_selftest(args, logger) -> int:
    import tempfile
    from common import (
        find_uuids, norm_key, norm_name, file_hash, read_json, write_json,
        UUID_RE,
    )
    tmp = Path(tempfile.mkdtemp(prefix="skinpipe_selftest_"))
    fails = []
    # png header
    p = tmp / "t.png"
    write_png(p, 17, 9, (1, 2, 3, 255))
    info = image_info(p)
    if info != {"width": 17, "height": 9, "bit_depth": 8, "color_type": 6, "interlace": 0}:
        fails.append("png_info: %s" % info)
    # hash determinism + streaming
    if file_hash(p) != file_hash(p):
        fails.append("hash not deterministic")
    # json roundtrip with Chinese
    j = tmp / "t.json"
    write_json(j, {"中文": "换皮流水线", "path": "E:/下载/游戏"})
    if read_json(j)["中文"] != "换皮流水线":
        fails.append("json roundtrip")
    # uuid regex
    if not UUID_RE.match("3319fb8c-8fa5-4508-be6a-c9a40dc121b3"):
        fails.append("uuid regex")
    # normalization
    if norm_key("A\\B.PNG") != "a/b.png" or norm_name("Btn_Play - 2") != "btnplay2":
        fails.append("norm")
    if fails:
        logger.error("selftest FAILED: %s" % fails)
        return EXIT_FAIL
    logger.info("selftest OK（png header/hash/json 中文/uuid/norm 全部通过）")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skinpipe.py",
        description="游戏美术换皮流水线 (game-skinning-pipeline) v%s" % SCRIPT_VERSION)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--verbose", action="store_true", default=argparse.SUPPRESS,
                        help="输出扫描/匹配细节")
    common.add_argument("--fail-on-warning", action="store_true", default=argparse.SUPPRESS,
                        help="存在 warning 时以退出码 2 失败（CI/验收用）")
    common.add_argument("--json-log", type=Path, default=argparse.SUPPRESS,
                        help="追加写入机器可读 JSON 日志")
    parser.add_argument("--verbose", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--fail-on-warning", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--json-log", type=Path, default=None, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("manifest", parents=[common], help="扫描目录生成 asset_manifest.json")
    p.add_argument("--input", required=True)
    p.add_argument("--engine", choices=["unity-il2cpp", "unity", "cocos-2.4", "cocos-3.x"],
                   default=None)
    p.add_argument("--game", default=None)
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--include-dir", action="append", default=[])
    p.add_argument("--exclude-dir", action="append", default=[])

    p = sub.add_parser("atlas-extract", parents=[common], help="从 manifest 生成图集记录 atlas_extract/index.json")
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", type=Path, default=None)

    p = sub.add_parser("atlas-rebuild", parents=[common], help="把新单图按原 rect 原位贴回图集 PNG")
    p.add_argument("--index", required=True)
    p.add_argument("--atlas", required=True)
    p.add_argument("--new-assets", required=True)
    p.add_argument("--skin-map", type=Path, default=None)
    p.add_argument("--output", type=Path, default=None,
                   help="重建后的图集 PNG 输出路径（省略且 --in-place 时原位覆盖；"
                        "报告文件自动写在图集同名目录下 atlas_rebuild_report.md）")
    p.add_argument("--in-place", action="store_true",
                   help="原位覆盖原图集 PNG（必须先 --execute；备份写入 --backup-dir）")
    p.add_argument("--backup-dir", type=Path, default=None)
    p.add_argument("--allow-resize", action="store_true")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--execute", dest="dry_run", action="store_false")
    p.add_argument("--fail-on-manual", action="store_true")

    p = sub.add_parser("map", parents=[common], help="生成 skin_map.json 替换映射")
    p.add_argument("--manifest", required=True)
    p.add_argument("--new-assets", required=True)
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--aliases", type=Path, default=None)
    p.add_argument("--allow-format-change", action="store_true")
    p.add_argument("--fail-on-ambiguous", action="store_true")

    p = sub.add_parser("apply", parents=[common], help="按 skin_map 替换资源（默认 dry-run，--execute 才写入）")
    p.add_argument("--skin-map", required=True)
    p.add_argument("--root", type=Path, default=None,
                   help="源资源根目录（skin_map 中 src 为相对路径时用于解析）")
    p.add_argument("--backup-dir", type=Path, default=None)
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--execute", dest="dry_run", action="store_false")

    p = sub.add_parser("rollback", parents=[common], help="从 backup index 恢复原文件（默认 dry-run）")
    p.add_argument("--backup-dir", required=True)
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--execute", dest="dry_run", action="store_false")

    p = sub.add_parser("diff", parents=[common], help="对比 before/after manifest 输出 skin_diff")
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--skin-map", type=Path, default=None)
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--json", type=Path, default=None)

    p = sub.add_parser("verify", parents=[common], help="替换后完整性/构建验证")
    p.add_argument("--manifest", required=True)
    p.add_argument("--engine", default=None)
    p.add_argument("--source-root", type=Path, default=None)
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--cocos-build", type=Path, default=None,
                   help="CocosCreator.exe 路径；传入则执行 web-mobile CLI 构建")

    p = sub.add_parser("fixtures", parents=[common], help="生成合成测试数据（图集/新素材/特殊文件名）")
    p.add_argument("--output", required=True, type=Path)

    p = sub.add_parser("selftest", parents=[common], help="common 单元自检（不依赖第三方包）")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logger = Logger(verbose=args.verbose, json_log=args.json_log,
                    fail_on_warning=args.fail_on_warning)
    handlers = {
        "manifest": lambda: _run("manifest", args, logger),
        "atlas-extract": lambda: _run("atlas_extract", args, logger),
        "atlas-rebuild": lambda: _run("atlas_rebuild", args, logger),
        "map": lambda: _run("map", args, logger),
        "apply": lambda: _run("apply", args, logger),
        "rollback": lambda: _run("rollback", args, logger),
        "diff": lambda: _run("diff", args, logger),
        "verify": lambda: _run("verify", args, logger),
        "fixtures": lambda: cmd_fixtures(args, logger),
        "selftest": lambda: cmd_selftest(args, logger),
    }
    try:
        return handlers[args.command]()
    except SystemExit as e:
        return int(e.code or 0)
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # noqa: BLE001
        logger.error("执行失败: %s" % e)
        return EXIT_FAIL


def _run(name, args, logger) -> int:
    import atlas, diff_report, manifest, mapping, replace, verify  # noqa: PLC0415
    mod = {"manifest": manifest, "atlas_extract": atlas, "atlas_rebuild": atlas,
           "map": mapping, "apply": replace, "rollback": replace,
           "diff": diff_report, "verify": verify}[name]
    fn = {"manifest": "run_manifest", "atlas_extract": "run_atlas_extract",
          "atlas_rebuild": "run_atlas_rebuild", "map": "run_map",
          "apply": "run_apply", "rollback": "run_rollback",
          "diff": "run_diff", "verify": "run_verify"}[name]
    return getattr(mod, fn)(args, logger)


if __name__ == "__main__":
    sys.exit(main())
