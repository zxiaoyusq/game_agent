# Cocos Creator: launch, in-engine acceptance, CLI builds
> **何时读我**：要打开 Cocos Creator 做手验 / 要出 web-mobile 或 android 的命令行构建 / 构建日志开头报 EPERM 不知道该不该算失败 / 编辑器还开着又要跑构建
> **读完能做到**：按正确顺序起编辑器和命令行构建，核对场景树、设计分辨率与布局常量，拿到 web-mobile 与 jsb-link 产物，并判断日志里的 EPERM 是否无害、本轮构建是否真的成功
> **范围**：`CASE_ONLY_BLOCKUDOKU` + `GENERALIZED_PATTERN`

## Table of contents

- Launch Cocos Creator (GUI)

- In-engine acceptance steps

- CLI build: web-mobile

- CLI build: android

- Build log checking and the benign EPERM error

## 1. Launch Cocos Creator (GUI)

```powershell
& '${COCOS_2X}\CocosCreator.exe' --path 'E:\gameprogram\Blockudoku'
```

- First launch takes 1-3 minutes (asset import). Editor logs:  
`C:\Users\Administrator\.CocosCreator\logs\CocosCreator.log`.

- Project metadata: `project.json` declares `cocos-creator-js` engine 2.4.13,  
name `Blockudoku`.

- If a previous headless build is running, wait for it to exit first — two  
instances share the same `library`/`temp` folders and corrupt each other.

## 2. In-engine acceptance steps

With the editor open, verify before building:

1. Open the main scene (scene files live under `assets\`), confirm the Canvas  
design resolution is 720x1280 (project settings: `settings\project.json`  
or in Project Settings -> Project Data) and fit mode is `SHOW_ALL`.

1. Run preview: click Preview (or `Ctrl+P`), default preview server  
`http://localhost:7456`. Check the Console panel for errors/warnings.

1. Verify the scene tree has the expected nodes: `Canvas/MainMenu`,  
`Canvas/GameScene` (with `Board`, `Tray`, `HUD`), `Canvas/TutorialOverlay`,  
`Canvas/SettingsPanel`, `Canvas/HowToPanel`, `Canvas/StatsPanel`,  
`Canvas/DailyPanel`.

1. Verify layout constants in the scene/scripts (the 1:1 target against the  
original game):

- Board background 356x356, board cells 38x38, cell pitch 38

- Tray slot 100x100, slot center gap 110 (two slots apart -> 220)

- HUD pinned to the top, no black bars at 720x1280

1. Check asset references resolve (no missing textures in the Assets panel),  
and that SLICED sprites keep their size mode before assigning frames.

1. Quit the editor before CLI builds (`Ctrl+Q` or close window) to avoid  
`library` lock conflicts.

## 3. CLI build: web-mobile

Use `modules/cocos-qa/scripts/build_web.ps1` (wraps the sequence below), or run manually:

```powershell
$creator = '${COCOS_2X}\CocosCreator.exe'
$log = 'C:\Users\Administrator\Documents\Codex\2026-08-04\c-users-administrator-documents-codex-2026\work\build_web.log'
$err = '...\work\build_web.err'
$p = Start-Process -FilePath $creator `
-ArgumentList '--path','E:\gameprogram\Blockudoku','--build','platform=web-mobile;debug=true' `
-RedirectStandardOutput $log -RedirectStandardError $err -PassThru -WindowStyle Hidden
$deadline = (Get-Date).AddMinutes(6)
while (-not $p.HasExited -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 5 }
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force; throw 'web build timed out' }
```

- Output: `E:\gameprogram\Blockudoku\build\web-mobile\` (`index.html`,  
`assets\...`, `src\...`).

- A successful build ends with `Successfully built!` (or similar) in the log.

- debug=true keeps readable JS (`index.js` contains markers like  
`var CELL = 38;` and `SMOOTH_DAMP_TIME`), useful for APK content checks.

## 4. CLI build: android

Use `modules/cocos-qa/scripts/build_android.ps1`, or run manually with  
`'--build','platform=android;debug=true'` in the same Start-Process pattern  
(log `build_android.log`). Timeout 8 minutes.

- Output: `E:\gameprogram\Blockudoku\build\jsb-link\` containing  
`frameworks\runtime-src\proj.android-studio\` plus `assets\`, `src\`,  
`jsb-adapter\`, `main.js`, `project.json` (the jsb-link payload).

- The android Gradle project at  
`build\jsb-link\frameworks\runtime-src\proj.android-studio` is already  
patched for this machine:

`settings.gradle` includes only `:libcocos2dx` and `:Blockudoku`  
(`:instantapp` removed — it fails to configure on modern SDKs).

- `gradle.properties`: compile/target SDK 34, build tools 34.0.0,  
`PROP_APP_ABI=arm64-v8a:armeabi-v7a`, release signing with  
`debug.keystore` (password 123456).

- `app\build.gradle` has `applicationVariants.all` +  
`variant.mergeAssets.doLast` that copies `assets/`, `src/`, `jsb-adapter/`  
and `main.js`/`project.json` into the merge output.

- Do not re-run the Cocos android build while the previous Gradle output is  
in use; close the emulator install first if re-packaging.

## 5. Build log checking and the benign EPERM error

- Every CocosCreator CLI log starts with:  
`Error: EPERM: operation not permitted, unlink 'C:\Users\Administrator\.CocosCreator\logs\CocosCreator.log'`.  
This is a locked log file and is **harmless** — the build proceeds. Do not  
treat it as a failure.

- To judge success: check the tail of the log for `Successfully` and absence  
of `Build failed`/`Error` after initialization; then verify the output  
directory exists and its `index.html`/`assets` are fresh (timestamp).
