# Cocos Creator 2.4.13 .fire 场景序列化速查
> **何时读我**：手写或修复 Cocos Creator 2.4.13 的 .fire 场景文件 / 场景能导入但节点树建不起来 / 节点引用错位或脚本压缩 UUID 对不上
> **读完能做到**：按对象索引布局补全节点与组件最小字段，用变量追踪生成引用并跑校验脚本，从编译产物取出脚本压缩 UUID，产出能正常加载的 .fire
> **范围**：`GENERAL_DEFAULT`

来源：2026-07-31 Sudux 项目修复实战（AI 反编译 Cocos 项目）

## 对象索引布局

`.fire` 是 JSON 数组，所有引用用 `{"__id__": N}` 指向数组索引：

- \[0\] `cc.SceneAsset` → `scene: {"__id__": 1}`

- \[1\] `cc.Scene` → `_children: [{"__id__": 2}]`

- \[2..\] 节点与组件混排，节点 `_components` 引用组件索引，组件 `node` 引用节点索引

## 节点最小字段

```json
{
"__type__": "cc.Node", "_name": "Canvas", "_objFlags": 0,
"_parent": {"__id__": 1}, "_children": [{"__id__": 3}],
"_active": true, "_level": 0, "_components": [{"__id__": 5}],
"_prefab": null, "_opacity": 255,
"_color": {"__type__": "cc.Color", "r": 255, "g": 255, "b": 255, "a": 255},
"_contentSize": {"__type__": "cc.Size", "width": 960, "height": 640},
"_anchorPoint": {"__type__": "cc.Vec2", "x": 0.5, "y": 0.5},
"_trs": {"__type__": "TypedArray", "ctor": "Float64Array", "array": [px,py,pz, 0,0,0, sx,sy,sz,1]},
"_eulerAngles": {"__type__": "cc.Vec3", "x": 0, "y": 0, "z": 0},
"_is3DNode": false, "groupIndex": 0, "_id": ""
}
```

注意 2.4.13 新格式用 `_trs`（TypedArray 10 元素），老格式用分开的 `_position/_scale/_quat`。官方模板 `resources/static/template/new-scene.fire` 是权威参照。

**缺失 `_skewX/_skewY/_groupIndex` 会导致加载异常**（症状：层级空白 / `_updateOrderOfArrival` 类报错）。生成节点时对照官方模板补齐：`"_skewX": 0, "_skewY": 0, "_groupIndex": 0`。`_level` 可以留（编辑器会重算）。

## 引用 id 校验（重建后必跑）

用 `add()` 动态构建对象时，**children/parent 的 `__id__` 必须来自变量追踪，不能手写数字**——手写 id 会与真实分配错位（例如以为 23 是 GameManager 节点，实际是 cc.Button 组件），场景虽能导入但节点树建不起来。

写回后校验全部引用：

```python
for i, o in enumerate(data):
if o.get('__type__') == 'cc.Node':
for c in o.get('_children', []):
assert data[c['__id__']]['__type__'] == 'cc.Node', f'[{i}] children->{c["__id__"]} 非节点'
p = o.get('_parent')
if isinstance(p, dict):
assert data[p['__id__']]['__type__'] in ('cc.Scene','cc.Node'), f'[{i}] parent 非 Scene/Node'
```

## 脚本组件

```json
{
"__type__": "91c55BCnSVCxL0axLfDCezO",  // 压缩 UUID，不是完整 uuid！
"_name": "", "_objFlags": 0,
"node": {"__id__": 3}, "_enabled": true, "__prefab": null,
"loadingNode": {"__id__": 4},   // properties 引用按属性名序列化，未设置用 null
"_id": ""
}
```

压缩 UUID 只能从编译产物提取：`temp/quick-scripts/dst/assets/scripts/.js` 里的 `cc._RF.push(module, '', '')`。

## Sudux 项目脚本压缩 ID 清单（示例）

| 脚本 | 完整 uuid | 压缩 ID |
|---|---|---|
| BootGame.js | 91c55042-9d25-42c4-bd1a-c4b7c309ecce | 91c55BCnSVCxL0axLfDCezO |
| GameController_Reconstructed.js | fd48e833-2bbe-4a76-bdc2-889fd5e99c0c | fd48egzK75Kdr3CiJ/V6ZwM |
| SudokuGame.js | a1b2c3d4-e5f6-7890-abcd-ef1234567005 | a1b2cPU5fZ4kKvN7xI0VnAF |
| AudioManager.js | (见 meta) | 77779T0gNFJTJL9ygDo+Wpk |

压缩 ID 是 uuid 的有损 base64 变体（22 字符），无法从完整 uuid 推算，必须读编译产物。

## 常见组件字段

- `cc.Label`: `_string/_N$string/_fontSize/_lineHeight/_N$horizontalAlign/_N$verticalAlign/_N$fontFamily/_N$overflow/_N$cacheMode`

- `cc.Button`: `duration/zoomScale/clickEvents/_N$interactable/_N$transition/_N$normalColor/.../_N$target`

- `cc.Canvas`: `_designResolution/_fitWidth/_fitHeight`

- `cc.Camera`: `_projection/_ortho/_orthoSize/_nearClip/_farClip/_clearFlags/_cullingMask`

## 场景结构参考（Sudux 正常版）

```
Scene
└── Canvas (cc.Canvas, 960x640)
├── Main Camera (cc.Camera)
├── BootManager (BootGame 组件)
│   ├── LoadingScreen → Label "Loading Sudux..."
│   └── MainMenu → Title/Subtitle/ButtonsContainer(4×Button+Label)
└── GameManager (GameController_Reconstructed 组件)
└── GameScene (active=false)
├── SudokuGrid / NumberPad / TimerDisplay / ToolsPanel
└── VictoryPanel (active=false)
```
