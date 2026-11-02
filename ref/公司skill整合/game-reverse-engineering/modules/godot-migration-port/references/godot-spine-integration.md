# Godot 接入 Spine 动画（GENERAL_DEFAULT / GENERALIZED_PATTERN）

> **何时读我**：哥哥要把 Unity/Cocos 提取出来的 Spine 资源接进 Godot 4.x，或已经接了却遇到编辑器看不到骨骼、动画名存在但不播、桌面正常 Android 不显示、效果被弹窗盖住、播完切场景还有残留时。
> **读完能做到**：从确定插件与版本边界开始，把骨骼数据、atlas 文本、atlas 页 PNG 和 Godot 资源链配成互相可解释的完整一套，建可编辑的固定宿主并写一层解耦的业务适配器，最后按"资源/动画/场景/平台/视觉/业务"六项验收矩阵逐项关闭，清楚桌面通过不等于 Android 通过、能播放不等于业务分支已接入。
> **范围**：`GENERAL_DEFAULT` + `GENERALIZED_PATTERN`

本文是 Unity/Cocos 提取物迁移到 Godot 4.x 时的通用 Spine 接入流程。具体插件类名、资源后缀和运行时 API 以当前项目选定的 GDExtension 为准；JigsawCard 的 `SpineSprite`、`SpineSkeletonDataResource`、`SpineAtlasResource` 和 `SpineSkeletonFileResource` 只是一个已验证映射示例，不能当作所有插件的固定 API。

本文只处理 Spine 插件、资源链、固定宿主、播放器和平台验证；业务阶段、跨页面顺序与最终交付遵循 [Godot 重制端到端生产流程](end-to-end-restoration-workflow.md)。

## 1. 先确定插件和版本边界

1. 记录源 Spine minor、目标 runtime、Godot 小版本、操作系统和 Android ABI。
2. Godot 使用 GDExtension 时，插件二进制必须为当前 Godot 小版本构建；Godot 4.x 之间也不能假设 ABI 兼容。没有匹配构建版时，用同版本 `godot-cpp` 源码编译，不能只改插件或骨骼文件的版本字符串。
3. 先做一个空场景 smoke：插件能加载、创建一个 SkeletonData、播放一个已知动画，并在桌面和目标 Android 包中都能渲染。插件能被编辑器识别不等于 Android 库已被打包。

## 2. 资源链必须完整

每个骨骼实例至少需要一套互相匹配的资源：

```text
骨骼数据（.json 或 .skel/.skel.bytes）
        ↓
atlas 文本（.atlas/.atlas.txt）
        ↓
atlas 页面 PNG（一个或多个，含声明尺寸和 region）
        ↓
Godot SkeletonData + Atlas + SkeletonFile 资源
```

迁移前做以下检查：

- 骨骼数据中的 Spine minor 与 atlas/附件数据一致；必要时完整转换到目标 runtime。
- atlas 声明的 page width/height、PNG 实际尺寸、region 的 xy/size、rotate、orig/offset/trim 均可互相解释。
- 通过原始资源身份（bundle/CAB/pathID 或等价索引）追踪 PNG 和材质，不能按文件名猜同名纹理。
- 对每个 region 做边界检查，确认旋转后仍不越界；不要只改 page size 或只改骨骼版本字符串。
- 记录源、转换后和 Godot 导入资源的 SHA-256；转换脚本默认 dry-run，支持备份和回滚。

## 3. 在 Godot 中建立可编辑资源

推荐将每套骨骼拆成可复用资源和一个固定宿主场景：

```text
res://assets/spine_runtime/<id>.tres       # SkeletonDataResource
res://assets/spine_runtime/<id>.atlas.tres # AtlasResource（插件若需要）
res://scenes/effects/<id>.tscn              # Node2D/Control + SpineSprite
```

宿主场景应包含稳定节点名、SkeletonData 引用、初始 skin、默认动画、渲染层、缩放/锚点和可选的 AnimationPlayer。`owner` 必须正确写入，使编辑器重新打开场景时能看到并编辑骨骼。UI 中的骨骼要明确 CanvasLayer、Control/Node2D 坐标系、pivot 和 z/sibling 顺序。

固定宿主的意义是让美术能在编辑器中调整位置、缩放、遮罩和层级；运行时只改变业务状态、动画名、显隐和参数，不在启动时无条件创建第二套 Skeleton 节点。旧场景或资源损坏时可以有明确的回退路径，但回退必须记录日志，不能静默掩盖缺失引用。

## 4. 播放器适配层

插件 API 不同，建议在项目内包一层小型 `SpineEffect`/`SpinePlayer` 适配器，把业务与插件解耦。伪代码如下，方法名按当前插件映射：

```gdscript
@tool
class_name SpineEffect
extends Node2D

@export var animation_name := ""
@export var loop := false
@export var next_animation := ""
@export var overlay_animation := ""
@export var overlay_next_animation := ""

@onready var spine = $SpineSprite

func play_configured() -> void:
    play(animation_name, loop, next_animation)
    if overlay_animation != "":
        play_overlay(overlay_animation, overlay_next_animation)

func play(name: String, looping := false, following := "") -> void:
    assert_animation_exists(name)
    spine.animation_state.clear_tracks()
    spine.skeleton.set_to_setup_pose()
    spine.animation_state.set_animation(name, looping, 0.0)
    if following != "":
        spine.animation_state.add_animation(following, 0.0, looping)

func stop() -> void:
    spine.animation_state.clear_tracks()
    spine.skeleton.set_to_setup_pose()
    visible = false
```

适配层必须处理：动画名不存在、SkeletonData 尚未绑定、重复播放、重置 setup pose、主轨道/overlay 轨道、循环与后续动画、停止后隐藏、编辑器预览和运行时释放。非循环动画的完成回调要绑定宿主生命周期；宿主删除、换场景或暂停时，取消回调和 Timer/Tween。

## 5. 编辑器预览与业务触发

- `@tool` 预览只用于编辑器显示固定节点和某个安全时间点，不要在编辑器保存时写入玩家状态或运行中的 Tween。
- 业务触发要由原版 owner 和稳定事件驱动，例如进入页面、正确拼接、结算开始或按钮确认；不能用全局节点扫描或任意延迟猜测触发时机。
- 评价字、Emoji、胜利印章、猫、横幅和粒子即使都使用 Spine，也要分别记录资源身份、宿主、播放顺序、轨道、层级和结束条件。一个资源能播放不等于业务分支已接入。
- 需要跨弹窗置顶的效果固定一个根级 Overlay 宿主，保持最后 sibling；照片/卡片内部效果留在自己的坐标系，避免弹窗层级遮挡或坐标漂移。

## 6. 验收矩阵

静态门禁和运行时门禁必须分开：

1. 资源：骨骼、atlas、PNG、材质和 SkeletonData 引用无缺失，所有 region 不越界。
2. 动画：列出真实动画名，逐个加载并推进早/中/晚帧；验证 loop、停止、重播、后续动画和 overlay 混合。
3. 场景：编辑器重新打开 `.tscn/.tres` 可见可编辑；运行时复用唯一宿主，连续打开/关闭不重复创建、不残留节点。
4. 平台：桌面、导出 APK 和目标设备分别验证库、资源包内路径、首帧和完整播放；桌面通过不能替代 Android 通过。
5. 视觉：在原版同一设计分辨率和设备分辨率抓早/中/晚帧，检查 bounds、缩放、锚点、层级、透明边界和遮挡。
6. 业务：逐一验证输入、前置条件、库存/存档、触发 owner、反馈、奖励提交和退出清理。没有业务证据的动画只标为“资源可播放”。

## 7. 常见失败与修复方向

| 症状 | 常见根因 | 修复方向 |
|---|---|---|
| 编辑器看不到骨骼，运行时临时出现 | 运行时 `new Node`，没有固定宿主 | 在 `.tscn` 中预置 Spine 节点和资源引用，运行时查找复用 |
| 能加载但画面错位/越界 | atlas page 尺寸、旋转或 trim 不匹配 | 回到源身份和 region bounds，按两轴重建，不直接拉伸 PNG |
| 动画名存在但不播放 | SkeletonData 未绑定、同值 setter 短路、轨道未清空 | 绑定资源后 clear tracks、setup pose、set animation，并抓设备早期帧 |
| 桌面正常、Android 不显示 | GDExtension ABI/架构不匹配或资源未进 APK | 用目标 Godot/ABI 构建插件，检查 APK 库和资源清单 |
| 效果被弹窗盖住 | Overlay 挂在内容节点或 sibling 顺序错误 | 固定根级 Overlay，明确 CanvasLayer/z/sibling |
| 播完切场景仍有粒子或回调 | Timer/Tween/回调未绑定宿主生命周期 | 使用节点绑定的可取消回调和 generation/epoch |

## 8. 交付记录

每次接入记录：源版本、目标 runtime、Godot/插件版本、资源哈希、转换命令、宿主场景、动画清单、桌面/Android 证据路径、未覆盖的业务分支和回滚位置。没有这些记录时，只能交付“资源导入成功”，不能称为 Spine 功能还原完成。
