# 宿主 App 内嵌功能逆向：QQ 宠物 (Adelie/Ergo) 案例

范围：`GENERALIZED_PATTERN`（方法）+ `CASE_ONLY_QQPET`（字面值）。禁止把 QQ 包名、Activity、CDN、groupId、资源 ID、版本号照搬到其它项目；应迁移的是下面的判断方法与流程。

## 1. 案例背景

- 宿主：腾讯 QQ（包名、版本、设备路径属案例值），非独立游戏 APK。
- 目标：QQ 内"宠物"功能 = 3D AI 宠物养成（入口 `AdelieFragmentActivity` + `PetMainFragment`）。
- 诉求：识别引擎 → 拉取全部资源(含代码/逻辑) → 生成 3D/2D 预览 → 输出系统拆解 MD/HTML。
- 环境：MuMu 模拟器(root) 跑 QQ，加真机对照；**QQ 本体不是可 run-as/debuggable 的独立小游戏**，工具假设与独立 APK 不同。

## 2. 引擎识别：宿主内嵌功能的三个关键坑

### 坑 1：后台其它游戏"污染"窗口判定（重要）

`dumpsys activity top` 曾命中 `org.cocos2dx.lib.Cocos2dxGLSurfaceView`，一度误判 QQ 宠物是 Cocos。
实际它属于**后台另一个独立游戏**(blockmaster)的残留窗口。

方法：
1. 先看 `topResumedActivity` + `dumpsys window | grep mCurrentFocus`，确认哪个窗口真的在前台；
2. 用 `dumpsys activity activities` 列 task 栈，把目标 Activity 的窗口与其它后台 Activity 的窗口分开；
3. 用 `dumpsys activity top` 里目标 Activity 段(非全部)的 View Hierarchy 判断其真实渲染视图（本例为 `TextureView`/Kuikly 容器，而非 Cocos GLSurfaceView）；
4. 渲染视图只是入口线索，真正的"页面技术栈"看该 Activity 的 Fragment 实现与反编译类。

### 坑 2：宿主 App 内嵌功能不是独立小游戏，别按独立 APK 拆

- 资源不在"游戏自己"的 APK，而在**宿主 data 目录**：
  - `files/ZRes/.../res/<module>/`(页面 Kuikly 包)、`cache/zplan/...`(3D 缓存)、`files/mmkv/`(全部配置)。
- 页面代码以 **Kuikly 动态包**下发：`kuikly_dynamic.zip` → 内含 `pet_*.apk` → 该 apk 内是 **classes.dex**(Kotlin)，不是 JS。
- 结论链：downloadUrl 是 remote；下载后解出 apk/dex → jadx 反编译 → 得到页面 Java 源码。
- 需要 root(或模拟器 root)才能读 `files/`、`cache/`、`app_lib/`，独立 APK 提取器对宿主无意义。

### 坑 3：Activity 内可能有 WebView/TextureView/GL 多视图共存，别只看一屏

用 `dumpsys activity top` 目标 Activity 段的 `View Hierarchy` 完整树确认；本例是 Kuikly(Compose/View)+TextureView 组合，不是 Cocos。

## 3. 设备能力闸门：运行时配置控制"能不能进"

### 现象
模拟器上进入功能弹"请在手机端体验"（平板/机型不被支持文案）。与反调试、模拟器检测都无关——是**设备类型判定 + 远程开关**共同拦的。

### 判定链定位（方法）
1. 从反编译找提示文案常量(如 `"请在QQ手机端体验"`)→ 反查持有该配置的数据类(字段 `tablet_unavailable_toast` 等) → 再找引用该数据类的判断方法(如 `PetQQMC.g()`)；
2. `g()` 读远程开关 groupId 与设备类型枚举，再调 `PadUtil` 判断 DeviceType(TABLET/FOLD/PHONE)：
   - 开关未开 → false；`TABLET && enable_tablet<1` → false；`FOLD && enable_fold<1` → false；机型黑名单/白名单再过滤。
3. `PadUtil` 按厂商分支(Brand)判定：小米读 `persist.sys.muiltdisplay_type` + characteristics；华为读 characteristics/姿态 feature；三星读 feature 属性；非 OEM 默认按 `screenLayout>=XLARGE` 且屏幕≥7" 判 TABLET。
4. 判定结果缓存在**进程内 static**，改配置后必须 force-stop 重启才生效。

### 绕过（方法，勿照搬 key）
- 设备判定 → 把模拟器分辨率/密度调到使 swdp<600 仍被拦时，说明还有 `enable_tablet` 之类远程开关，改**本地下发的配置缓存**(MMKV/配置文件)把对应开关值从 0→1；
- 改法：先备份 → 同长字节替换(0→1，长度不变避免破坏容器) → chown/chmod 还原属主 → force-stop 重启；
- 验证链：PadUtil 日志(`initDeviceType`)、能否进入功能、uiautomator 按钮出现。

## 4. 本地 vs 远程资源判断方法

结论方法(通用)：**"已加载资源"分两类来源，用三重证据区分**：
1. **APK 内扫描**：zipfile 遍历 apk entries，命中的 pet/模块文件数(本例 APK 内几乎只有配置文件) → 证明美术/代码几乎全远程；
2. **下载痕迹**：客户端缓存里的 etag/manifest 记录(如 `avatarDownload/<hash>/etag.json` 的 etag+filepath) = 真实发生过远程下载的清单；
3. **版本清单**：宿主"远程配置中心"(如 unitedconfig MMKV) 内嵌各模块 JSON：id/version/downloadUrl/compOrigFileDownUrl/isLoadFromPresetAssets/diffInfoList → 既是本地/远程标注，也是 CDN 目录模板与**差分包历史**来源。

区分产物分级：
- 本地打包(仅少量配置) / 远程预下载(配置声明的 engine/adopt 整包 zip，直链可 CDN 拉) / 远程按需(进页/动作才下) / 运行时下发配置。

## 5. 资源容器与编解码笔记

### MMKV 常见形态(宿主配置)
- `key` + varint length + value；value 可能再套 base64(双重) 或 protobuf/JSON。
- 解析顺序：先 hex 看前几字节(len/tag)，再按需去 length 前缀、去 base64、再当 protobuf walk 或 JSON 读。
- 案例：`PetHomeResource` 缓存 = len 前缀 + base64 包裹的 protobuf，内含 petId→(home/feed/shower/talk/shadow 资源组 / 模型资源ID / 状态胶囊 / 毛色配色) 的映射。

### zplan/Filament 缓存结构(Ergo 3D)
```
cache/zplan/filament/cache/
  Resource/Resource/<hash>/{*.gltf,*.bin,*.ktx2,<name>.crc64.<n>.v3.manifest}
  Resource/Download/           .fasset (Filament 预处理资产)
  Resource/Shaders/            .filamat 材质 + .bin
  Resource/{Particle,ETag,tmp}
  avatarDownload/<hash>/etag.json
```
- glTF 由 **Unreal 4.26 glTF 导出**；`.ktx2` 贴图 + `.filamat` 材质 + `zplanlite-filamat://` 引用是引擎私有，浏览器 model-viewer 不能直接渲染(需转 PNG 或专用渲染)。
- 动画文件两类：standalone(自带网格, 可独立播放) 与 track-only(仅动画轨道, 骨架节点布局与 model 完全一致时才能合并)。

### 页面 UI 框架(Kuikly)
- 动态包 `kuikly_dynamic.zip` = 一个 `pet_*.apk` + `kuikly_config.json`；
- `pet_*.apk` 内部只有 `classes.dex`；反编译得到页面 Java(混淆为 a/b/c 单字母包)。这不是 Spine/Unity，也别当小游戏 H5(无 js)。

## 6. HTML 预览：3D 模型/动画 + 2D 画廊(与 Spine 预览互补)

案例引擎产出物形态(供复制结构，字面值勿搬)：

```
art_preview/
  libs/model-viewer-umd.min.js    # 用 UMD 版!
  3d_preview.html                 # model-viewer 逐卡片预览
  2d_gallery.html                 # 贴图画廊 + lightbox 放大
  assets/clean/<pet>/[model.gltf | _anim_<id>/animation.gltf]
  index.json / gallery.json
```

### model-viewer 三坑
1. **dist 有两版**：`model-viewer.min.js` 是 ES module(含 export，`<script src>` 报 Unexpected token 'export')；要用 **`model-viewer-umd.min.js`**(IIFE)才能普通 script 引入注册 `<model-viewer>`。
2. **多卡片**：不要在单个 viewer 上反复切 src 做"主窗+缩略图"，否则 IntersectionObserver 反复 `BAILING OUT EARLY`/src 竞争被清空；直接每卡片一个独立 `<model-viewer>` 最稳。
3. **动画合并**：track-only 动画需并入 model。前置条件：两文件 **node 布局一致(同节点数/同名骨架)**；合并时把 anim 的 buffers/bufferViews/accessors 追加并**重索引**(bufferView.buffer += buf_off; accessor.bufferView += bv_off; sampler.input/output += acc_off)，channel.target.node 因同布局不变。多动画同目录会因 `animation.bin` 同名冲突 → 每动画独立子目录再单独引用。

### 预览验证(无头)
- `chrome --headless=new --screenshot` + puppeteer(WebGL 需 `--enable-unsafe-swiftshader --ignore-gpu-blocklist`)；
- 检查 `availableAnimations`、`currentTime` 推进、canvas 非空像素、卡片 src 正确；
- 2D 画廊用 PIL 读尺寸、无头截图抽样验证。
- file:// 无法 fetch → 必须 `python -m http.server`；中文文件名用 ascii 副本或 encodeURI 访问。

## 7. 各系统拆解交付

同一套"设计意图速览 / 功能地图(页面→模块→dex) / 远程配置 group 表 / 证据边界 / 遗漏"模板(见 unity-extract Tile Explorer 参考)。本案例额外沉淀：
- 功能页拆解从 Kuikly 包名推(pet_academy/pet_pk/feed_claim...)比 UI 点得更全；
- 商业化/付费行为可在 UI 层实测(装扮购买弹窗文案/钻石不足提示)，不需服务端密钥；
- 明确"服务端未开放分支/其它用户个性化装扮"为无法由本地推导的边界。

## 8. 复现步骤概要

1. 环境：宿主 App 登录到目标功能(模拟器 root 或真机 adb)，先确认 `topResumedActivity`。
2. 无法进入 → 按第 3 节定位设备闸门并绕过。
3. 拉目录：`cache/` 引擎缓存、`files/ZRes` 页面包、`files/mmkv` 配置、`app_lib`/`qqso` 引擎 so。
4. 预载整包 zip 直链从配置声明的 URL 直接 curl(不需登录)。
5. 页面包：解 kuikly zip → 取 apk → 取 classes.dex → jadx。
6. 引擎资产按第 5 节分类，3D 模型整理为可预览 glTF，按第 6 节生成页面。
7. 输出系统拆解 MD + 汇总 HTML(全部 MD 内嵌 + 导航 + 预览链接)。

## 9. 案例专属值(禁止复制)

- 包名 com.tencent.mobileqq、QQ 版本号、Activity(AdelieFragmentActivity/PetMainFragment/UniteSearchActivity)。
- groupId `107805`、`pet_preload_res_config`、`enable_tablet` 等 key。
- CDN 域(qqpet.gtimg.com / shiply-adelie…)、预载包文件名、URL 模板中的时间戳目录。
- 宠物 ID(1000001..1009999)、资源 ID(4003xxx/5000xxx/9990xxx)、MMKV 文件名(united_config_mmkv_*)。
- MuMu 端口/设备序列号、Qt 数量(5 模型/10 动画/112 图/15xxx 文件)、开关与 UI 坐标。
- 以上只在本案例成立，其它宿主内嵌功能必须重新发现自己的 Activity、配置 key、CDN 和资源 ID。
