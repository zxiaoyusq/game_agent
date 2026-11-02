---
name: cocos-creator-project-repair
description: Use when 用户要诊断或修复 Cocos Creator 项目打不开、Play 黑屏、场景加载报错、`.fire` 引用损坏、脚本组件序列化错误，或反编译/迁移后的 Cocos 项目无法运行。
version: 1.0.0
created: "2026-07-31"
author: bai-lian
tags: [cocos, cocos-creator, scene-repair, fire-file, game-engine]
---

# Cocos Creator 项目修复

## 执行卡（先用这张卡，再读正文）

**我管什么**：诊断并修复 Cocos Creator 项目打不开、Play 黑屏、场景加载报错、`.fire` 引用损坏、脚本组件序列化错误，以及反编译/迁移后跑不起来的工程。不管从零复刻游戏。

**第一步做什么**：跑 `python modules/cocos-creator-repair/scripts/check_fire_refs.py <场景 .fire 路径>`，把自引用和悬空引用先清干净。

**做完怎么算完成**：
- [ ] 引用检查无输出：无节点把 `_children` 指向自己，无节点 `_parent` 指向的父节点 children 里缺它
- [ ] 所有 `_children` 指向的 `__type__` 是 `cc.Node`，所有 `_parent` 是 `cc.Scene` / `cc.Node`
- [ ] 每个 cc.Label 带 `_materials`，每个 cc.Camera 带 `_renderStages:1` + `_alignWithScreen:true`
- [ ] 每个 cc.Node 带齐 `_skewX/_skewY/_groupIndex`，Main Camera 的 `_contentSize` 是 960x640
- [ ] 每个 cc.Sprite 的 `_spriteFrame` 填的是 subMetas 里的子资源 uuid
- [ ] Play 后不再是黑屏 + Draw Call 1

**红线（不可违反）**
- 重建场景时 children/parent 的 id 绝不硬编码：必须用变量追踪每次 `add()` 的返回值，否则场景能导入但层级空白 + 报 `child._updateOrderOfArrival is not a function`。
- 黑屏两大必填项：cc.Label 必须带 `_materials`（默认材质 uuid `eca5d2f2-8ef6-41c2-bbe6-f9c79d09c432`），缺失时完全不渲染；cc.Sprite 的 `_spriteFrame` 必须填 `.meta` 里 `subMetas[''].uuid` 子资源 uuid，填主资源 uuid 会大量报 `spriteFrame.textureLoaded is not a function` 并黑屏。
- `cc.AudioManager` 不是引擎内置类，不许在 `properties` 里当类型引用；`cc.Class` 不支持类级 `data: {...}`，静态数据必须进 `ctor()`。
- 判断编辑器是否真的打开，看进程名 `CocosCreator`，不看窗口标题——`Tabbit Browser` 预览窗会伪装成编辑器标题。
- 手写场景只是救活反编译坏文件的手段，不是复刻路径；动手前必须先确认逆向资源导出目录里素材在不在。
- 白底按钮上的 Label 默认白字会看不见，按钮文字要显式设成深色 `_color`。

**卡住时按顺序读**：
- 不知道 `.fire` 字段该有什么 / 压缩 ID 怎么取 → `modules/cocos-creator-repair/references/fire-file-format.md`
- 黑屏但脚本无报错（Draw Call 1）→ 本文件「手写场景的黑屏陷阱（本次 Sudux 实测关键）」
- 素材 uuid、材质 uuid 查不到 → `modules/cocos-creator-repair/references/builtin-assets-and-spriteframes.md`
- 编辑器打不开 / 反复弹登录 / 窗口坐标 → 本文件「编辑器登录与窗口操作（Windows）」与「从 Dashboard 打开项目的 UI 流程」

全局五步循环与六条铁律见 `references/execution-protocol.md`。

范围：核心场景/引用/黑屏诊断是 `GENERAL_DEFAULT`；Sudux 路径、窗口坐标、UUID 和素材数量属于项目案例，执行时必须重新发现。

## 适用场景

- Cocos 项目（尤其 AI 反编译/从 HTML 迁移而来）打不开、Play 黑屏、场景加载报错

- `.fire` 场景文件是手写/程序生成的，编辑器加载时 `RangeError: Maximum call stack size exceeded at cc_Node._initProperties`

- 控制台报 `Unknown type of Xxx.data, property should be defined in 'properties' or 'ctor'`

## 核心诊断步骤

### 1. 场景文件自引用检查（栈溢出根因）

`.fire` 是 JSON 数组。加载时 Cocos 按 `_children`/`_parent` 引用建树，**自引用或悬空引用 → 无限递归 → `_initProperties` 栈溢出**。

```python
import json
data = json.load(open(r'E:\path\Main.fire', encoding='utf-8'))
for i, obj in enumerate(data):
if obj.get('__type__') == 'cc.Node':
kids = [c.get('__id__') for c in obj.get('_children', [])] if obj.get('_children') else []
parent = obj.get('_parent', {})
pid = parent.get('__id__') if isinstance(parent, dict) else None
# 检查: children 含自己、parent 声称是 X 但 X 的 children 里没有它
if i in kids:
print(f'!!! 节点{i} 自引用 children: {obj.get("_name")}')
if pid is not None and pid != 1:  # 1 是 Scene
pnode = data[pid]
pkids = [c.get('__id__') for c in pnode.get('_children', [])] if pnode.get('_children') else []
if i not in pkids:
print(f'!!! 节点{i}({obj.get("_name")}) parent={pid} 但 parent children 缺失')
```

### 2. 脚本组件在场景中的 `__type__` 是压缩 UUID

自定义脚本组件在 `.fire` 里的 `__type__` **不是**完整 uuid 也不是脚本名，而是压缩 ID（22 字符，如 `91c55BCnSVCxL0axLfDCezO`）。

**提取方法**（编译产物）：`temp/quick-scripts/dst/assets/scripts/.js` 第一行附近：

```js
cc._RF.push(module, '91c55BCnSVCxL0axLfDCezO', 'BootGame');
```

第二个参数即压缩 ID。批量提取：

```bash
cd E:\project\temp\quick-scripts\dst\assets\scripts
for f in *.js; do id=$(grep -oE "cc\._RF\.push\(module, '[^']+'" "$f" | head -1 | sed "s/cc._RF.push(module, '//;s/'//"); echo "$f -> $id"; done
```

### 3. 脚本 `data:` 静态属性报错

Cocos 2.4 `cc.Class` **不支持类级 `data: {...}` 字段**，报：  
`Unknown type of BootGame.data, property should be defined in 'properties' or 'ctor'`

修复：把静态数据移入 `ctor()`：

```js
// 错误写法
data: { currentVersion: '1.0.0', buildDate: '2024-07-30' },
// 正确写法
ctor() { this.currentVersion = '1.0.0'; this.buildDate = '2024-07-30'; },
```

### 4. 反编译场景常见症状

- 节点 parent/children 引用错乱（手写生成器没维护双向引用）

- **没有挂任何脚本组件**（组件数组全空，游戏逻辑不存在）

- 没有 Main Camera 节点（Play 黑屏）

- `cc.AudioManager` 当属性类型用——这不是引擎内置类，是脚本运行时挂到 cc 全局的单例，**不能在 properties 里当类型引用**，删除该属性

## 重建 .fire 场景文件

手写场景时参照官方模板 `CocosCreator/resources/static/template/new-scene.fire`（新格式含 `_trs` TypedArray），组件模板可从损坏的旧文件里提取（cc.Label/cc.Button/cc.Canvas 字段结构可直接复用）。

节点最小字段集：`__type__/cc.Node` + `_name/_parent/_children/_active/_components/_color/_contentSize/_anchorPoint/_trs/_is3DNode/_id`。

脚本组件对象结构：

```json
{
"__type__": "91c55BCnSVCxL0axLfDCezO",  // 压缩 UUID
"_name": "", "_objFlags": 0,
"node": {"__id__": 3}, "_enabled": true, "__prefab": null,
"loadingNode": {"__id__": 4},  // properties 里的引用按名字序列化
"_id": ""
}
```

场景加载验证：写回后重启编辑器（脚本会重新编译），在资源管理器双击 Main 场景打开，看层级管理器是否出现节点树、控制台是否报错。

### 手写场景的黑屏陷阱（本次 Sudux 实测关键）

**症状**：场景导入成功、层级管理器有完整节点树、脚本无报错，但 Play 后黑屏、Draw Call 1（只有 1 次绘制调用 = UI 完全没渲染）。

**根因排查顺序**（由浅入深）：

1. **cc.Label 必须带 `_materials` 数组**（引擎默认材质 uuid `eca5d2f2-8ef6-41c2-bbe6-f9c79d09c432`）——缺失时 Label 完全不渲染，这是黑屏最常见根因：

```json
"_materials": [{"__uuid__": "eca5d2f2-8ef6-41c2-bbe6-f9c79d09c432"}]
```

1. **cc.Camera 必填字段**（对照官方模板补齐）：

```json
"_cullingMask": 4294967295, "_clearFlags": 7,
"_backgroundColor": {"__type__":"cc.Color","r":0,"g":0,"b":0,"a":255},
"_depth": -1, "_zoomRatio": 1, "_targetTexture": null,
"_fov": 60, "_orthoSize": 10, "_nearClip": 1, "_farClip": 4096, "_ortho": true,
"_rect": {"__type__":"cc.Rect","x":0,"y":0,"width":1,"height":1},
"_renderStages": 1, "_alignWithScreen": true
```

`_renderStages:1` + `_alignWithScreen:true` 决定相机渲染 UI 并对齐屏幕，缺失 → UI 不渲染。  
3. **cc.Canvas 组件**：`_designResolution` 960x640、`_fitWidth:false`、`_fitHeight:true`（对齐官方模板，不是 true/true）。  
4. **Canvas 节点应挂 cc.Widget 组件**（屏幕对齐）：`alignMode:1, _alignFlags:45, _left/_right/_top/_bottom:0`。  
5. **Main Camera 节点 `_contentSize`** 应为 960x640（官方模板值），不是 0x0。

**运行时脚本错误排查**：黑屏但场景结构正常时，用 headless Chrome 抓预览 console：

```bash
chrome --headless=new --enable-logging=stderr --virtual-time-budget=6000 http://localhost:7456/ 2>&1 | grep -iE 'CONSOLE|error|TypeError'
```

无 JS 错误 = 问题在渲染管线（Label 材质/Camera 字段），不是脚本逻辑。

## 编辑器登录与窗口操作（Windows）

- **登录态**: `~/.CocosCreator/profiles/user_token.json` 存有 session（`cocos_uid`/`email`/`nickname`）。登录窗会反复弹，Electron 窗口 SendKeys 经常打不进（占位符不变、报 `301: Missing Username`）。

- **剪贴板粘贴是 SendKeys 的可靠替代**：先点击输入框聚焦，`[System.Windows.Forms.Clipboard]::SetText('xxx')` 再 `SendKeys::SendWait('^v')`。实测对 Cocos Electron 登录框有效，SendKeys 逐字符输入无效。

- **点击坐标务必从窗口矩形推算**：同一登录窗口两次 vision_analyze 估的输入框坐标可能差 100+ 像素（一次说 (512,405)、一次说 (500,298)），用错坐标点击 → 输入全部落空。正确流程：`EnumWindows` 拿窗口真实 RECT → 用窗口内相对布局推算 → 点击后截图验证再继续。

- **两个窗口注意区分**: `Creator Dashboard`（编辑器内嵌，448,180 1024x680）vs `Cocos Dashboard`（独立启动器，360,141 1200x758），坐标不同，点登录前先 EnumWindows 拿真实矩形。

- **编辑器可能最小化**: 标题 `CocosCreator |  - Tabbit`，位置 -32000,-32000 表示最小化。用 `ShowWindow(hwnd, 9)` + `SetForegroundWindow(hwnd)` 恢复。

- **cua-driver 对 Cocos/Electron 窗口不可靠**（capture 返回 0x0、list_windows 空）——用 PowerShell `EnumWindows` + `GetWindowText` 拿窗口矩形，`SetCursorPos` + `mouse_event` 模拟点击，`SendKeys` 输文本。UIAutomation 对 Electron 内部控件拿不到（Edits: 0）。

- 完整屏幕截图：PowerShell `CopyFromScreen` 存 PNG，再 `vision_analyze` 看内容（注意裁剪窗口区域更准）。

## 让编辑器自动打开正确场景（start-scene）

编辑器启动时默认打开 Untitled 空场景（预览黑屏、Draw Call 1）的常见原因是 `settings/project.json` 的 `start-scene` 为空。手动在资源管理器双击场景经常不生效（UI 操作被预览窗口/登录窗干扰）。

**可靠做法**：把 `start-scene` 设为 Main.fire 的 uuid（来自 `assets/Main.fire.meta`），重启编辑器即自动加载：

```json
{ "start-scene": "cab48347-e208-4021-b4f9-acdc229a9a6a" }
```

**验证场景是否被编辑器成功导入**（不用开 UI）：看 `library/imports//.json` 的 mtime——若晚于你写回 Main.fire 的时间，说明导入成功；`library/uuid-to-mtime.json` 里也应出现 `relativePath: 'Main.fire'`。

## 从 Dashboard 打开项目的 UI 流程

命令行 `CocosCreator.exe --project ` 会内嵌 Dashboard 并要求登录，且不把项目加进"最近打开"。用户自己的独立 Cocos Dashboard 有登录态，优先用它。**两条路径，优先卡片**：

**路径 A（最快）— 首页"最近打开"卡片双击**：

1. 启动独立 Dashboard 后首页即有"最近打开"项目卡片

2. 双击目标项目卡片（Sudux 卡片窗口内相对坐标约 (255,415) → 绝对 (615,556)）

3. 脚本开始编译（`temp/quick-scripts/dst/...` 生成）+ 编辑器窗口标题变 `Cocos Creator -  - db://assets/.fire` = 成功

4. 注意：vision_analyze 对卡片坐标的估算**每次会漂移 100+ 像素**（同一次会话给出过 (300,538)、(2,359)、(255,415)），用已实测有效的坐标，点一次截图验证再继续

**路径 B — "打开其他项目..."文件夹对话框**：

1. 点顶部导航 **"打开其他项目..."**（Dashboard 窗口内相对坐标约 (315,96)）

2. 弹 Windows 文件夹选择对话框（"选择一个项目路径"，标题是 GBK 乱码如 `ѡ��һ����Ŀ·��`）

3. 点底部 **"文件夹:" 输入框** → Ctrl+A → 剪贴板粘贴完整路径 → **回车**（回车等价于确认，比找"选择文件夹"按钮可靠）

4. 等编辑器加载，场景标签应显示 Main

## 陷阱

- **重建场景时 children/parent 引用 id 绝不能硬编码**：用 `add()` 动态 append 对象时，手写 `[3,6,23]` 之类的数字会和实际分配 id 错位（真实 id 23 可能是 cc.Button 组件而非 GameManager 节点）→ 场景能导入但层级空白 + 控制台报 `TypeError: child._updateOrderOfArrival is not a function`。**必须用变量追踪每个 add() 的返回值**，children/parent 一律引用变量。写完后跑完整引用校验（所有 `_children` 指向的 `__type__` 必须是 cc.Node，`_parent` 必须是 cc.Scene/cc.Node）。

- **cc.Node 缺 `_skewX/_skewY/_groupIndex` 字段也会加载异常**：对比官方模板 `resources/static/template/new-scene.fire` 的 cc.Node 字段集，补齐缺失字段（`_skewX:0 _skewY:0 _groupIndex:0`）再写回。`_level` 可留（编辑器会重算），但这三个字段缺失会导致 `_updateOrderOfArrival` 类异常。

- **`~/.CocosCreator/settings.json` 缺失 → 命令行启动报 `Load profile failed: local://settings.json` 且反复弹登录窗**。修复：`cp ~/.CocosCreator/profiles/settings.json ~/.CocosCreator/settings.json`（profiles 下那份含 `recently-opened` 等项目状态）。

- **窗口标题会伪装**：Cocos 预览浏览器进程名是 `Tabbit Browser`，其窗口标题可能是 `CocosCreator |  - Tabbit`，与编辑器窗口标题几乎一样，且常被误认成编辑器。**判断编辑器是否真的打开，看进程名 `Get-Process -Name CocosCreator` + 主窗口是否可见**，不要只看窗口标题。遗留的 Tabbit 预览窗口（黑屏 FPS 60）可能是旧进程，不代表编辑器状态。

- **验证"场景是否被编辑器成功导入"靠 library 缓存而非 UI**：`library/imports//.json` 的 mtime 晚于你写回 Main.fire 的时间 = 导入成功；`temp/quick-scripts/dst/assets/scripts/.js` 生成 = 脚本编译成功。两者都没有 = 编辑器还停在启动早期（登录窗/加载中），不要反复点 UI。

- **`ENOTEMPTY: directory not empty, rmdir temp/quick-scripts/dst/assets` 删不掉的真正原因**：① 当前 shell 的 cwd 可能在项目 temp 里（`cmd //c` 的输出会显示 `E:\Gameprogram\Sudux\temp\...>`，说明你自己的终端占着句柄）——先 `cd` 到项目外再 `rm -rf temp`；② 残留的 `Tabbit Browser` 预览进程持有句柄——`Get-Process -Name 'Tabbit Browser' | Stop-Process -Force` 后再删。**顺序：cd 出项目 → 杀 Tabbit/Cocos 进程 → rm -rf temp → 删 library 场景缓存**，一次到位。

- **`cc.Sprite._spriteFrame` 必须引用 PNG 的子资源 uuid（subMetas），不是主资源 uuid**：`.meta` 里 `subMetas[''].uuid` 才是 spriteFrame 引用值。填主资源 uuid → 控制台大量 `TypeError: spriteFrame.textureLoaded is not a function` + UI 黑屏（Draw Call 1）。例：default_btn_normal.png 主 uuid `e851e89b-faa2-4484-bea6-5c01dd9f06e2` → spriteFrame 子资源 uuid `f0048c10-f03e-4c97-b9d3-3506e1d58952`；default_panel.png 主 `d81ec8ad-...` → 子资源 `9bbda31e-ad49-43c9-aaf2-f7d9896bac69`。材质 uuid：builtin-2d-label `e02d87d4-e599-4d16-8001-e14891ac6506`、builtin-2d-sprite `eca5d2f2-8ef6-41c2-bbe6-f9c79d09c432`。完整速查见本模块 `modules/cocos-creator-repair/references/builtin-assets-and-spriteframes.md`。

- **Label 白字放白底按钮 = 看不见（\\"只有白色方块\\"）**：default_btn_normal.png 是白色底图，Label 默认 `_color` 255,255,255 白字在白底上不可见。按钮文字 Label 要设深色 `_color`（黑字）。

- **手写场景是救活反编译坏文件的最后手段，不是复刻游戏的路径**：AI 反编译/复刻知名游戏的项目通常已有**逆向资源导出目录**（如 `E:\download\sudoku-re\assets-export\`：319 Sprite/156 贴图/17 音效/7 字体 + `REVERSE_ANALYSIS_REPORT.md` + 复刻计划文档）。正确路径是**导入官方素材组装完整 UI（面板/图片/动效）**，用户验收的是完整游戏不是空壳。动手前先查逆向导出目录和计划文档，确认资源在不在。

- headless Chrome 截图对 rAF 动画页面不可靠（截图停在中间帧，数字滚动到一半）——验证静态内容用 `--force-prefers-reduced-motion`

- 数字滚动/入场动画要"默认可见 + JS 触发"：初始文本=目标值、无 `.loaded` class 时 opacity:1，JS 加载后再加 class 播放动画，防止 JS 失败内容不可见

- 编辑器打开项目时若 Dashboard 弹登录，别反复 kill 进程——先检查 user_token.json 是否存在

## 参考

- `modules/cocos-creator-repair/references/fire-file-format.md` — .fire 序列化格式速查与脚本压缩 ID 清单

- `modules/cocos-creator-repair/scripts/check_fire_refs.py` — 场景父子引用完整性检查脚本（`python check_fire_refs.py Main.fire`）

## 素材批量导入与 meta 生成（Sudux 实测，2026-08）

从逆向导出目录（如 `E:\download\sudoku-re\assets-export\`）批量导入素材到 Cocos 2.4 项目时，**手写 .meta 比让编辑器逐个导入快且可控**，但格式必须精确：

### 目录规划

```
assets/resources/UI/       ← Sprite/*.png (319 个)
assets/resources/Fonts/    ← Font/*.otf,*.ttf (7 个)
assets/resources/Audio/    ← AudioClip/*.wav (17 个)
```

### meta 格式（Cocos 2.4.13 实测可用）

- **PNG = `texture` importer**，必须含 `subMetas.`（子资源 sprite-frame）——**spriteFrame 引用用的是子资源 uuid**（`subMetas..uuid`），不是主 uuid；width/height 可先填 0（编辑器导入后重算）

- **OTF/TTF = `font` importer**：`{"ver":"1.1.50","importer":"font","imported":true,"uuid":"...","files":[],"subMetas":{},"userData":{}}`

- **WAV = `audio-clip` importer**：结构同上，importer 为 `audio-clip`

- 主 uuid 和子资源 uuid 都随机生成（`uuid.uuid4()`）

### 关键：素材→uuid 映射表

生成 meta 的同时**把 `sprite名 → spriteFrame 子资源 uuid` 写进 `_sprite_uuids.json`**（放 `assets/resources/UI/` 下）。后续手写 .fire 场景时直接查映射表填官方素材的 spriteFrame uuid，避免逐个翻 .meta：

```python
sprite_uuids[name] = sub_uuid  # name = png 文件名去扩展名
# 场景里 cc.Sprite 的 _spriteFrame 填 sub_uuid
```

### 验证

- meta 写完后启动编辑器让它导入：看 `library/imports//.json` mtime 是否晚于写回时间

- 资源清点用 cocos-reverse-engineering 的 Phase 5 脚本：`bash scripts/find-assets.sh /assets`

- 完整可复用脚本：`E:\hermes\scripts\sudux_gen_metas.py`（319 sprite + 7 font + 17 audio 一次生成）

## Cocos 编辑器实时通道

Creator 3.8.x 的编辑器操作与中间自检可按 `modules/cocos-mcp-channel/SKILL.md` 执行；2.4.x 或无 MCP 时走本模块文件级/CLI 路径。预览、编辑器引用检查和正式构建/设备验收分别记录证据。
