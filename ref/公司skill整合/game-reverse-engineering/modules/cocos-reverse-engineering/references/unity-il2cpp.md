# Unity IL2CPP sibling workflow (non-Cocos targets)

> **何时读我**：哥哥要做 Unity 外设系统定位、IL2CPP 类名与活动定位，或拿 Sudoku 案例做对照时——例如 Phase 2 打 Cocos 指纹只返回 `ENGINE=unknown`、目标其实是 Unity IL2CPP 却不知道走哪条工具链。
> **读完能做到**：按四项指纹确认目标是不是 Unity IL2CPP，跑通 Il2CppInspectorRedux + UnityPy 的取数链，按命名空间拆出类型并定位 LiveOps 活动、循环模式、推送四件套与四层远端配置，最后按「signatures only / Ghidra 方法体」如实声明分析深度。
> **范围**：`GENERALIZED_PATTERN` + `CASE_ONLY_SUDOKU`

Proven on **Sudoku.com 7.8.0** (`com.easybrain.sudoku.android`, Easybrain): a  
target that looked like a Cocos job until Phase 2 came back empty. When  
`modules/cocos-reverse-engineering/scripts/detect-project.sh` prints no Cocos fingerprints (`ENGINE=unknown`), do  
NOT run `cc-reverse` — identify the real engine first and route to the right  
toolchain. Sibling skill `game-build-engine-identification` covers the  
engine-level routing for Cocos / Unity / other engines.

## 1. Confirm it is Unity IL2CPP

| Fingerprint | Where to look |
|---|---|
| IL2CPP runtime | `lib//libil2cpp.so` (case: 78 MB) + `libunity.so` + optional `lib_burst_generated.so` |
| Metadata | `assets/bin/Data/global-metadata.dat` — magic `0xFAB11BAF`; **check encryption first** (case: v39.0, unencrypted → every name readable) |
| UnityFS bundles | `assets/bin/Data/data.unity3d` — UnityFS header + version string (case: `6000.3.16f1`) |
| Shell trap | Outer Java/Kotlin shell (`classes*.dex` ×10) carries ads/IAP/Firebase/GPGS — the game core lives in the Unity data; don't be misled by the DEX layer |

## 2. Toolchain (this machine)

- **Il2CppInspectorRedux** — `${IL2CPP_INSPECTOR}\`  
(CLI needs .NET at `E:\Gameprogram\dotnet`); standalone zip also at  
`E:\download\sudoku-re\Il2CppInspectorRedux.CLI-win-x64.zip`

- **UnityPy 1.25.2** — `${PYLIBS}\` (`sys.path.insert` then import)

- **Ghidra/IDA + `il2cpp.json`** (case: 140 MB) — only needed for method  
bodies; type + field + signature analysis is usually enough

- **Python 3** — binary AXML manifest parsing + IL2CPP stub extraction

## 3. Workflow

1. Unpack the XAPK/APK (`7z`). An XAPK splits into several APKs —  
`config.arm64_v8a.apk` holds the native libs; the base APK holds DEX +  
Unity data (`E:\download\sudoku-re\base\`, `...\arm64\`).

1. Verify `global-metadata.dat` magic + version; confirm encryption status.

2. Run Il2CppInspectorRedux → C# stub dump `il2cpp\cs\il2cpp.cs` (18 MB:  
full types/fields/method signatures/RVAs, **empty bodies**) + 100+ dummy  
DLLs in `il2cpp\dll\` for dnSpy/ILSpy type-tree browsing.

1. Extract at scale: grep the stub file by namespace, one domain per file.  
Proven greps for the Sudoku case: `^namespace Sudoku`,  
`^namespace Easybrain.Events`, `Easybrain.Scripts.Notifications`,  
`Easybrain.Config`, `Easybrain.EGAS`, `Easybrain.EBCS`,  
`Easybrain.EasyAb`. Curate `key-*.txt` files (interfaces, controllers,  
enums, DTOs) for documentation.

1. Parse the binary AndroidManifest (AXML) with Python → `manifest-strings.txt`  
(string pool) + `manifest-tree.txt` (element tree). Catalogue  
services/receivers/providers, permissions and intent-filters — the  
push/lifecycle surface lives here.

1. Export assets with UnityPy (Sprite/Texture2D → PNG, AudioClip → WAV,  
TextAsset → JSON, Font → OTF). A high MonoBehaviour count means dense  
ScriptableObject config.

1. Write the report and state the analysis level: **signatures only** vs  
Ghidra method-body decompilation.

## 4. PowerShell 5.1 pitfalls

- Console codepage is GBK: read UTF-8 files with `.read_text('utf-8')` in  
Python; print Unicode via `sys.stdout.buffer.write(text.encode('utf-8'))`.

- Keep extraction logic in `.py`/`.ps1` files; don't inline long Unicode  
strings through `powershell -Command`.

## 5. Case study — Sudoku.com 7.8.0 peripheral systems

Scale: 146 assemblies / 9,823 types / 81,080 methods / 769 namespaces,  
**un-obfuscated + unencrypted metadata**. Namespace map: `Sudoku.*` game core  
(1,896 classes), `Easybrain.*` platform layer (58 assemblies), third-party  
(Spine, DOTween, TMP, NiceVibrations, Unity.Notifications...).

Four peripheral systems were extracted as a reusable LiveOps blueprint:

### 5.1 LiveOps event framework — `Easybrain.Events.Core` (246+ types)

- Cloud flow: `MasterConfig` → `MasterConfigEvent[]` → CDN package download →  
`CommonEventsProcessorBase` state machine → run →  
`CommonEventTerminator` (take-down \& cleanup).

- `MasterConfigEvent` carries `Meta` (EventType/EventId/UpdatedAtUnix/  
DurationSec/`StartConditions` Dictionary\) and `Packages[]`  
(PackageType/PackageId/Url/SizeBytes/**Crc**).

- Gating \& rollout: `CommonEventStartConditions` (show only when conditions  
met), `CommonEventGradualLaunch` (灰度), `Easybrain.GradualConditions`,  
`Easybrain.ESM.Checkpoint` (progress checkpoints); banners via  
`CommonEventsBannersController`.

- Reused event modules: BookStory (145), PaperPlaneTournament (138),  
EventPreparation (136), PostcardsLeaderboards (122), SnakesAndLadders (101),  
Postcard (94), CrocoQuest (80), WaterSort (67), MapSimple/MapUnlock.

### 5.2 Recurring modes

- `DailyChallenge` (165 types): calendar, monthly rewards, notification adapter  
(`SudokuDcNotificationAdapter` → system notifications via  
`NotificationData{Id,Title,Body,LargeIcon,TimeToShow}`).

- `Sudoku.Scripts.TimeAttack` (71): backend + opponents + leaderboard + weekly  
trophies. `WinStreaks`/`ScoreRun`: streak rewards + reward levels.  
`MegaLevels`: giant levels. `Trends`: win-rate percentile stats.

### 5.3 Push notifications — `Easybrain.Scripts.Notifications`

- `INotificationProvider` abstraction: Initialize / ScheduleNotification(  
title,message,targetTime,id,intentData,repeatType) / CancelAll / Cancel /  
GetLaunchNotificationId.

- `NotificationProviderAndroid` (Unity Notifications wrapper) +  
`NotificationProviderMock` (editor/dev no-op) — the standard "abstract +  
real + mock" trio.

- `NotificationsController`: min interval `_minSecondsBetween = 600`, priority  
queue, reschedule on foreground (`ScheduleNewNotifications`), deep-link via  
`IntentData` + `LaunchByNotification` event.

- `NotificationPriority`: EventsCore=400 > DailChallenge=200 > Streaks=100 —  
only the top priority fires per slot.

- FCM: `com.easybrain.fcm.FcmMessagingService` + standard  
FirebaseMessagingService; Android side: UnityNotificationManager +  
UnityNotificationRestartReceiver (BOOT_COMPLETED), POST_NOTIFICATIONS.

### 5.4 Remote config — four separated layers

- `EasyConfig` — `GetConfigValue(name, default)`, `_UpdateTimeout=3f`,  
ConfigUpdated event, local+remote merge (`TryGetMergedValue`).

- `EGAS` — EasySerializer resources with ETag/Crc caching  
(`CachedResourceMetaV2`), batch queue (default size 4), `EGASServerLink`  
ScriptableObject (URL/timeout/retry), InitData statuses  
(unpublished/published/draft/testing).

- `EBCS` — AssetBundle content distribution: `CheckCrc`,  
`TryRetryRequestWithNextCdn` (CDN rotation on failure), persistent cache  
(`CachedContentProvider`).

- `EasyAb` — A/B groups (`TryGetGroup`, GroupUpdated) ↔  
`base\assets\sdk\ab_test.json` (5 experiments: ab_unlock_new,  
ab_avatars_new, ab_gs_toolbar_new, ab_gsfocus_new, ab_score_system_new).

- Config files: `ff_keys.json` (api_key + hmac_key), Base64-encrypted  
`config`/`config_tablet` (NOT decrypted — contains internal endpoints),  
`LogSettings.json` (per-module log switches).

### 5.5 Assets \& data formats

- 58,041 objects / 51 types; 663 exported files / 12.5 MB: 319 sprites,  
156 textures, 17 audio, 7 fonts, 164 TextAsset config JSONs.

- `.ebr` win-rate puzzle bank: custom header (6×uint32 LE) + gzip JSON  
(`{"Id":1953,"WinRate":"63.6996",...}`) — feeds difficulty calibration.

## 6. Reusable design takeaways

- **LiveOps before shipping**: events are server-config-driven templates  
(`MasterConfig` → themed minigame); adding an event ships no client build.

- **Push with priorities + abstraction**: one provider interface, mock for dev,  
priority constants, deep-link intent data, foreground reschedule.

- **Config separated by concern**: app config (EasyConfig) / resources (EGAS) /  
content bundles (EBCS) / experiments (EasyAb), with CRC + CDN rotation +  
graceful degradation everywhere.

- **Methodology**: start from the cloud-config keys and the push/event  
interfaces — they expose the whole system surface fastest.

## 7. Artifacts

- Full report: `E:\download\sudoku-re\REVERSE_ANALYSIS_REPORT.md`

- Stub dump: `E:\download\sudoku-re\il2cpp\`

- Peripheral extracts: `E:\download\sudoku-re\peripheral-extract\`  
(`events.*.cs.txt`, `recurring.*.cs.txt`, `push.*.cs.txt`,  
`config.*.cs.txt`, `key-*.txt`, `manifest-strings.txt`, `manifest-tree.txt`)

- Assets: `E:\download\sudoku-re\assets-export\`
