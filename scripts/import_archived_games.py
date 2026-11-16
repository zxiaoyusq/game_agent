"""导入本次四款游戏包，保留原始来源与目录，不执行附件里的初始化脚本。"""

import argparse
import hashlib
import html
import json
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
GAMES = {
    "Arrow_Out_Puzzle_Lite": {
        "slug": "arrow-out-puzzle-lite", "name": "箭头解谜 · Arrow Out Puzzle Lite",
        "category": "益智解谜", "description": "观察箭头的方向与阻挡关系，依次移出箭头，解开关卡。",
    },
    "Crazy_Knifes": {
        "slug": "crazy-knifes", "name": "疯狂飞刀 · Crazy Knifes",
        "category": "动作闯关", "description": "把握飞刀的节奏，挑战关卡中的目标。",
    },
    "Solitaire_Klondike_Classic": {
        "slug": "solitaire-klondike-classic", "name": "经典接龙 · Solitaire Klondike Classic",
        "category": "纸牌", "description": "经典克朗代克接龙：交替颜色整理纸牌，按花色完成归位。",
    },
    "Checkers_Pocket": {
        "slug": "checkers-pocket", "name": "口袋西洋跳棋 · Checkers Pocket", "category": "棋盘游戏",
        "description": "已收录上传的 Checkers Pocket 目录，等待补齐完整游戏。",
        "unavailable_reason": "上传目录只有插屏、激励广告的测试按钮，没有棋盘玩法脚本和美术资源，暂时无法游玩。",
    },
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    digest = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    host = ROOT / "scripts/game-import/browser-host.js"
    output = ROOT / "games"
    if any((output / game["slug"]).exists() for game in GAMES.values()):
        raise SystemExit("目标目录已存在，未覆盖现有游戏。")
    with ZipFile(args.archive) as archive, tempfile.TemporaryDirectory(prefix="import-games-") as temporary:
        staging = Path(temporary)
        counts = {folder: 0 for folder in GAMES}
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)
            # 忽略 macOS 附带项和所有 .git 等隐藏目录，不传播其配置或钩子。
            if not path.parts or path.parts[0] not in GAMES or any(part.startswith('.') for part in path.parts):
                continue
            if path.is_absolute() or '\\' in entry.filename or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("压缩包包含不安全路径或符号链接")
            if entry.is_dir():
                continue
            destination = staging / GAMES[path.parts[0]]["slug"] / "source" / Path(*path.parts[1:])
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(entry))
            counts[path.parts[0]] += 1
        for folder, metadata in GAMES.items():
            directory = staging / metadata["slug"]
            if not (directory / "source/game/index.html").is_file():
                raise ValueError(f"{folder} 缺少已核对的入口")
            # 缺少游戏本体的 Checkers 只存来源和说明，不发布广告按钮假入口。
            if not metadata.get("unavailable_reason"):
                dist = directory / "dist"
                shutil.copytree(directory / "source/game", dist / "game")
                shutil.copyfile(host, dist / "browser-host.js")
                title = html.escape(metadata["name"])
                description = html.escape(metadata["description"], quote=True)
                (dist / "index.html").write_text(f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title><meta name="description" content="{description}">
<style>html,body,.game{{width:100%;height:100%;margin:0;overflow:hidden;background:#17232b}}iframe{{display:block;width:100%;height:100%;border:0}}</style></head>
<body><div class="game"><iframe id="iframe" title="{title}" allow="autoplay; fullscreen" allowfullscreen></iframe></div><script src="./browser-host.js"></script></body></html>
''', encoding="utf-8")
            (directory / "game.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
            (directory / "import-manifest.json").write_text(json.dumps({
                "archive": args.archive.name, "sha256": digest, "source_folder": folder, "files": counts[folder],
                "notes": "原始文件保留在 source；过滤隐藏目录和 macOS 附带文件；运行版使用无广告浏览器外壳。",
            }, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
        # 所有条目准备好后再加入游戏目录，避免列表读到未复制完整的运行包。
        for metadata in GAMES.values():
            shutil.move(str(staging / metadata["slug"]), str(output / metadata["slug"]))
            print(f"已导入：{metadata['name']}")


if __name__ == "__main__":
    main()
