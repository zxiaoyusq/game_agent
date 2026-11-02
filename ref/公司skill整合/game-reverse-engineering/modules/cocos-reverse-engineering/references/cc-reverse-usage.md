# cc-reverse CLI reference
> **何时读我**：要用 `cc-reverse` 工具链跑反编译、要查它的命令行参数与输出布局，或反编译出了岔子（认不出引擎版本、脚本只剩 `"use strict"`、场景解出来是空的、大工程内存溢出）要排查时。
> **读完能做到**：对 2.3.x/2.4.x/3.x 任一编译产物正确调用 `cc-reverse`（`--key`、`--version-hint`、`--bundle`、`--assets-only`/`--scripts-only`、`cc-reverse.config.js`），看懂输出工程目录结构，并按症状→原因→修法表定位失败。
> **范围**：`GENERAL_DEFAULT`

`cc-reverse` is the Node.js engine that does the actual decompilation. The skill scripts are thin wrappers around it — this file is the authoritative CLI reference.

## Synopsis

```
cc-reverse [OPTIONS] --path 
```

## Options

| Option | Description |
|---|---|
| `-p, --path ` | **Required.** Path to the compiled build root. |
| `-o, --output ` | Output directory. Default: `./output`. |
| `-v, --verbose` | Print per-file progress and dump the AST staging dir on exit. |
| `-s, --silent` | Disable progress spinners/bars. Useful for CI. |
| `-k, --key ` | XXTEA key for `.jsc` decryption. When omitted, `cc-reverse` tries to extract the key from `main.js` / `application.js` automatically. |
| `--version-hint ` | Force the engine series: `2.3.x`, `2.4.x`, or `3.x`. Auto-detected by default. |
| `--bundle ` | (3.x only) Unpack only this bundle. Repeatable: `--bundle main --bundle resources`. |
| `--assets-only` | Skip the script pass. |
| `--scripts-only` | Skip the asset pass. |
| `-V, --version` | Print the version. |
| `-h, --help` | Print help. |

## Engine autodetection

`cc-reverse` looks for these markers, in order:

1. `src/settings.js` + `src/project.js` + `res/` → **2.3.x**

2. `main.js` + (`settings.js` or `src/settings.js`) + (`assets/` or `res/`) → **2.4.x**

3. `assets/*/config.json` or `src/settings.json` + `application.js` → **3.x**

If nothing matches, it errors out with the expected layouts. Override with `--version-hint`.

## Configuration file

Place `cc-reverse.config.js` in your working directory (the directory from which you invoke `cc-reverse`):

```js
module.exports = {
output: {
createMeta: true,
prettify: true,
includeComments: true,
},
codeGen: {
language: 'typescript',      // 'typescript' | 'javascript'
moduleType: 'commonjs',      // 'commonjs' | 'esmodule' | 'amd'
indentSize: 2,
indent: 'space',             // 'space' | 'tab'
},
decrypt: {
key: null,                   // or a string; --key overrides this
},
assets: {
extractTextures: true,
extractAudio: true,
extractAnimations: true,
optimizeSprites: false,
spriteOutputMode: 'single',  // 'single' | 'atlas'
},
};
```

## Output layout

Regardless of engine version, the output mirrors a fresh Cocos Creator project:

```
output/
assets/
Scene/           .fire        + .fire.meta                 (2.x)
Scene/           .scene       + .scene.meta                (3.x)
Scripts/         .ts          + .ts.meta                   (2.x)
Scripts/         .js          + .js.meta                   (3.x — JS only)
Texture/         .png         + .png.meta
Audio/           .       + ..meta
Animation/       .anim        + .anim.meta
Spine/           .json / .atlas / .png + .meta
DragonBones/     _ske.json / _tex.json / _tex.png + .meta
...
RECOVERY_REPORT.md
project.json        (editor descriptor)
```

For 3.x, the bundle name is preserved as a subdirectory: `assets/main/…`, `assets/internal/…`, `assets/resources/…`, `assets//…`.

## Troubleshooting matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `Cannot find module` when running | Missing install step | `cd $(npm root -g)/cc-reverse && npm install` |
| Detection says "unknown" on an obvious Cocos dir | Path points at the parent of the build | Pass the child that actually contains `main.js` / `application.js` |
| Produces `assets/Scripts/*.ts` files that are just `"use strict";` | The build used an unusual module wrapper or the script was still encrypted | Check for `.jsc` in input; verify the key; try `--version-hint` explicitly |
| 3.x bundle unpacks but scenes are empty | The `config.json` couldn't be parsed (encrypted `index.js`) | Use `find-jsc-key.sh` + `-k `, then re-run |
| Sprite frames come out blank | `spriteOutputMode: 'single'` can't find the texture UUID | Try `spriteOutputMode: 'atlas'` in `cc-reverse.config.js` |
| Recovered scene references missing UUIDs | Some assets live in a bundle you didn't unpack (3.x) | Re-run without `--bundle` so all bundles unpack |
| `process out of memory` on a big game | Babel is parsing a huge `project.js` | Increase heap: `NODE_OPTIONS=--max-old-space-size=8192 cc-reverse …` |
| 3.x game only has `src/chunks/*.js` → no TS output | Expected: 3.x ships TypeScript compiled to ES5; the TS source cannot be recovered | Accept JS output; use sourcemaps if shipped |

## When to hand-edit

Some tasks `cc-reverse` intentionally doesn't do — they need human judgement:

- **Reconstructing the TS class hierarchy in 3.x.** The ES5 output uses `__extends(Cls, _super)` wrappers. You can't mechanically recover the TypeScript source; at best you get readable ES5. Use a JS-to-TS assistant (or this skill under `/reverse-cocos` with the resulting code) for the next pass.

- **Cleaning up UUID-named files the build kept as raw-assets.** 2.x's `raw-assets/` sometimes contains files whose original name is gone. `cc-reverse` preserves the UUID names and emits a meta with `rawTextureUuid` set; rename them after inspection if you care about filenames.

- **Merging split prefabs.** 3.x sometimes splits one prefab into multiple import docs (a "packed" IFileData). The tool writes the packed form as-is; if you want individual `.prefab` files, split them manually after checking the `SharedClasses` table.
