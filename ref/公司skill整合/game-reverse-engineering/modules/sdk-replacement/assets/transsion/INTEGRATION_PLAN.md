# Wall Kickers 原包 sidecar 注入实施手册（结局 A）

> 目标包：`com.kumobius.android.walljumper` v4.4(25) ｜ 方式：sidecar 注入 ｜ 结局：A（保留原 SDK 类，切断其实际联网）
> 依赖工件：`../01_baseline_surfaces/`（基线/证据/契约）、`../02_sdk_pack/transsion_sdk_pack/`（SDK 素材）

---

## 0. 架构与替换点（事实来自反编译）

```
libKumoGame.so (C++ / ZEngine)
          JNI 调用 64 个方法
        
com.kumobius.android.INativeResponder         契约不变，不改
        
         implements
com.kumobius.android.KumoAppActivity
    adsInit()         KumoAppBase.getAdsFeatureFactory().create()   IAdsFeature(19 方法)
    analyticsInit()   KumoAppBase.getAnalyticsFeatureFactory()...   IAnalyticsFeature(7 方法)
    iapInit()         IapFeatureFactory（Google Play Billing，保持不动）
    achievementsInit()  Google Play Games（保持不动）

原实现：AdsFeatures（AppLovin MAX + ironSource/LevelPlay + Unity Ads + Fyber）
新实现：HisavanaAdsFeature（Hisavana 聚合）   本目录 HisavanaAdsFeature.java
原实现：游戏内 IAnalyticsFeature 实现         新实现：HisavanaAnalyticsFeature（Athena）
```

**为什么结局 A 可行**：只要 `AdsFeatures` 不再被实例化，AppLovin/ironSource/Unity/Fyber 的 SDK 初始化与广告请求就无从发生；这些类继续留在包内（满足"保留原 SDK"）。

---

## 1. 步骤（命令级）

### 步骤 1：基线（已完成）
```powershell
# 产物：01_baseline_surfaces/baseline.json（APK/dex SHA-256、版本、工具链）
& 'C:\Program Files\Python312\python.exe' -X utf8 E:\codex_apk_work\Wallkickers\sdk_swap\tools\wj_baseline.py
```

### 步骤 2：解码工程（已完成）
```powershell
java -jar E:\codex_apk_work\blockmaster_pro_swap\work\tools\bin\apktool_2.9.3.jar d -f `
  -o E:\codex_apk_work\Wallkickers\sdk_swap\01_baseline_surfaces\decoded_base `
  E:\codex_apk_work\Wallkickers\_apk\base.apk
# 结果：smali / smali_classes2..4 + 文本 AndroidManifest.xml
```

### 步骤 3：编译适配层  独立 dex
适配层引用两类"外部类"：游戏的 `com.kumobius.android.*` 与 Hisavana 的 `com.hisavana.*`。二者都不在本机 jar 里，采用 **stub jar 编译法**（只用于编译期，不进包）：

```powershell
$D8   = 'E:\AndroidSdk\build-tools\34.0.0\d8.bat'
$JAVAC= 'E:\Program Files\Eclipse Adoptium\jdk-17.0.18+8\bin\javac.exe'
$AJAR = 'E:\AndroidSdk\platforms\android-34\android.jar'
$W    = 'E:\codex_apk_work\Wallkickers\sdk_swap\03_adapter_draft'

# 3.1 stub 源（契约类，只有签名）
#     游戏侧：IAdsFeature / IAnalyticsFeature / IFeatureFactory / KumoAppActivity / KumoAppBase
#     SDK 侧：com.hisavana.mediation.* / com.hisavana.common.* / com.transsion.ga.AthenaAnalytics / U0.a
#      由 stub/ 目录提供（见 ../03_adapter_draft/stub/README.md）
# 3.2 编译 stub 成 jar（仅 classpath）
& $JAVAC -source 8 -target 8 -d $W\stub_build (Get-ChildItem $W\stub -Recurse -Filter *.java)
& jar cf $W\stub.jar -C $W\stub_build .

# 3.3 编译适配层（classpath = android.jar + stub.jar）
& $JAVAC -source 8 -target 8 -cp "$AJAR;$W\stub.jar" -d $W\adapter_build `
    $W\HisavanaAdsFeature.java $W\HisavanaAnalyticsFeature.java `
    $W\WjHisavanaFeatureFactory.java $W\WjSdkInstaller.java

# 3.4 转 dex（min-api 21）
& $D8 --min-api 21 --lib $AJAR --output $W\adapter_dex (Get-ChildItem $W\adapter_build -Recurse -Filter *.class)
# 结果：$W\adapter_dex\classes.dex  入包改名为 classes9.dex
```

> 备选：不编译 Java，直接把适配层写成 smali（`smali_classes5/com/kumobius/android/features/...`）。契约已由 `feature_api.json` 固化，两种方式等价。

### 步骤 4：注入传音 SDK 素材（4 个 dex）
```
02_sdk_pack/transsion_sdk_pack/dex/hisavana_common_app.dex    classes15.dex（参考命名，本包顺延为 classes5.dex）
02_sdk_pack/transsion_sdk_pack/dex/hisavana_athena_sdk.dex    classes6.dex
02_sdk_pack/transsion_sdk_pack/dex/firebase_part1.dex         classes7.dex
02_sdk_pack/transsion_sdk_pack/dex/firebase_part2.dex         classes8.dex
03_adapter_draft/adapter_dex/classes.dex                      classes9.dex
```
> Wall Kickers 现有 `classes.dex..classes4.dex`，新 dex 从 `classes5.dex` 起顺延；APK 内同名同序，构建时用 zip 覆盖。

### 步骤 5：Manifest 变更
1) **加入**（源 `02_sdk_pack/.../manifest/AndroidManifest.fragment.xml`，70 条）：
   - Hisavana：`TAdInterstitialActivity`、`com.hs.adx.*` 相关 Activity/Provider、`com.hs.ads.APP_KEY` meta-data 等；
   - Athena：`com.transsion.athena.aidl.AthenaTrackService`、`com.transsion.dataservice.permission.READ/WRITE`、`tran_athena_version` meta-data；
   - Push/其它按需（AhaPush 若要一并接，加 `net.bat.*` 声明）。
   - 适配层自身无需新组件（工厂由代码装配）。
2) **停用原厂自动初始化入口（结局 A 必做）**：

| 组件 | 处理方式 |
|---|---|
| `com.applovin.sdk.AppLovinInitProvider` | 删除该 `<provider>`（类保留在包内） |
| `com.ironsource.lifecycle.IronsourceLifecycleProvider` | 删除 |
| `com.ironsource.lifecycle.LevelPlayActivityLifecycleProvider` | 删除 |
| `<meta-data android:name="com.unity3d.services.core.configuration.AdsSdkInitializer" .../>` | 删除 |

> 保留 Google Play Games / Billing 相关组件（IAP、榜、成就继续可用）。

### 步骤 6：装配（覆盖工厂）
在 `decoded_base/smali_classes3/com/kumobius/android/KumoAppBase.smali` 的 `onCreate()` 末尾（`return-void` 之前）插入：

```smali
    invoke-static {p0}, Lcom/kumobius/android/WjSdkInstaller;->install(Landroid/content/Context;)V
```
要求 `WjSdkInstaller` 位于 `com.kumobius.android` 包（`KumoAppBase.setAdsFeatureFactory` 为包内可见）。

备选（不改 `KumoAppBase`）：改 `KumoAppActivity.adsInit()/analyticsInit()` 中的两处 `invoke-static {..}, Lcom/kumobius/android/KumoAppBase;->getAdsFeatureFactory()`  指向 `WjHisavanaFeatureFactory`。

### 步骤 7：回编 / 对齐 / 签名
```powershell
$APKTOOL='E:\codex_apk_work\blockmaster_pro_swap\work\tools\bin\apktool_2.9.3.jar'
$BT='E:\AndroidSdk\build-tools\34.0.0'
java -jar $APKTOOL b E:\...\decoded_base -o stage_unsigned.apk      # 资源链接失败dex 失败，见 skill V35 复盘
# 覆盖 dex（务必用步骤 4 的 5 个 dex）
# 然后用 zip 覆盖写入，保留原压缩方式（resources.arsc 保持 STORED/对齐）
& "$BT\zipalign.exe" -f -p 4 stage_unsigned.apk stage_aligned.apk
& "$BT\apksigner.bat" sign --ks <keystore> --ks-key-alias <alias> --out wallkickers_transsion_v1.apk stage_aligned.apk
```

### 步骤 8：门禁与验收
```powershell
# 静态
& 'C:\Program Files\Python312\python.exe' -X utf8 D:\skills\game-reverse-engineering\modules\sdk-replacement\scripts\scan_original_sdk_surfaces.py `
  --apk-dir E:\...\decoded_base --out ..\01_baseline_surfaces\surfaces_after.json
# 隔离门禁（需要真机抓包 CSV）
& 'C:\Program Files\Python312\python.exe' -X utf8 ...\capture_network_evidence.py --input capture.csv --config ..\01_baseline_surfaces\isolation-config.json --out network_evidence.json
& 'C:\Program Files\Python312\python.exe' -X utf8 ...\verify_vendor_isolation.py --apk-dir E:\...\decoded_base `
  --isolation-config ..\01_baseline_surfaces\isolation-config.json --network-evidence network_evidence.json `
  --out verification.json
# 验收报告
& 'C:\Program Files\Python312\python.exe' -X utf8 ...\gen_sdk_acceptance_report.py --evidence network_evidence.json --verification verification.json --out 验收报告.md
```
真机三层（DNS / TLS SNI / HTTP Host）：blocked（applovin/applvn/supersonicads/inner-active/unity3d/fyber）全 0；allowed（hisavana/transsion）1 成功。
业务验收：激励视频播完发奖、插屏展示关闭、断网冷启动 3/3 可玩可得分。

---

## 2. 风险与回滚

| 风险 | 处置 |
|---|---|
| dex 顺序/命名错误导致 `ClassNotFoundException` | 保持 `classesN.dex` 连续；`classes.dex` 不可替换；用 `aapt2 dump badging` + 启动日志确认 |
| 适配层 stub 编译的签名与真实 SDK 不一致 | 以 `feature_api.json` + `bridge_reference/*.java` 为准；首启抓 logcat `NoSuchMethodError` |
| Hisavana 初始化时机（需主进程） | `TAdManager.init` 放主进程；`isMainProcess` 判定参考 HisavanaSDK.java |
| 原厂 SDK 仍有残留连接 | 复查 Manifest 自动初始化入口 + 真机三层抓包；`AdsFeatures` 不得被任何路径实例化 |
| 回滚 | 保留原 `base.apk`（sha256 见 baseline.json），一键重打包 |

## 3. 待办清单（阻塞项）

- [ ] hisavana appId、激励/插屏/Banner 广告位 ID
- [ ] athena track_type / referrer appId / appKey（BM 值不可复用）
- [ ] `google-services.json`（目标包名）若只接 Hisavana+Athena 可暂缓
- [ ] arm64-a8 split（真机验收必需；本机仅 x86_64）
- [ ] 分发授权确认
