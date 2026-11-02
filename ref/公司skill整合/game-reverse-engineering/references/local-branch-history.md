# 本机旧分支的独有版本记录

范围：历史来源记录。本文件保存 v8.5.0 portable 包未包含的本机分支更新说明。两条分支曾使用相同版本号表示不同更新，不能按数字覆盖内容；本次融合以 portable 8.5.0 为基础，当前入口版本为 8.5.1。

以下原记录描述当时的环境和部署结果，不代表当前全部路径、版本和工具数量已验证。功能入口已按新结构归入对应模块，完整原树另有替换前备份。

- **8.0.0 (2026-09-14)**：新增第十四模块 `cocos-mcp-channel`（Cocos 3.8.x MCP 实时通道：harness 无人值守驱动编辑器。Funplay MCP v0.6.3/MIT 已装入 `%USERPROFILE%\.CocosCreator\builtin-extensions\3.8.7\`；通道选型表、启动脚本 `start_cocos_mcp.ps1`、端口机制 8765/20000-29999、harness HTTP 接入、core 39/full 105 工具面精要、与 prefab-bake/cocos-qa/cocos-creator-repair/ui-feature-pipeline 的去重分工、无人值守七步 SOP）。意图分发表与路由表同步；`ui-feature-pipeline` 阶段 4、`prefab-bake` 已知坑、`cocos-qa` Pipeline 加通道提示；scope-map 加模块行；工具环境表 Cocos 路径更新为 `C:\ProgramData\cocos\editors\Creator\`（E:\Gameprogram 旧路径失效）。定位：MCP 为第二通道（实时），文件级+CLI 为第一通道（2.4.x 唯一），验收证据等级不互替。

- **7.5.0 (2026-09-10)**：发布方式改为**单一维护源 + 目录联接**。本技能纳入全机统一技能池 `D:\skills`，13 个 harness 的 skills 目录下均为指向该池的 junction，因此"改一处即全端生效"，废弃原先的"改本源 → 复制到 8 端 → validate_skill.ps1 比对多端哈希"流程（该流程正是历次多端版本漂移的成因）。本节"技能发布与同步"已重写；合并时以本仓 v7.4.0(.agents) 为权威副本，其余 12 端副本收入 `D:\skills\_archive\game-reverse-engineering\` 存档。

- **7.4.0 (2026-09-08)**：沉淀"宿主 App 内嵌功能逆向"新案例 `references/host-app-embedded-qqpet-case.md`（QQ 宠物 Adelie/Ergo，`GENERALIZED_PATTERN` + `CASE_ONLY_QQPET`）。新经验：(1) 引擎识别陷阱——`dumpsys activity top` 会被后台独立游戏的渲染视图(如 Cocos GLSurfaceView)污染，须用 topResumedActivity/focus/目标 Activity 段过滤归属后再判引擎；(2) 宿主内嵌功能不是独立小游戏，页面=Kuikly 动态包(apk 内 classes.dex, Kotlin 非 JS)，3D=自研 Ergo+Filament 私有格式(.filamat/.ktx2/zplanlite://)；(3) 设备能力闸门定位与绕过——远程开关+设备类型判定拦截时，改宿主远程配置缓存(MMKV)同长字节替换+force-stop 重启；(4) MMKV→base64→protobuf 逐层解析法；(5) 本地/远程三重证据(APK 扫描/下载痕迹/远程配置内嵌清单)；(6) glTF track-only 动画并入 model(节点布局一致+accessor/bufferView/buffer 重索引，每动画独立目录防 bin 同名冲突)；(7) model-viewer 预览坑：必须用 UMD 版(ES module 版 script 引入报 export 错)、逐卡片独立 viewer(单 viewer 反复切 src 会被 IntersectionObserver 清空)、HTTP 服务(不能 file://)；无头 Chrome+swiftshader 验证法。同步更新 engine-identification 模块(宿主内嵌识别章节)、scope-map(新案例注册表+可迁移行)。

- **7.0.1 (2026-10-08)**：sdk-replacement 模块补传音（Transsion）体系供应商附录`modules/sdk-replacement/references/android-transsion-sdk-suite.md`（Hisavana/Athena/AhaPush/PalmUpdate 构成、私有 Maven 获取、初始化与广告/埋点 API 契约、Manifest 清单、常见坑）、`modules/sdk-replacement/references/transsion-material-pack-index.md`（素材登记与一键重建）、`assets/transsion/`（接口化宿主替换范式示例）、`modules/sdk-replacement/scripts/extract_transsion_sdk_pack.py`（成品 APK 回收素材 + 自动抹密钥）。
