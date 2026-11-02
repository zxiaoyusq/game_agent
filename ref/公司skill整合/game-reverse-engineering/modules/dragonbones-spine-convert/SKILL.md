---
name: dragonbones-spine-convert
description: "Use when (1) converting DragonBones (DB 5.0/5.5) *_ske.json / *_tex*.json / png assets into Spine 3.8 JSON+Atlas, (2) verifying converted Spine JSON loads in the real Spine editor/viewer or the official 3.8 runtime, (3) debugging Spine JSON load failures like \"Value cannot be converted to float: array\" (curve format), atlas region issues, or silent NaN from lenient JS runtimes, (4) producing a QA report (per-group pass/fail, animation and attachment counts) for game asset recovery pipelines."
---

# DB to Spine 3.8 Convert + QA

## 执行卡（先用这张卡，再读正文）

**我管什么**：把 DragonBones 5.0/5.5 的 `*_ske.json`、`*_tex*.json`、png 转成 Spine 3.8 JSON + Atlas，并跑三级 QA 直到真 Spine Skeleton Viewer 3.8.99 打开每一个文件；转完之后的引擎内接入与美术重做不管。

**第一步做什么**：用显式参数跑 `python modules/dragonbones-spine-convert/scripts/db2spine.py --src <dragonbones_root> --out <spine_output_root>`（默认值是 Blast Block! 项目路径，不许依赖默认值）。

**做完怎么算完成**：
- [ ] 每组产出 `<group>.json` + `<group>.atlas` + png + `preview.html` + `lib/spine-player.js`
- [ ] Step 2 结构扫描：4.x 数组式 curve 计数为 0，`c2` 计数与曲线数对得上
- [ ] Step 3 官方 runtime 全量加载：每组全部动画可播、贴图附件全部在 atlas 中解析成功
- [ ] Step 4 真 viewer 批量打开：每组 PASS = 进程存活（窗口已建）且 stderr 为空
- [ ] 三级全过后才写出 QA 报告（逐组 pass/fail、动画与附件数）

**红线（不可违反）**
- 三级 QA 缺一不算过：结构健全 → 官方 3.8 runtime 全量加载 → 真实 viewer 批量打开；只看"转换成功"一律不通过。
- 绝不允许只凭 JS runtime 测试就宣布成功——它宽松，会吞掉真实编辑器拒绝的格式错误。
- 输出必须是 Spine 3.8 曲线格式 `"curve":a,"c2":b,"c3":c,"c4":d`，不得回退成 4.x 数组。
- 转换器的 `LIB` 与 Blast Block! 默认路径要改成当前工程，不许把上一项目的路径当通用值。
- viewer 只能走官方 `skeletonViewer-3.8.99.jar`；3.8 编辑器已不再免费，不要用试用启动器去装 3.8。

**卡住时按顺序读**：
- 曲线格式、NaN、atlas 重复区域、PNG padding 等坑 → `modules/dragonbones-spine-convert/references/pitfalls.md`
- runtime 加载报错 → Step 3 报告的 stderr，再回 Step 1 重转
- viewer 打不开或 jar 拿不到 → `modules/dragonbones-spine-convert/scripts/verify_spine38.ps1` 的 `-Root/-Viewer/-Report/-Progress` 参数

全局五步循环与六条铁律见 `references/execution-protocol.md`。

## Overview

Converts DragonBones 5.0/5.5 armatures to Spine 3.8 JSON + Atlas, generates per-group browser previews, and runs a 3-level QA that ends with the **real Spine Skeleton Viewer 3.8.99** opening every file. The real-Spine step is mandatory: lenient runtimes hide format bugs that the real editor rejects.

## Prerequisites

- Python 3.9+ (converter), Node.js (runtime QA), Java 9+ (viewer QA)
- Official Spine 3.8 runtime file `spine-player.js` (3.8.75) - reuse any existing copy from a prior conversion output
- Official Skeleton Viewer 3.8.99 jar (free): `https://esotericsoftware.com/files/sv/skeletonViewer-3.8.99.jar`
  - The full Spine 3.8 *editor* is NOT free anymore: trial launchers only install the latest version; 3.8 requires a paid license. The viewer is the official 3.8 loader for exported data.

## Workflow

### Step 1 - Convert

```bash
python scripts/db2spine.py --src <dragonbones_root> --out <spine_output_root>
```

Input layout per group: `<group>/<group>_ske.json` (or `-lite`), `<group>_tex*.json`, `*.png`.
Output per group: `<group>.json` + `<group>.atlas` + pngs + `preview.html` + `lib/spine-player.js`.

- Defaults are the Blast Block! project paths (edit the top of the script or pass `--src/--out`).
- Edit `LIB` in the script if `spine-player.js` lives elsewhere.
- The converter already emits Spine-3.8 curve format (`"curve":a,"c2":b,"c3":c,"c4":d`) - do not revert to 4.x arrays.

### Step 2 - Structural sanity scan

Scan every output JSON for 4.x-format curve arrays (must be 0) and confirm `c2` counts match:

```powershell
Get-ChildItem <out> -Recurse -Filter *.json |
  Select-String -Pattern '"curve"\s*:\s*\[' | Measure-Object
```

### Step 3 - Official 3.8 JS runtime full load

```bash
node scripts/qa_spine_load.js <spine_output_root> <path_to_spine-player.js> <report.json>
```

Loads every group with `SkeletonJson` + `TextureAtlas`, plays every animation 1+ frames, verifies texture attachments resolve in the atlas, and writes a per-group JSON report. This catches most structural problems quickly, but it is **not** authoritative.

### Step 4 - Real Spine viewer batch open (authoritative)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_spine38.ps1 `
  -Root <spine_output_root> -Viewer <skeletonViewer-3.8.99.jar> `
  -Report <report.csv> -Progress <progress.log> [-Limit N]
```

Opens every `<group>.json` in the real 3.8.99 viewer; PASS = process alive (window built) AND stderr empty. This is the only check that reproduces the editor's strict parser. Run with `-Limit 3` for a quick smoke test; drop `-Limit` for the full batch (~8 min for 116 groups).

### Step 5 - Visual spot check

Open 2-3 representative files (multi-page atlas, high curve count) in the viewer and confirm the skeleton renders (screenshot + OCR the window, or eyeball it). Also open `<group>/preview.html` in a browser to confirm playback.

## Decision rules

- All groups PASS step 4 -> conversion is Spine-3.8-compatible. Ship the QA report.
- Any FAIL -> read the stderr head from the report. Common causes and fixes are in `modules/dragonbones-spine-convert/references/pitfalls.md`; most are converter-side fixes followed by re-running Step 1 to 4.
- Never declare success on the JS runtime test alone.

## Resources

- `modules/dragonbones-spine-convert/scripts/db2spine.py` - DB 5.0/5.5 to Spine 3.8 converter (fixed curve format, atlas, preview, index)
- `modules/dragonbones-spine-convert/scripts/qa_spine_load.js` - official 3.8 runtime full-load + play + attachment resolution QA
- `modules/dragonbones-spine-convert/scripts/verify_spine38.ps1` - real Skeleton Viewer 3.8.99 batch open/verify
- `modules/dragonbones-spine-convert/references/pitfalls.md` - the pitfalls and fixes learned (curve format, NaN trap, atlas dup regions, PNG padding, viewer acquisition, etc.)
