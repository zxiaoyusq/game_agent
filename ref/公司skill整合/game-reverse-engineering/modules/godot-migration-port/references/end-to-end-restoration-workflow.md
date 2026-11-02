# Godot 重制端到端生产流程（GENERAL_DEFAULT / GENERALIZED_PATTERN）

> **何时读我**：哥哥要开一个 Unity/Cocos 老项目的 Godot 重制，或已经做到一半却说不清"现在到哪一步了、这一步做完能不能往下走、能不能说它还原了"时。
> **读完能做到**：按 S0–S7 决定先做什么、每阶段的交付物和门禁是什么，并用八种证据状态（`inventory_only` 到 `unknown`）如实标注每个页面/功能/动画的还原程度，知道只有 `verified` 才能关闭矩阵项、`fitted` 必须保留差异和替换入口。
> **范围**：`GENERAL_DEFAULT` + `GENERALIZED_PATTERN`

本文是 `godot-migration-port` 的主流程。它负责决定先做什么、每阶段交付什么、何时可以进入下一阶段。具体技术细节按需转到原切图门禁、Spine、差距闭环和案例文档，避免多份流程互相覆盖。

## 一、统一状态与证据词汇

每个页面、功能、动画、声音和数据规则只能处于以下状态之一：

| 状态 | 含义 |
|---|---|
| `inventory_only` | 文件或符号存在，尚未证明运行时引用 |
| `static_confirmed` | Prefab、序列化字段、PPtr、配置或资源链已确认 |
| `runtime_observed` | 原版自然运行中看见或听见 |
| `controlled_runtime_confirmed` | 通过可逆数据探针跨过边界并观察到原版行为 |
| `implemented` | 重制工程已接入，但尚未完成目标平台验收 |
| `verified` | 同状态功能回归和目标平台视觉/音频验收通过 |
| `fitted` | 资源或状态有证据，但曲线、时距或动态值只能拟合 |
| `unknown` | 当前版本没有足够证据；保持空值、关闭或待取证 |

`inventory_only`、单元测试通过、场景节点存在或编辑器能预览，都不能写成“已还原”。只有 `verified` 可以关闭矩阵项；`fitted` 必须保留差异和替换入口。

## 二、S0–S7 主流程

### S0：范围、版本与证据基线

1. 固定原版 APK/包哈希、版本、包名、入口、设备、设计分辨率、网络状态和玩家存档原始字节哈希。
2. 建立覆盖矩阵：启动、主页、所有入口、引导、局内、提示、暂停、结算、下一步、返回主页、后期解锁、商业化和异常恢复。
3. 每项记录原版证据、重制证据、owner、状态、缺口和验收动作。截图文件名不算证据，必须查看内容并核对前台包名。
4. 原版、重制、旧报告和不同构建的证据分开保存；不能用旧版本画面覆盖当前版本未知项。

**门禁**：版本谱系、原始存档备份、覆盖矩阵和权威素材路径均已落盘；无法确认的项明确标为 `unknown`。

### S1：资产身份、转换与 Godot 导入

1. 用 bundle/CAB/pathID/PPtr 或等价索引确认 Texture2D、Sprite、Material、AudioClip、AnimationClip、Spine 数据、atlas 和 PNG 的真实引用链。
2. 保存源字节与 SHA-256；二进制转换必须可回滚、可重跑并通过真实格式解析。不得只改版本字符串、文件后缀或名称。
3. 区分 Sprite 逻辑画布、trim、offset、pivot、border、旋转 region、atlas page 和父级变换；按 X/Y 分别处理，不直接拉伸紧裁图。
4. 在 Godot 建立 `.tres`、AtlasTexture、SpriteFrames、音频资源和导入配置；检查所有引用可解析。

**门禁**：资产清单可追溯到源身份；转换前后哈希和命令已记录；Godot headless 导入无缺失引用；源资产未被覆盖。

### S2：玩法、数据与事务语义

1. 从原版输入和状态变化反推真实模型，不按游戏类型套常见规则。对组移动、碰撞、提示、奖励、章节推进等建立互斥候选并用同一 fixture 排除。
2. 模型提交和表现反馈分层。声音、粒子、连击、库存扣除与结算只能订阅权威提交结果，不能从触摸或视觉位置猜成功。
3. 所有奖励、广告奖励、提示消耗和结算提交使用唯一事务 ID 与幂等账本；退出、重入和重复回调不能重复发放。
4. 存档测试使用隔离路径；跨进程恢复覆盖棋盘、计时、步数、分组、待播演出和已提交奖励。

**门禁**：真实输入回放通过；模型快照、视觉位置和业务提交各有断言；取消、越界、连点、末步、暂停、离场和重载不会破坏状态。

### S3：UI、Spine、音频、粒子与 Prefab 固化

1. 原切图路线使用可编辑 Control/Node2D、AtlasTexture、NinePatchRect、AnimationLibrary/AnimationPlayer 和固定 Spine/粒子宿主；整页截图只在用户明确接受的快照原型路线使用。
2. 动态业务值由脚本绑定，固定的是资源、锚点、层级、初始状态和时间线。禁止运行时无条件 `new` 第二套视觉节点。
3. Spine 分别证明资源能解析、动画能播放、业务分支能触发；评价字、Emoji、印章、Logo、按钮和猫等不能因名称相近而互换。
4. 普通移动和正确拼接等声音从提交语义分支触发，并校验播放时机、并发、暂停和场景退出清理。
5. 高密度特效按 emitter 提取 enabled、材质、图集、burst、shape、lifetime、velocity、父级变换和触发点；原 renderer disabled 的宿主保留但不绘制。

**门禁**：编辑器重开场景仍可见可编辑；连续打开/关闭无节点增生或迟到回调；原版与重制同分辨率、同状态、同阶段视觉比较达标。

### S4：跨页面流程、后期系统与配置来源

1. 建立唯一演出协调 owner：末次局内反馈完成后，按资格顺序播放条件激励、结算基础段、后期系统段，再开放退出。所有等待有限时且可由 epoch/cancel 淘汰。
2. 排行榜、Daily、图鉴等按资格、首次开放、首次引导、局内增量、结算、返回主页、周期结束建立状态矩阵。固定宿主不能代替真实调用链。
3. 业务 owner 先提交不可变 completion snapshot；演出 gate 只消费显式 `rank_result`、`collect_elements`、`daily_result` 等 payload。无 payload 时直接放行，不按关卡数强播。
4. 所有未知配置字段使用当前受检版本 snapshot defaults，覆盖资格、配额、AB、样式、奖励、payload、开关和位置。运行时优先级按字段 owner 定义：已提交玩家状态或一次性状态、当前 provider 明确值、打包快照默认值；没有证据时保持 `null`、空数组或关闭，禁止启发式补值。
5. 快照只有一份运行时来源。Facade/配置服务加载快照，未来 SDK provider 覆盖；页面、解锁演出和结算分支必须通过测试证明读取同一来源。
6. 外围 SDK 使用 `Autoload facade + adapter + policy + config`；默认 Null/Local adapter。同意、频控、AB 稳定边界、事件 owner 和奖励 proof 在业务层定义，不散落在页面按钮中。

**门禁**：有 payload 播放并阻塞退出，完成后放行；无 payload 直接放行；首次引导只播一次；快照默认和 provider 覆盖均有消费者测试；返回、重开和跨日无重复奖励或悬挂事务。

### S5：分层 QA 与视觉关闭

按以下顺序验证，前一层失败不进入下一层：

1. 静态：资源哈希、引用、动画名、固定宿主、导出 include/exclude。
2. 逻辑：确定性 fixture、状态迁移、事务幂等、存档回环、生命周期清理。
3. 桌面：真实渲染、编辑器可编辑性、早/中/晚帧和音频事件。
4. Android：真实触控、返回键、暂停/后台/杀进程、屏幕适配、ABI 和包内资源。
5. 原版对比：静态 UI 用同状态截图；动画使用真实 PTS 的起爆/峰值/衰减或入场/稳定/退场阶段。自动指标辅助定位，肉眼可见构图错误仍判失败。

每次失败回到“现象 → owner/资源/坐标/时序假设 → 单变量实验 → 最小修复 → 定向回归”，不能用全量重写掩盖根因。

**门禁**：覆盖矩阵中的目标项达到 `verified`；所有 `fitted/unknown` 有具体残差、证据缺口和后续替换条件。

### S6：最终构建与设备验收

1. 任何生产脚本、场景、资源或配置在 APK 导出后改变，旧 APK 立即失效；重新导出、验签、安装并在最终包复跑相关路径。
2. 校验 APK SHA-256、size、v2/v3 签名、ABI、关键资源/配置存在、QA/docs/tools 未误入包。
3. 导出可能重启 ADB；安装前重新 `adb connect` 并确认目标序列号。安装前后分别读取玩家存档原始 bytes 哈希。
4. 设备驱动不能只 `sleep` 后盲点：用至少两个独立视觉锚点或状态信号判定页面 ready。模拟器首帧可能停住时，可发送落在空白区的无副作用输入，再读取本次确认帧。
5. 首次引导/遮罩会拦截返回和底层按钮；自动化脚本必须按 UI 状态机先完成引导并等待动画结束，再导航。绿色按钮、单一颜色或旧截图不能作为页面身份的唯一判断。
6. fixture 在 `finally` 恢复所有受影响文件并重新读回 SHA-256。联系表与原始单图矛盾时，以已确认的原始帧为准，重新生成联系表。

**门禁**：最终 APK 在目标设备完成冷启动和关键流程；Logcat 无脚本错误、FATAL 或 ANR；测试前后用户存档和设置逐字节一致；证据明确绑定最终 APK 哈希。

### S7：收口、交接与 Skill 迭代

1. 更新 `HANDOFF.md`：目标、权威素材、最终 APK/哈希、设备状态、修改文件、测试结果、未关闭项、回滚点和下一步。
2. 报告区分 `verified`、`fitted`、`unknown`，撤回旧的“100%”声明。最终验证不能用历史 APK、旧存档或别的包截图。
3. 只把多项目可复用的判断方法写入通用参考；项目数字、坐标、哈希和资源名写入案例文档。
4. 更新模块版本、根技能版本和 landing-log；运行结构、链接和全树哈希校验。多端目录可能是 junction/别名时先读入字节快照再同步，禁止目录互拷造成自覆盖。
5. Windows 上运行第三方 Python 校验器时显式使用 UTF-8（如 `python -X utf8 ...`）；默认区域编码造成的 `UnicodeDecodeError` 属于校验器启动失败，修正环境后必须复跑，不能当作内容通过或内容失败。

**门禁**：交接文件可让新 Agent 不读旧会话直接继续；Skill 入口能路由到本流程及专项参考；校验器通过；未完成项没有被语言包装成完成。

## 三、按问题读取专项参考

| 当前问题 | 读取 |
|---|---|
| 原切图身份、Sprite 几何、Prefab 固化、包体 | [native-restoration-gates.md](native-restoration-gates.md) |
| Spine 插件、版本转换、资源链、轨道和 Android ABI | [godot-spine-integration.md](godot-spine-integration.md) |
| 已观察差距的定位、最小修复和四层回归 | [restoration-gap-to-qa.md](restoration-gap-to-qa.md) |
| 用户明确接受整页截图底图的快照原型 | [art-remake-playbook.md](art-remake-playbook.md) |
| SDK 桩和 Android 导出排除 | [sdk-stub-android-exclusion.md](sdk-stub-android-exclusion.md) |
| JigsawCard 已验证案例与未闭合边界 | [jigsawcard-restoration-lessons.md](jigsawcard-restoration-lessons.md) |
| 每个真实里程碑对技能的回填记录 | [landing-log.md](landing-log.md) |

## 四、最小交付物集合

- `inventory`：源资产身份、格式、引用、哈希和转换记录。
- `coverage matrix`：页面/状态/分支/owner/证据/状态/验收动作。
- `snapshot defaults`：当前受检版本全部未知配置的唯一缺省源与证据说明。
- 固定 `.tscn/.tres`：UI、Spine、粒子和 AnimationPlayer 宿主。
- 自动化回归：模型、事务、配置消费者、生命周期和存档恢复。
- 原版/重制证据：同状态截图或同 PTS 阶段帧、音频事件、Logcat。
- 最终 APK 审计：哈希、签名、包内资源、安装和存档不可变结果。
- `HANDOFF.md` 与版本化 Skill 回填记录。
