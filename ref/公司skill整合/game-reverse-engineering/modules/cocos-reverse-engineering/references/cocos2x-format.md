# Cocos Creator 2.x build format
> **何时读我**：要判断一个 Cocos 2.x 的编译产物是 2.3.x 还是 2.4.x，要读懂 `src/settings.js` 里的 CCSettings 字段，或要看懂 `res/import/` 下那种「压缩数组」形式的资产 JSON 与 22 位压缩 UUID 时。
> **读完能做到**：认出 2.3.x/2.4.x 两套目录布局，从 CCSettings 取到场景表、rawAssets、assetTypes 与 types 属性名映射，并把压缩数组形式的资产 JSON 还原成带字段名的对象、正确展开压缩 UUID。
> **范围**：`GENERAL_DEFAULT`

The 2.x series covers **2.3.x** and **2.4.x**, plus older 1.x / 2.0-2.2 builds (which share the same layout). There are two main variants.

## 2.3.x layout

```
/
index.html
main.js
src/
settings.js          /.json
raw-assets//.
```

- **`settings.js`** is a single-line executable JS that assigns to `window.CCSettings`. `cc-reverse` evaluates it with a stub `window` and extracts the object.

- **`project.js`** is a modulepack: one IIFE per user script, keyed by the script's UUID. The AST walker in `codeAnalyzer.js` splits it into per-file ASTs and regenerates each as a `.ts` file.

- **`res/import/`** holds one JSON per asset (scenes, prefabs, sprite frames, etc.). UUID is split into a 2-char bucket prefix.

- **`res/raw-assets/`** holds the native payload (png, mp3, wav, plist, …).

## 2.4.x layout

```
/
index.html
main.js                 /.json
native//.
res/                    /
import//.json
native//.
config.json         <-- tiny per-subpackage manifest
remote/                 <-- remote bundle cache (usually empty on first run)
```

- **Either** `assets/` or `res/` is used — depends on which template the developer picked. Both can coexist.

- **Subpackages** (wechat/mini-game splits) replicate the `import/`+`native/` structure per subpackage. `settings.js` lists them under `CCSettings.subpackages`.

- **Encrypted scripts** (`.jsc`) live alongside `.js`. `main.js` loads them via `cc._RF.push(...)` or the custom XXTEA wrapper.

## CCSettings fields that matter

From `src/core/settings.ts` in the 2.x engine, the production `CCSettings` object has (not exhaustive):

- `platform: 'web-desktop' | 'web-mobile' | 'wechatgame' | …`

- `groupList: string[]` — physics/collision groups.

- `collisionMatrix: number[][]`

- `rawAssets: { assets?: Record, internal?: {...}, resources?: {...} }` — the asset manifest. `typeIndex` indexes into `assetTypes`.

- `assetTypes: string[]` — parallel list of class names (`cc.SpriteFrame`, `cc.AudioClip`, …).

- `uuids: string[]` — compressed 22-char UUIDs. `rawAssets[i].assets[key]` entries reference these by index.

- `scenes: { name, url, uuid }[]` — registered scenes.

- `packedAssets: Record` — multi-asset packs.

- `types: Record` — **the compressed-type property-name map**. When an asset JSON is stored as a flat array `[typeIndex, val1, val2, …]`, you need `types[className]` to know which property each value corresponds to.

- `subpackages: Record` — subpackage manifest.

- `launchScene: string` — URL of the launch scene.

- `jsList: string[]` — raw `.js` files (plugins) loaded before user scripts.

- `hashAssetFile: boolean` — if true, asset filenames include a content hash.

`cc-reverse` persists `global.settings = { CCSettings:  }` after `parseSettings()`.

## The "compressed" asset JSON format (2.x)

An asset JSON can be in one of two shapes:

### Plain object form

```json
{
"__type__": "cc.SceneAsset",
"_name": "GameScene",
"scene": { "__id__": 1 },
...
}
```

`__id__` is a back-reference to the top-level array index. `__uuid__` is used for cross-asset references (resolved via `uuids[]`).

### Compressed array form

```json
[
["cc.SceneAsset", "cc.Node", "cc.Sprite", ...],
[0, "GameScene", 1],
[1, "Canvas", null, [{"__id__": 2}], true, ...],
...
]
```

- `[0]` is the **type list** (`types` array).

- Each subsequent element is `[typeIndex, value1, value2, ...]`.

- Property names come from `CCSettings.types[typeName]` when present, or fall back to the built-in lookup table (`src/core/typeDefinitions.js` in cc-reverse).

`resourceProcessor.js` handles both forms via `restoreCompressedData()` → `resolveReferences()` → `decodeUuids()`.

## UUID compression

22-char base64-ish representation of a standard 36-char UUID. See `src/utils/uuidUtils.js` — `decodeUuid()` expands it, `compress_uuid()` / `decompress_uuid()` go the other way. The 3.x engine uses the same algorithm, which is why `cc-reverse`'s utility works for both.

## Asset types handled by default (2.x)

- `cc.SceneAsset` → `.fire` + meta

- `cc.SpriteFrame` → `.png` + `.png.meta` (with subMetas)

- `cc.AudioClip` → `` + `.meta`

- `cc.TextAsset` → `.json` + `.meta`

- `cc.AnimationClip` → `.anim` + `.meta`

- `sp.SkeletonData` → `.json` + `.atlas` + `.png`(s) + `.meta`

- `dragonBones.DragonBonesAsset` → `_ske.json` + `.meta`

- `dragonBones.DragonBonesAtlasAsset` → `_tex.json` + `_tex.png` + `.meta`

To add a new type, `resourceProcessor.registerHandler(typeName, handler)` — the handler receives `(data, uuidKey, { parentData, index })` and should emit files via `fileManager.writeFile()` and queue textures via the `cacheReadList` / `cacheWriteList` pair.

## Meta version notes

`cc-reverse` currently writes `ver: "1.2.7"` on asset metas and `ver: "1.0.8"` on script metas. These are 2.4.5-era values. Cocos Creator editors may refuse or silently upgrade metas from older versions — if the project fails to import, open it in the matching editor major version (2.4.x recommended) and let it rewrite the metas.
