# JSC decryption (XXTEA + gzip)
> **何时读我**：遇到 `.jsc` 要解密，或怀疑构建用了 XXTEA，需要找密钥、验证密钥对不对，或解密结果是乱码 / 是 gzip 时。
> **读完能做到**：按 2.x/3.x、web/native 各落点找到 XXTEA 密钥（含 `[0x61, 0x62, …]` 字节数组形式），用单文件方式验证候选密钥，并按症状表判断解密失败的真实原因。
> **范围**：`GENERAL_DEFAULT`

Cocos Creator games can ship user JavaScript as `.jsc` files instead of `.js`. These are XXTEA-encrypted; some builds also gzip the plaintext before encryption. This reference explains where to find the key, how to verify it, and why decryption sometimes fails.

## Algorithm

```
plaintext = 
optionally: plaintext = gzipSync(plaintext)
ciphertext = xxtea.encrypt(plaintext, xxtea.toBytes(key))
// stored as .jsc
```

`cc-reverse`'s decrypter (`src/core/jscDecryptor.js`):

```js
const decrypted = xxtea.decrypt(data, xxtea.toBytes(key));
try   { return Buffer.from(pako.inflate(decrypted)); }  // gzipped → inflate
catch { return Buffer.from(decrypted); }                 // not gzipped
```

If the output starts with `0x1F 0x8B`, gzip inflation is needed. `cc-reverse` attempts inflation unconditionally and falls back to raw bytes on failure, so you don't need to specify which variant a build used.

## Where the key lives

### 2.x

- `main.js` — search for one of:

`var xxteaKey = "…"` / `window.xxteaKey`

- `encryptKey = "…"`

- `XXTEA_KEY = "…"`

- `cc.Class({... encryptKey: "…" …})`

- A bare string passed into a `decryptXxtea(...)` helper near the top of the file.

- `src/main.js` for 2.3.x where everything is under `src/`.

- Custom `xxtea.js` or `encrypt.js` shipped alongside `main.js`.

The default for Cocos Creator 2.x's built-in encryption is a **UUID-shaped string** derived from the project UUID — it is literally put in the build. `find-jsc-key.sh` matches `[0-9a-f]{8}-[0-9a-f]{4}-…` patterns for this reason.

### 3.x web build

- `application.js` — the launcher; the key is sometimes passed to the engine config.

- `src/settings.json` — may contain `assets.encrypted: true` and an `xxtea` field in some templates.

- `cocos-js/cc.*.js` — the engine bundle. Rare but possible.

### 3.x native build

The key is stored **inside the native binary** via CMake variable `SCRIPT_XXTEAKEY` (see `templates/common/Classes/Game.cpp`). To recover it from a shipped APK/executable:

1. Unzip the APK.

2. Run `strings lib/arm64-v8a/libcocos.so | grep -E '^.{8}-.{4}' | head -20` — the key is typically a short printable string near the start of the `rodata` section.

3. Cross-reference with `strings` against the bundled config to narrow candidates. The correct key will decrypt at least one `index.*.jsc` cleanly.

If the developer used a **custom XXTEA wrapper** (replacing the stock one), the key may be obfuscated — e.g. XOR'd with a constant at startup. In that case, running the decrypted wrapper step-by-step in a Node REPL is often the fastest path.

## Byte-array keys

Some builds store the key as `[0x61, 0x62, 0x63, …]` (or the decimal equivalent) and assemble it at load time. `find-jsc-key.sh` detects this pattern and reconstructs the string:

```js
var _k = [0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68];
window.xxteaKey = String.fromCharCode.apply(null, _k);
```

If the key is split across multiple arrays or mixed with dynamic computation, manual extraction is needed — the automated scanner is intentionally conservative about false positives.

## Verifying a candidate key

Pick any `.jsc` file and decrypt it alone:

```bash
cc-reverse --path  --key  --scripts-only -o /tmp/cc-verify
head -c 200 /tmp/cc-verify/assets/Scripts/*.js | head -20
```

A correct key produces readable JavaScript (with `cc._RF.push(...)` / `cc.Class(...)` / `Object.defineProperty(exports, …)` / `System.register(...)`). A wrong key produces random bytes — often binary garbage that fails to decode as UTF-8.

## Why decryption can fail

| Symptom | Cause | Fix |
|---|---|---|
| Output is garbage | Wrong key | Re-run the key finder; try any near-match candidates |
| Output starts with `0x1F 0x8B` but `cc-reverse` errored | gzip inflate didn't match — truncated file | Verify the `.jsc` was copied in full |
| Some `.jsc` decrypt, others don't | Different bundles use different keys (rare but happens on subpackages) | Pass `--bundle ` and try other candidate keys per bundle |
| `xxtea.decrypt` returns null | Not actually XXTEA, or key length mismatch | The file may use a custom algo. Inspect `main.js` for the decrypt call site |
| All files decrypt but assets are empty | You decrypted the assets as scripts | `.jsc` is scripts only; assets are plain JSON |
| 3.x `config.json` has `"encrypted": true` but no `.jsc` anywhere | The build is a web build; `encrypted` only activates on native | Ignore the flag; decrypt nothing |

## Legal / ethical note

The skill is intended for reverse engineering games **you have a right to analyze** — your own releases, games under an interoperability exception in your jurisdiction, or CTF/security-research contexts. XXTEA is a thin protection; being technically bypassable does not grant legal authorization. When in doubt, ask the game's owner or stop.
