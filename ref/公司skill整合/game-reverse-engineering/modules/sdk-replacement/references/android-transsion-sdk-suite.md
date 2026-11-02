# Android 传音体系 SDK 套件（Hisavana / Athena / AhaPush / PalmUpdate）

Scope: `GENERALIZED_PATTERN`（接入流程、初始化契约、门禁可迁移）
凡 appId、appKey、track_type、referrerId、域名、包名、类名版本号  `DO_NOT_COPY_LITERAL_VALUES`，每个项目必须重新取证。

适用：给第三方 APK / 二开包接入传音（Transsion）系商业化与增长组件，或把已接入传音 SDK 的成品包回收成可复用素材。
配套脚本：`modules/sdk-replacement/scripts/extract_transsion_sdk_pack.py`（从成品包回收素材）、`modules/sdk-replacement/scripts/verify_vendor_isolation.py`（隔离门禁）。

---

## 1. 套件构成（按职责分，不是"一个 SDK"）

| 组件 | 职责 | 典型包名根 | 依赖形态 |
| --- | --- | --- | --- |
| **Hisavana**（含 ADX/SSP） | 广告聚合：激励视频/插屏/开屏/Banner/原生 | `com.cloud.hisavana.*`、`com.hisavana.*`、`com.hs.adx.*` | `com.cloud.hisavana.sdk.mediation:mediation-lib` + 各广告网络 `-lib` + adapter |
| **Athena**（Growth Analytics） | 行为埋点 + 广告归因 | `com.transsion.ga.*`、`com.transsion.json/galileo/oneid` | `com.transsion.api:athena-ga`、`athena-attribution`（另有 snowball 变体） |
| **HSA Data** | 设备/宿主数据上报（Athena 的落库通道之一） | `cn.hsdata.*` | 随 Athena/宿主壳 |
| **AhaPush** | 本地/常驻推送 | `net.bat.pushCore.*` | 渠道包内置 |
| **PalmUpdate** | Palm 商店更新（ps 渠道） | `com.transsion.upgradesdk.*` | 渠道包内置 |
| **ChannelSdkBridge** | ps/gp 渠道桥（渠道差异收敛点） | 宿主自定义 | 宿主代码 |
| **ABTest / DeviceInfo / DStudio / DeepLink** | 实验、设备画像、数据工作室、深链 | 宿主自定义 | 宿主代码 |
| 广告网络依赖 | Vungle / Pangle(穿山甲) / AdMob mediation / SafeDK | `com.vungle.*`、`com.bytedance.*`、`com.pgl.*`、`com.google.ads.mediation.*`、`com.safedk.*` | 随聚合层 `-lib` 或宿主基线包 |

**关键判断**：`com/transsion` 只占很小一部分（示例工程 312 类），而 Hisavana 相关（1062）+ Pangle adapter + Vungle adapter 才是体积主体。做"是否有完整 SDK"的判断，必须按**组件分别核对**，不要用一个总量数字下结论。

---

## 2. 获取途径（按优先级）

1. **官方私有 Maven（干净路线，推荐）**
   - 仓库：`mvn.shalltry.com`（maven-public / ad-releases）、`artifact.transsion.com`、`nexus.trasre.com`
   - 坐标示例（版本号随项目变，禁止照抄）：`com.cloud.hisavana.sdk.mediation:mediation-lib`、`com.transsion.api:athena-ga`、`com.transsion.api:athena-attribution`
   - 只有拿到仓库账号，才能走"真实 gradle 依赖 + 官方 AAR"的干净接入；本机 Gradle 缓存通常**没有**这些产物，先确认可访问性。
2. **从成品包回收（常见现实）**：`scripts/extract_transsion_sdk_pack.py --apk <shipped.apk> --out <pack>`
   - 判定逻辑：按类前缀区分核心组件（hisavana / transsion / ahapush / palm_update / adx），`cn/hsdata` 只作弱标记；
   - 默认只抽候选 dex 与常用 native so；配置样例要 `--include-config` 且会自动抹密钥；
   - 产物含 `PACK_MANIFEST.json`（sha256 + 类数 + 来源 APK 哈希）与 `REDACTION-REPORT.md`。
3. **官方 SDK 文档**：Hisavana 接入文档（聚合初始化、广告位 API、Manifest 要求）以官方文档为准，回收物只用于补缺。

> 回收态素材是"注入态"的：可能混有宿主自身类（例如小计数 dex 里是宿主桥接代码），注入前必须逐类确认归属。

---

## 3. 接入契约（事实层：以反编译证据为准，版本间可能变化）

### 3.1 初始化顺序（最容易踩坑）

```text
Application/Provider 启动
   主进程判定（非主进程要轮询回主线程再初始化）
        TAdManager.init(activity, AdConfigBuilder)
             setAppId(appId)       平台申请
             setDebug(false) / testDevice(false) / setMuteVideo(false)
             isInitAdMob(true)     取决于实际广告源组合
             setInternalDefaultAdVersion(offlineId)
             setCloudCompleteListener(onCloudComplete(code,msg))
                  code==0 后才建议首次广告请求（云配置/广告位下发完成）
```

要点：
- **必须主进程**初始化；示例工程用 `getRunningAppProcesses()` 比对 `packageName` 判定，非主进程会起 Timer 轮询直到回到主进程。
- 初始化应早于首个广告请求，但**不要**在 `onCloudComplete` 之前就大量预加载。
- Athena 的初始化与 Hisavana 相互独立；两者都在宿主 Application/Provider 阶段完成即可，注意不要被其它 SDK 的 Provider 抢先生效（见 6 进程判定坑）。

### 3.2 广告 API（Hisavana）

```java
// 激励视频
TAdRequestBody body = new TAdRequestBody.AdRequestBodyBuild().setAdListener(listener).build();
new TRewardedAd(activity, slotId).setRequestBody(body).loadAd();     // 加载
boolean ready = instance.hasAd();                                    // 就绪判定
instance.setRequestBody(showBody);                                   // 展示前重挂监听
String token = instance.enterScene(scene, 1);                        // 场景 token（返回字符串）
instance.show(activity, token);                                      // 真正展示
instance.destroy();                                                  // 关闭/错误后销毁
// 插屏：TInterstitialAd 同构；Banner：TBannerView（需宿主提供容器 id，示例为 banner_container）
```

`TAdListener` 回调语义（做状态机时必须全接）：

| 回调 | 含义 | 典型处理 |
| --- | --- | --- |
| `onLoad()` | 加载成功 | 置 ready；若此前有"请求即播放"的排队场景，在此触发 show |
| `onError(TAdErrorCode)` | 加载失败 | 置 not-ready，记录 errorCode/errorMessage，按退避重试 |
| `onShow(int)` | 开始展示 | 置 playing；暂停游戏/暂停 BGM |
| `onClicked(int)` | 点击 | 埋点 |
| `onRewarded()` | **发奖点** | 只在此回调发奖（不要用 onClosed 代替） |
| `onClosed(int)` | 关闭 | 置 not-playing、清 ready、destroy |
| `onShowError(TAdErrorCode)` | 展示失败 | 回滚状态、destroy、按需重载 |

### 3.3 埋点 API（Athena）

```java
AthenaAnalytics.e0(1);                                  // 初始化模式
AthenaAnalytics.S(context, appKey, trackType, false, true);
AthenaAnalytics.d0(false); AthenaAnalytics.c0(false);    // 日志/开关
AthenaAnalytics.a0(referrerAppId);
// 事件：包 Bundle（custom_track_name / vaid / param / ext）后统一提交
new U0.a(eventName, trackType).c(bundle, null).b();
```

要点：
- 事件名、track_type、referrerId、VAID 取值都必须来自**本项目**的传音后台，示例值不可复用。
- `ext` 里通常会带宿主包名/版本；这是"宿主  数据后台"的归属标识，改包名后必须同步。
- 详细的链路排障（AIDL 自环、进程模式缓存、日志多但无上传）见
  `modules/cocos-reverse-engineering/references/android-athena-aidl-loop-and-upload-verification.md`。

---

## 4. Manifest 与资源要求（合并清单）

从成品包回收后逐条核对（脚本 `--decoded` 会输出片段）：

| 类别 | 内容 |
| --- | --- |
| 权限 | `com.transsion.dataservice.permission.READ/WRITE` 等 |
| meta-data | 聚合 `com.hs.ads.APP_KEY`、`tran_athena_version`、Firebase 相关（若一并接） |
| Activity | `com.cloud.hisavana.sdk.common.activity.TAd*Activity`、`com.hs.adx.hella.activity.FullScreenActivity`、`com.hs.adx.interwebview.InterWebViewActivity`、`com.vungle.ads.internal.ui.VungleActivity`（启用 Vungle 时） |
| Service | `com.transsion.athena.aidl.AthenaTrackService` 等 |
| Provider/Receiver | Athena/HSA 相关接收器（如 `cn.hsdata.android.TDReceiver`，示例中 `enabled=false`） |
| 资源 | Banner 容器 id、通知 icon/color、`queries`（部分 SDK 需要查询商店/浏览器） |

第三方免责字段（SafeDK 等）在成品包中大量存在，属于宿主基线包，不必强行搬运。

---

## 5. 注入方式（与 sdk-replacement Phase 5 对应）

| 场景 | 做法 |
| --- | --- |
| 宿主持有源码/工程（Cocos、gradle 工程） | 官方 AAR + Manifest 合并 + 宿主初始化器（最干净） |
| 宿主只有成品 APK（无源码） | **sidecar 注入**：新增 `classesN.dex` + Manifest 合并 + 宿主侧工厂/桥接替换（推荐同时保留原 SDK 类做隔离 = 结局 A） |
| 宿主已有"可替换实现"的抽象层 | 优先改工厂/接口实现，而不是改调用方（改动面最小，可回滚） |

**接口化宿主的替换范式**（GENERALIZED_PATTERN，示例见 `modules/sdk-replacement/assets/transsion/`）：
1. 找到广告/埋点的抽象接口（示例：`IAdsFeature` 19 方法、`IAnalyticsFeature` 7 方法）；
2. 写一个"传音实现"实现同一接口（奖励=incentivised、插屏=video 的语义映射要按宿主原实现确认）；
3. 通过宿主提供的工厂 setter / 委托点装进去；
4. 原实现类保留但不再被实例化  原厂 SDK 不初始化、不联网（结局 A）。

---

## 6. 常见坑（都是踩过的）

| 坑 | 现象 | 处理 |
| --- | --- | --- |
| 非主进程初始化 | 初始化无效或广告不回来 | 先判主进程，非主进程轮询回主进程 |
| 进程模式被缓存 | 后续在正确时机初始化也不生效 | 重载/重启进程；不要反复调 `initSDK()` 掩盖 |
| 云配置未就绪就请求 | 首屏广告成功率低 | 等 `onCloudComplete(code==0)` |
| Athena AIDL 自环 | 日志刷屏、后台无数据 | 见 Athena 排障文档（进程分类 + 落库/上传链路） |
| 只删 Manifest Provider 就以为停用了原 SDK | 仍有原厂流量 | 必须同时确认"该实现不再被实例化"，并用真机三层抓包验证 |
| dex 注入顺序 | `ClassNotFoundException` / `NoSuchMethodError` | 新 dex 命名连续（classesN 顺延），`classes.dex` 不替换；首启看 logcat |
| 依赖广告网络 adapter 缺失 | 聚合初始化成功但无填充 | 按实际开启的广告源补齐 adapter（Vungle/Pangle/AdMob）与对应 so |
| 密钥外泄 | 把 AAR/配置连 appId、APP_KEY 一起提交 | 一律 DO_NOT_COPY_LITERAL_VALUES；素材包只留抹除后的样例 |

---

## 7. 验收（与 sdk-replacement Phase 7/8 一致）

1. 静态：`scan_original_sdk_surfaces.py`（线索）；
2. 门禁：`verify_vendor_isolation.py`（blocked 域族三层 0 命中、allowed 1 成功、Seed 门禁）；
3. 真机：DNS / TLS SNI / HTTP Host 三层抓包；模拟器通过不算；
4. 业务：激励视频播完**发奖**、插屏展示关闭、Banner 展示；Athena 目标事件在后台可见；
5. 断网：冷启动 3/3 可玩、可产生真实得分（广告 no-op 不阻塞）。

---

## 8. 素材包索引

本机已有一份完整回收物（BlockMaster 传音版）：

| 位置 | 说明 |
| --- | --- |
| `E:\codex_apk_work\Wallkickers\sdk_swap\02_sdk_pack\transsion_sdk_pack\` | 4 个 dex + Manifest 片段 + so + 桥接参考源码 + `COMPLETENESS.md` |
| `E:\codex_apk_work\Wallkickers\sdk_swap\03_adapter_draft\` | 接口化宿主适配层示例（IAdsFeature/IAnalyticsFeature）+ 命令级实施手册 |

重生成（任意成品包）：见 `transsion-material-pack-index.md`。
