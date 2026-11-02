# Android BlockMaster V30/V31 实战：Hisavana 广告资源合并 + No Space/More Games/评分移除

> **何时读我**：Hisavana 全屏广告弹成透明 Activity 卡死（Window 0x0、系统返回键也退不出），或要按 V31 移除 No Space/More Games/评分入口、改 HEK 加密资源时读我。
> **读完能做到**：用 androguard + ARSCParser 判定 DEX 里 R 类 ID 与资源表错位，把缺失的 Hisavana 资源按未占用新 ID 合入并放到更早加载的 dex，用 HEK 保头脚本改 NoSpace 预制体，并跑完 V31 静态门禁。
> **范围**：`CASE_ONLY_BLOCKMASTER`

范围：`CASE_ONLY_BLOCKMASTER` · `DO_NOT_COPY_LITERAL_VALUES`。

来源：`E:\codex_apk_work\blockmaster_pro_swap\work`（Block Blast 10.4.7 基座 → Block Master，包名 `com.driftsand.game.blockmaster`）。  
适用：NIS/BB 壳 + cocos2d-jsb + Hisavana 广告 + Athena 统计 + 远程热更的 Android 换皮/上架改造。  
与 `android-blockmaster-moregames-settings.md` 互补；本篇重点记录「广告 DEX 合入但资源没合入导致全屏广告透明卡死」和「V31 UI 入口移除」的完整踩坑链。

---

## 1. Hisavana 全屏广告“透明 Activity 卡死”根因与修复

### 1.1 现象

- 真机死亡后启动 `com.cloud.hisavana.sdk.common.activity.TAdInterstitialActivity`。

- Activity 一直 `RESUMED`，但 Window 是 `0x0`、`shown=false`、`alpha=0.0`，系统返回键也退不出。

- logcat 里看不到 `interstitial.onShow` / `onError` / `TAdInterstitialActivity` SDK 日志。

### 1.2 根因

- APK 只把 Hisavana SDK 的 DEX 合并进去，**没有合入 SDK 对应的 Android 资源**（layout/drawable/string/style/color/dimen/id）。

- Hisavana `TAdInterstitialActivity.d0()` 会按 materialStyle 调用 `setContentView(R.layout.activity_t_ad_interstitial_*)`。

- 资源缺失/错位时异常被 `A1()` 的 catch 吞掉，只打日志不 `finish()`，于是留下透明空 Activity。

- 更隐蔽的是：DEX 里的 R 类字段值（如 `n0.activity_t_ad_interstitial_01_layout = 0x7f0b0025`）在目标 APK 中可能指向 **integer** 资源或**不存在**的资源，`setContentView` 实际拿不到 layout。

### 1.3 检测方法（androguard + ARSCParser）

```python
from androguard.core.dex import DEX
from androguard.core.axml import ARSCParser

d = DEX(open('classes15.dex','rb').read())
a = ARSCParser(open('resources.arsc','rb').read())

for c in d.get_classes():
if c.get_name() == 'Lcom/cloud/hisavana/sdk/n0;':
for f in c.get_fields():
rid = f.get_init_value().get_value()
info = a.get_id('com.driftsand.game.blockmaster', rid)
print(f.get_name(), hex(rid), info)
```

- 如果 `info[0]` 是 `integer` 而不是 `layout`，说明 R 类 ID 与 APK 资源表错位。

- 用 `a.get_res_configs(rid)` 返回 `[]` 表示该 ID 在资源表中不存在。

### 1.4 修复步骤

1. 从完整 Hisavana 参考 APK（如 `blockmaster_apktool`）把缺失资源合入当前 apktool 工程 `stage2_sdk`。

2. **不要覆盖现有 `res/values/public.xml`**，只追加新 public 项，并为每种资源类型分配未占用的新 ID（例如 layout 从 `0x7f0d01f9` 起）。

3. 把 Hisavana R 类（`j0/k0/l0/m0/n0/o0/q0/r0/s0`）放到 **比原 Hisavana DEX 更早加载的 dex**（如 `smali_classes14` → `classes14.dex`），用新 ID 覆盖旧 R 类字段值。

- Android 类加载按 dex 顺序，先加载的类会屏蔽后加载的同名类。

1. 修改后必须用 androguard 再次校验：所有 R 字段的 ID 在 `resources.arsc` 中都能解析到正确类型。

2. 修复 `HisavanaSDK.ShowInterstitialAd()`：创建 `GameTInterstitialAd` 时误用 `_rewardAdListener`，要改成 `_interstitialAdListener`。

3. 给 `TAdInterstitialActivity.A1()` catch 块加失败保险：发送 `_error` 广播 + `finish()`，避免任何异常后残留透明 Activity。

### 1.5 Windows 大小写碰撞坑（N0/n0）

- Hisavana DEX 同时存在 `Lcom/cloud/hisavana/sdk/N0;` 和 `Lcom/cloud/hisavana/sdk/n0;`。

- Windows 目录大小写不敏感，apktool/baksmali 全量反编译会把其中一个类覆盖丢失。

- 解法：不要全量反编译；用 dexlib2 `Baksmali.disassembleDexFile(dexFile, outDir, threads, options, classTypes)` **只导出需要的类**，避免同目录出现仅大小写不同的两个类。

- 也可以只把需要覆盖的 R 类/逻辑类放到较早 dex，原 Hisavana DEX 保持不动，完全绕开大小写问题。

---

## 2. HEK:XOR v03 资源保头修改

### 2.1 格式

- 头部：`b"HEK:"` + 4 字节版本标记（常见 `03 00 01 02`）。

- 正文：明文与 16 字节循环密钥 XOR。

- 本项目密钥：`65485d8a-8161-4c`。

- XOR 后可能是明文 JSON，也可能再套 gzip（`1F 8B`）。

### 2.2 修改示例（No Space Left 隐藏）

- 目标：`assets/assets/resources/import/f8/f837c0bd-...json`

- 基线 SHA256：`7D7CDAC04677F427A82B259A5F32F572155604774960961DBDF1915D8F7DC9ED`

- 解密后是 Cocos 序列化数组；`nospace` 节点对象形如：

```json
[4, "nospace", 1, [[6,-5,[2],3]], [0,"2407...",1,0], [5,490,91]]
```

- 该预制体的 `cc.Node` 类定义没有 `_active` 字段，因此把 `nospace` 的 `_opacity`（第二个数据字段）改为 `0`，等效隐藏文字，避免改动类 schema。

- 重新加密时：保留 `HEK:` + 版本头，只加密正文；写完再解密复读校验。

### 2.3 保头脚本要点

```python
raw = open(path,'rb').read()
header, body = raw[:8], raw[8:]
dec = bytes(b ^ KEY[i % len(KEY)] for i,b in enumerate(body))
# 修改 JSON
new_body = new_text.encode('utf-8')
new_body = bytes(b ^ KEY[i % len(KEY)] for i,b in enumerate(new_body))
open(path,'wb').write(header + new_body)
```

- 禁止把明文直接覆盖到加密资源路径。

- 修改前校验基线 SHA256，避免模糊改到其他资源。

---

## 3. V31 UI 移除（No Space / More Games / 评分）

### 3.1 双 JS 副本必须同步

- 本地：`assets/assets/main/index.7d3cd.js`

- Seed：`assets/remote_seed/patch/patch/assets/main/index.146a7.js`

- 只改本地会导致热更/Seed 覆盖后旧逻辑复活。

- 两份 JS 都要做同一组补丁，并记录补丁前后 SHA256。

### 3.2 More Games

- 设置数据生产数组移除 `m.enSetupKeys.moreGames`。

- 删除本地 `assets/assets/G0_F*EntryTrait` 四个目录；如果 Seed 也有，同步删除。

- 清理 Seed 明文清单 `baseM`、`project.manifest` 中 `assets/G0_F*` 条目。

- 已有 `showMiniGameList()` 和 `onMoreGameClick()` 前面加 `return;` 断链。

- 新增 `assets/bm_v31_patch_sanitizer.js`，在 `main.js` 启动早期精确删除 `patch`/`patch_temp` 下白名单中的 G0 Trait 目录，输出 `bm_moregames_sanitize_ok` 标记。

禁止删除整个 patch 目录，禁止用全场景递归模糊隐藏看门狗。

### 3.3 评分/Google Play

- `CommentSkin_Module` 的 `confirmFiveStarCallNativeComment` 已可 no-op。

- 游戏自身有三处 `callNativeComment` 桥接：

`NativeActivity.callNativeComment`

`NativeComment.callNativeComment`

`NativeUtils` 风格 `jsb.reflection.callStaticMethod(... "callNativeComment" ...)`

- 全部改成 `e.callNativeComment = function(e) {};`，保留函数签名。

- 不要全局拦截 `play.google.com`，广告点击仍需要能打开商店/落地页。

---

## 4. 构建链（V30/V31 通用）

```
apktool b stage2_sdk -o stage2_sdk_unsigned_v.apk
合并 bm_rebuilt_dex_clean/{classes2,4,de,de3}.dex -> classes15..18
合并 more_settings_bridge_dex/classes.dex -> classes19.dex
zipalign -f -p 4
apksigner sign --ks E:\blockh5\config\keystore --ks-key-alias blockmaster ...
```

- dex 与 `lib/*.so` 用 `ZIP_STORED`。

- 版本保持 `1.0.1.7 / 1017`。

- 最终 APK 要重新跑静态门禁，不要只检查源码目录。

## 5. 静态门禁要点

- `nospace_text_active=0`

- `moregames_setup_producers=0`

- `moregames_entry_prefabs=0`

- `moregames_trigger_traits=0`

- `rating_store_bridges_reachable=0`

- 最终 APK 内 `G0_F` 条目数为 0

- 广告关键资源（Hisavana layout/drawable/string/style）在 `resources.arsc` 中可解析

## 6. 关键脚本/文件位置（本次实战）

- `tools/BakSelect.java`：选择性 baksmali 导出，规避 Windows 大小写碰撞。

- `tools/merge_hisavana_resources.py`：从参考工程合并缺失资源并分配新 ID。

- `tools/patch_r_smali.py`：按 `hisavana_id_map.json` 重写 R 类 smali 字段值。

- `patch_v31_nospace_prefab.py`：HEK 保头修改 NoSpace 预制体。

- `patch_v31_js.py`：双 JS 同步移除 moreGames setup + no-op callNativeComment。

- `stage2_sdk/assets/bm_v31_patch_sanitizer.js`：启动期清理旧 More Games Trait 目录。

- `verify_v31_ui_removal.py`：最终 APK 静态门禁。
