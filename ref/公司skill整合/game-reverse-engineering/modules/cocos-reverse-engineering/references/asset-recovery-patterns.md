# Asset recovery patterns
> **何时读我**：拿到已还原的 Cocos 工程，要定位某个具体资产（场景、预制体、贴图、音频、动画、Spine/龙骨、脚本），要顺着 UUID 追依赖，或要清点工程里有什么、提取 HTTP 接口与第三方 SDK。
> **读完能做到**：用现成命令列出场景、把拼图帧追到贴图、按目录盘出音频/动画/脚本清单，并套模板把每个资产记成带 UUID/路径/依赖的条目。
> **范围**：`GENERAL_DEFAULT`

Patterns and commands for navigating a recovered Cocos Creator project to find specific assets, trace dependencies, and document what's inside.

## Scene inventory

### 2.x

```bash
# All scenes in the recovered project
find /assets/Scene -name '*.fire'

# Scenes registered in settings (authoritative order)
grep -oE '"launchScene":\s*"[^"]+"' /src/settings.js
grep -oE '"scenes":\s*\[[^]]+\]' /src/settings.js
```

### 3.x

```bash
# All scenes per bundle
find /assets -name '*.scene'

# Launch scene
jq -r '.launch.launchScene' /src/settings.*.json

# Scenes in a bundle's config
jq '.scenes' /assets/main/config.json
```

## Prefab dependency tracing

Scenes reference prefabs by UUID. Given a scene, list every prefab it references:

```bash
# 2.x — __uuid__ values in a .fire file
grep -oE '"__uuid__":\s*"[a-f0-9-]+"' /assets/Scene/MainScene.fire | sort -u

# 3.x — depend uuids in an IFileData. SharedUuids is position 1 in the array.
jq '.[1]' /assets/main/import//.json
```

Then look up the asset by UUID in `cc-reverse`'s recovered file tree — all recovered assets are named by either their original name (2.x with `_name`) or by UUID.

## Sprite frame → texture mapping

Every `cc.SpriteFrame` references a `cc.Texture2D` (2.x) or a `cc.ImageAsset` (3.x). The meta file written by `cc-reverse` records the `rawTextureUuid`:

```bash
# Find the texture a sprite frame uses
grep -rA1 '"":' /assets/Texture/*.meta   
| grep rawTextureUuid
```

If the texture UUID doesn't exist on disk, the sprite frame was pointing at an asset in another bundle — unpack that bundle (`--bundle `).

## Audio catalogue

```bash
# Duration / format summary (requires ffprobe)
for f in /assets/Audio/*; do
ffprobe -v quiet -of json -show_format "$f"   
| jq -r "[\"$f\", .format.format_name, .format.duration] | @tsv"
done
```

## Animation clip inspector

```bash
# List tracks and event points in a 2.x .anim file
jq '{name: ._name, sample, speed, tracks: .curveData | keys}'   
/assets/Animation/.anim
```

## Spine / DragonBones

Validate what was recovered:

```bash
# Spine — each skeleton needs json + atlas + png(s)
ls /assets/Spine/*

# DragonBones — _ske + _tex + texture
ls /assets/DragonBones/*
```

If only the JSON is present and no PNG, the texture lived under a different UUID in another bundle — re-run without `--bundle` restrictions.

## Script inventory

### 2.x

```bash
# Top-level user scripts
ls /assets/Scripts/*.ts | wc -l

# Inventory grouped by common prefix (detects namespaces / SDK packs)
ls /assets/Scripts/*.ts   
| xargs -n1 basename   
| awk -F_ '{print $1}'   
| sort | uniq -c | sort -rn | head -20

# Find all require() calls — shows third-party deps
grep -hoE "require\(['\"][^'\"]+['\"]\)" /assets/Scripts/*.ts   
| sort -u
```

### 3.x

Source recovered from `src/chunks/*.js` is **ES5 JavaScript** (compiled from TypeScript). Common patterns to scan for:

```bash
# Classes declared with __extends
grep -rnE '__extends\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,' /assets/Scripts/

# Modules exported via System.register dependencies
grep -rnE 'System\.register\(\[([^]]+)\]' /assets/Scripts/

# Component decorators compiled from @ccclass('X')
grep -rnE '_a\.register\s*=\s*function\|CCClass\.[A-Za-z]+' /assets/Scripts/
```

## Third-party SDK detection

Cocos games commonly ship these SDKs — spotting them up-front narrows your analysis:

| SDK | Signature to grep |
|---|---|
| AppLovin MAX | `MaxAds`, `MaxAdsEvents`, `AppLovinMAX` |
| Unity Ads | `UnityAdsPlugin`, `UnityAds.init`, `UADS` |
| Google AdMob | `AdMob`, `admob`, `com.google.android.gms.ads` |
| IronSource | `IronSource`, `ironSrc`, `IronSourceEvents` |
| GameAnalytics | `GameAnalytics`, `gameanalytics`, `GA_EVENT` |
| Firebase | `firebase.`, `FirebaseApp`, `FirebaseMessaging` |
| Bugly | `Bugly`, `CrashReport`, `bugly-sdk` |
| Cocos Analytics | `cc.analytics`, `cocos.analytics` |
| Facebook | `FB.`, `FacebookSDK`, `com.facebook` |

```bash
# Broad SDK sweep
grep -rlE 'AppLovin|UnityAds|AdMob|IronSource|GameAnalytics|Firebase|Bugly|FacebookSDK'   
/assets/Scripts/
```

## HTTP endpoint extraction

Cocos games often use `cc.loader.load`, `cc.assetManager.loadRemote`, or `XMLHttpRequest` / `fetch` directly.

```bash
# Base URLs
grep -rnEo 'https?://[A-Za-z0-9./_?=&%+-]+' /assets/Scripts/   
| sort -u

# API endpoint helpers
grep -rnE 'XMLHttpRequest|fetch\(|axios\.|cc\.loader\.load|assetManager\.loadRemote'   
/assets/Scripts/

# Common custom HTTP wrappers
grep -rnE 'HttpClient|NetManager|NetMgr|RequestManager|APIManager'   
/assets/Scripts/
```

## Asset documentation template

For each noteworthy asset, record:

```markdown
###  ()

- **UUID**: ``
- **Path**: `assets//`
- **Referenced by**: 
- **Dependencies**: 
- **Notes**: 
```

For scenes, add:

```markdown
### 

- **Root node count**: 
- **Total nodes**: 
- **Components used**: 
- **Prefabs instantiated**: 
- **Sprites / textures**: 
```

## Finding "unknown" assets

`find-assets.sh` reports unknown asset types at the end of its output. For each unknown:

1. Open the import JSON and look at `SharedClasses[0]` (3.x) or `data[0].__type__` (2.x).

2. Look up that class in the engine source (`cocos/` tree for 3.x, `cocos2d/` for 2.x).

3. If it's a recognised class, write a handler and register it:

```js
// cc-reverse.config.js (or a custom src/core/handlers/ file)
resourceProcessor.registerHandler('sp.SkeletonAnimation', (data, uuid, ctx) => {
// emit files…
});
```

1. If it's a custom project-defined class, the data is only meaningful inside the original scripts — keep the raw JSON and rely on the recovered `.ts`/`.js` to understand it.
