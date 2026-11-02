# Android Cocos 原厂联网隔离与真机验收（Block Master V35）

> **何时读我**：要给 Cocos JSB 换皮包切断 Block Blast/HungryStudio 原厂联网、同时保住传音/Hisavana 渠道，或阻断后日志疯狂重试、需要真机网络层证据做验收时读我。
> **读完能做到**：分层隔离 JS 远端配置与原厂 SDK/APM（Bugsnag 只关交付层），按调用方契约返回 inert success 避免重试风暴，并在真机上用 DNS/TLS/HTTP Host 三层抓包加联网断网冷启动与实玩闭环出验收结论。
> **范围**：`CASE_ONLY_BLOCKMASTER`

范围：`CASE_ONLY_BLOCKMASTER` · `DO_NOT_COPY_LITERAL_VALUES`。域名、appId、证书、SDK 归属和 V35 结论只属于该项目。

本章记录 Block Master V35 在“保留主玩法与传音体系、切断 Block Blast/HungryStudio 原厂联网”中的修复过程。适用于带本地 Seed、运行时 patch、原厂 SDK 壳和第三方聚合广告的 Cocos JSB APK。

## 目录

1. [目标与边界](#1-目标与边界)

2. [JS 与远端配置隔离](#2-js-与远端配置隔离)

3. [原厂 SDK、崩溃和广告隔离](#3-原厂-sdk崩溃和广告隔离)

4. [Athena 上报与内容净化](#4-athena-上报与内容净化)

5. [构建与 Seed 完整性](#5-构建与-seed-完整性)

6. [真机验收](#6-真机验收)

7. [常见误判与禁止做法](#7-常见误判与禁止做法)

8. [V35 案例证据](#8-v35-案例证据)

## 1. 目标与边界

四个结果必须同时成立：

- 主玩法联网、断网都能启动并连续游玩。

- 原厂热更、配置、小游戏、归因、崩溃和独立广告链不产生真实网络连接。

- Athena、Hisavana、Palm/Aha 等目标渠道链路保持可用。

- 主玩法所需远端 bundle 已固化进 APK Seed，不能靠恢复原厂服务器解决启动失败。

推荐按单变量分层处理：

1. JS 原厂接口和动态配置。

2. Android 原厂自动初始化组件。

3. 崩溃/APM 的实际交付层。

4. 目标渠道上报和广告回归。

每层独立构建、清数据安装、联网和离线冷启动。出现 Loading、黑屏、崩溃或首个可玩场景未到达时，先回滚本层，不要继续叠加。

## 2. JS 与远端配置隔离

### 2.1 活跃 JS 与 Seed 副本必须双改

仅修改 `assets/assets/main/index.*.js` 不够。APK 首启可能从 Seed/patch 恢复第二份旧脚本，覆盖本地修改。至少检查：

- 当前运行入口 `assets/assets/main/index.*.js`。

- `assets/remote_seed/patch/patch/assets/main/index.*.js`。

- 安装后 `files/patch`、数据库或 MMKV 中是否还有旧副本。

用运行时文件哈希和关键标记确认“设备实际执行的是哪一份”，不能只看反编译目录。

### 2.2 URL 参数可绕过静态字符串替换

V35 已把默认 trait 地址改为本地端点，但 Test 环境 getter 仍执行 `getUrlParameterValue("traitServerUrl")`，运行参数又把地址改回 `https://gametester.afafb.com/game_init`。

安全修复：

- Test 与 Prod getter 都强制返回本地端点，例如 `bm-local://trait-server/game_init`。

- 同时检查 URL 参数、远程 trait、数据库配置和 patch 参数，不只替换 fallback 字符串。

- 用运行日志确认最终解析后的 URL，而不是只做静态 grep。

### 2.3 本地 trait 响应必须来自已验证缓存

可从真机/模拟器已成功运行版本的 `jsb.sqlite` 提取 `block-blast-server_experiment_config`，再清除 MoreGames、评分、活动入口等不需要的 trait，作为本地已知良好响应。

本地响应要保持原 schema。若直接返回空字符串或抛错，业务层可能把它当作网络失败并持续重试。

### 2.4 阻断请求时返回“兼容成功”，不要制造异常风暴

为可选原厂功能返回 Promise rejection、HTTP error 或语法错误，曾触发：

- `cocos_res_reporter` 重试。

- 持续重发和日志风暴。

- `Uncaught SyntaxError`。

- 加载流程被可选接口拖死。

正确做法是按调用方契约返回 `{}`、空列表或本地 trait 等 inert success，并让正常回调链结束。若本地 `POST_BuriedPoint` 参与通用请求流程，还要填写 timing、URL、HTTP code，并先调用 `handleServerResponse`，否则旧诊断值和重试状态会残留。

### 2.5 守卫只拦原厂域名

可以在 XHR、fetch、项目通用 `Http.requestAsync/request` 和 Cocos downloader 中对明确原厂域名做白名单外阻断，但不得：

- 包装 `jsb.reflection.callStaticMethod`。

- 在顶层粗暴禁用 `cc.assetManager.loadRemote`。

- 改写或重编码 `settings.*.js`。

- 改变 `bmLoadSettings()` 加载顺序。

静态保留的原厂 URL 可以只是缓存键或配置键。是否联网必须用 DNS、TLS SNI、HTTP Host 证明，不能看到字符串就判定失败。

## 3. 原厂 SDK、崩溃和广告隔离

### 3.1 自动初始化与隐藏初始化要分别查

应检查并按需关闭：

- Firebase provider/Remote Config 自动初始化。

- AppLovin、GMA、Facebook Audience Network、Unity Ads 等原厂独立初始化。

- SafeDK 的静态入口、生命周期和真实 `start` 调用。

- 原厂 APM 的配置拉取和上传实现。

SafeDK 的真实入口可能不在显眼的 Provider，而在 `com/safedk/android/SafeDK.smali`。APM 也可能隐藏在短包名混淆类中。只删 Manifest provider 不等于组件已经停用。

### 3.2 Bugsnag 不能简单把 start 置空

把 `Bugsnag.start()` 直接 no-op 后，原壳后续仍调用 `Bugsnag.setContext`，会导致：

```text
IllegalStateException: You must call Bugsnag.start before any other Bugsnag methods
```

正确折中：

- 保留 Bugsnag 初始化骨架，满足壳层调用顺序。

- 在 `DefaultDelivery` 等实际交付层 no-op，阻断网络上传。

- 允许出现 `BugsnagNDK initialization` 等本地初始化日志，但要求 Bugsnag DNS/TLS/HTTP 命中为 0。

报告应写“交付层已关闭”，不要错误宣称“组件完全没有初始化”。

### 3.3 Hisavana 的供应商不等于原厂独立广告

Hisavana 聚合链可能最终选择 AdMob adapter。看到 `mediator=AdMob Network` 不代表原厂 GMA 独立链已复活。应根据请求发起者、聚合回调和展示事件判断归属：

- Hisavana 发起、Hisavana 回调、Hisavana `ad_show`：属于目标聚合链。

- 原厂 Application/Provider 独立初始化并直接请求：才属于应关闭的原厂链。

因此 Hisavana 实际依赖的 adapter 可以 dormant 保留，不要按 SDK 名称一刀切删除。

## 4. Athena 上报与内容净化

目标事件只送 Athena 的目标 appid（本案例为 `5943`），SnowBall 的 `4987` 只用于归因注册，不应成为业务事件目的地。

V35 还发现：网络请求已经被本地守卫阻断，但旧 URL 会作为诊断字段被 Athena 事件带出。处理时应在 `BMAthenaBridge.callNativeDataUpload` 等最终封装点净化 hostname。

不要只替换完整 URL。Android `JSONObject` 可能把斜杠编码成 `https:\/\/...`，导致全文匹配失效；替换 `gametester.afafb.com` 这样的 hostname 更稳妥。

Athena 最低验收证据：

- 初始化/事件日志中 `appid=5943`。

- 上传结果 `upload success code=0`。

- 不出现把业务事件发送到 4987 的证据。

- 传输内容不携带原厂可识别 URL、域名或账号标识。

## 5. 构建与 Seed 完整性

### 5.1 apktool 资源失败不一定等于 DEX 失败

逆向基座可能存在重复资源 ID，apktool 在资源链接阶段失败，但新 smali 仍可先编译出有效 DEX。已验证的兼容构建方式是：

1. 从修改后的 stage 工程编译新 DEX。

2. 将新 DEX 覆盖进只读的已知良好基线 APK。

3. 保留基线资源结构。

4. `zipalign -p 4` 后用正式证书签名。

5. 检查 APK 内新标记、DEX 哈希、版本和证书。

不要把已知的资源链接失败误判为所有代码都没编译。也不要并发启动两个写同一输出目录的构建任务；共享中间产物会造成随机失败或混入旧 DEX。

### 5.2 Seed 要逐项验证

禁止用目录大小判断资源完整性。必须检查 settings、manifest、cacheList、文件存在性和哈希，最低门禁：

```text
missing=0
unmapped_bundles=0
hash_conflict=0
```

## 6. 真机验收

最终结论必须在真实联网手机上完成，模拟器只能做阶段回归。

### 6.1 启动和实玩

- 清装；若系统卸载返回 `DELETE_FAILED_INTERNAL_ERROR`，执行 `pm clear`，确认 Welcome 首启流程重新出现，并记录该替代步骤。

- 显式启动 `org.cocos2dx.javascript.AppActivity`。部分真机使用通用 monkey/resolve 方式会卡住。

- 联网冷启动三次、断网冷启动三次。

- 每组至少完成一局或产生真实得分，再恢复网络复验。

- Android 14 通知权限弹窗会打断计时；处理弹窗后废弃该次结果并重新测试。

Release 机型上 `console.log` 可能不进入 logcat。若 `bm_scene_ok` 不可见，可用首个可玩业务事件（如 `usr_data_guide_3_end`、`usr_data_enter_game`）加截图和实际拖拽得分作为等价证据。

### 6.2 网络证据

logcat 中原厂关键字为 0 只能说明日志没暴露请求，不是网络层证明。第三方 QA 应使用 PCAPdroid、测试路由器、Charles/mitmproxy 或等效抓包，至少检查：

- DNS query。

- TLS SNI。

- HTTP Host。

- 目标 IP、协议、触发步骤和连接次数。

对 `afafb.com`、HungryStudio、BlockBlast、youxi123、Bugsnag 等原厂域名族，三层命中都必须为 0。Athena/Hisavana/Palm/Aha 等目标渠道请求应保留成功证据。

## 7. 常见误判与禁止做法

| 现象 | 错误结论 | 实际处理 |
|---|---|---|
| APK 中仍有原厂 URL | 一定仍联网 | 可能只是 inert cache key；用 PCAP 判定 |
| 改了默认 URL 仍请求原地址 | 替换未打包 | 先查 URL 参数、trait、数据库和 patch 覆盖 |
| 阻断后日志疯狂重试 | 需要更强全局断网 | 返回 schema-compatible inert success |
| Bugsnag 有初始化日志 | 仍在上传 | 检查 delivery 层与 DNS/TLS/HTTP |
| Hisavana 展示 AdMob | 原厂广告复活 | 按聚合请求/回调链判定归属 |
| `bm_scene_ok` 没日志 | 游戏未进入 | Release logcat 可能丢 console；用事件、截图、实玩交叉证明 |
| 模拟器通过 | 最终合格 | 最终必须在真实手机网络下抓包与实玩 |

## 8. V35 案例证据

- 包：`BlockMaster_v35_palm_full.apk`

- 包 SHA256：`B83BD3645CFB927D82655A9B1A12D8C4474D6CD16470081761B48371A28FA182`

- 证书 SHA256：`5ed39fe63ace82381412d5847c77000341baf399384ac64d036960cccde0ad29`

- 静态门禁：`modules/sdk-replacement/scripts/verify_vendor_isolation.py`（原 verify_v35 系列已并入该通用脚本）

- Seed 门禁：`modules/sdk-replacement/scripts/prepare_offline_seed.py --check-only`

- 第三方说明：`docs/BlockMaster_V35_第三方QA验收说明.md`

- 一条龙工作流：`modules/sdk-replacement/SKILL.md`（A/B/C 三档 + P0-P8 阶段；本案例按 B 档"断网离线内置"执行）

- 真机结果：联网三次、离线三次冷启动通过；实际拖拽得分后恢复联网通过；Athena `appid=5943` 且 `code=0`；Seed `missing=0`、`unmapped_bundles=0`、`hash_conflict=0`。

最后原则：隔离的是原厂“实际连接和数据交付”，不是无差别删除所有旧类和字符串。任何兼容骨架都可以保留，但必须通过运行路径和网络层证据证明它不再向原厂发送数据。
