---
name: prefab-bake
description: Use when an agent reskins or builds UI in runtime code (nodes created / sprites replaced at boot) and the user opens the editor and cannot see or edit the new look, says the prefab still shows the old UI, asks to 固化/烘焙 UI 回 prefab, make prefabs WYSIWYG editable by artists, bake runtime reskin back into .prefab JSON, split mockups into reusable controls, or verify editor view equals runtime view in Cocos Creator 2.x/3.x projects. Also covers prefabs edited by direct JSON manipulation when the CLI cannot edit prefabs.
---

# Prefab 烘焙 / WYSIWYG 固化 (prefab-bake)

## 执行卡（先用这张卡，再读正文）

**我管什么**：把运行时 `apply*()` 代码换肤反向固化回 `.prefab` / `.tscn` 资产，使编辑器所见 = 运行时所感、美术可直接编辑；不管纯换图（走 `skinning-pipeline`）、不管 prefab 损坏修复（走 `cocos-creator-repair`）。

**第一步做什么**：先取证定位运行时换肤的唯一 owner（哪个 TS 在 onLoad/onShow 改尺寸/换 spriteFrame/建节点），通读它的 `apply*` / `setup*` / `style*`，落成「函数 → prefab 字段」映射清单；未锁定唯一 owner 前不许动 prefab。

**做完怎么算完成**：
- [ ] 映射清单里每个数字都能追到具体 prefab 字段，没有来源不明的常数
- [ ] 原 prefab 已原样备份到带日期的 backup 目录，且烘焙脚本有幂等 guard
- [ ] 写回后 JSON 重解析成功、fileId 唯一、对象数 = 原有 + 新增预期值
- [ ] Cocos CLI 构建 / asset-db 重新导入无报错
- [ ] headless 冒烟探针值与烘焙表全等或仅差 Widget 重算位，console errors=0，截图目检
- [ ] 多分辨率冒烟（设计分辨率 + 一高一矮，如 9:16 与 9:20）各跑一遍且适配确实生效

**红线（不可违反）**
- 烘焙期间禁止删除/清空任何运行时布局函数及其调用点（apply*Layout / fit 缩放 / Widget 适配必须原样保留并保持调用）；只允许把"创建节点"改成"按名查找、缺失才创建"——烘焙 ≠ 删除运行时适配
- 改 prefab 前必须先备份；烘焙脚本必须幂等（检测到已烘焙标记节点即退出）并支持从备份一键恢复
- 重新烘焙必须先读回现有资产、保留同名节点的位置/尺寸/字号等布局值（R2），硬编码数字只作新节点默认值，不许凭记忆写
- 运行时代码不得写布局常量（R3）；节点名与引用（owner / fileId / uuid / `.meta`）不得用布局值当身份（R5）
- 全屏背景禁止双轴拉伸：统一 `s = max(viewW/srcW, viewH/srcH)`，禁止 `setContentSize(max(minW,viewW), max(minH,viewH))`；背景四边 Widget 在 prefab 和运行时都必须禁用
- 编辑器可见 ≠ 运行正确：必须过重解析 + 构建 + 冒烟探针 + 多分辨率门禁，只做编辑器目检不算完成

**卡住时按顺序读**
- 出现"改了没生效"、生成器覆盖美术调整 → `### 1c. 布局真源契约` 的 R1–R5，落地模板 `### G2. 生成器必须"读回再写"`
- 运行时写死 `offset_*/font_size/custom_minimum_size`、两态排版 → `### G3. 运行时代码改成"基线驱动"`
- 需要写回归门禁 / 复现往返验证 → `### G4. 回归门禁模板` 与 `modules/prefab-bake/references/godot-layout-preservation-case.jigsawcard.md`
- Cocos 字段名不确定（`_lpos` / `_alignFlags` / fileId / Sprite `_type`）→ `## 3. Cocos 3.x prefab JSON 字段速查`

全局五步循环与六条铁律见 `references/execution-protocol.md`。

把"运行时代码换肤"反向固化回 `.prefab` 资产，使 **编辑器所见 = 运行时所感**，
美术可以直接在 Cocos Creator 编辑器里打开 prefab 继续调整。

范围标签：正文流程与序列化字段表是 `GENERAL_DEFAULT`（Cocos 引擎格式，跨项目通用）；
"从 TS 运行时函数逐值反推"的工作方式是 `GENERALIZED_PATTERN`；案例里的具体坐标、
uuid、尺寸是案例值（`DO_NOT_COPY_LITERAL_VALUES`）。

## 0. 什么时候用（症状 → 判断）

| 症状 | 判断 |
|---|---|
| 编辑器打开 prefab 显示旧版视觉；运行时/真机显示新版 | 运行时代码换肤（启动时 `apply*()` 改属性/新建节点），prefab 未回写 → 本模块 |
| 项目里根本找不到某界面的 prefab（纯代码拼的界面） | 先把界面落成 prefab-first（本模块 + 按现有界面克隆结构），再烘焙 |
| 只是换图片/图集（不改节点结构） | 用 `skinning-pipeline`（manifest/apply/verify），不需要本模块 |
| prefab 打不开/引用悬空/编辑器崩 | 先用 `cocos-creator-repair` 修好再谈烘焙 |

关键前提（先取证，别假设）：**找到运行时换肤的唯一 owner**（哪个 TS 在 onLoad/onShow
里改尺寸/换 spriteFrame/建节点），把它的每次调用翻译回 JSON。换肤代码散在多处时，
先确认哪个是真实执行路径（`0.` 全局证据规则）。

## 1. 决策：烘焙 vs 重搭

- 运行时逻辑已稳定、视觉已验收 → **烘焙**（本模块，改 JSON，保 uuid，保 .meta）。
- 界面要大改版 → 编辑器重搭 prefab + 保留组件绑定，再删运行时换肤代码。
- 两者共用一条铁律：**烘焙后运行时 apply* 函数必须幂等**（已有节点复用、重算同值），
  否则"编辑器所见"和"运行时所感"会分叉成两套。

### 1b. 适配关系铁律（用户验收返工教训，最高优先级）

**烘焙 ≠ 删除运行时适配。** prefab 只固化"设计分辨率快照"（编辑器 WYSIWYG 用）；
运行时按设备可见区/安全区重排的适配函数（apply*Layout / fit 缩放 / Widget 调整）
**必须原样保留并保持调用**。反例（真实返工案例）：烘焙时把 `applyBv2Layout()` 连同
调用点一起删除，静态值只对设计纵横比正确——9:16→9:20 等其他分辨率上 bg 不铺满、
按钮错位、拼图板比例失真，用户验收直接打回，只能从会话记录恢复函数重接。

正确架构是"双真值"：
1. **prefab = 设计稿快照** → 美术在编辑器打开即见最新视觉、可直接改；
2. **运行时 apply 适配函数 = 设备真值** → 每次界面打开按 `view.getVisibleSize()`/
   安全区重算位置尺寸（对烘焙节点 find-first 复用，重算结果覆盖快照值）。

由此推出烘焙脚本的三条硬约束：
- 烘焙期间 **禁止删除/清空任何运行时布局函数及其调用点**（只允许把"创建节点"改为
  "按名查找、缺失才创建"）；
- 烘焙值必须与适配函数在设计分辨率下的输出**逐值一致**（同一公式算出来，不要手算），
  这样运行时重排前后视觉无跳动；
- 烘焙若关闭了某些 Widget（硬放置节点），适配函数必须覆盖这些节点的完整定位，
  不能留"既无 Widget 又无运行时赋值"的孤儿节点。

**适配实现的选型（返工后定案）**：
- **首选：Widget 锚定烘焙**（无需运行时布局代码）——顶部元素 TOP、底部元素 BOTTOM、
  居中 BOTTOM|CENTER（`_horizontalCenter=0`），偏移=设计稿位置换算；bg 用等比 cover
  （3 行代码，禁止 Widget 四向拉伸——会变形）。对任意窗口/设备比例稳健，编辑器可视化可调。
- 母版坐标映射类适配函数（place/master→visible 拉伸）**对自由比例环境（编辑器预览、
  桌面浏览器）不稳健**——极矮/极宽可视区会把 UI 压扁；若必须保留，需验证横屏极端比例。
- 编辑器预览窗口是自由比例——QA 冒烟必须包含一个横屏极端 case（如 1280×720）。

### 1c. 布局真源契约（2026-10-07 事故后新增，最高优先级）

> **事故**：把主页 prefab（`HomeArt.tscn`）的文字节点位置/字号调好并保存，运行时**不生效**，
> 只有图片调整生效（用户口径"改了没反应"）。根因不是"没保存"，而是**两个写入者在改同一个资产文件**：
>  `tools/home_art_builder.gd` 把每个 Label/Sprite 的矩形与字号**硬编码**，再由
> `generate_home_art.gd` 把结果**写回 `res://scenes/shell/HomeArt.tscn`**正是美术编辑的那个文件；
>  `HomeSlices.gd` 在每次 `refresh()` 里**无条件覆写** rank 标签的 rect/字号。
> 于是"重新烘焙"或"运行时刷新"都会把美术的调整打回默认值。

**契约（烘焙后资产 = 布局真源）**：

| # | 规则 | 说明 |
|---|---|---|
| R1 | **一个文件只能有一个布局真源** | 烘焙器/生成器的产物与美术编辑的文件是同一个文件时，它就是唯一真源；生成器只能"读回来再写"，不能"凭记忆写"。 |
| R2 | **重新烘焙必须保留美术侧布局** | 生成同名节点前先读回现有资产，保留 `position / size / offset_* / font_size / font_color / outline_* / alignment`（Godot）、`_lpos / _contentSize / Widget 四边 / fontSize`（Cocos）。硬编码数字只作**新节点默认值**。 |
| R3 | **运行时代码不得写布局常量** | 需要两态（有标题/无标题、锁定/解锁）或依赖文本宽度时：**先采样资产基线，再按基线推导**，不要写第二套魔法数字。 |
| R4 | **R2/R3 都要有回归门禁** | 快照关键节点  重跑烘焙器（或调一次运行时代码） 任一 rect/字号/颜色变化即 FAIL。 |
| R5 | **保留"对象身份"，只让"布局值"可变** | 节点名与引用（`owner`、fileId、uuid、`.meta`）由烘焙器保证稳定；**不要用布局值当身份**。 |

**R2 判别口诀**：生成器里出现的每个数字，问一句"美术如果也调了这个值，谁赢？"
答不出"美术赢"，就得改成读回式。

**R3 判别口诀**：运行时写死的 `Rect2/Vector2/offset_*/font_size` 就是布局常量；
能表达成"基线  比例"或"基线 + 偏移"的一律改成基线推导；纯动画/形变（tween、缩放、粒子、
随可见区重算的响应式适配）不属此列，**保持原样**。

## 2. 工作流（七步）

1. **读 TS 换肤函数**：通读 `apply*` / `setup*` / `style*`，列出"函数 → prefab 字段"
   的映射清单（位置/尺寸/spriteFrame/颜色/描边/Widget/开关/新建节点）。
2. **备份**：原样复制 prefab 到带日期的 backup 目录；烘焙脚本必须幂等
   （检测到已烘焙标记节点即退出），并支持从备份一键恢复。
   **并且：重新烘焙不得抹掉美术在编辑器里调过的布局**产物与美术编辑的是同一个文件时，
   必须先读回现有资产、保留同名节点的布局值（见 1c 的 R2 与 Godot 侧 G2 模板），
   否则用户会看到"改了没生效"（2026-10-07 实证事故）。
3. **dump prefab**：遍历 JSON 列出节点树 + 组件明细（索引|名字|active|pos|size|sf uuid|Label 值）。
   注意 Cocos 3.x 根节点 `_parent` 为 `null`，从数组 index 1 开始走树。
4. **逐值换算**：运行时函数里的每个数都要能追到 prefab 字段：
   - 设计基准固定（如 fitWidth 下的设计分辨率）；contain 缩放
     `fitSpriteInside(node, maxW, maxH)` 需要**原图 PNG 尺寸**（读 PNG IHDR：
     宽=字节16-19，高=20-23），`scale=min(maxW/w0,maxH/h0)`，写回 `UITransform._contentSize`；
   - Widget 对齐只写 `_top/_bottom/_left/_right/_alignFlags`，`_lpos` 会被运行时
     Widget 重算——烘焙值仍要写对（编辑器无运行时时以 _lpos 显示）；
   - 新建节点：node + `cc.PrefabInfo` + 每个组件 + `cc.CompPrefabInfo{fileId}`，
     fileId 为 22 位随机 base64，**全文件去重校验**；
   - **Sprite 依赖 UITransform**：push 节点时必须同时建 UITransform，否则运行期/编辑器渲染异常；
   - 运行时 `Graphics`/`tween`/事件监听**不可序列化** → 视觉部分转为 PNG + Sprite
     （SIMPLE/CUSTOM），交互部分留在 TS（本来就留在 TS）。
5. **写回 + 校验**：`JSON.stringify(arr,null,2)` 写回后立即重解析；断言：
   fileId 无重复、对象数 = 原有 + 新增预期值、关键节点字段与换算表一致。
6. **重建 + 冒烟**：构建产物里该 prefab 重新生成；headless 冒烟打开该界面，
   探针读运行时节点值与烘焙值比对（应全等或仅差 Widget 重算位），截图目检。
7. **文档**：按宿主项目的迭代规则追加 changelog + 备份目录 + 脚本路径。

## 3. Cocos 3.x prefab JSON 字段速查（GENERAL_DEFAULT）

序列化数组：`[0]=cc.Prefab{data}`,之后对象用 `{__id__:n}` 互引。

- `cc.Node`：`_name,_objFlags,__editorExtras__,_parent,_children,_active,_components,
  _prefab,_lpos{Vec3},_lrot{Quat},_lscale,_mobility,_layer,_euler,_id`
  （UI 层常用 `_layer=33554432`；子节点继承父 layer，新节点显式赋父 layer）。
- `cc.PrefabInfo`：`{root:{__id__:1},asset:{__id__:0},fileId,instance:null,
  targetOverrides:null,nestedPrefabInstanceRoots:null}`。
- `cc.CompPrefabInfo`：`{fileId}`（22 位）；组件 `node` 回指宿主、`__prefab` 回指 CompPrefabInfo。
- `cc.UITransform`：`_contentSize{Size},_anchorPoint{Vec2}`（UI 默认 anchor 0.5,0.5）。
- `cc.Sprite`：`_type`（0=SIMPLE 1=SLICED 2=FILLED 3=MESH）、
  `_sizeMode`（0=CUSTOM 1=TRIMMED 2=RAW）、`_spriteFrame{__uuid__,__expectedType__:'cc.SpriteFrame'}`、
  `_color`、`_enabled`；SpriteFrame uuid 形如 `<asset-uuid>@f9941`（取自同目录 `.png.meta`）。
- `cc.Label`：`_string,_fontSize,_actualFontSize,_lineHeight,_overflow`（0=NONE 1=RESIZE_HEIGHT
  2=SHRINK）、`_enableWrapText,_isBold,_isItalic,_isUnderline,_horizontalAlign/_verticalAlign`
  （0=LEFT 1=CENTER 2=RIGHT）、`_color,_enableOutline,_outlineColor,_outlineWidth,
  _enableShadow,_shadowColor,_shadowOffset,_cacheMode,_isSystemFontUsed,_i18nKey`。
- `cc.Widget`：`_alignFlags` 位掩码 TOP=1|V_CENTER=2|BOTTOM=4|LEFT=8|CENTER=16|RIGHT=32、
  `_top/_bottom/_left/_right,_enabled`。
- `cc.Layout`：`_enabled,_type,_resizeMode,_spacingX,_spacingY`；烘焙"运行时关掉 Layout"
  就是 `_enabled:false`。
- `cc.Button`：`_normalSprite{__uuid__}` 等可选；事件绑定不序列化。
- `sp.Skeleton`：至少序列化 `_skeletonData{__uuid__,__expectedType__:'sp.SkeletonData'}`、
  `defaultSkin/defaultAnimation`、`_premultipliedAlpha`、`_timeScale`、缓存模式、调试开关和
  `loop`；宿主仍必须有 `cc.UITransform`。资源 uuid 取骨骼 `.json.meta`/`.skel.meta`，不要
  把 atlas 或 PNG uuid 填进 `_skeletonData`。
- 可复用 FX 宿主：节点名固定为运行时可精确查找的名字，Prefab 中 `active:false` 且直连
  SkeletonData；播放时 `find-first → active=true → 重置 Tween/UIOpacity → enabled=true →
  paused=false → clearTracks → setAnimation`；结束时停用节点，**不得 destroy 已烘焙宿主**。
  动态创建只作旧 Prefab/资源异常回退。
- 嵌套 prefab 实例：子节点带 `_prefab{fileId}` 且 PrefabInfo.instance 非空——**不要**
  把烘焙节点插进嵌套实例内部；插到宿主自有节点下。

## 4. 验收门禁（全部通过才算完成）

1. 重解析 JSON 成功 + fileId 唯一；
2. Cocos CLI 构建（asset-db 重新导入）无报错——prefab JSON 非法会在这里爆；
3. 冒烟：界面可打开、探针值与烘焙表全等、console errors=0（区分探针自身噪音，
   如页面全局缺 `cc.UITransform` 导出导致 `getComponent(undefined)` 报错——改用
   `node.components` 按 `constructor.name` 探测）；
4. 截图目检（列表页/详情页/各弹窗状态逐屏）；
5. **多分辨率冒烟**：至少设计分辨率 + 一高一矮纵横比（如 9:16 与 9:20）各跑一遍，
   断言适配生效（bg 尺寸随可见区变化、关键节点按比例重排）——只测设计分辨率
   放不走"适配被删"这类回归；
6. 编辑器实开 prefab 目检（交付用户）。
7. Spine 宿主门禁：每个运行时 `Fx.play(parent, group)` 都能在对应 parent 下找到唯一同名
   烘焙节点；SkeletonData 非空、fileId 唯一、首次与二次播放都正常，回收后节点仍在层级中。

## 5. 已知坑（案例提炼，GENERALIZED_PATTERN）

- **"产物 = 美术编辑的那个文件"的生成器**（2026-10-07 实证）：生成器把硬编码 layout 写回它自己的产物
  路径，而这个路径正是美术在编辑器里编辑的资产  每次重跑都覆盖美术调整，用户看到的是"改了没生效"。
  修法见 1c 与 G2：读回现有资产  同名节点保留布局  硬编码只作新节点默认值；
  配套门禁见 G4。**不要用"禁止重跑生成器"来规避**那会让烘焙流程死掉。

- **CLI 无 prefab 编辑能力**：Cocos Creator CLI 只能构建，不能改 prefab →
  只能直接改 JSON 或编辑器 GUI；脚本化必走 JSON。
- **PowerShell 启动 CocosCreator.exe 构建**：`&` + `*>` 重定向会 EPIPE 断管、
  构建静默夭折（产物 mtime 不更新）；用 `Start-Process -RedirectStandardOutput/
  -RedirectStandardError` 落文件，再轮询进程退出 + 产物 mtime + 日志 "Finished"。
- **脚本重复执行**：终端输出被污染时"看似失败实际已写盘"，二次执行产生双份节点 →
  幂等 guard（首个烘焙标记节点存在即退出）+ 先备份。
- **print/exit 丢输出**：冒烟脚本 `process.exit(0)` 在 Windows 管道上丢缓冲日志 →
  延迟 800ms 再退出，或落盘后读文件。
- **fitSpriteInside 非幂等陷阱**：它按 spriteFrame 原图尺寸重算——烘焙值必须与
  运行时重算值一致（同一原图、同一 maxW/maxH），否则每帧/每次 onShow 会跳动。
- **全屏图片禁止双轴拉伸**：背景使用 `spriteFrame.originalSize`（缺失时才回退 frame 宽高），
  统一计算 `s=max(viewW/srcW, viewH/srcH)`，把 UITransform 写为 `srcW*s × srcH*s` 并居中。
  Prefab 设计快照用同一公式烘焙，运行时每次按可见区重算；背景上的四边 Widget 必须在 Prefab
  和运行时都禁用。`setContentSize(max(minW,viewW), max(minH,viewH))` 会独立改变宽高，必然拉长图片。
- **新档案默认进度**：冒烟"点击已解锁项"前先解锁（写进度 store），否则全锁点不到详情。
- **Widget `_horizontalCenter` 是比例不是像素**（CC3.8.7 实测）：0.44 → 节点偏移
  0.44×父宽。居中一律写 0；需要绝对像素水平偏移时改用 LEFT/RIGHT（`_isAbsLeft/Right=true`）。
- **并发构建污染**：多轮启动 CocosCreator CLI 构建若前一轮未真正退出，会堆积数十个
  进程互写 build 目录——产物混合多个源状态，冒烟数值诡异且"改了没生效"。每轮构建前
  `Get-Process CocosCreator | Stop-Process -Force` + 删 build 输出目录 + 单实例构建；
  验证产物时直接 grep 构建产物里的特征字符串（新函数名/删除的函数名）。
- **CDP 探针误用 window.find**：eval 里调 `find(x,y)` 而非注入的 `f(x,y)` 时，
  Chrome 原生 `window.find` 会静默接住调用（不报错、恒返回 null）——子节点查找
  全部落空且 errors:0，极难察觉。注入的查找函数统一只用一个别名，且首条冒烟
  应断言"已找到的节点的子节点查找"非空。
- **从会话记录恢复代码**：LLM 会话的 read 工具输出带行号前缀（`NNN:` / `NNN `），
  恢复函数体时要剥前缀并**过滤读取输出的上下文头**（import 片段等垃圾行），
  否则会把垃圾行插进 TS 造成 SyntaxError（构建 17% 失败、产物只剩 src/）。
- **结算 FX 层级归属**：把庆贺/Emoji 挂在弹窗内容节点并 `setSiblingIndex(0)` 会稳定被最终
  弹窗遮住。需要跨弹窗置顶的视觉反馈应在弹窗根节点预烘焙独立 Overlay，并把 Overlay 与
  FX 都放到最后 sibling；照片内评价字仍留在照片/成功弹窗局部层，避免坐标系漂移。
- **Spine 组件动态新增不可编辑**：运行时 `new Node + addComponent(sp.Skeleton)` 即便显示正确，
  编辑器仍不可见。所有已接入骨骼先烘焙宿主与 SkeletonData，运行时只选择动画、坐标、缩放
  和显隐；完整数据修复/跨端 QA 见 `modules/cocos-qa/references/spine-fx-repair-qa.md`。
- **玩法状态不可偷带程序框体**：收集目标、选中态、完成标记应由布尔/枚举状态驱动；不要在拼图块
  上临时 `new Graphics` 画呼吸描边并把它当状态本体。正式画面不需要该提示时只保留状态，销毁旧
  调试节点；运行态 QA 扫描目标容器内的 `Graphics`/特征节点名，断言拼好后覆盖框数量为 0。

## 6. 案例锚点（CASE_ONLY，只取方法不取值）

- 怀旧时光拼图（huaijiushiguang-pintu 项目 skill）：`working/materialize_*.cjs` 四连
  （PageMain/PageHome/PopResult/PopXaingce）+ `working/dump_*.cjs` +
  `working/backups/<date>_materialize_*_prechange/` + `working/restore_runtime_layout.cjs`
  （适配函数从 DSH 会话记录恢复的返工案例）。该案例的可复用模式：
  "读 TS apply 函数 → 换算表 → pushNode 工具集 → 重解析校验 → 双段冒烟（列表+详情）→
  多分辨率适配冒烟"；不可复制：任何坐标、uuid、750×1334 基准、codex_* 命名、852×1846 母版。

## Godot 场景固化（.tscn/.tres）含"重新烘焙不砸美术"的完整规范

固定 UI/Spine 节点、骨架资源、切片边距与 AnimationPlayer 时间线保存为 `.tscn/.tres`，运行时只查找复用；
正确设置 `owner`，重开编辑器验证可编辑，再实机验证。**不要把用户状态或整页 UI 截图当预制体**。
见 [原生还原门禁](../godot-migration-port/references/native-restoration-gates.md)。

### G1. 什么时候会自动重写场景（危险信号清单）

出现下面任一情况，说明这个 `.tscn` **会被脚本重写**美术在里面调的任何布局都可能被覆盖，必须按 G2 处理：

- 仓库里存在"生成器"：`tools/*builder*.gd` / `tools/generate_*scene*.gd|py` / `tools/build_*scene*`，
  里面有 `PackedScene.new()` + `ResourceSaver.save(packed, "res://.../*.tscn")`；
- 生成器的输出路径与美术编辑的资产路径**完全相同**（这是设计缺陷，必须先修）；
- 同一节点在两处被写：`.tscn` 里一套值，`scripts/*.gd` 里又用常量赋一套值。

自查命令（本项目实测有效）：

```powershell
# 1) 谁在写 tscn
Get-ChildItem tools,scripts -Recurse -Include *.gd,*.py -File |
  Select-String -Pattern 'ResourceSaver\.save|\.tscn.*write_text|save\(packed'
# 2) 谁在运行时写布局常量
Get-ChildItem scripts -Recurse -Include *.gd -File |
  Select-String -Pattern '\.offset_(left|top|right|bottom)\s*=|\.custom_minimum_size\s*=|add_theme_font_size_override|\.position\s*=\s*Vector2'
```

### G2. 生成器必须"读回再写"（R2 落地模板）

生成器开头读回现有场景，建"节点名  已调值"表；生成同名节点时套用；硬编码只作新节点默认值。

```gdscript
const OUTPUT: String = "res://scenes/shell/HomeArt.tscn"
var _keep: Dictionary = {}

func _load_keep_values() -> void:
	_keep.clear()
	if not ResourceLoader.exists(OUTPUT): return
	var packed := load(OUTPUT) as PackedScene
	if packed == null: return
	var probe: Node = packed.instantiate()
	if probe == null: return
	_collect_keep(probe)
	probe.free()

func _collect_keep(node: Node) -> void:
	if node is Control:
		var c := node as Control
		var e := {"kind": "control", "position": c.position, "size": c.size}
		if node is Label:
			var l := node as Label
			e["font_size"] = l.get_theme_font_size("font_size")
			e["font_color"] = l.get_theme_color("font_color")
			e["outline_color"] = l.get_theme_color("font_outline_color")
			e["outline_size"] = l.get_theme_constant("outline_size")
			e["h_align"] = l.horizontal_alignment
			e["v_align"] = l.vertical_alignment
		_keep[_keep_key(node.name)] = e
	elif node is Node2D:
		_keep[_keep_key(node.name)] = {"kind": "node2d", "position": (node as Node2D).position,
			"scale": (node as Node2D).scale, "rotation": (node as Node2D).rotation}
	for child: Node in node.get_children():
		_collect_keep(child)

## Godot 写盘会把节点名里的 "@" 规范成 "_"（@Label@13 -> _Label_13），
## 所以保留表的键与查找都要规范化，否则"每日"这类自动命名节点永远匹配不上。
func _keep_key(node_name: String) -> String:
	return node_name.replace("@", "_")

func _apply_keep(node: Node) -> void:
	var key := _keep_key(node.name)
	if not _keep.has(key): return
	var e: Dictionary = _keep[key]
	# ...按 kind 套用上面的字段；Label 还要套 font_size/颜色/描边/对齐
```

**顺序陷阱**：`_apply_keep()` 必须在节点**已经改名之后**调用
（先 `label.name = "ChapterTitle"` 再套用），否则查的是默认名 `StaticLabel`，等于白做；
而且 `_label()` 这类工厂函数里如果先套用、调用方再改名，会连续套错两次。

### G3. 运行时代码改成"基线驱动"（R3 落地模板）

```gdscript
## 首次采样基线；Lv.N 状态原样使用，倒计时状态按基线比例推导
var _baseline: Dictionary = {}

func _apply_layout(unlocked: bool) -> void:
	if _baseline.is_empty():
		_baseline = {"left": _label.offset_left, "right": _label.offset_right,
			"top": _label.offset_top, "bottom": _label.offset_bottom,
			"font": _label.get_theme_font_size("font_size")}
	if not unlocked:
		_restore_baseline()
		return
	var base_w: float = maxf(1.0, float(_baseline["right"]) - float(_baseline["left"]))
	var centre: float = (float(_baseline["left"]) + float(_baseline["right"])) * 0.5
	var new_w: float = base_w * (128.0 / 102.0)          # 原设计的宽比
	_label.offset_left = centre - new_w * 0.5
	_label.offset_right = centre + new_w * 0.5
	_label.add_theme_font_size_override("font_size", int(round(float(_baseline["font"]) * (19.0 / 24.0))))
```

同族修法（都是"基线 + 推导"）：
- **两态竖向排版**（有标题/无标题）：基线取"有标题"版，另一态 = 基线顶端  标题高度；
- **随文本宽度贴边的标签**：宽度照测，**间距**取基线（`gap = baseline_end  (baseline_start + 旧宽)`），不要硬编码 `+34`；
- **重复出现前的复位**（动画回位、重进弹窗）：复位值取**首次读到的 prefab 位置**，不要写死坐标。

### G4. 回归门禁模板（R4）

```gdscript
# scripts/qa/test_prefab_tuning_keep.gd  快照  重跑生成器  比对，任一变化即失败
const KEYS := ["ChapterTitle", "TileCount", "StaticLabel", "DailyDate", "_Label_13"]
# 1) 从 OUTPUT 场景快照这些节点的 position/size/font_size
# 2) 重新 build_art() 并 pack 到 user:// 临时场景（不要覆盖真实资产）
# 3) 逐项比对，打印 OK/FAIL，最终 quit(failures)
# 现状基线：PREFAB_TUNING_KEEP_RESULT checks=5 failures=0
```

### G5. 一个真实项目的自查结果（2026-10-07，jigsawcard-godot）

| 写入者 | 产物 | 处置 |
|---|---|---|
| `tools/home_art_builder.gd` + `generate_home_art.gd` | `scenes/shell/HomeArt.tscn` | 加读回保留（R2）+ 改成可 headless 跑的 SceneTree 入口 |
| `tools/build_settlement_fireworks.gd` | `scenes/effects/SettlementFireworks.tscn` | 同款读回保留；往返 32/32 节点位置不变 |
| `generate_settlement_scene.py` / `streak_generate_scene.py` / `restore_popup_slices.py` / `serialize_spine_prefabs.py` | 多个 popup/effect 场景 | **一次性重建脚本，未改**：重跑前必须先按 G2 加保留逻辑 |
| `HomeSlices.gd` / `HardFinishToast.gd` / `RankRow.gd` / `SettlementDialog.gd` | 运行时 | 改为基线驱动（R3）|
| 动画/响应式（`HomeMotion.gd`、`TweenMotion.gd`、`GameHUD.gd` 形变等）| 运行时 | **不动**：不属于布局常量 |

案例细节与可复现命令（含取证顺序与坑）：[Godot 布局保留案例](references/godot-layout-preservation-case.jigsawcard.md)；
项目内审计文档 `docs/PREFAB_LAYOUT_PRESERVATION_20261007.md`、回归门禁 `scripts/qa/test_prefab_tuning_keep.gd`。

### G6. 交付前自查（贴进 checklist）

- [ ] 所有会写回 `.tscn` 的脚本，都在同一个函数里先 `_load_keep_values()` 再构建（G1 命令扫一遍）
- [ ] 生成器里每个硬编码布局数字，都能回答"美术改了谁赢"= 美术赢（R2）
- [ ] 运行时没有任何 `offset_* / font_size / custom_minimum_size` 常量写入（G1 第二条命令的输出逐条确认）
- [ ] `_apply_keep()` 调用发生在节点改名之后（G2 顺序陷阱）
- [ ] 名字匹配对 `@``_` 规范化（G2）
- [ ] R4 门禁存在且在 CI/交接清单里；现状 `failures=0`
- [ ] 编辑器实开资产，确认美术调完保存后**重跑一次烘焙器**仍保持（G5 的往返验证方式）

## Cocos 编辑器实时通道

Creator 3.8.x 的编辑器操作与中间自检可按 `modules/cocos-mcp-channel/SKILL.md` 执行；2.4.x 或无 MCP 时走本模块文件级/CLI 路径。预览、编辑器引用检查和正式构建/设备验收分别记录证据。
