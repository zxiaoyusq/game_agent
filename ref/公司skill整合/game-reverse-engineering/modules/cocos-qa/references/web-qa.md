# Web QA: headless Chrome CDP acceptance
> **何时读我**：要跑 headless Chrome 自动验收 / 要接 36 项检查或真实拖动探针 / 怀疑截图来自旧构建或 localStorage 残留造成假通过 / 要规范截图的存放和命名
> **读完能做到**：起服务连 CDP，用 `modules/cocos-qa/scripts/qa_driver.js` 与 `modules/cocos-qa/scripts/qa_drag_v2.js` 拿到 36/36 与 DRAG PLACE OK，并把 13 张 Web 验收截图按规范命名存进指定目录
> **范围**：`CASE_ONLY_BLOCKUDOKU` + `GENERALIZED_PATTERN`

## Table of contents

- What the harness does

- start_qa.ps1

- The 36-check driver (qa_driver.js)

- The real-drag probe (qa_drag_v2.js)

- Run sequence and expected output

- Screenshot naming and storage

## 1. What the harness does

`start_qa.ps1` starts two processes, then Node drivers talk to Chrome over the  
Chrome DevTools Protocol (CDP) on port 9224:

1. `python -m http.server 8123 --directory E:\gameprogram\Blockudoku\build\web-mobile`

2. Headless Chrome opening `http://127.0.0.1:8123/index.html` with a fresh  
`--user-data-dir` profile and `--window-size=720,1280`.

The drivers inject JS into the page through `Runtime.evaluate`. The game  
exposes a debug API on `window.__blockudoku` (state getters/setters and action  
helpers) plus `window.__bootReady`, which the checks rely on.

## 2. start_qa.ps1

Run from the work dir; prints Chrome PID, profile path, and `CDP OK` when port  
9224 responds. Key details:

- `--headless=new`, `--no-sandbox`, `--disable-gpu`, `--remote-debugging-port=9224`.

- Fresh profile per run (`chrome_profile_qa_HHmmss`) to avoid localStorage  
carry-over between runs.

- If `CDP not ready` appears, wait a few seconds and re-check  
`http://127.0.0.1:9224/json/version` before failing.

## 3. The 36-check driver (qa_driver.js)

`modules/cocos-qa/scripts/qa_driver.js` connects to the page target, then:

1. Forces a 720x1280 viewport with  
`Emulation.setDeviceMetricsOverride {width:720,height:1280,deviceScaleFactor:1,mobile:false}`  
**then reloads** — without this the SHOW_ALL canvas letterboxes.

1. Waits for boot: `window.cc && cc.find('Canvas') && window.__bootReady`.

2. Runs the checks below and screenshots each stage to `SHOT_DIR`  
(env `SHOT_DIR` or `qa_shots` next to the script).

Check list (36 assertions):

| # | Check |
|---|---|
| 1 | main menu reachable (logo, new game, settings, howto, sound, active) |
| 2 | tutorial overlay shows on first launch (text, hand, skip button) |
| 3 | tutorial completes and hides after 3 next-clicks |
| 4 | new game: 81 cells + 3 slots + score 0, not game over |
| 5 | 1:1 layout: cell 38px, board 356, slot 100, slot gap 220, pitch 38 |
| 6 | place block at (0,0) succeeds |
| 7 | score gain equals placed cell count |
| 8 | color consistency: placed cells keep the tray color |
| 9 | line clear: +3 cells +10 match = gain 13, groups 1, matched 9 |
| 10 | row 0 cleared to 000000000 |
| 11 | score after line clear = 13 |
| 12 | streak: 3 groups cleared simultaneously |
| 13 | streak combo: 4 cells + 30 match + 27 streak + 25 GreekPi = 86 |
| 14 | game-over detection: no piece fits anywhere |
| 15 | greedy fill placed pieces (natural game over path) |
| 16 | game over detected |
| 17 | best score recorded |
| 18 | second chance button present |
| 19 | second chance: board cleared, score kept, panel gone |
| 20 | back to menu: continue available + best shown |
| 21 | continue resumes saved score |
| 22 | sound toggle works (AudioManager sync) |
| 23 | settings panel opens |
| 24 | howto panel opens |
| 25 | music toggle persists + AudioManager sync (localStorage '0'/'1') |
| 26 | vibration toggle persists |
| 27 | stats panel shows records + per-game stats |
| 28 | daily panel: calendar + play today |
| 29 | daily mode starts with target |
| 30 | daily target reached flags celebration |
| 31 | daily result saved with stars |
| 32 | daily game-over panel: title/target/stars |
| 33 | undo returns selected piece to tray |
| 34 | all-clear: placement empties whole board |
| 35 | all-clear awards combo bonus |
| 36 | zero console errors |

Expected final line:

```
TOTAL 36 checks, 36 passed, 0 failed
```

Exit code is 0 only when all pass. If a check fails, read the `extra` JSON in  
the FAIL line, fix the code, rebuild web-mobile, and re-run.

## 4. The real-drag probe (qa_drag_v2.js)

`modules/cocos-qa/scripts/qa_drag_v2.js` verifies the actual input path (mouse events -> Cocos  
touch -> drag smoothing -> preview -> snap -> placement):

1. Clicks `btn_new_game`, waits for `GameScene` + `window.__blockudoku`.

2. Disables touch emulation, reads `Tray/slot_0` world position via  
`convertToWorldSpaceAR`.

1. Converts design coordinates (origin center, y up) to CSS pixels  
(origin top-left) on the 720x1280 viewport: `x+360, 640-y`.

1. Dispatches `Input.dispatchMouseEvent` mousePressed/mouseMoved/mouseReleased  
at intermediate points, checking mid-drag state: `_dragActive`,  
`selectedSlot`, piece position, drag target, preview cell count.

1. Releases over board cell (row 4, col 2), then asserts the board has placed  
cells and prints score.

Expected final line: `DRAG PLACE OK` (exit 0).

## 5. Run sequence and expected output

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-08-04\c-users-administrator-documents-codex-2026\work
powershell -File scripts\start_qa.ps1     # expect "CDP OK 200"
node scripts\qa_driver.js                 # expect 36/36 + screenshots
node scripts\qa_drag_v2.js                # expect DRAG PLACE OK
```

Notes:

- Re-run `qa_driver.js` needs a fresh browser session: stop Chrome (kill the  
PID printed by start_qa.ps1) before starting a new QA round, or localStorage  
state (e.g. tutorial seen) changes first-run checks.

- The drag probe intentionally disables touch emulation because the driver  
dispatches mouse events; re-enable nothing — the browser is discarded after.

## 6. Screenshot naming and storage

`qa_driver.js` writes PNGs into `SHOT_DIR`. Always set `SHOT_DIR` to a session  
folder (e.g. `$env:SHOT_DIR='...\work\qa_shots'`) so the skill folder stays  
clean — the script default is `qa_shots` next to itself. Canonical names:

```
01_main_menu, 02_game_start, 03_after_place, 04_streak, 05_game_over,
06_after_revive, 07_menu_after_back, 08_settings, 09_howto, 10_stats,
11_daily, 12_daily_result, 13_all_clear
```

These are the web-side acceptance screenshots used by the vision check and the  
delivery sync.
