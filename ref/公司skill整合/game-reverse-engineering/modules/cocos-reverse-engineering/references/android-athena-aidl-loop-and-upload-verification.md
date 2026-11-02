# Android Athena AIDL self-loop and upload verification

> **何时读我**：埋点日志刷个不停但后台收不到数据，或要做 AIDL 回路取证、怀疑 AIDL 进程被误判成 Athena remote 进程、要证明「日志到底有没有真的上传」时读我。
> **读完能做到**：按四层证据链（事件创建 → 入库 → 发请求 → 服务端 code=0）判定一次埋点是否真的上传成功，并用进程分类修正 AIDL 自回路，而不是靠降日志等级或改事件名掩盖现象。
> **范围**：`GENERALIZED_PATTERN`

Scope: `GENERALIZED_PATTERN`. Reuse the evidence model, but treat every appId, endpoint, process, table, supplier and bridge name as `DO_NOT_COPY_LITERAL_VALUES`.

Use this reference when a rebuilt Cocos/JSB APK prints Athena logs continuously,  
the backend receives no useful analytics, or ad traffic exists but its active SDK  
ownership is unclear.

## Core rule

Repeated analytics logs do not prove repeated uploads. Prove the complete chain:

```text
business bridge -> Athena worker -> local DB -> HTTP request -> server success
```

If the process is misclassified as an Athena remote process, the chain may instead  
become a self-loop:

```text
main process -> AIDL service -> same main process -> AIDL service -> ...
```

Suppressing logs, changing event names, or repeatedly calling `initSDK()` does not  
repair this state.

## Recognition matrix

| Evidence | Healthy main-process path | AIDL self-loop |
|---|---|---|
| `AthenaTrackService receive appId` | zero or isolated cross-process calls | rises continuously |
| `TrackByAidl tid` | zero for normal in-process tracking | rises with receive count |
| `save event to DB` | present | absent |
| `--> upload` | present after enqueue/config | absent |
| ` | `code:0`, `message:suc` | absent |
| log volume | bounded | can grow to hundreds of MB |

Count these markers over a short bounded window before editing code. A useful  
failure signature is many matched AIDL send/receive pairs with zero database and  
upload lines.

## Diagnose process classification before changing event code

1. Confirm manifest `ApplicationInfo.processName`, the runtime process name used  
by Athena, and `Application.getProcessName()`.

1. Decompile the exact bundled Athena version and locate its cached process-mode  
field. Do not assume field names are stable between versions.

1. Inspect initialization order. Android `ContentProvider` instances run before  
the first Activity; another SDK provider can initialize Athena before an  
Activity lifecycle callback.

1. Check whether the result is cached. In one Athena 3.1.x build, private static  
integer `j` used `-1=unknown`, `0=main`, `1=remote`. Once a bad early init  
wrote `1`, moving a later call to `onActivityCreated()` did not recompute it.

The field name and values above are a recognition example, not a universal API.  
Verify them in the target DEX before patching.

## Minimal safe correction

Prefer an official process-selection API when the bundled SDK exposes one. When  
it does not, a version-scoped compatibility helper may set the verified cached  
mode before Athena initialization.

Requirements:

- set the verified main-process mode before project-owned SDK initialization;

- repeat immediately before the intentional `initSDK()` call so an earlier  
provider cannot leave stale state;

- wrap reflection in `try/catch Throwable` and emit one bounded log line;

- keep the change isolated in an added bridge DEX when possible;

- never disable the Cocos remote loader or wrap  
`jsb.reflection.callStaticMethod` to solve analytics.

Example after verifying that `j=0` means main process in this exact SDK:

```java
static void forceAthenaMainProcessMode() {
try {
Field field = AthenaAnalytics.class.getDeclaredField("j");
field.setAccessible(true);
field.setInt(null, 0);
Log.i("BMAthenaFix", "Athena main-process mode forced: j=0");
} catch (Throwable error) {
Log.e("BMAthenaFix", "Unable to force Athena main-process mode", error);
}
}
```

Do not ship this pattern by field-name guesswork. Re-derive field semantics when  
the SDK changes.

## Official logging and environment split

```bash
adb shell setprop log.tag.Athena DEBUG
adb shell setprop debug.athena.test_mode true
adb logcat -s Athena > athena-test.txt
```

Test mode routes configuration/upload to endpoints such as  
`dsc-test.shalltry.com` and `dsu-test.shalltry.com`. A production dashboard may  
correctly show nothing from that run.

For a separate production proof:

```bash
adb shell setprop debug.athena.test_mode false
adb shell am force-stop 
adb shell monkey -p  -c android.intent.category.LAUNCHER 1
adb logcat -s Athena > athena-production.txt
```

Restore the intended developer test setting afterward. A device property is not  
the same as a hard-coded release configuration.

## Four-level upload proof

Do not report success after seeing only the business bridge log.

1. Event created: `track event:{"appid":...,"event":...}`

2. Event persisted: `save event to DB:{"tid":...,"db_count":...}`

3. Packet sent: `--> upload:{"host":".../athena/checkpoint/v3/upload",...}`

4. Server accepted: `<-- upload success:{"code":0,"message":"suc",...}`

If forcing a flush, wait until the database-save line appears. Calling flush  
immediately after enqueue can run before the worker stores the event and create  
a false "nothing uploads" conclusion.

For DriftSand integrations, the backend may need to query the envelope:

| Field | Example meaning |
|---|---|
| `appid` | `5943` |
| `tid` | `594360000015` |
| top-level `event` | `Drift_Sand` |
| `_customTrackName` | actual business event name |
| `_param` | original event parameters |

Searching only for the JavaScript name as a top-level event misses correctly  
uploaded envelope events.

## Frida on x86/Houdini

Frida spawn hooks can crash an x86 emulator running ARM libraries through  
Houdini before application startup. Do not immediately classify that as a game  
crash. Launch normally, wait for the process, attach Frida, inspect one bounded  
probe, then reproduce on a real ARM device. Dynamic instrumentation is evidence,  
not the shipped fix.

## Controlled DEX overlay after apktool resource failure

Apktool may assemble a changed smali DEX and fail later while linking problematic  
decoded resources. This is not a successful full build, but the assembled DEX  
can be used for a controlled binary overlay only when:

- only smali in that DEX changed;

- compiled resources from the signed baseline must remain intact;

- DEX timestamp and a unique marker prove it was rebuilt;

- the APK entry is checked after replacement;

- old signature entries are removed, then the APK is zipaligned and signed.

Never generalize this into "ignore apktool errors". If resources or manifest  
changed, repair the resource build instead.

## Identifying the active advertising path

Manifest declarations show what is packaged, not what dispatched an ad. A  
mediation SDK can retain dormant supplier adapters. Trace the game bridge's  
`load/show/isReady` calls, record mediation app and slot IDs, capture runtime  
cloud-control/request logs, and inspect the top Activity while the creative is  
visible.

Hisavana may dispatch a creative supplied by AdMob, Mintegral, or another  
adapter. A supplier Activity alone does not prove the game returned to an  
original AppLovin business path.

## Acceptance gate

- Clean install and three cold starts reach the Cocos scene.

- AIDL loop counters stay zero for normal in-process events.

- Database saves are present.

- Test-mode upload returns `code=0`.

- Production-mode upload returns `code=0` when production reporting is in scope.

- Backend lookup uses the correct app ID, TID, and envelope fields.

- APK version, SHA-256, signer, alignment, and installed version are recorded.

- A real ARM device follows emulator validation for release candidates.

## Common mistakes

| Mistake | Correct response |
|---|---|
| Lower log level to stop the loop | Fix process classification. |
| Rename events before checking storage | Prove worker/DB path first. |
| Move init to Activity and assume order is fixed | Check providers and cached static state. |
| Treat test upload as production proof | Verify endpoint and dashboard environment. |
| Flush immediately after track | Wait for DB enqueue. |
| Treat Frida/Houdini spawn SIGSEGV as APK failure | Launch normally and attach. |
| Identify an ad SDK from manifest presence | Trace mediation and supplier separately. |
| Ignore an apktool failure | Reuse only a proven DEX under the strict overlay conditions. |
