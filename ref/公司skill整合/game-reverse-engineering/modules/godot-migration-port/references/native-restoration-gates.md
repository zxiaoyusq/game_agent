# 原切图、Spine 与功能还原门禁

> **何时读我**：哥哥要在 Godot 重制里判定某一项"算不算真的还原了"——原切图身份与几何对不对、字节保真和 Spine 资源链是否完整、功能与动画是否算一次完整事务、prefab 固化到什么程度、最终包体怎么验，或撞到 Android 返回键、模拟器桌面不可见、隔离副本导出灰屏这类专项门禁时。
> **读完能做到**：按第 1~6 节与第 8~14 节的专项门禁逐项验收，取到规定类型的证据（而不是截图文件名或"桌面通过"），并知道第 7、13 节的 JigsawCard 数字只是案例锚点、不得当作其他项目的前置条件。
> **范围**：`GENERALIZED_PATTERN`（末节版本/数量为 `CASE_ONLY_JIGSAWCARD`）

范围：方法为 `GENERALIZED_PATTERN`，末节数字为 `CASE_ONLY_JIGSAWCARD`。本门禁补充迁移流程，不表示当前案例已完整还原。

本文负责原生资产、功能事务、场景固化和包体的专项门禁；完整 S0–S7 阶段顺序见 [Godot 重制端到端生产流程](end-to-end-restoration-workflow.md)。

## 1. 证据与任务清单

按“资产提取 → 玩法与 UI 结构 → 行为/动画接入 → 场景固化 → 最终包实机验收”推进。每个页面/入口记录原版证据、当前实现、差距、验证方式。配置 JSON、静态 Prefab、运行时 AB 与旧分析报告可能冲突，分别保留来源及版本。截图文件名不能证明内容，必须查看。撤回缺乏证据的历史“100%”结论。

## 2. 切图身份与几何

Sprite 用 bundle/CAB + pathID 定位，m_Name 仅作标签。加载外部 PPtr 依赖包后，提取切片、旋转、pivot、border、完整父级变换。Unity 到 Godot 显式处理 Y 翻转、镜像和 NinePatchRect 左/上/右/下边距，不能只抄局部 scale。AtlasTexture 保留区域像素并设置 padding/extrusion，逐片验证 RGBA。

同名图片或像素差可能只是裁切差异；须看画面才能判定猫脸、黄脸或皮肤。用户要求原切图时，全屏截图只能作参考，不能替代可编辑控件与布局。

## 3. 字节保真与 Spine

保留原包、原导出物及 SHA-256。m_Script 若为 bytes 则直接保存；字符串须先确定 UnityPy 解码方式并逆编码。禁止一律 Latin-1，禁止 replace/ignore。仅在证明具体损坏链后修复旧导出物。

一类已验证的损坏链是二进制经过 UTF-8 surrogateescape 解码，又以 surrogatepass 写出；候选恢复如下：

```python
candidate = damaged.decode("utf-8", "surrogatepass").encode("utf-8", "surrogateescape")
assert candidate.decode("utf-8", "surrogateescape").encode("utf-8", "surrogatepass") == damaged
```

回环只是必要条件，还要真实格式解析和渲染；未知损坏不能套用此公式。

记录 Spine 导出 minor、目标 runtime、Godot 版本与平台 ABI。不匹配时选兼容 runtime 或完整数据转换，禁止只改版本字符串。验证加载、动画全集、时间推进、真实早中晚帧、混合轨道、循环/停止/重开以及 Android 包内库。安装成功与资源加载成功不等于播放成功。

Godot 中的通用接入步骤、`SpineSprite`/SkeletonData/Atlas 资源链、`.tres/.tscn` 固定宿主、主轨道与 overlay 播放适配器，以及跨平台失败模式见 [godot-spine-integration.md](godot-spine-integration.md)。

## 4. 功能与动画作为一次事务

每个入口追踪输入、前置条件、库存/存档、引导/动画、业务提交、反馈、退出清理，明确唯一 owner 和一次提交点。提示不得用 debug auto_solve 代替还原；先取证 guide/自动交换/AB 模式，覆盖次数不足、连点、拖拽中、暂停、换关、最后一步和取消。

同时检查下一关权威 level、棋盘交互复位、奖励幂等、章节推进、暂停计时、全局引用释放。测试隔离存档并校验玩家文件未变。关卡图片内容与玩法配置分别保留来源；证据冲突时不能直接套用旧报告参数。

## 5. Godot 预制体固化

固定 UI/Spine 宿主序列化到 `.tscn`，骨架、图集、材质保存原生资源，UI 时间线保存 AnimationPlayer 轨道。运行时查找复用固定节点；动态业务状态仍由脚本驱动。这里的固化不是把 UI 截成整张图。

生成器设置正确 owner、稳定节点名和资源引用，不能保存玩家状态或正在运行的 Tween。重新打开场景检查可见、可编辑及依赖齐全，再验证连续打开/关闭/重置不重复生成、不残留动画和遮挡。桌面与 Android 分别验收。

## 6. 包体、测试与发布

按最终 APK ZIP compressed_size 分类统计，分清源图、导入缓存与包内大小。JPEG 无损导入可能膨胀；修改有损导入需保留源哈希、原配置和质量指标，不能称无损。重复纹理仅逐项排除已证实等价且无独立引用者，禁止 tex_* 通配删除。

安装最终 APK，核对 Spine 库及资源后实机测试；旧包截图不能替代。备份脚本用 .txt 或 .gdignore，避免重复 class_name。测试结束等待声音自然播放完，区分退出未释放声音与持续泄漏。

技能多端发布先检查父目录 junction/别名；将所有源字节读入暂存快照后写入目标，禁止对可能别名的目录直接 copytree。写后比较全树 SHA-256 并运行结构门禁；空文件或校验脚本无输出不是通过。

## 7. 已验证案例与未完成边界（CASE_ONLY_JIGSAWCARD）

2026-09-11：45 个 Spine 文件别名恢复成 42 份唯一数据，源版本包含 4.1.24/4.1.08；完整转换为 4.2.11 后，在 Godot 4.6.2 对 85 个动画条目执行加载及推进，抽查真实画面。这不证明所有原版触发点已正确接入。

530 张 JPEG 原文件哈希不变，质量 0.95 导入后缓存约 792.04→207.40 MiB，三张样本 PSNR 约 42.7–44.5 dB；这不是无损，最终 APK 仍需测量。737 张 tex_ 图片确为重复，另 25 张同前缀不重复。

进度 AB 三张切图仍为黄脸，不能宣称猫脸恢复。原始章节 JSON 与旧报告及当前实机存在冲突。完整提示效果、全部页面、动画时间线和最终包仍需验收，不得写成已完成经验。

## 8. 图集尺寸与裁切留白补充（GENERALIZED_PATTERN）

逐页对照 Spine atlas 声明尺寸、实际 PNG 尺寸、旋转后的 region 边界；按 bundle SHA-256 + CAB + pathID 回读原 Texture2D 和 atlas TextAsset，并比较解码 RGBA 与文本字节哈希。同名纹理只能作为候选，不能代替身份或引用链。原 Texture2D 与导出 PNG 相同但页面尺寸不同，尚不能独自证明整页缩放、补边或错图；结合 region 透明像素覆盖、原 Material 引用及真实渲染区分。非等比页面必须分别计算两轴，证据不支持的页保留待查，禁止批量猜修。

只有整页缩放证据成立时，才评估页面坐标归一化：同步处理 page size、region xy/bounds、trim offset、original size；旋转 region 的页面轴与本地宽高轴须交换。不得只改 page size，或只缩 bounds 而保留旧 trim。保留骨架 attachment 逻辑尺寸与原图，记录整数像素舍入误差；验证全部 region 边界、动画加载推进和真实关键帧。转换默认 dry-run，以原/目标哈希识别未改、已改、未知三态，备份与逐字段映射用于回滚，防止重复缩放。

Unity Sprite 的逻辑画布、实际裁切、textureRectOffset、pivot 与 UI RectTransform 是不同量。导出紧裁图不得直接拉伸填满逻辑矩形；按原裁切偏移恢复透明画布或等价子节点布局，再套父级适配变换。明确偏移的坐标方向及整数舍入。Image 类型与 border 无证据时，不把普通贴图擅改九宫格。静态外观恢复不能证明按钮路由、计分或粒子触发已实现。

## 9. 组玩法与延迟生命周期补充（GENERALIZED_PATTERN）

不能把“拼图”默认实现为单块绝对归位。用同一原版布局逐步实测：离原点连接是否成功、拖任意成员是否移动整组、第二个独立组是否改变进度、组汇合、重叠移动、单块/异形组碰撞是否拆组、越界与取消。分别检验绝对正确数、总连接数、最大连通组等候选进度模型；最大组规则只在证据支持时采用。槽置换先生成完整计划再原子提交，测试槽双射、组形状、回填链与撤销/取消后的状态。未取证的碰撞分支不得宣称完全一致。

玩法语义改变时同步审查旧 QA：不得用 auto_solve 或 original_index 归位断言掩盖错误。可安排明确的初始 fixture，但业务提交必须走真实开始/移动/释放；提示按其实际目标与新增连接验证，并确认末步扣费、反馈、结算各自顺序。分开检查模型快照和拖动中的可视坐标，覆盖异触点释放、快速连续拖组和最后一步。

延迟反馈必须绑定所属场景生命周期；换关、暂停、离场与开始下一次拖动都要定义取消边界。使用 generation/epoch 淘汰旧反馈，并清理所属 Tween/Timer；不能只在下一次释放时更新 epoch。若 await 定时器在 owner 删除后产生残留，改用可取消的节点绑定回调并实测退出。完成已提交但结算待播时，明确暂停策略，避免结算因 paused 被丢弃。测试必须覆盖延迟期间立即返回、重载、下一次拖动及末步暂停，等待超过延迟后再核对奖励、场景与 ObjectDB/计时器警告，不能只凭 failures=0 判断通过。

## 10. 配置快照与后期系统门禁（GENERALIZED_PATTERN）

未知配置不能散落为脚本常量。按当前受检版本生成唯一 snapshot defaults，保留资格、配额、AB、样式、奖励、payload、开关和位置的实际值；缺失 payload 保持 `null`/空，已关闭功能保持关闭。运行时由配置 facade 加载，显式玩家状态或 provider payload 按字段 owner 覆盖，并用消费者测试证明入口、解锁演出和结算分支读取同一来源。

排行榜、Daily、图鉴等后期系统使用显式 completion snapshot 和可取消 Gate。固定节点、资源与坐标只能证明静态结构；缺少原版动态 payload 时，时间线必须标为 `fitted`，不能按关卡号强播或以占位数据写回存档。完整阶段和验收见 [端到端生产流程 S4–S6](end-to-end-restoration-workflow.md)。

## 11. Android 物理返回键与全局弹窗栈门禁（GENERALIZED_PATTERN）

移动端（尤其是 Android）平台下，物理/手势返回键（`KEYCODE_BACK` / `KEY_BACK`）是核心操作习惯。在 Godot 4 移植中，默认存在以下严重缺陷：
1. **默认自动退出进程**：Godot `SceneTree.auto_accept_quit` 默认值为 `true`，收到系统 `KEYCODE_BACK` 会直接将应用切入后台或销毁，即便当前有全屏弹窗或二级界面处于打开状态。
2. **弹窗未关闭即退后台**：若未做全局输入拦截，用户在设置、每日挑战、章节图册、排行榜等弹窗按返回键，会直接跳出游戏，造成极其恶劣的体验。

**强制门禁规范**：
- **全局拦截退出**：在主场景入口（如 `Main.gd` 的 `_ready()`）中必须显式声明 `get_tree().set_auto_accept_quit(false)`，接管退出生命周期。
- **弹窗优先级栈与输入消费**：在 `Main.gd` 或全局控制器中的 `_unhandled_input(event)` 统一捕获 `KEY_BACK`：
  ```gdscript
  func _unhandled_input(event: InputEvent) -> void:
      if event is InputEventKey and event.pressed and event.keycode == KEY_BACK:
          if _try_close_topmost_dialog():
              get_viewport().set_input_as_handled()
              return
          # 若无弹窗打开，再提示退出确认或优雅处理
  ```
- **GDScript 动态样式修改 API 铁律**：动态生成或刷新弹窗文本样式时，禁止使用字典索引访问（如 `label.theme_override_font_sizes["font_size"] = x` 会导致运行时静默失效或报错），必须调用官方覆盖 API：`label.add_theme_font_size_override("font_size", val)` 与 `label.add_theme_color_override("font_color", color)`。

## 12. 模拟器/真机桌面会话与可见性门禁（GENERALIZED_PATTERN）

在自动化测试、CI/CD 或智能体驱动真机/模拟器验收时，极易产生“自动化已跑通通过，但用户物理屏幕看不到任何画面”的隔离假象：
1. **无头引擎与前台 GUI 分离**：如 MuMu 12 等现代 Android 模拟器，CLI 或服务启动时常以底层无头虚拟机引擎（如 `MuMuVMMHeadless.exe`）运行，ADB（如 `127.0.0.1:16384` 或 `emulator-5554`）能够正常连接，`screencap` 与 `input tap` 均能采集真实渲染帧，但模拟器的 Windows 桌面宿主窗口处于隐藏模式（`Visible=0, Rect=(0,0,0,0)`）。
2. **Windows Desktop 会话隔离**：自动化代理进程若在沙箱桌面环境（如 `exebox-*`）执行，直接调用 Win32 GUI API 会操作到虚拟沙箱桌面，无法将窗口显示给物理显示器（`default` 桌面）。

**强制门禁规范**：
- **区分 ADB 帧验收与用户交付验收**：脚本测试只需 ADB Surface 帧，但向用户做最终实机交付或演示时，必须确保模拟器/镜像窗口在物理桌面可见。
- **Win32 桌面绑定与窗口唤起规范**：跨会话/沙箱唤起模拟器窗口时，必须将当前线程桌面切换至交互桌面后呼出：
  ```python
  hDefault = OpenDesktopW('default', 0, False, 0x01FF)
  SetThreadDesktop(hDefault)
  ShowWindow(hwnd_mumu, 9)  # SW_RESTORE
  SetForegroundWindow(hwnd_mumu)
  ```
- **权威存档基线双向不可变门禁**：验收全流程必须维护明确的官方基线存档（如关卡数、金币数、提示道具数及其 SHA-256 哈希）。测试开始前检查并推入基线存档，测试结束后必须立刻执行双向核验与恢复（`su -c cp ... && sha256sum ...`），严禁残留脏测试存档污染玩家真实进度。

## 13. JigsawCard 已验证回填（CASE_ONLY_JIGSAWCARD）

本案例的完整结果、证据路径和未完成边界见 [jigsawcard-restoration-lessons.md](jigsawcard-restoration-lessons.md)。已经落地的门禁结果包括：Spine 4.1 数据转换到目标 runtime 后的全动画加载/推进抽查；真实连接组拖放、组移动、回填、拆组与提示事务回归；成功拼接外框/粒子/边缘光与 1 像素边界修复；结算 WIN、大图历史卡、三统计、火苗页和跨进程续局的 Android 专项验证；530 张用户替换图片源哈希和最终包体指标保护；每日挑战 42 格月历与 12 月奖杯陈列室；章节图册多章 25 块拼图蒙版；Android 物理返回键全量弹窗栈拦截；MuMu 12 桌面会话窗口恢复与 16 项自动化回归套件（0 FAIL）。

这些结果只能证明对应覆盖范围，不证明所有原版页面、音效、触发点、评价字/Emoji 分支或关卡配置已经完成。复用本案例时必须重新建立设备前台 guard、APK/存档哈希、原版与重制版本谱系，并把无效录像从证据集中剔除。

## 14. 隔离副本、类索引与导出验收门禁（GENERALIZED_PATTERN）

为打包或测试做工程隔离副本时，**忽略边界必须与源工程一起复制**（`.gdignore`、`.gitignore`、exclude 清单）。jigsawcard 2026-10-10 灰屏事故链：隔离脚本漏带 `docs/.gdignore` → 归档的 `BoardModel.gd` 进入副本并以 `class_name` 抢注全局类 → APK 类索引指向包内不存在的路径 → 进关灰屏，且静态检查与 QA 全绿，无法提前发现。

强制门禁：

- 隔离副本逐项核对忽略边界与源工程一致；归档/备份脚本（`.txt` 或 `.gdignore` 化，见第 6 节）不得进入参与编译的目录。
- 导出验收**双查**：① 包内类索引/元数据（`validate_runtime_class_cache` 类校验）② 真实场景执行（`--headless` 或实机进关）。只查①会漏"类索引指向不存在路径"，只查②会漏边缘分支。
- 生产构建固化为"隔离副本导出 + 包内索引核对"脚本（jigsawcard：`tools/build_verified_android.py`），禁止手工复制工程后导出。
- 任何"归档旧脚本/挪动 .gd 文件"类变更后，必须重跑导出 + 进关冒烟——`class_name` 冲突是静默的。

（CASE_ONLY_JIGSAWCARD）修复后交付 `jigsawcard-fixed-20261010.apk`（300.9 MiB，SHA-256 `b6259506…d302`），隔离回归 49/0、56/0、38/0、86/0、24/0、19/0（检查项/失败数），用户实机确认灰屏、拖动跟随、合并延迟与接缝修复。
