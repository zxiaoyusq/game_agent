# Android build, APK packaging, MuMu install and screenshot
> **何时读我**：要出 Android APK 并装进 MuMu 跑验收截图 / Gradle 报 NDK Root is empty / 装完还是旧界面、怀疑 APK 里没打进新代码 / adb 连不上模拟器或截图是空文件
> **读完能做到**：配好 NDK、SDK、JDK 环境变量，删掉 mergeAssets 陈旧缓存重建 APK，用 aapt 验证包内确是新代码，再连 MuMu 安装启动、二进制安全截图并走完关键界面验收
> **范围**：`CASE_ONLY_BLOCKUDOKU` + `GENERALIZED_PATTERN`

## Table of contents

- Environment variables

- Gradle APK build (with the stale-cache fix)

- Verify the APK really contains new code

- MuMu: start emulator, adb connect

- Install, launch, screencap

- Error table

## 1. Environment variables

Set before every Gradle invocation (also done by `modules/cocos-qa/scripts/gradle_apk.ps1`):

```powershell
$env:NDK_ROOT        = '${ANDROID_NDK}'
$env:ANDROID_SDK_ROOT = '${ANDROID_SDK}'
$env:ANDROID_HOME    = '${ANDROID_SDK}'
$env:JAVA_HOME       = 'E:\Program Files\Eclipse Adoptium\jdk-17.0.18.8-hotspot'
```

Missing `NDK_ROOT` produces `NDK Root is empty` from the Cocos Gradle plugin.  
`local.properties` (`ndk.dir`, `sdk.dir`) is already present in the generated  
project, but the env vars keep the Cocos plugin happy.

## 2. Gradle APK build (with the stale-cache fix)

Android project root:

```
E:\gameprogram\Blockudoku\build\jsb-link\frameworks\runtime-src\proj.android-studio
```

**Critical:** the `mergeAssets.doLast` task in `app\build.gradle` copies the  
jsb-link payload into the merge output, but Gradle incremental caching keeps  
the *previous* merged assets unless they are wiped. Before  
`assembleRelease`, always delete:

```
app\build\intermediates\assets\release
```

Then run (also wrapped by `modules/cocos-qa/scripts/gradle_apk.ps1`):

```powershell
cd 'E:\gameprogram\Blockudoku\build\jsb-link\frameworks\runtime-src\proj.android-studio'
.\gradlew.bat assembleRelease --no-daemon
```

APK output:

```
app\build\outputs\apk\release\Blockudoku-release.apk
```

The build is signed with `debug.keystore` (from  
`${COCOS_2X}/resources/static/build-templates/native\debug.keystore`,  
password 123456), so `adb install -r` accepts it directly.

## 3. Verify the APK really contains new code

The #1 failure mode is a "successful" APK built from stale `index.js`. Check:

```powershell
& '${ANDROID_BUILD_TOOLS}\34.0.0\aapt.exe' dump badging $apk | Select-String 'package:|launchable-activity'
& '${ANDROID_BUILD_TOOLS}\34.0.0\aapt.exe' list $apk | Select-String 'assets/index.js'
```

Then extract the game bundle and grep for build markers. In the current build  
the bundle is `assets/assets/main/index.js` (older layouts may put it at  
`assets/index.js`; locate it with `aapt list $apk | Select-String 'index.js'`).  
Extract via copy-APK-to-`.zip` + `Expand-Archive`, or `tar -xf`:

- `var CELL = 38;` (1:1 layout constant)

- `SMOOTH_DAMP_TIME` (drag smoothing)

- `"PLAY", 30` or similar recent feature marker

If markers are missing, delete `app\build\intermediates\assets\release` again  
and rebuild — do not patch around the cache.

## 4. MuMu: start emulator, adb connect

```powershell
$mumu = 'F:\Program Files\Netease\MuMu Player 12\nx_main\mumu-cli.exe'
& $mumu info -v 0              # JSON state; check is_android_started
& $mumu control -v 0 launch    # start if not running
& $mumu adb -v 0 -c connect    # prints the adb endpoint (e.g. 127.0.0.1:16384)
& '${ANDROID_PLATFORM_TOOLS}\adb.exe' connect 127.0.0.1:16384
& '${ANDROID_PLATFORM_TOOLS}\adb.exe' devices
```

MuMu 12 exposes adb on `127.0.0.1:16384` by default (confirm via  
`mumu-cli.exe adb -v 0 -c connect`). `is_android_started: false` means the VM  
is not booted yet; run `control -v 0 launch` and wait ~25s before connecting.  
If `offline`, disconnect and reconnect.

## 5. Install, launch, screencap

```powershell
$adb = '${ANDROID_PLATFORM_TOOLS}\adb.exe'
& $adb install -r '...\Blockudoku-release.apk'
& $adb shell am start -n org.cocos2d.blockudoku/org.cocos2dx.javascript.AppActivity
Start-Sleep -Seconds 8   # JS boot + asset load
& $adb exec-out screencap -p > shot.png   # binary-safe variant in mumu_shot.ps1
```

Use `modules/cocos-qa/scripts/mumu_shot.ps1` for the binary-safe version (PowerShell `>`  
corrupts binary output; the script uses `Start-Process -RedirectStandardOutput`).

Known identity (verified with `aapt dump badging`):

- package: `org.cocos2d.blockudoku`

- launchable activity: `org.cocos2dx.javascript.AppActivity`

Acceptance walkthrough on device:

1. Boot screen -> main menu; screenshot.

2. Tap New Game; screenshot the fresh board.

3. Drag a piece onto the board; screenshot mid-drag and after placement.

4. Build a line clear; screenshot.

5. Open Settings and Daily panels; screenshot each.

6. After any code change, reinstall (`-r`) — but note Android may show a  
"replaced" dialog once; tap it manually if the flow stalls.

## 6. Error table

| Symptom | Cause / fix |
|---|---|
| `NDK Root is empty` | env vars not set; set NDK_ROOT before Gradle |
| Old UI in the installed app | stale `mergeAssets` cache; delete `app\build\intermediates\assets\release`, rebuild, reinstall |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | uninstall first (`adb uninstall org.cocos2d.blockudoku`) or use `-r` on same signature |
| `Activity class does not exist` | wrong activity name; re-check with `aapt dump badging` |
| `adb offline` | `adb disconnect 127.0.0.1:16384` then connect again |
| screenshot file empty/corrupt | binary pipe corrupted; use `mumu_shot.ps1` or `exec-out` redirection via Start-Process |
