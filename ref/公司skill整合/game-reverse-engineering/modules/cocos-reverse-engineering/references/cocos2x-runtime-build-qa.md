# Cocos Creator 2.4.x runtime, build and QA knowledge
> **何时读我**：还原出的 2.4.x 工程要重新导入、要用命令行构建，或要在无头浏览器里验收运行结果时；也包括搞不懂「单场景 + 运行时代码搭 UI」的工程该去哪里找真正的场景图。
> **读完能做到**：写出让 2.4.x 编辑器顺利重导入的贴图 `.meta`，避开 Sprite/Label 同节点、`label.color` 渲染成白、Label 自动撑大节点尺寸等运行期坑，用 CLI 完成构建（按 "Built ... successfully" 判定而非退出码），并用 Chrome CDP 做无头 QA 与截图断言。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_SUDUX`

Hard-won facts from rebuilding and verifying a 2.4.13 web-mobile game  
(`E:\Gameprogram\Sudux`, a Sudoku replica with a fully runtime-built UI).  
Useful when a recovered project needs to be re-imported, re-built, or  
verified in a headless browser.

## 1. Texture / sprite-frame `.meta` format (2.4.x)

When re-importing recovered PNGs into a 2.4.x project, write a standard  
texture meta next to each PNG. The editor will re-import and normalize it.

```json
{
"ver": "2.3.7",
"uuid": "",
"importer": "texture",
"type": "sprite",
"wrapMode": "clamp",
"filterMode": "bilinear",
"premultiplyAlpha": false,
"genMipmaps": false,
"packable": true,
"width": 604,
"height": 149,
"platformSettings": {},
"subMetas": {
"": {
"ver": "1.0.6",
"uuid": "",
"importer": "sprite-frame",
"rawTextureUuid": "",
"trimType": "auto",
"trimThreshold": 1,
"rotated": false,
"offsetX": 0, "offsetY": 0,
"trimX": 0,   "trimY": 0,
"width": 604, "height": 149,
"rawWidth": 604, "rawHeight": 149,
"borderTop": 0, "borderBottom": 0, "borderLeft": 0, "borderRight": 0,
"subMetas": {}
}
}
}
```

Editor behaviour observed with 2.4.13:

- A **running editor re-imports changed PNGs and rewrites the meta**  
automatically (auto-trim at `trimThreshold: 1`, recomputed  
`trimX/trimY/offsetX/offsetY`, trimmed `width/height`). Keep the texture  
UUID stable so scene/script references survive the re-import.

- If the PNG is already cropped tightly to its content, the editor trims  
only the 1-2 px transparent padding and leaves `offsetX/offsetY = 0` —  
the sprite frame then renders exactly the content when used with  
`SizeMode.CUSTOM`.

- `packable: true` is safe; frames still resolve via runtime `resources.load`.

## 2. Runtime asset loading from the `resources` bundle

Assets under `assets/resources/` are compiled into the `resources` bundle and  
load at runtime by path (relative to the resources root, no extension):

```js
cc.resources.load('UI/gen/logo', cc.SpriteFrame, (err, sf) => { ... });
```

- Wrap loads in a batch counter if the UI depends on several textures; never  
proceed to build the UI before all frames arrive (or provide a Graphics  
fallback per missing sprite).

- A loaded `cc.SpriteFrame` has `.name` equal to the asset name — useful in  
automated QA to assert which frame a Sprite is showing.

- `cc.find('Canvas/SomeNode/子节点')` path lookup handles Chinese node names,  
as long as the string is valid UTF-8.

## 3. Engine quirks that break naive UI code (2.4.x)

These cost real debugging time on the Sudux project:

1. **A `Sprite` and a `Label` must not share the same node.** The second  
render component added disables the first. Put the Label on a child node  
and read it back with `node.getComponentInChildren(cc.Label)`.

1. **`label.color` can silently render white** in some build/component  
combinations. Tint the **node** instead (`labelNode.color = ...`) and keep  
`label.color = cc.Color.WHITE`.

1. **Label auto-sizing overrides the node content size.** A 52×52 pad key  
shrank to ~14×50 after adding a Label with a computed size. Set an explicit  
`setContentSize(...)` on a child label node and/or use  
`cc.Label.Overflow.CLAMP`.

1. **Trimmed sprite frames have hidden offsets.** A meta with  
`trimType: auto` yields a frame whose displayed rect is  
`(trimX, trimY, width, height)` with `offsetX/offsetY` — when rendering a  
UI element in code, the quad is shifted by the offset. Simplest fix:  
physically crop the PNG to its content before import (then trim ≈ 0).

1. **Button feedback**: `cc.Button.Transition.SCALE` + `zoomScale` ~0.9–0.94  
is the standard lightweight transition; `node.on('click', cb)` works for  
real taps and for synthetic clicks in QA.

## 4. CLI build automation (2.4.x, Windows)

Build a project from the command line even while the editor has it open:

```powershell
& "${COCOS_2X}\CocosCreator.exe" `
--path "E:\Gameprogram\Sudux" --build "platform=web-mobile;debug=true"
```

- On success the log ends with `Built to "\build\web-mobile"
``successfully`. **The process exit code can be 1 anyway** (noise such as  
`EPERM ... CocosCreator.log`); verify success by the "Built ... successfully"  
line and by the `main.js` hash/timestamp changing in `build/web-mobile`.

- Typical incremental build takes ~20 s on a warm machine.

- The editor's own **in-app preview server (e.g. port 7456) serves stale  
compiled caches** — the CLI build is the authoritative artifact for QA.

## 5. Headless QA of a compiled build (Chrome CDP)

Drive a running build without a display:

1. Launch headless Chrome with a debug port and a dedicated profile dir:  
`chrome.exe --headless=new --remote-debugging-port=9224 --user-data-dir=`.

1. Connect to `http://127.0.0.1:/json/version`, open the  
`webSocketDebuggerUrl`, then `Target.createTarget` + `Runtime.enable`.

1. Evaluate with `Runtime.evaluate { expression, returnByValue: true }`.  
Wait first for `window.cc && !!cc.find('Canvas')`, then for the UI being  
built (sprites load async).

1. Simulate input with `node.emit('click')` (Buttons) and  
`cell.emit(cc.Node.EventType.TOUCH_END, new cc.Event.EventTouch())` (cells).

1. Screenshot via `Page.captureScreenshot`; assert visuals with PIL pixel  
analysis (count colour-band pixels per screen region) when image viewing  
tools are unavailable.

**Chinese node-name pitfall (Windows/PowerShell)**: piping an inline JS probe  
through PowerShell mangles UTF-8, so `cc.find('Canvas/MainMenu/经典数独')`  
resolves to `null`. Write the probe to a UTF-8 `.js` file (or use `\uXXXX`  
escapes) and run `node probe.js`.

## 6. "Single scene + runtime-built UI" architecture

A refactored/replicated game may ship a **nearly empty scene**: `Main.fire`  
contains only `Canvas` + one component (e.g. `BootGame`), and the component  
builds the whole menu/game/victory UI in `onLoad` with `cc.Node` +  
`cc.Sprite`/`cc.Label`/`cc.Button`.

Consequences for reverse engineering:

- Do not expect the UI in the scene/prefab JSON — the scene asset is a stub.

- The **boot script is the real scene graph**; read it to catalogue nodes,  
sprite names, and `cc.resources.load` paths.

- Assets are referenced **by string path at runtime**, not by UUID, so the  
recovered asset tree only needs to preserve `assets/resources/`  
(plus valid metas) for the game to find them.

- `Sprite.SizeMode.CUSTOM` + explicit `setContentSize` is the dominant  
pattern; recovered projects following it are easy to rebuild from script  
alone.
