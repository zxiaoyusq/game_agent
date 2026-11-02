# 全局规则（证据 / 边界 / 环境 / 门禁）

> **何时读我**：任何取证、换皮、二开任务动手之前。
> **读完能做到**：按全局证据规则分清证据等级与版本角色、守住原版 owner 与稳定边界提交，并知道格式解密边界、环境实时发现要求和最小交付门禁。
> **范围**：`GENERAL_DEFAULT`

本文件从根 `SKILL.md` 拆出，属于 `GENERAL_DEFAULT`（BlockMaster 专属规则单独见 `references/blockmaster-case-rules.md`，属 `CASE_ONLY_BLOCKMASTER`）。任何取证、换皮、二开任务在动手前先读一遍本文件。

## 全局证据规则

1. **先找真实执行路径。** APK 中存在文件或字符串，不证明运行时使用它；桥接调用或 `dispatch` 日志，也不证明广告、埋点或远端平台成功。
2. **分清证据等级。** 静态结构、脚本测试、模拟器、真机画面/日志、网络抓包、平台后台确认是不同等级，报告不得互相替代。
3. **分清版本角色。** 当前工程的直接重打包基底优先决定行为；旧版 APK、历史抓包、AB 快照用于对照，不能混称当前原版。BlockMaster 的 10.4.7/9.5.0 关系属于 `CASE_ONLY_BLOCKMASTER`（见 `references/blockmaster-case-rules.md`），其他项目必须自己重建版本谱系。
4. **保留原版单一所有者（owner）。** 视觉、输入、广告结算等生命周期问题，先找到原版负责 show/hide/restore/commit 的唯一 owner 和事件顺序。禁止用全局扫节点、遍历所有 proxy、清空对象池、任意延迟回调等方式覆盖原逻辑。
5. **异步只准备，稳定边界才生效。** 代码、bundle、材质和 Trait 可以后台加载，但不得在拖拽、预消除、动画、广告回调等进行中途热启停。只在原代码证实的稳定边界提交（commit），例如 `new_game` 或对应动画结束。
6. **一个事件、一个 owner、一次提交。** 同一清屏 epoch 只能提交一次最终材质/颜色/效果组；特殊材质不得被后到的普通配色覆盖。
7. **不把体验修复变成流程阻塞。** Replay 第一条新局事件立即放行，后台准备不得成为 awaited gate；广告回调只结算一次并回到原游戏路径。
8. **保留可回退路径。** 先做最小补丁，维护最后已知良好版本和版本差异矩阵；出现新回归时先与原版 owner 和最后良好版本比对，不继续叠加补丁。
9. **保护器不得变成第二套玩法算法。** 可解性、越界或崩溃保护只在原版输出确实无效时做最小后验修复；判定语义必须与原版 solver 一致。除功能正确性外，还要比较保护器触发率、候选分布和极端形状频率，防止"零死局但玩法失真"。
10. **交付必附未知清单。** 未解决问题、缺失的权限与环境、矛盾证据按 `references/unknowns-ledger-template.md` 登记并在交付报告附带。三条主链路另按各自模块的义务清单模板逐条关闭义务（`modules/godot-migration-port/references/obligation-ledger-template.md`、`modules/skinning-pipeline/references/obligation-ledger-template.md`、`modules/sdk-replacement/references/obligation-ledger-template.md`）；静态候选与未验证的推断不得关闭义务。

BlockMaster V123/V124 的完整反例、根因和验收门禁见 `modules/gameplay-logic-reverse/references/blockmaster-v123-v124-lifecycle-regression.md`。

## 格式与解密边界

- Cocos/Unity 指纹只用于路由；外层 Java/Kotlin 壳不代表游戏本体引擎。
- `.jsc`、HEK、AFFA 是不同层。**先读头、版本字节和真实加载器，不得把所有 `HEK:` 文件都当作 v03 XOR。** 现有 `decrypt_v03_resources.py` 只适用于已确认的 v03；其他版本优先复用原生加载器或已验证的项目专用解密链，并保留原始密文副本。
- 资源"在包内"不等于运行时可达。还要验证索引、版本、依赖、Trait 映射、配置/handler、监听器、对象池和实际渲染层。
- 不重新分发无授权的原始游戏资产、密钥或用户数据；交付以脚本、映射、差异、验证报告和可复现步骤为主。采集行为同时遵守 `modules/vision-device-testing/references/collection-boundaries.md` 的负面清单：凭据、Cookie、授权头、原始网络体与用户隐私数据不采集、不留存、不入交付。

## Android Cocos JSB 通用边界（GENERAL_DEFAULT / GENERALIZED_PATTERN）

- 主 assets JS、Seed/remote patch、设备 `files/patch` 可能是不同执行副本；先用哈希和标记确认当前实际入口。
- 不粗暴禁用 `jsb.reflection.callStaticMethod`、全部远程加载或全局网络。只隔离已确认的原厂连接，并按调用契约返回 schema-compatible 本地结果。
- 引导状态优先读取原游戏持久化进度，残留 UI 节点只能辅助。任何"前 N 次不触发"都必须由当前项目代码或产品规则证明。
- 动态视觉资源启用必须同时满足主资源与配套配置/handler/pool 就绪。未就绪只能延期到下一稳定边界，不能本轮晚到覆盖。
- 低端机降级应减少粒子数量、并发、时长或分辨率；不得直接关闭整组 Trait，也不得把加载/启用放到触摸和清屏热路径。
- 广告供应商、Banner、奖励/插屏、埋点平台和原厂隔离分别取证。广告与埋点最终结论必须在真机网络环境验证。
- QA/debug 签名包仅用于验收，不等同正式发布包。安装后核对设备 APK 哈希、版本、ABI、签名与本地候选一致。

## 工具与环境规则

模块中记录的本机路径、版本号、设备序列号和历史检查数量都只是案例或默认值。每次任务开始先实时发现并验证：

- 可用 Python/Node/Java/Android SDK/Cocos Creator/adb 路径与版本；
- Godot 可执行文件与版本（重建场景基线：本机 `${GODOT}`，skills 声明 4.3+ 兼容）；
- 当前连接设备、ABI、Android 版本、包名和签名；
- 当前 Git 分支、HEAD、工作树脏改和实际构建基底；
- 当前 APK 的 SHA-256、zipalign、签名、versionName/versionCode。

不要把固定 Python 补丁版本、固定检查数量或模拟器固定端口等历史值写成通用前置条件。下表只是本机历史案例默认值，不是前置条件：

| 工具 | 案例路径 | 用途 |
|---|---|---|
| Cocos Creator 2.4.13 / 3.8.7 | `${COCOS_2X}\` / `${COCOS_3X}\` | 构建/QA |
| AssetRipper GUI Free | `${ASSETRIPPER}\` | Unity 提取 |
| Il2CppInspectorRedux / UnityPy | `${IL2CPP_INSPECTOR}\` / `${PYLIBS}\` | IL2CPP 反编译 / Unity 资产提取 |
| Android SDK / NDK / JDK 17 | `${ANDROID_SDK}` / `${ANDROID_NDK}` | Android 打包 |
| MuMu 12 | `F:\Program Files\Netease\MuMu Player 12\`（adb 端口以实测为准） | 模拟器 QA |
| Godot 4.6.2 stable | `${GODOT}` | Godot 重建/迁移目标引擎 |
| 逆向资产参考 | `E:\download\sudoku-re\`、`E:\Gameprogram\Sudux`、`E:\Gameprogram\Blockudoku` | 素材复用/回归 |

测试数据：合成夹具与全链路 QA 证据见 `modules/skinning-pipeline/references/test-fixtures.md`；生成合成夹具 `python modules/skinning-pipeline/scripts/skinpipe.py fixtures --output "<dir>"`；只读真实数据（不修改）`E:\download\sudoku-re\assets-export\`。

## 仓库内脚本清单

以下脚本/参考此前长期只存在于维护源（未随早期副本分发），现已全部纳入本仓库，按模块目录存放；任何旧副本缺失时从本仓库/Maintenance 源同步，不要凭空重写加密或解码逻辑：

- `modules/cocos-reverse-engineering/scripts/`：`decrypt_jsc.py`（XXTEA 解密 .jsc，与 xxtea-node 全缓冲+includeLength 语义一致）、`decrypt_v03_resources.py`、`pkm_to_png.py`（ETC1 PKM→PNG，ETC2 明确报错）、`restore_skeleton_data.py`、`verify_assets.py`。
- `modules/gameplay-logic-reverse/scripts/`：`extract_js_from_heap.py`、`extract_algo_traits.py`、`extract_decorator_registry.py`、`gen_remote_manifest.py`、`download_remote_trait_bundles.py`、`associate_trait_dirs.py`、`trait_dir_evidence.py`、`build_trait_acceptance.py`、`gen_acceptance_report.py`、`frida_capture_eval.py`。
- `modules/sdk-replacement/scripts/`：`capture_network_evidence.py`、`scan_original_sdk_surfaces.py`、`prepare_offline_seed.py`、`generate_seed_copier.py`、`verify_vendor_isolation.py`、`gen_sdk_acceptance_report.py`。
- 参考：`modules/cocos-reverse-engineering/references/android-jsb-reskin-pitfalls.md`（10.4.7 换皮+SDK 注入踩坑，V30-V35 案例的前置阅读，`CASE_ONLY_BLOCKMASTER`）。

## 最小交付门禁

- 变更前有失败证据；变更后有针对根因的自动测试或静态门禁。
- 交付报告附带未知清单；未闭合义务、已豁免项与矛盾证据逐条列出，不写无证据的"已完成"。
- 对高风险运行时改动执行冷启动、Replay、新局、普通消行、清屏、引导、特殊材质、广告前后恢复和长时稳定性矩阵。
- 网络类结果明确区分模拟器、真机日志、PCAP 和平台后台。
- Git 只纳入源码、生成器、测试、配置快照和报告；排除 APK、密钥、反编译树、缓存、临时文件、设备日志和截图，除非用户明确要求。

## 本地补充工具入口（8.5.1）

- `modules/cocos-mcp-channel/scripts/start_cocos_mcp.ps1`：Creator 3.8.x MCP 探测/启动，正式连通用 get_editor_state 核对。
- `modules/sdk-replacement/scripts/extract_transsion_sdk_pack.py`：传音素材脱敏回收，配套接口示例在该模块 assets/transsion。
- `modules/sdk-replacement/scripts/generate_seed_copier.py`：接口与完成标记合并，布局见 `modules/sdk-replacement/references/seed-copier-generation.md`。
- `scripts/resolve_environment.ps1`：工具路径读 `$env:VAR` 并验证；ANDROID_NDK 是版本目录，SPINE_VIEWER/ASSETRIPPER/GODOT 是完整文件；只设 .env 不生效。
