# Cocos Creator 2.4.13 内置资源 UUID 速查 + 场景重建实战（2026-07-31 Sudux）
> **何时读我**：要在手写场景里引用 Cocos Creator 内置资源 / Sprite 一赋值就大面积报错或 UI 黑屏 / 手写节点报 _updateOrderOfArrival is not a function / 相机字段缺失导致 Play 黑屏但 FPS 正常
> **读完能做到**：查表拿到材质与 spriteFrame 子资源 UUID，补齐 cc.Node、cc.Camera、cc.Canvas、cc.Label 的缺失字段，重建出能正常显示的场景
> **范围**：`GENERAL_DEFAULT`

## 内置资源 UUID（default-assets，场景序列化直接引用）

来源：`CocosCreator_2.4.13/resources/static/default-assets/`（读对应 `.meta`）

### 材质（cc.Label / cc.Sprite 的 `_materials`）

| 材质 | uuid | 用途 |
|------|------|------|
| builtin-2d-label.mtl | `e02d87d4-e599-4d16-8001-e14891ac6506` | Label 组件 `_materials` |
| builtin-2d-sprite.mtl | `eca5d2f2-8ef6-41c2-bbe6-f9c79d09c432` | Sprite 组件 `_materials` |
| builtin-2d-base.mtl | `6f801092-0c37-4f30-89ef-c8d960825b36` | 通用 2D base |

### 图片（注意：**子资源 spriteFrame uuid**，不是主资源 uuid）

| 图片 | 主资源 uuid | spriteFrame 子资源 uuid |
|------|-------------|--------------------------|
| default_btn_normal.png | `e851e89b-faa2-4484-bea6-5c01dd9f06e2` | `f0048c10-f03e-4c97-b9d3-3506e1d58952` |
| default_btn_pressed.png | `b43ff3c2-02bb-4874-81f7-f2dea6970f18` | （读 meta subMetas） |
| default_btn_disabled.png | `71561142-4c83-4933-afca-cb7a17f67053` | （读 meta subMetas） |
| default_panel.png | `d81ec8ad-247c-4e62-aa3c-d35c4193c7af` | `9bbda31e-ad49-43c9-aaf2-f7d9896bac69` |

**铁律**：`cc.Sprite._spriteFrame` 必须填 **subMetas 里的 spriteFrame uuid**。填主资源 uuid → `TypeError: spriteFrame.textureLoaded is not a function` 大量报错、UI 黑屏（Draw Call 1）。提取方法：读 `xxx.png.meta` → `subMetas['<name>'].uuid`。

## 手写 .fire 场景缺失字段清单（对比官方 new-scene.fire）

官方模板：`CocosCreator_2.4.13/resources/static/template/new-scene.fire`（7 对象：SceneAsset/Scene/Canvas/cc.Canvas/cc.Widget/Main Camera/cc.Camera）

### cc.Node 缺失会报 `child._updateOrderOfArrival is not a function`

手写节点必须含：`_skewX:0` `_skewY:0` `_groupIndex:0`（+ 已有的 `_parent/_children/_components/_active/_contentSize/_anchorPoint/_trs/_is3DNode/groupIndex/_id`）。

**引用 id 绝不能硬编码**：生成场景时 children/parent 引用必须用 add() 返回的实际索引变量追踪；硬编码数字（如 Canvas children=[3,6,23]）会导致引用指向 cc.Label/cc.Button 等非 Node 对象 → 加载时 `_updateOrderOfArrival is not a function` 崩溃。生成后用脚本断言所有 `_children`/`_parent`/组件 node 引用都指向 `cc.Node`。

### cc.Camera 缺失字段（Play 黑屏但 FPS 60）

对齐官方模板：`_depth:-1`（不是 1）、`_orthoSize:10`、`_nearClip:1`、`_farClip:4096`、`_backgroundColor:黑(0,0,0,255)`、`_renderStages:1`、`_alignWithScreen:true`、`_rect:{0,0,1,1}`。缺 `_renderStages`/`_alignWithScreen` → UI 层不渲染。

### cc.Canvas / cc.Widget

- Canvas 组件：`_fitWidth:false` `_fitHeight:true`（官方值）
- Canvas 节点要挂 `cc.Widget` 组件（alignMode:1, _alignFlags:45），负责 UI 屏幕对齐
- Main Camera 节点的 `_contentSize` 应为 960x640（不是 0x0）

### cc.Label 必须字段

- `_materials:[{__uuid__: e02d87d4...}]`（builtin-2d-label）——缺材质 Label 不渲染
- `_color` 深色值：按钮白底上白字看不见（"四个白色方块"现象）
- `_N$string` 与 `_string` 都写

## Sudux 实战记录（2026-07-31）

- 项目：`E:\Gameprogram\Sudux`（Sudoku.com 7.8.0 复刻，AI 从 Unity APK 反编译重构为 Cocos 2.4.13）
- 坏文件：`Main.fire` 47 对象手写伪场景，节点 21/24 自引用 → `_initProperties` 栈溢出
- 修复后：64 对象场景（Canvas→BootManager/BootGame + GameManager/GameController，4 按钮挂 default_btn_normal 背景，Background 挂 default_panel）
- 最终卡点：**完整 UI 素材本应来自逆向导出** `E:\download\sudoku-re\assets-export\`（319 Sprite/156 贴图/17 音效/7 字体），而非手写空壳——正确路径是先导入官方素材再组装 UI 面板
- 逆向报告：`E:\download\sudoku-re\REVERSE_ANALYSIS_REPORT.md`（Unity 6000.3.16f1 / IL2CPP / 663 资产已导出）
- 复刻计划：`C:\Users\Administrator\Documents\Qoder\2026-07-30\chat-1\SUDUX_REPLICA_FINAL_PLAN.md`（完成度 65%，UI 面板/动效待做）

## 编辑器进程与登录（本机）

- 命令行 `CocosCreator.exe --project` 内嵌 Dashboard 反复 `Load profile failed: local://settings.json`（~/.CocosCreator/settings.json 缺失时）——复制 profiles/settings.json 到根级可缓解，但仍优先用独立 `Cocos Dashboard 2.2.1`（${COCOS_DASHBOARD}\CocosDashboard.exe，有登录态）
- 独立 Dashboard 打开项目：双击"最近打开"里的项目卡片（Sudux 卡片实测坐标窗口相对 (255,415) → 绝对 (615,556)，vision 坐标会漂移 100+ 像素，以实测为准）
- Electron 登录窗 SendKeys 无效 → 剪贴板粘贴（Clipboard::SetText + ^v）有效
- 改场景后重启编辑器 = 清理 temp + 删 library/imports 场景缓存 + 重新打开项目；验证用 library 缓存 mtime 而非 UI
