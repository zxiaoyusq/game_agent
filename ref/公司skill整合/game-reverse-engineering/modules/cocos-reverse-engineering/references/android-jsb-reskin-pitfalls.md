# Android JSB 换皮 + SDK 注入踩坑集（BlockMaster Pro 10.4.7）

> **何时读我**：遇到 DEX/JS-Java 桥/SeedCopier/SDK 注入踩坑——换皮与 SDK 注入同时做、apktool 资源重链失败、想全局禁 jsb.reflection、Seed 或远程 bundle 覆盖本地改动时读我。
> **读完能做到**：区分资源链失败与 DEX 编译失败，只对确认的原厂域名做白名单外阻断而不全局禁桥，按发起者/回调/展示判定聚合广告归属，并照构建交付检查单收口。
> **范围**：`GENERALIZED_PATTERN` + `CASE_ONLY_BLOCKMASTER`

范围：`CASE_ONLY_BLOCKMASTER` · `DO_NOT_COPY_LITERAL_VALUES`。本文是 V30–V35 案例链的前置阅读：记录"换皮与 SDK 注入同时发生"时最容易翻车的 DEX、JS-Java 桥、聚合广告/埋点和 Seed 拷贝四类问题。包名、版本号、类名、域名、appId、证书与结论只属于该项目；其他项目只能迁移每条末尾的"可迁移要点"。

## 0. 为什么单独建这一篇

换皮（资源替换）和 SDK 注入（广告/埋点/账号）在同一个 APK 里互相干扰：

- 换皮动的是 `assets/` 与资源配置，SDK 注入动的是 `classes.dex` 与 `lib/`；
- 两者都可能触碰 `settings.js`、`jsList`、`bundleVers` 和启动顺序；
- 只验证"画面变了"或"广告弹了"都不够：要同时回归主玩法、网络隔离、上传与启动。

V30–V35 的逐项案例分别在：

- `android-blockmaster-v31-ad-resource-and-ui-removal.md`（Hisavana 资源 / More Games / V30-V31 构建链）；
- `android-blockmaster-v35-vendor-isolation-and-real-device-qa.md`（原厂联网隔离与真机三层网络证据）；
- `android-reskin-repack.md`（版本重基、split ABI、Seed、签名门禁）。

## 1. DEX 层：换皮包 + SDK 注入包的版本对齐

### 1.1 直接基底必须唯一且可复现

BlockMaster 当前工程的直接重打包基底是 Block Blast 10.4.7；9.5.0 只用于历史对照。混合两个版本会把 owner、事件顺序和资源格式拼成一套"原版代码"，后续所有门禁都会失真。

- 开工先记录：基底包 SHA256、证书 SHA256、versionName/versionCode、ABI 列表；
- 所有 smali/diff 都基于同一次 `apktool d` 输出，禁止跨反编译目录拼装；
- 构建产物重新校验 DEX 哈希、版本、证书、zipalign 与安装后设备 APK 哈希。

### 1.2 资源重链失败 ≠ DEX 编译失败

逆向基座可能存在重复资源 ID：apktool 在资源链接阶段失败，但新 smali 仍可先编译出有效 DEX。已验证的兼容构建方式：

1. 从修改后的 stage 工程编译新 DEX；
2. 将新 DEX 覆盖进只读的已知良好基线 APK；
3. 保留基线资源结构；
4. `zipalign -p 4` 后用正式证书签名；
5. 检查 APK 内新标记、DEX 哈希、版本和证书。

不要把资源链接失败误判成"所有代码都没编译"；也不要并发启动两个写同一输出目录的构建任务（共享中间产物会造成随机失败或混入旧 DEX）。

### 1.3 注入 SDK 的类不要无差别删除

聚合广告、埋点和 APM 常以短包名混淆类存在，Manifest provider 只是入口之一。隔离目标是"切断实际连接与数据交付"，不是把旧类删干净：

- 保留可证明 inert 的兼容骨架（如初始化桩 + 交付层 no-op）；
- 用运行日志、DNS/TLS/HTTP-Host 三层证据证明不再发数据；
- 报告写"交付层已关闭"而非"组件完全没有初始化"。

## 2. JS-Java 桥：`jsb.reflection` 是双刃剑

### 2.1 不要全局禁桥

`jsb.reflection.callStaticMethod` 同时承载游戏逻辑与 SDK 桥接，全局禁用会打烂主玩法。只对已确认的原厂域/原厂类做白名单外阻断，且优先在统一的请求入口（项目 Http.requestAsync/request、XHR、fetch、Cocos downloader）拦截，而不是在反射层一刀切。

### 2.2 settings / jsList 不能随意重编码

`settings.*.js`、`jsList`、`bundleVers` 是加载器与业务共同依赖的索引。改字段名、改编码或改变 `bmLoadSettings()` 顺序，会造成"看到了新配置但加载器没读"或"加载器读了但业务不认"的假替换。

- 只改值，不改结构和顺序；
- 用运行时日志确认最终解析结果，而不是只 grep 字符串；
- 静默保留的原厂 URL 可能只是缓存键/配置键，不能据此判"还在联网"。

### 2.3 URL 参数会覆盖静态替换

V35 曾出现：默认 trait 地址已改本地端点，但 Test 环境 getter 仍执行 `getUrlParameterValue(...)`，运行参数又把地址改回原厂。修复必须同时覆盖 URL 参数、远程 trait、数据库配置和 patch 参数，并最终以运行日志里的解析后 URL 为准。

## 3. Hisavana / Athena：聚合链与上报净化

### 3.1 供应商名 ≠ 独立链

Hisavana 是聚合链：最终可能选择某个 AdMob adapter。看到 `mediator=AdMob Network` 不等于原厂独立 GMA 链已复活。归属判定按"请求发起者 → 聚合回调 → 展示事件":

- Hisavana 发起、Hisavana 回调、Hisavana `ad_show`：属于目标聚合链；
- 原厂 Application/Provider 独立初始化并直接请求：才是应关闭的原厂链。

因此聚合链实际依赖的 adapter 可以 dormant 保留，不要按 SDK 名称一刀切删除。

### 3.2 事件目的地只送目标 appid

业务事件只送目标渠道的 appid；归因注册用的旧 appid 不应成为业务事件目的地。上报最后封装点（如 `callNativeDataUpload`）要做 hostname 净化：

- Android `JSONObject` 会把斜杠编成 `https:\/\/...`，全文 URL 匹配会失效；
- 直接替换 hostname（域名级）比替换完整 URL 稳；
- 检查上传结果 `code=0`、目的地 appid、事件内容不携带原厂可识别标识。

### 3.3 Bugsnag 类"置空 start"陷阱

把 `Bugsnag.start()` 直接 no-op 后，原壳继续调用 `setContext` 会抛 `IllegalStateException`。正确折中：保留初始化骨架满足调用顺序，在实际交付层（如 `DefaultDelivery`）no-op 阻断上传；允许本地初始化日志，但要求该组件 DNS/TLS/HTTP 命中为 0。

## 4. Seed / 远程 bundle：换皮头号暗坑

### 4.1 SeedCopier 实例

换皮后设备实际执行的可能不是主 APK 内的 `assets/remote_seed`，而是安装后拷贝到 `files/` 的 Seed。典型注入路径：

- 主 APK 内 `assets/remote_seed/...` → 首启后拷贝/释放到 `files/...`；
- `files/patch`、数据库、MMKV 中存在旧副本；
- 远程 bundle 依赖链（`remoteBundles`/`bundleVers` + dep-chain `loadBundle`）指向 `assets/remote_seed` 之外的位置。

### 4.2 验证方法

- 对主 APK Seed、`files/patch`、设备缓存分别做哈希与关键标记；
- 运行时确认"设备实际执行的是哪一份"；
- Seed 完整性逐项检查：settings、manifest、cacheList、文件存在性与哈希，最低门禁：

```text
missing=0
unmapped_bundles=0
hash_conflict=0
```

- 禁止用目录大小判断完整性。

### 4.3 网络替换要"兼容成功"

为可选原厂功能返回 rejection、HTTP error 或语法错误，会触发重试风暴（`cocos_res_reporter` 重试、持续重发、`Uncaught SyntaxError`、加载流程被拖死）。正确做法是按调用方契约返回 `{}`、空列表或本地 trait 等 inert success，并让正常回调链结束；若本地埋点参与通用请求流程，还要填 timing/URL/HTTP code 并先调用 `handleServerResponse`。

## 5. 构建与交付检查单

- [ ] 基底唯一：记录 APK/证书/版本/ABI，10.4.7 与 9.5.0 不混用；
- [ ] 构建：DEX stage 编译 → 覆盖只读基线 → zipalign → 正式签名 → 哈希复核；
- [ ] 桥：`jsb.reflection` 未全局禁；settings/jsList 结构未改；
- [ ] URL：参数/远程 trait/数据库/patch 全覆盖，以运行日志解析后 URL 为准；
- [ ] 聚合：按发起者/回调/展示判定归属，adapter 可 dormant 保留；
- [ ] 上报：只送目标 appid，hostname 净化，`code=0`；
- [ ] Seed：主 APK / files / 设备缓存三份哈希对齐，门禁全 0；
- [ ] 网络：真机 DNS/TLS/HTTP-Host 三层，原厂域名族 0 命中，目标渠道成功；
- [ ] 回归：联网/断网冷启动各三轮，真机实玩一局后恢复网络复验。

## 6. 可迁移要点（跨项目）

1. 先锁定"唯一直接基底"，所有后续工作基于同一次反编译输出；
2. 资源链失败与 DEX 编译成功并行评估，不做单向误判；
3. 隔离 = 切断实际连接与数据交付，保留可证明 inert 的骨架；
4. 桥与全局开关分开处理；配置索引只改值不改结构；
5. URL 替换要覆盖所有覆盖源，并以运行日志为准；
6. 聚合供应商归属看请求/回调/展示链，不看 SDK 名称；
7. 埋点离开封装点净化 hostname，防 `https:\/\/` 编码绕过；
8. Seed/远程目录以设备实际执行副本为准，不做目录大小校验；
9. 阻断一律返回 schema-compatible inert success，禁止制造异常风暴；
10. 最终判定在真实手机网络下完成，模拟器只是阶段回归。
