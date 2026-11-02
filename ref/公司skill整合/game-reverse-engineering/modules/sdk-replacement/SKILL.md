---
name: sdk-replacement
description: Use when 用户要完全替换或切断原游戏所有联网与 SDK、把联网内容下载并内置到游戏、接入替代 SDK，或只要"原厂联网隔离 + 新 SDK 联网切换"的一条龙改造；适用于 Cocos Creator JSB / Unity IL2CPP / Android 原生壳 APK。先按意图分发到 cocos-reverse-engineering、gameplay-logic-reverse 证据链与本模块脚本。
version: 1.2.0
updated: 2026-10-12
---

# 完全替换 SDK 一条龙工作流

## 执行卡（先用这张卡，再读正文）

**我管什么**：把原游戏的所有联网与 SDK 完全替换或切断——切断原厂连接、把联网内容内置进包、接入替代 SDK，覆盖 Cocos Creator JSB / Unity IL2CPP / Android 原生壳 APK；不管无合法分析权的项目、需要保留原厂联机的网游、纯 Web 小游戏。

**第一步做什么**：先和需求方钉死 A（联网供应商切换）/ B（断网离线内置）/ C（二进制级完全替换）三种结局中的**一个**，写进 `acceptance_contract.md`，再建 `baseline.json`（APK 与证书 SHA-256、versionName/Code、重打包基底、设备、抓包工具版本、起止时间）。

**做完怎么算完成**：
- `baseline.json`、`surfaces.json`、`isolation-config.json`、`acceptance_contract.md` 四件齐全，且被后续脚本实际读取。
- blocked 域族三层（DNS query / TLS SNI / HTTP Host）0 命中；A 档另需新渠道 allowed 域族成功请求，B 档则新旧供应商均无请求并证明内容本地可玩。
- Seed 门禁 `missing=0`、`unmapped_bundles=0`、`hash_conflict=0`，且不是靠目录大小判出来的。
- 真机联网冷启动 ×3、断网冷启动 ×3，每组至少产生真实得分，恢复网络复验通过。
- 交付报告由 `modules/sdk-replacement/scripts/gen_sdk_acceptance_report.py` 生成，并附义务清单与未知清单。

**红线（不可违反）**
- 结局未钉死前不许动手，也不许提前宣称"C 已完成"；按验收契约选择 A 或 B；C 的二进制摘除在 Phase 6 单独评估，并声明其运行模式遵循 A 还是 B。
- 模拟器与 logcat 只算阶段证据：最终结论必须来自真机的 DNS/TLS/Host 三层抓包，logcat 里原厂关键字为 0 不算断。
- Seed 完整性 = 文件存在性 + 哈希 + manifest 自洽；禁止只用目录大小判断完整。
- 被拦的可选功能（配置/埋点/实验）返回 schema 兼容的 inert success，不得抛 rejection / HTTP error；但奖励广告与支付不可用必须明确失败且不发货，不许用 inert success 混过去。
- 隔离的是"实际连接与数据交付"，不是无差别删类；删类前先删引用链，一次只删一个 SDK。
- 示例里的包名、域族、appId、证书、路径都是案例值，必须传入本项目自己的配置，禁止照搬。

**卡住时按顺序读**：
- 广告无反馈、奖励回调、重复领取、后台弹窗 → `modules/sdk-replacement/references/ad-fallback-and-reward-lifecycle.md`。
- SeedCopier 固化模式 → `modules/cocos-reverse-engineering/references/android-reskin-repack.md` §三。
- 抓包该留什么、不该留什么 → `modules/vision-device-testing/references/collection-boundaries.md`。
- JNI、二进制消息、非 JSON 协议取证 → `modules/sdk-replacement/references/custom-protocol-evidence.md`。

全局五步循环与六条铁律见 `references/execution-protocol.md`。

范围：方法属于 `GENERALIZED_PATTERN`，可迁移到同类项目；包名、域名、appId、证书、路径、Trait 名、事件名、hook 偏移、资源数量属于 `DO_NOT_COPY_LITERAL_VALUES`，每个项目必须重新取证。BlockMaster V35 案例的证据形态见 `modules/cocos-reverse-engineering/references/android-blockmaster-v35-vendor-isolation-and-real-device-qa.md`（只抄方法，不抄数值）。

## 广告反馈专项入口

仅处理广告未接入、按钮无反馈、失败弹窗或重复领奖时，先读 [广告未接入与奖励生命周期](references/ad-fallback-and-reward-lifecycle.md)。该专项盘点业务入口、同步/异步返回、请求与领取幂等、暂停归属和真实回调 QA；不自动启动以下供应商替换全流程，也不新增未知商业玩法。Godot、Unity 与 Cocos 均按当前调用契约应用。

## 1. 目标与三种"替换"结局

动手前先和需求方钉死一个结果（三者不同，验收标准也不同）：

| 结局 | 定义 | 必要条件 | 验收一句话 |
|---|---|---|---|
| A. 联网供应商切换 | 切断原厂所有实际网络连接，新 SDK（广告/统计/账号/内购）自己联网 | 隔离原厂 + 新 SDK 接入 | PCAP 中原厂域族 DNS/TLS/Host 三层 0 命中；新域族 >0 且成功 |
| B. 断网离线内置 | 原厂与新 SDK 都不联网，联网内容（远端 bundle/trait/配置）已内置本地 | 全部内容内置 + 本地响应兼容原 schema | 联网/断网冷启动均进入可玩场景；无任何下载行为 |
| C. 二进制级完全替换 | 原 SDK 的 DEX/类/资源/Manifest 条目从包里彻底消失 | 证据驱动的类/资源/Manifest 摘除 + A/B 回归 | 新包静态扫描不到原 SDK 类；全链路回归通过 |

**关键判断**：A 已满足绝大多数"替换 SDK"商业化诉求，且风险最低；C 是"彻底消失"但不是"必须做到"。同一运行模式不能同时声称 A（新 SDK 联网）和 B（新旧 SDK 均不联网）。供应商切换并内置远程内容通常是 A 档加 Seed；若用户要求在线/离线双模式，分别写 A/B 的契约和验收证据。C 在 Phase 6 评估并明确其运行模式，不提前宣称完成。

## 2. 适用与不适用

- 适用：Cocos Creator 2.x/3.x JSB（`libcocos2djs.so` + `assets/` + 远程 bundle/Seed）；Unity IL2CPP（远程 Addressables/AssetBundle + 原生 SDK 壳）；原生 Java/Kotlin 壳 + 广告/统计 SDK 的 Android APK。
- 不适用：纯 Web/小游戏（走另类离线化流程，可参考外部资料但本模块验收以 APK 为准）；需要保留原厂服务器联机的网游（本流程只做隔离不做反向代理）；没有合法分析权的游戏（先确认授权范围）。

## 3. 前置与依赖

1. 已读 `modules/cocos-reverse-engineering/SKILL.md`（Phase 1-3 提包/解密）与 `modules/gameplay-logic-reverse/SKILL.md`（远端 bundle/Trait 证据链）。
2. 本项目前置阅读：`modules/cocos-reverse-engineering/references/android-jsb-reskin-pitfalls.md`（DEX/JS-Java 桥/SeedCopier/SDK 注入踩坑）、`android-reskin-repack.md` §三（SeedCopier 模式）。
3. 工具：apktool（或 jadx→smali 编译链）、adb、zipalign/apksigner、Python（本项目脚本均走 `python`）、真机 + 抓包（PCAPdroid / mitmproxy / Charles 之一）、可写主机跑下载。
4. 所有脚本都是**参数化通用模板**：默认示例值属于案例，使用前用 `--help` 核对；涉及项目私有值（包名、域族、appId、证书、路径）必须传入你自己的配置，禁止直接照搬示例。

## 4. 八阶段工作流

```text
Phase 0 取证与目标声明 ──► Phase 1 原厂联网面盘点 ──► Phase 2 隔离策略契约
        │                                                     │
        ▼                                                     ▼
Phase 3 联网内容内置 ──► Phase 4 原厂隔离实现 ──► Phase 5 新 SDK 接入
        │                                                     │
        ▼                                                     ▼
Phase 6（可选）二进制彻底移除 ──► Phase 7 构建与 APK 门禁 ──► Phase 8 真机验收与交付
```

### Phase 0：取证基线与目标声明（半天）

**产出**：`baseline.json`。固定记录：APK SHA-256、签名证书 SHA-256、versionName/Code、直接重打包基底（原版还是上一版改动）、设备序列号、抓包工具版本、开始/结束时间。**不记录不写结论。**

```bash
python modules/sdk-replacement/scripts/scan_original_sdk_surfaces.py --apk-dir <decoded> --out surfaces_baseline.json
shasum -a 256 <apk>
```

- 先确认"包内字符串"≠"运行时连接"：静态结果只做线索，永远以 Phase 8 网络层证据为准。
- 用同一基底做三次独立解包，记录哈希/文件数变化，排除工具随机性。

### Phase 1：原厂联网面盘点（静态 + 动态）

**目标**：列出一张"原厂域族 + SDK 载体 + 自动初始化 + 事件链路"清单。

1. 静态扫描（`scan_original_sdk_surfaces.py`）：Manifest provider/activity/service、`assets/…/settings`、JS 源码、smali 类名、keys.xml 中的 API key、URL 正则、appId 正则。
2. 动态捕获：`gameplay-logic-reverse/scripts/frida_capture_eval.py`（hook eval/require 拿运行时明文）、logcat 的请求日志、PCAP 首跑抓包。
3. 归类域族：原厂（block/严禁）vs 目标渠道（allowed/保留）vs 中立 CDN（先归原厂，后续按证据迁移）。
4. 绘制链路：谁发请求（XHR/fetch/http.requestAsync/Cocos downloader/原生 OkHttp/WebView）、谁初始化（Provider/Application/隐藏入口）、谁消费回调（广告展示/埋点上报）。

**输出**：`surfaces.json`、`network_capture/*.csv`（字段：`ts,direction,type(QUERY|TLS|HOST),domain,ip,path,status`）。

**采集边界**：抓包按[采集负面清单](../vision-device-testing/references/collection-boundaries.md)执行——只留 DNS/TLS/Host 元数据与状态码，不留请求/响应 body、Cookie、授权头与凭据；logcat 或截图中混入凭据时立即剔除并记录剔除动作。

### Phase 2：隔离策略契约（定"断什么、留什么、本地化什么"）

写 `isolation-config.json`，后续脚本都读它：

```json
{
  "project": "<your-project-id>",
  "blocked_domain_families": {"<vendor-a>": ["*.a.com", "a-cdn.com"], "<vendor-b>": ["*.b.net"]},
  "allowed_domain_families": {"<new-sdk>": ["*.new-sdk.io"]},
  "js_rewrites": [{"file": "assets/.../index.js", "old": "<vendor-base-url>", "new": "<local-endpoint-scheme>"}],
  "native_off": [{"sdk": "<vendor-a>", "kind": "provider|activity|start|delivery"}],
  "seed": {"from_device_patch": "<device-pull>/files/patch", "from_device_gamecaches": "<device-pull>/files/gamecaches", "apk_asset_root": "assets/remote_seed", "marker": ".seed_done"},
  "target_events": ["<your-new-sdk-event>"]
}
```

**验收契约**（写进 `acceptance_contract.md`）：blocked 域族三层 0 命中；allowed 域族至少一个成功请求；Seed 门禁 `missing=0/unmapped_bundles=0/hash_conflict=0`；断网冷启动进入可玩场景。

### Phase 3：联网内容内置（离线化）

**Cocos 2.x/3.x 远程 Bundle**：`_CCSettings` 里有 `remoteBundles`（远程名单）与 `bundleVers`（全部 bundle 版本）。远程 bundle 有依赖链，必须先 `loadBundle` 拿到 `deps` 再按拓扑加载。

1. 生成清单：`python modules/gameplay-logic-reverse/scripts/gen_remote_manifest.py --settings <settings.js> --url-template "<cdn>/<bundle>/<version>/config.json" --out remote_manifest_full.json`（URL 模板按本项目 CDN 实际结构填）。
2. 批量下载：`python modules/gameplay-logic-reverse/scripts/download_remote_trait_bundles.py --manifest remote_manifest_full.json --out remote_traits/raw`（断点续传、403 记账、重试）。
3. 关联本地目录：`python modules/gameplay-logic-reverse/scripts/associate_trait_dirs.py --local <decoded>/assets --remote remote_manifest_full.json --out local_dir_to_remote_bundle.json`。
4. 逐目录证据：`python modules/gameplay-logic-reverse/scripts/trait_dir_evidence.py --heap code_windows.json --catalog trait_catalog.txt --json-out trait_dir_evidence.json`。
5. **SeedCopier 固化**（参考 `modules/cocos-reverse-engineering/references/android-reskin-repack.md` §三）：

- 真机跑一次原版，等远程内容下载完，pull `files/patch` + `files/gamecaches`；
- 放进 `assets/remote_seed/patch`、`assets/remote_seed/gamecaches`；
- 先核对当前真实加载器读的是 filesDir 根目录还是其子目录；以下示例仅用于已证实的 files/patch、files/gamecaches 布局，其他布局显式调整 roots / target-subdir。
- 用 `python modules/sdk-replacement/scripts/generate_seed_copier.py --package <your.pkg> --asset-dir assets/remote_seed --roots patch,gamecaches --target-subdir . --marker .seed_done --out SeedCopier.java` 生成拷贝类；
- 在 `Application.onCreate` 的 `super.onCreate()` **之后**、壳初始化**之前**调用；标记文件存在则跳过；递归拷贝；写标记。

6. 门禁：`python modules/sdk-replacement/scripts/prepare_offline_seed.py --seed-out <apk-project>/assets/remote_seed --manifest <project.manifest> --check-only`，输出必须满足 `missing=0`、`unmapped_bundles=0`、`hash_conflict=0`。**禁止只用目录大小判断完整性。**

**Unity/Addressables**：远程组需离线模式时，将远程 catalog+asset bundles 加入 StreamingAssets 或本地服务器目录，并把 `remote` URL 指回本地；参考 Unity Addressables "include remote in build for offline use" 讨论（见文末外部参考）。本模块脚本按文件级通用，不依赖引擎。

### Phase 4：原厂隔离实现（最小补丁）

原则：**隔离的是原厂"实际连接和数据交付"，不是无差别删除所有旧类和字符串。** 任何兼容骨架可保留，但必须用运行路径 + 网络层证据证明它不再向原厂发数。

1. **JS 层**：只拦截明确原厂域族的请求出口（XHR/fetch/项目通用 `Http.requestAsync`/Cocos downloader），白名单外放行目标渠道。禁止：包装 `jsb.reflection.callStaticMethod`、顶层禁用 `cc.assetManager.loadRemote`、改写 `settings.*.js` 加载顺序。
2. **返回 schema 兼容的 inert success**（仅限可选配置/诊断，不适用于奖励广告或支付；这些能力不可用时必须明确失败且不发货）：被拦的可选功能（配置/埋点/实验）返回 `{}`/空列表/本地 trait，**不要**抛 rejection/HTTP error/语法错误——否则触发重试风暴和加载流程拖死（参考 V35 复盘的 `cocos_res_reporter` 案例）。若本地响应参与通用请求流程，要填 timing/URL/HTTP code 并先调 `handleServerResponse`。
3. **URL 参数旁路必须堵死**：Test 环境 getter 可能读 `getUrlParameterValue("traitServerUrl")` 把地址改回原厂。默认值、URL 参数、远程 trait、patch 参数、数据库配置四处都要查；用运行日志确认最终解析 URL。
4. **原生层**：分别检查并关闭——Firebase/Remote Config provider 自动初始化、AppLovin/GMA/FAN/Unity Ads 独立初始化、SafeDK 静态入口与真实 `start`、APM 配置拉取与上传。只删 Manifest provider ≠ 组件停用；隐藏入口要单独定位。
5. **崩溃/APM 交付层 no-op**：保留初始化骨架满足调用顺序，在 `DefaultDelivery` 等实际交付层阻断上传。允许本地初始化日志，要求 DNS/TLS/HTTP 命中为 0。报告写"交付层已关闭"，不要宣称"完全没有初始化"。
6. **内容净化**：在最终封装点（如 `xxxBridge.callNativeDataUpload`）净化 hostname/appid 等诊断字段；注意 JSON 会转义斜杠（`https:\/\/...`），替换 hostname 比替换完整 URL 稳妥。
7. **归属判定**：聚合广告链（如某聚合最终选择 AdMob adapter）按"请求发起者/聚合回调/展示事件"判断归属，不按 SDK 名一刀切删除。

### Phase 5：新 SDK 接入

两种接入层，按目标选：

| 层 | 做法 | 适合 |
|---|---|---|
| JS 兼容层（快） | 用本地 JS/JSON 实现原调用契约（同一函数名、同 schema、同回调），入口指向本地实现 | 只换"供应商"，业务侧少改代码 |
| 原生 sidecar（稳） | 新 SDK 以独立模块注入，通过桥接注册到现有入口；原 SDK 类保留或摘除 | 需要原生能力（支付/推送/合规）或 C 级彻底替换 |

要点：

- 初始化顺序：新 SDK 初始化放壳 Application 后期或首个业务场景，避免与 SeedCopier/原厂骨架抢时序；同一 epoch 唯一 owner。
- 回调契约：新 SDK 的异步回调必须由单一 owner 提交；广告前后恢复、生命周期暂停/恢复不能丢。
- 与守卫共存：新 SDK 域族加入 `allowed_domain_families`，否则会被白名单误伤。
- 事件/埋点：确认目标事件最终只送到目标 appid，不把原厂可识别 URL/账号标识带出。

### Phase 6（可选）：二进制级彻底移除

仅当 Phase 1 证据完整且需求方确认"类必须消失"时执行：

1. 按类/资源清单摘除：DEX 类（smali 删除 → 重新编译 DEX）、Manifest provider/activity/service/permission、资源（layout/strings/keys）、SO 内导出（如需，单独评估）。
2. 保留"兼容骨架"判断：若原壳其他类仍引用被删类，会 `NoClassDefFoundError`——先删引用链，再删类；一次只删一个 SDK，构建后回归。
3. 重打包：DEX 覆盖（不是整包反编译再回编）、`zipalign -f -p 4`、apksigner；`extractNativeLibs=false` 时 `.so` 必须 ZIP_STORED。
4. 静态验收：`scan_original_sdk_surfaces.py` 复查被删 SDK 标记为 0；不足以证明无联网，仍需 Phase 8。

### Phase 7：构建与 APK 门禁

- 构建链：新 DEX 编译 → 覆盖只读已知良好基线 APK → 保留基线资源结构 → `zipalign -p 4` → 正式证书签名。apktool 资源链接失败 ≠ DEX 失败（见 V35 复盘）；不要并发两个写同一输出目录的构建。
- 静态门禁：`python modules/sdk-replacement/scripts/verify_vendor_isolation.py --apk-dir <decoded> --isolation-config isolation-config.json --network-evidence network_evidence.json --seed-dir <seed> --manifest <project.manifest> --out verification.json`。
- 门禁语义：blocked 域族三层 >0 → FAIL；Seed `missing/unmapped/hash_conflict` 任一 >0 → FAIL；被禁 SDK 静态标记存在只做风险提示（说明"字符串仍在但连接已断"），不直接判 FAIL。
- 冒烟：冷启动 3 次 + 联网/断网各 3 次 + 一局实玩。

### Phase 8：真机三层网络验收与交付

**模拟器只能做阶段回归，最终结论必须在真实联网手机上获得。**

1. 清装（`DELETE_FAILED_INTERNAL_ERROR` 时用 `pm clear` 替代并记录）；显式启动主 Activity；处理系统弹窗后废弃该次结果。
2. 联网冷启动 ×3、断网冷启动 ×3；每组至少一局或产生真实得分；恢复网络复验。
3. 抓包看三层：**DNS query、TLS SNI、HTTP Host**，外加目标 IP/协议/触发步骤/连接次数。只看到 logcat 原厂关键字为 0 不是网络层证明。
4. 目标渠道（新 SDK）必须保留成功证据（DNS+TLS+HOST 命中、业务事件、平台后台确认）。
5. 生成交付报告：`python modules/sdk-replacement/scripts/gen_sdk_acceptance_report.py --evidence network_evidence.json --verification verification.json --contract acceptance_contract.md --out 验收报告.md`。

### Godot 重构项目：先恢复契约，再接供应商

当目标是 Unity/Cocos → Godot 重构，且正式 AdMob/分析/支付参数尚未提供时，先交付可替换插件骨架，不把“暂无 SDK”当成跳过外围系统的理由：

1. 用一个 Autoload facade 统一 Ads、Analytics、Consent、Remote Config、Attribution、Crash、IAP、Push、Social；业务脚本禁止直接引用供应商类。
2. 每类能力通过 adapter 注入。默认 Null adapter 明确返回 unavailable；Local adapter 只记录本地诊断，不伪造上传或展示成功。
3. service enabled 与用户 consent 是两道门。consent 必须本地持久化，并在 adapter 初始化前恢复；门禁必须发生在 adapter 调用、广告请求记账和奖励 ledger begin 之前，否则重启会丢失选择，未同意/被抑制的激励请求也会残留 pending 事务。专项测试使用隔离的 `user://` 路径，避免污染真实玩家选择。
4. 奖励只接受供应商 earned callback，并要求非空 proof；transaction ID 持久化，重复回调、重放和进程重启均不得重复发货。广告 adapter 不直接修改金币或道具。
5. 把广告关卡门槛、单会话次数、冷却、动画/Gameplay/modal 抑制、缓存数量和 timeout 写入独立 policy config。静态配置证实与运行时推断分别标级。
6. AB/Remote Config 先 stage，再在 app_start/home_enter/level_start/settlement_closed 等稳定边界 apply；Gameplay 或完成动画期间拒绝热切换。profile key 使用本地生成的匿名值，不放入事件属性。
7. 建立事件目录：唯一事件名、owner、必填/可选字段、证据级别、PII 规则。未知事件或缺少必填字段不得进入 adapter。
8. 动态路径加载的 JSON/schema/policy/event catalog 必须显式加入 Godot export preset；桌面存在不能证明 APK 包内可达，最终用安装包启动与 logcat 验证。

这个阶段只能称“外围契约与离线 provider 已还原”。真实供应商完成仍需 SDK 二进制、应用/广告位配置、隐私后台、平台回执和 Phase 8 网络验收。

## 5. 证据等级与常见误判

| 证据 | 等级 | 说明 |
|---|---|---|
| APK 静态字符串 | 线索 | 不证明运行时会连；可能有 inert cache key |
| Manifest/SDK 类存在 | 线索 | 不证明初始化和连接 |
| 模拟器 logcat | 阶段证据 | 不是网络层证明 |
| 真机 DNS/TLS/HOST 抓包 | 决定证据 | 三层全 0 才算断 |
| 目标渠道平台后台 | 佐证 | 与抓包、业务事件互相印证 |

| 现象 | 错误结论 | 实际处理 |
|---|---|---|
| 改了默认 URL 仍请求原厂地址 | 替换未打包 | 查 URL 参数 / trait / 数据库 / patch 覆盖 |
| 阻断后日志疯狂重试 | 需要更强全局断网 | 返回 schema 兼容 inert success |
| Bugsnag 有初始化日志 | 仍在传 | 看 delivery 层 + 三层抓包 |
| 聚合链展示别的网络 adapter | 原厂广告复活 | 按请求/回调/展示归属判定 |
| 真机无 console 日志 | 游戏没进 | 用业务事件 + 截图 + 实玩交叉证明 |
| 目录大小一致 | Seed 完整 | 文件存在性 + 哈希 + manifest 自洽 |

## 6. 脚本清单

| 脚本 | 用途 |
|---|---|
| `modules/sdk-replacement/scripts/scan_original_sdk_surfaces.py` | 静态盘点 SDK 载体/URL/appId/自动初始化点 |
| `modules/sdk-replacement/scripts/capture_network_evidence.py` | CSV 网络证据分类（QUERY/TLS/HOST 三层） |
| `modules/sdk-replacement/scripts/prepare_offline_seed.py` | Seed 固化 + `--check-only` 完整性门禁 |
| `modules/sdk-replacement/scripts/generate_seed_copier.py` | 生成 SeedCopier 拷贝类模板 |
| `modules/sdk-replacement/scripts/verify_vendor_isolation.py` | 隔离静态+网络+Seed 三门禁汇总 |
| `modules/sdk-replacement/scripts/gen_sdk_acceptance_report.py` | 生成验收报告 Markdown |
| `modules/gameplay-logic-reverse/scripts/gen_remote_manifest.py` 等 | 远程清单/下载/目录关联/逐目录证据/算法 Trait/验收报告/Frida 捕获（详见玩法逻辑模块） |

## 7. 交付物清单

`baseline.json`、`surfaces.json`、`isolation-config.json`、`acceptance_contract.md`、`remote_manifest_full.json`、`remote_traits/`、`SeedCopier.java`、改动 diff 清单、`verification.json`、`network_evidence.csv`、`验收报告.md`、改动后 APK（含 SHA-256/证书）。

交付时同时附带[义务清单](references/obligation-ledger-template.md)（按档位实例化、逐条关闭）与[未知清单](../../references/unknowns-ledger-template.md)（交付必附）。未执行档位按豁免记录，不写"已完成"。

## 8. 外部参考（碎片，非一条龙）

- Cocos 远程 Bundle 离线化实战（OPPO 快游戏移植）：https://www.liesauer.net/blog/post/1040.html — `remoteBundles`/`bundleVers` + 依赖链拓扑加载。
- Cocos 官方论坛"Can Remote Bundle be part of APK as well?"：https://forum.cocosengine.org/t/can-remote-bundle-be-part-of-apk-as-well/56729 — `settings.json` 的 `remoteBundles` 重定向实现。
- 预下载 Bundle 到本地讨论：https://forum.cocos.org/t/topic/158586 — `preloadDir` 与首次 active 后缓存。
- Unity Addressables 离线/内置远程内容：https://docs.unity3d.com/Packages/com.unity.addressables@1.18/manual/AddressableAssetsHostingServices.html
- Android 应用代码打补丁/库注入通用方法（OWASP MASTG）：https://mas.owasp.org/MASTG/techniques/android/MASTG-TECH-0041/
- 反例——全应用无效代理断网（会断 WebView、无法选择性保留新 SDK）：https://www.52pojie.cn/forum.php?mod=viewthread&tid=1792928 — A 档使用域族级隔离保留新 SDK；B 档按明确的全供应商断网契约本地化，不能套用 A 档验收。

## 版本记录

完整版本史见 `references/changelog.md`（模块级）；总集级行为变更见根 `references/CHANGELOG.md`。专项里程碑记入 [落地日志](references/landing-log.md)，不把离线测试升级为厂商验收。

## JNI 与非 JSON 协议取证（按需）

SDK 的 Java 声明不能覆盖 JNI 动态注册面；需要追 native owner 时读 [原生取证](../../references/native-code-evidence.md) 和 [JNI/DEX 恢复门禁](../../references/protected-runtime-recovery.md)。二进制消息或离线响应需要帧/状态契约时读 [自定义协议取证](references/custom-protocol-evidence.md)，继续执行本模块真机网络验收。

## 传音 SDK 与 Seed 生成专项入口

- Transsion / Hisavana / Athena / AhaPush / PalmUpdate：读 `modules/sdk-replacement/references/android-transsion-sdk-suite.md` 与 `modules/sdk-replacement/references/transsion-material-pack-index.md`，当前配置与版本重新核对。
- 接口接入示例为 `modules/sdk-replacement/assets/transsion/`；脱敏素材回收脚本为 `modules/sdk-replacement/scripts/extract_transsion_sdk_pack.py`。示例不构成 SDK 运行成功证据。
- Seed 参数/目标布局读 `modules/sdk-replacement/references/seed-copier-generation.md`；旧参数和 v8.5 roots/Java/Smali 接口已合并，Smali 只输出未实现骨架。

B 档的隔离配置应把目标应用全部新旧供应商域族纳入 blocked，allowed_domain_families 留空；verify_vendor_isolation.py 的 allowed 检查据配置执行。不得用 --allow-missing-allowed 的 WARN 代替 A 档新渠道成功证据，B 档也须按完整联网面盘点和真机证据确认无漏项。

Seed 验收必须把 `--manifest` 指向本项目可解析的原始或本地化清单，路径与内容格式都按 prepare_offline_seed.py 的真实输入契约核对；只传 --seed-dir 不会验证成功。
