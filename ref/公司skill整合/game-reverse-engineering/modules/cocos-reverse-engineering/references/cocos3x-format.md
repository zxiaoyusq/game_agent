# Cocos Creator 3.x build format

3.x (the current mainline, backed by the engine at <https://github.com/cocos/cocos-engine>) replaces the 2.x monolithic `res/` + `project.js` layout with a **bundle-first** design. Every asset belongs to exactly one bundle; every bundle has its own `config.json`, its own uuid table, its own `import/`+`native/` tree, and its own (optional) encryption.

## Web build layout

```
<build>/
  index.html
  application.js           <-- launcher (new Application(); game.init({settingsPath}))
  style.css
  src/
    import-map.json         <-- SystemJS import map (module id → chunk path)
    system.bundle.js        <-- SystemJS runtime
    polyfills.bundle.js
    settings.[hash].json    <-- runtime settings (replaces window.CCSettings)
    chunks/<hash>.js        <-- user scripts (System.register modules)
  cocos-js/
    cc.[hash].js            <-- engine bundle
  assets/
    main/                   <-- the user's "main" bundle
      config.json
      index.js              <-- registration stub (loadBundle)
      import/<2>/<uuid>.json
      native/<2>/<uuid>.<ext>
    resources/              <-- only if project has resources/
      config.json
      index.js
      import/..  native/..
    internal/               <-- engine built-ins (default materials, fallback textures, …)
      config.json
      index.js
      import/..  native/..
    <custom-bundle>/        <-- any user-configured AssetBundles
  remote/                   <-- remote bundles cache
  subpackages/              <-- wechat/mini-game split (subpackage bundle mirrors assets/<name>)
```

Native builds (`native/` template) produce the same `assets/` tree plus `data/` zip-packed assets and a platform-specific binary that hosts the engine.

## `src/settings.json` (replaces `window.CCSettings`)

Canonical schema: `cocos/core/settings.ts` (`enum SettingsCategory`) plus the getters in `cocos/game/game.ts` (search for `querySettings`).

```jsonc
{
  "path": { … },
  "engine": {
    "debug": false,
    "macros": { … },
    "customJointTextureLayouts": [ … ]
  },
  "assets": {
    "server": "",
    "preloadAssets": [ "<uuid>", … ],
    "preloadBundles": [ { "bundle": "main", "version": "abc123" }, … ],
    "subpackages": { "<name>": { "version": "…" } },
    "remoteBundles": [ … ],
    "bundleVers": { "main": "abc123", "resources": "…" },
    "projectBundles": [ "main", "resources", "<custom>" ],
    "importBase": "import",
    "nativeBase": "native",
    "jsbDownloaderMaxTasks": 32
  },
  "scripting": {
    "scriptPackages": [ "virtual:///prerequisite-imports/main", … ]
  },
  "physics": { … },
  "rendering": {
    "renderMode": 0,
    "effectSettingsPath": "",
    "renderPipeline": "",
    "customPipeline": "",
    "msaa": false,
    "renderingScale": 1
  },
  "launch": {
    "launchScene": "db://assets/<scene-name>.scene"
  },
  "screen": { "exactFitScreen": true },
  "splashScreen": { … },
  "animation": { … },
  "profiling": { "showFPS": false },
  "plugins": {
    "jsList": [ "plugin-a.js", "plugin-b.js" ]
  },
  "xr": { "webxrCompatible": false }
}
```

- `launch.launchScene` → the scene UUID to open first.

- `assets.projectBundles` → the list of bundles to iterate.

- `plugins.jsList` → non-module plugin scripts (loaded before user code) — the 3.x analogue of 2.x `CCSettings.jsList`.

## Per-bundle `config.json`

Canonical schema: `IConfigOption` in `cocos/asset/asset-manager/config.ts` (lines 30–45). `processOptions()` (lines 149–225) is the reference decoder — if you're porting logic, read that function first.

```jsonc
{
  "name": "main",                  // bundle name
  "importBase": "import",          // default
  "nativeBase": "native",          // default
  "base": "assets/main/",          // relative to the build root
  "deps": ["internal"],            // other bundles this one needs
  "uuids": ["fcmR3XADNLgJ1ByKhqcC5Z", …],   // 22-char compressed UUIDs
  "paths": {
    "0": ["textures/bg", 3],                 //   path, typeIndex
    "1": ["prefabs/player", 5, 1]            //   path, typeIndex, subAssetFlag
  },
  "scenes": {
    "GameScene": "0",               //   scene name → uuidIndex-as-string
    "MenuScene": "12"
  },
  "packs": {
    "<packUuid>": ["<uuid1>", "<uuid2>", …]  // packed multi-asset files
  },
  "versions": {
    "import": ["<uuidIdx>", "ver", …],       // [index, version] pairs
    "native": ["<uuidIdx>", "ver", …]
  },
  "redirect": ["<uuidIdx>", "<bundleIdx>", …],
  "debug": false,                            // false → uuids[] is compressed
  "types": ["cc.Texture2D", "cc.Prefab", "cc.SceneAsset", …],  // class id lookup
  "extensionMap": {
    ".png": ["<uuid>"],             // uuids whose native file is a png
    ".cconb": ["<uuid>"]
  },
  "encrypted": false                // native builds only; true → index.jsc
}
```

### Reconstructing the URL for an asset

```
// From url-transformer.ts `combine()` + helper.ts `getUrlWithUuid()`
import: `${base}${importBase}/${uuid.slice(0,2)}/${uuid}${ver?'.'+ver:''}.${extension||'json'}`
native: `${base}${nativeBase}/${uuid.slice(0,2)}/${uuid}${ver?'.'+ver:''}${ext}`
```

Examples:

- `assets/main/import/fc/fc991dd7-0033-4b80-9d41-c8a86a702e59.json`

- `assets/main/native/fc/fc991dd7-0033-4b80-9d41-c8a86a702e59.png`

When `config.json` has `"debug": false`, each entry in `uuids[]` is a 22-char compressed value — expand it with the same `decodeUuid` algorithm used in 2.x (see `cocos/core/utils/decode-uuid.ts`).

## The serialized asset format (IFileData)

Every `.json` under `import/` decodes to an `IFileData` tuple. Full definition in `cocos/serialization/deserialize.ts` (`interface IFileData`, lines 323–342):

```ts
type IFileData = [
  /* 0 File.Version            */ number,
  /* 1 File.SharedUuids        */ string[] | 0,       // 0 = EMPTY
  /* 2 File.SharedStrings      */ string[] | 0,
  /* 3 File.SharedClasses      */ Array<IClass | string>, // class defs
  /* 4 File.SharedMasks        */ IMask[],
  /* 5 File.Instances          */ Array<IClassObjectData | OtherObjectData>,
  /* 6 File.InstanceTypes      */ number[] | 0,       // typeID per OtherObjectData
  /* 7 File.Refs               */ RefsData,
  /* 8 File.DependObjs         */ (number | IClassObjectData)[],
  /* 9 File.DependKeys         */ number[],
  /* 10 File.DependUuidIndices */ number[]
];

type IClass = [
/* 0 */ ctorName: string | ctor,
/* 1 */ keys: string[],                              // property names
/* 2 */ propTypeOffset: number,                      // split between simple & advanced
/* 3..*/ dataTypeIDs: number[]                       // one per advanced property
];

type IMask = [
/* 0 */ classIndex: number,
/* 1..*/ propertyIndices: number[],
/* last */ offsetBetweenSimpleAndAdvanced: number
];

type IClassObjectData = [
/* 0 */ maskIndex: number,
/* 1..*/ values: any[]                               // simple values inline, advanced by DataTypeID
];
```

Key differences from 2.x's "compressed array":

- **Class definitions are in-document** (`SharedClasses`) rather than global (`CCSettings.types`). You no longer need settings to rehydrate an asset.

- **Property ordering is per-mask**: two objects of the same class can have different masks if some properties use default values. Mask = "which properties are present". `IClassObjectData[0]` is the mask index, not the class index — look up class via `SharedMasks[maskIndex][0]`.

- **Back-references are inline integers**, not `{"__id__": n}`. A negative value in an advanced slot is a reverse index into `Instances`.

- **Asset refs** (`__uuid__` in 2.x) are now resolved via `DependObjs` / `DependKeys` / `DependUuidIndices`. The asset uuid lives in `SharedUuids`; `DependUuidIndices[i]` indexes into it; `DependObjs[i]` is the object that gets the ref; `DependKeys[i]` is the property name.

- `DataTypeID` discriminates advanced property kinds — `ValueType` (Vec2/Vec3/Color/…), `TRS`, `CustomizedClass` (nested IClassObjectData), `Dict`, `Array`, `AssetRef`, `InstanceRef`, `TypedArray`, etc. See `enum DataTypeID` in `deserialize.ts`.

### Packed form (`IPackedFileData`, lines 395–408)

Multiple assets share one document. `SharedUuids/Strings/Classes/Masks` are shared; `sections: IFileData[]` contains the per-asset slices. Used when the build packs several scenes/prefabs to reduce HTTP requests.

## CCON binary (.cconb / .ccon)

Binary variant of IFileData — format in `cocos/serialization/ccon.ts`:

```
u32  magic  = 0x4E4F4343      // "CCON" little-endian
u32  version                  // 1 = JSON body, 2 = notepack body
u32  totalByteLength
u32  jsonLen
u8[] jsonBlob                 // v1: UTF-8 JSON, v2: notepack (msgpack-ish)
// 8-byte aligned chunks follow:
for each chunk:
u32  chunkLen
u8[] chunkBytes
```

The `jsonBlob` is an `IFileData`. Chunks are referenced by index from inside the JSON (for example, mesh vertex buffers and animation curve data live in chunks). For v2 you need a notepack / msgpack decoder — see `external/deserialize/notepack_decode.js` in the engine repo.

## Scripts in 3.x

**User code ships as SystemJS modules under `src/chunks/*.js`** (or concatenated into `src/main.bundle.js` on some templates). Source is **TypeScript compiled to ES5 JavaScript** — you cannot recover TS, only JS.

```js
System.register(["cc"], function ($$exp, $$ctx) {
"use strict";
var cc, Player;
return {
setters: [function (_cc) { cc = _cc; }],
execute: function () {
// compiled class body
$$exp("Player", Player = /** @class */ (function (_super) {
__extends(Player, _super);
function Player() { ... }
return Player;
}(cc.Component)));
}
};
});
```

- The `src/import-map.json` maps the virtual module IDs (`virtual:///prerequisite-imports/main`) back to chunk files.

- `settings.scripting.scriptPackages` lists the packages to `System.import()` before `cc.game.run()`.
- `settings.plugins.jsList` lists raw (non-module) plugin scripts — these are direct `<script>` inclusions.

**Each bundle's `index.js`** is a registration stub — *not* user code. It declares the bundle's paths and calls `cc.assetManager.loadBundle` equivalents. This is the **only** script file that gets XXTEA-encrypted when `config.encrypted === true` (on native builds).

## Encryption (native only)

Reference implementation: `scripts/native-pack-tool/source/base/default.ts` → `encryptScripts()` (line ~481):

```ts
if (this.params.compressZip) {
content = gzipSync(content);
content = xxtea.encrypt(content, xxtea.toBytes(this.params.xxteaKey));
} else {
content = xxtea.encrypt(xxtea.toBytes(content), xxtea.toBytes(this.params.xxteaKey));
}
// Write as <name>.jsc, and set config.encrypted = true
```

Runtime consumer: `platforms/native/engine/jsb-loader.js` (around line 215) picks `index.<ver>.jsc` when `config.encrypted` is true, otherwise `index.<ver>.js`.

- **Scope**: only the bundle's `index.js` file. User scripts in `src/chunks/*.js` are **not** XXTEA-encrypted (they're minified/obfuscated but not encrypted).

- **Key storage**: 2.x usually embedded the key in `main.js`. 3.x native puts it in the binary via CMake variable `SCRIPT_XXTEAKEY` (`templates/common/Classes/Game.cpp` lines 32–53). On web builds the key can be in `application.js` or `src/settings.json` (search `xxtea`, `encryptKey`). For native-only games, recovering the key usually requires inspecting the shipped `libcocos.so` / executable.

## Asset-type handlers worth supporting

Property names are recoverable from `SharedClasses[*][1]` so you don't need a hardcoded type table for 3.x (unlike 2.x), but these are the common types you'll encounter and their native-file conventions:

| Class | Native extension(s) | Notes |
|---|---|---|
| `cc.SceneAsset` | — | Root of `.scene` files |
| `cc.Prefab` | — | IFileData with scene-graph |
| `cc.SpriteFrame` | — | References `ImageAsset`/`Texture2D` |
| `cc.ImageAsset` | `.png` / `.jpg` / `.webp` / `.pvr` / `.pkm` / `.astc` | The raw pixel source |
| `cc.Texture2D` | — | Wraps `ImageAsset`, no native file |
| `cc.TextureCube` | — | 6 ImageAsset refs |
| `cc.AudioClip` | `.mp3` / `.ogg` / `.wav` / `.m4a` |
| `cc.TextAsset` | `.txt` (or whatever `_native` says) |
| `cc.JsonAsset` | — | JSON embedded in document |
| `cc.BufferAsset` | `.bin` |
| `cc.Mesh` | `.bin` or `.cconb` | Vertex/index in native or CCON chunks |
| `cc.Material` | — | References `EffectAsset` + overrides |
| `cc.EffectAsset` | — | Shader source/IR in JSON |
| `cc.AnimationClip` | `.bin` (optional) / `.cconb` |
| `cc.SkeletalAnimationClip` | same | Subclass |
| `cc.Skeleton` | — | New in 3.x |
| `cc.ParticleAsset` | `.plist` (legacy) |
| `cc.Terrain` / `cc.TerrainAsset` | `.bin` |
| `cc.LabelAtlas` / `cc.BitmapFont` | `.fnt` |
| `cc.TTFFont` | `.ttf` |
| `sp.SkeletonData` | `.json` / `.skel` + `.atlas` + `.png`(s) | Spine |
| `dragonBones.DragonBonesAsset` | `.json` / `.dbbin` |
| `dragonBones.DragonBonesAtlasAsset` | `.json` + `.png` |

## Files in the engine to consult when extending the tool

- `cocos/core/settings.ts` — settings shape.

- `cocos/game/game.ts` — which settings fields are actually read at runtime (search `querySettings`).

- `cocos/asset/asset-manager/config.ts` — **source of truth for `config.json`**. Read `processOptions()`.

- `cocos/asset/asset-manager/url-transformer.ts` + `helper.ts` — uuid → URL.

- `cocos/core/utils/decode-uuid.ts` — 22-char compression (same as 2.x).

- `cocos/serialization/deserialize.ts` — IFileData / IClass / IMask shapes.

- `cocos/serialization/deserialize-dynamic.ts` — runtime deserializer, shows each DataTypeID handler.

- `cocos/serialization/ccon.ts` — CCON binary format.

- `external/deserialize/notepack_decode.js` — msgpack-ish decoder for CCON v2.

- `cocos/asset/asset-manager/parser.ts` — file-extension → handler table.

- `cocos/asset/asset-manager/pack-manager.ts` — packed-asset handling.

- `scripts/native-pack-tool/source/base/default.ts` — `encryptScripts()` for the reference XXTEA flow.

- `platforms/native/engine/jsb-loader.js` — runtime `.jsc` vs `.js` selection.

- `templates/web-mobile/*.ejs`, `templates/launcher/application.ejs` — what the shipped entry point looks like.
