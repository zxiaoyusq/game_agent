# Cocos Android 游戏换皮/重基打包手册

> **何时读我**：要做 Android 重打包/换皮/split ABI/签名——把老版改动重基到新版、把 split 分包合成单包、内置离线 Seed，或装机报 INSTALL_FAILED_INVALID_APK / CONFLICTING_PROVIDER 时读我。
> **读完能做到**：按改动清单逐项迁移完成版本重基，把分包 lib 合入并去掉 split 标记、对齐同版本 ABI 库，用 SeedCopier 内置远程内容，并跑完 ZIP_STORED / zipalign -p / 签名门禁。
> **范围**：`GENERALIZED_PATTERN`

范围：`GENERALIZED_PATTERN`。重基、Seed、ABI、压缩和签名门禁可迁移；版本、包名、路径和证书是 `DO_NOT_COPY_LITERAL_VALUES`。

场景：把一个 Cocos JSB Android 游戏（含加密壳 + 热更）换素材/改包名/换 SDK，或把既有改动**重基到新版本**（rebase），并产出可交付的单包 APK。  
来源：BlockMasterPro 项目实战（Block Blast 9.5.0 → 10.4.7 重基 + 换皮 + 离线内容内置）。

## 一、版本重基（rebase）工作流

老版本改动已稳定、但需跟官方新版走时：

1. **解码新 base**：`apktool d new_base.apk -o proj`（split 分发的 base 无 lib，见第二节）。

2. **产出旧改动清单**：对旧换皮工程与原版工程做递归 diff（assets/ + res/，排除 build/），生成 `状态|路径|大小` 清单——这是可迁移的"改动资产"。

3. **逐项迁移**（不能整目录覆盖——新版本文件结构会变）：

- 图标/静态图：直接覆盖同路径（uuid 资源先确认新版本有同路径，没有则按文件名搜索新路径）

- strings.xml：只做**键值级替换**（如 firebase 项目 ID），不整文件覆盖

- 加载器脚本（main.js）：**不要从旧版迁移**，按新版自己的加载器结构重新分析（见《启动卡 Loading 排查手册》）

- 主题 styles.xml：新版可能是全新主题体系，diff 后只迁键名存在的小改

1. **验证重名资源**：旧版 png 与新版 webp 同名（如 `loading_bg.png` vs `loading_bg.webp`）会触发 aapt2 重复资源错误——删一方保留新版格式。

2. **构建链**（见第五节）+ 安装验证。

## 二、Split 分发结构与 ABI 匹配（高频大坑）

- 商店分发的游戏 base APK **通常不含任何 lib/**，native 库全部在 `config.` 分包（split_config.arm64_v8a / x86_64）里。

- 单包化：解码 base → 把分包 `lib//*.so` 放进工程 `lib//` → 删 manifest 的 `android:isSplitRequired` / `android:requiredSplitTypes` / `android:splitTypes`。

- **ABI 库必须与 base 同版本**：新版 Java/dex 层 + 旧版 so = 崩溃（实测案例：9.5.0 的 ReactNative 是模块化 so 集 `libreact_*.so`+`libhermes*`，10.4.7 是单体 `libreactnative.so`；混搭后 `ReactContextInitParams.` 直接 AssertionError 闪退）。

- 获取同版本 arm64 库的途径：从已装同版本游戏的设备拉分包：`adb shell pm path com.xxx` → `adb pull /data/app/.../split_config.arm64_v8a.apk`（实测 Infinix Android 11 未 root 也可 pull）。

- x86_64 模拟器（MuMu/雷电）带 arm 翻译时可直接跑 arm64 单包（`primaryCpuAbi=arm64-v8a` 经 libhoudini），无需 x86_64 库也能测试。

## 三、离线内容内置（SeedCopier 模式）

目标：把游戏首次联网下载的远程内容（files/patch + files/gamecaches）直接打进 APK，首启免下载。

1. 在真实设备/模拟器上跑一次原版，等远程内容下载完成，拉取 `files/patch` + `files/gamecaches`（root 或 `run-as`；模拟器 root 最方便）。

2. 放进工程 `assets/remote_seed/patch/` 与 `assets/remote_seed/gamecaches/`（路径可自定义，与拷贝类约定一致）。

3. 写一个 SeedCopier 类（smali 或 Java），在 `Application.onCreate`（壳的 MyApplication）中 `super.onCreate()` 之后调用：

- 检查 `files/.bm_seed_done` 标记，存在则跳过

- 递归拷贝 assets/remote_seed/patch → files/patch、assets/remote_seed/gamecaches → files/gamecaches

- 完成后写标记文件

1. 判定生效：新装设备上 `.bm_seed_done` 出现 + 文件数对齐 + 无下载行为。注意拷贝类的 `Log.d` 在真机 logcat 可见（标签自定），是低成本验证手段。

2. 注意：内置内容必须与 `project.manifest` 自洽（md5/版本），否则游戏校验逻辑可能拒用。

## 四、包名/签名/共存坑

- 两个包都声明混淆 provider authority（如 `c.g`）时 `INSTALL_FAILED_CONFLICTING_PROVIDER`——A/B 对照前先卸载同 authority 的包。

- 同包名换 APK：签名必须一致，否则先 uninstall。

- 新包名 + 硬编码 authority：apktool 的 `--rename-manifest-package` **不会**改硬编码的 `android:authorities="com.old.xxx"`，要手动全局替换。

## 五、构建链（extractNativeLibs=false 时必须遵守）

targetSdk 30+ 且 manifest `android:extractNativeLibs="false"` 时：

1. apktool b 产出后，**所有 lib/\*.so 必须 ZIP_STORED（不压缩）**——用 Python zipfile 重写：so 条目 compress_type=ZIP_STORED。

2. zipalign `-f -p 4`（build-tools 34 用 `-p` page-align so；`-P 16` 是 35+ 的参数）。

3. apksigner 签名。

- 漏掉 STORED/对齐 → 部分设备 `INSTALL_FAILED_INVALID_APK: Failed to extract native libraries, res=-2`（模拟器可能放水、真机必炸）。

## 六、重基后必查清单

versionCode/Name 与目标一致；app 名/图标已换

ABI 库与 base 同版本（同分包源）

无重名资源（png/webp 双份）

smali_assets 嵌套 dex 已还原为二进制（见《启动卡 Loading 排查手册》踩坑 8）

.so STORED + zipalign -p + 签名

SeedCopier 接线在 super.onCreate 之后、壳初始化之前

真机冷启 2 次无闪退、无下载行为（或下载正常完成）
