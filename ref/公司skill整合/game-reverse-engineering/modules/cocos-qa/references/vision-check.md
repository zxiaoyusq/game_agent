# Screenshot acceptance and delivery sync
> **何时读我**：要用截图判断画面有没有过关 / 当前模型没有原生视觉能力 / 截图出现黑边、拉伸、像素化或文字被裁切 / 交付前要同步截图和产物
> **读完能做到**：判断该直接看图还是调视觉技能，用现成模板向视觉模型提问，按清单逐轮核对 Web 与设备截图，并跑交付同步脚本归档产物
> **范围**：`CASE_ONLY_BLOCKUDOKU` + `GENERALIZED_PATTERN`

## Table of contents

- When to use the vision skill

- vision_analyze.py usage

- Acceptance prompt templates

- Screenshot verification checklist

- Delivery sync (sync_delivery.ps1)

## 1. When to use the vision skill

- Models with native vision (GPT-5.x family, `gpt-5.6-*`) must inspect  
screenshots directly (`view_image` or rendering the image in the reply).

- Models without native vision (e.g. `gpt-5.2` / deepseek via himodels relay)  
must use the vision-analysis skill:  
`${HARNESS_CODEX}\vision-analysis\SKILL.md`.

Rule from the user: **when the image preview tool is unavailable, call the  
vision skill.** Never guess the content of a screenshot.

## 2. vision_analyze.py usage

```powershell
python "${HARNESS_CODEX}\vision-analysis\scripts\vision_analyze.py" `
--image "" --prompt "" --json
```

- `--prompt` defaults to detailed description; `--json` gives  
`{"success": true, "analysis": "...", ...}`.

- API key auto-loads from `XIAOMI_API_KEY` / `C:\Users\Administrator\.codex\.env`  
/ `E:\hermes\.env`; no manual key needed.

- Large images are auto-downscaled and retried; timeout is 120s.

## 3. Acceptance prompt templates (Chinese)

Main menu / layout:

```
这是一张 Blockudoku 游戏截图。请检查：1) 画面是否出现左右黑边或上下黑边；
2) 主菜单元素（logo、按钮、方块预览）是否居中且无错位；3) 是否有噪点、模糊或
像素化；4) 按钮文字是否可读、是否被裁切。
```

Color consistency:

```
请检查棋盘上已放置的方块颜色与底部托盘对应方块颜色是否一致，列出你看到的所有颜色。
```

Game board / line clear:

```
请描述棋盘状态：已放置多少方块、是否有整行或整列被消除、消除动画是否出现、
分数区域显示的数字是多少。
```

Device screenshot:

```
这是安卓模拟器截图。请确认游戏界面完整显示、无黑边、无拉伸变形，触摸目标
（托盘方块、按钮）尺寸正常且不重叠。
```

## 4. Screenshot verification checklist

For each screenshot round, confirm:

- Web shots (13 files from `qa_driver.js`) and device shots (MuMu) both exist  
and are fresh (not stale from an older build).

- No letterbox bars, no stretching, no pixelated/generated-text artifacts.

- Layout matches the 1:1 target: board centered, 3 tray slots evenly spaced,  
HUD visible at top.

- Placed-block colors match tray colors on both web and device.

- Key flows visible in the shot set: menu, game start, placement, streak/clear,  
game over + second chance, settings, daily panel, all-clear.

## 5. Delivery sync (sync_delivery.ps1)

Canonical script: `work\sync_delivery.ps1` (session-specific, not bundled).  
It performs, in order:

1. Replace `outputs\BlockudokuWebBuild` with a fresh copy of  
`E:\gameprogram\Blockudoku\build\web-mobile`.

1. Clean `build`/`library`/`temp`/`local` caches from the delivered project  
copy (`outputs\BlockudokuProject`).

1. Copy `Blockudoku-release.apk` and `debug.keystore` into  
`outputs\BlockudokuApk`.

1. Organize screenshots into `outputs\qa_screenshots` with the canonical  
names (web: `01_main_menu`...`14_all_clear`, device:  
`15_device_menu_tutorial`...`22_device_release_game`).

Outputs layout after sync:

```
outputs  
BlockudokuProject\      # source project (caches cleaned)
BlockudokuWebBuild\     # runnable web build
BlockudokuApk\          # signed release APK + keystore
qa_screenshots\         # renamed acceptance screenshots
Blockudoku_交接文档.md    # handover document (session-specific)
```

Run it only after both build and device QA pass, then re-verify the copied web  
build serves (`http.server` on the outputs copy) and the APK hash matches.
