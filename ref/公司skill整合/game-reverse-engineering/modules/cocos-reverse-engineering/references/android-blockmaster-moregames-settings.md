# Android BlockMaster 换皮二包（full/lite）实战总结：More Games 清除 + More Settings 原生弹窗恢复 + 热更缓存坑

> **何时读我**：BlockMaster 换皮二包要做 More Games 清除或 More Settings 原生弹窗恢复，或装完发现按钮还在、点设置卡 loading、改了半天进游戏还是旧样子时读我。
> **读完能做到**：同步改主 JS 与远程 patch JS 清掉 More Games 入口，自写 MoreSettingActivity + MoreSettingsBridge 打通原生弹窗，并识别 install -r 不清 files/patch 导致改动被旧缓存覆盖。
> **范围**：`CASE_ONLY_BLOCKMASTER`

范围：`CASE_ONLY_BLOCKMASTER` · `DO_NOT_COPY_LITERAL_VALUES`。

来源：`E:\codex_apk_work\blockmaster_pro_swap\work`（Block Blast 10.4.7 基座 → Block Master，包名 `com.driftsand.game.blockmaster`）。  
适用：NIS/BB 壳 + cocos2d-jsb + 远程热更（files/patch）的 Android 换皮/上架改造。与 `android-jsb-reskin-pitfalls.md` 互补；本篇聚焦「按钮/弹窗清理 + 热更缓存 + 商店覆盖」这一段。

---

## 1. 最终交付形态（v14）

| 项 | full | lite |
|---|---|---|
| 文件 | `BlockMaster_v14_full.apk` | `BlockMaster_v14_lite.apk` |
| versionName | `1.0.1.7-full` | `1.0.1.7-lite` |
| versionCode | 1000 | 1000 |
| applicationId | `com.driftsand.game.blockmaster` | `com.driftsand.game.blockmaster` |
| 签名 | debug.keystore（联调用，非商店签名） | 同左 |

两个变体包名相同，若要同时上架必须拆成不同 applicationId；否则互为覆盖。

## 2. 构建/重打壳流程

```
apktool b stage2_sdk/stage2_lite            -> stage2_{sdk|lite}_unsigned_v.apk
合并 bm_rebuilt_dex_clean/{classes2,4,de3,de}.dex  -> classes15..18（ZIP_STORED）
新增 more_settings_bridge_dex/classes.dex   -> classes19.dex
zipalign -p 4  +  apksigner（debug 或 release keystore）
```

- dex 一律 `ZIP_STORED`；`lib/*.so` 也 `STORED`，配合 extractNativeLibs=false。

- apksigner 批处理路径有 `\a` 转义坑（`apksigner.bat` 路径写成 `\apksigner` 会被当作 `\a` 转义），要用 `\\apksigner.bat`。

## 3. 踩坑清单（按发生顺序）

### 3.1 资源 ID 重映射（apktool 重建后必须修 R 常量）

- apktool 重建会**重排资源 type ID**，预编译 dex 里写死的 `R$xxx` 常量要对到新 APK 最终 ID。

- 已修案例：

hisavana 拉取线程 `Resources$NotFoundException #0x7f100131`：给 stage2_sdk 补 18 条 `Q/b` 字符串（固定 ID `0x7f14036b..0x7f14037c`）并同步 `Q/b.smali`。

- `R$xml.remote_config_defaults` 改到 `0x7f17000e`。

- `public.xml` 残留 `$ic_launcher_foreground__0` 导致 `no definition for declared symbol`，删掉该 public 项。

- `hs_common_dimens_111dp` 被当作 drawable 的警告属重映射缺口（暂不影响）。

- 教训：改动 res/public.xml 后，凡是 dex 里以 R 引用资源的 SDK，都要用最终 ID 反查补丁。

### 3.2 SDK 壳注入（BMInitProvider 模式）

- `com.blockmaster.sdk.BMInitProvider`（ContentProvider）里加 `checkedUpdate:Z`，按次序 init DeviceInfo/Firebase/FirebaseRemoteConfig/ChannelSdkBridge.initApplication。

- `BMInitProvider$1`（ActivityLifecycleCallbacks）：onActivityCreated 里 DStudioUtils、ChannelSdkBridge.initActivity、DeepLinkBridge init/handleIntent；onActivityResumed 里 onActivityResume/checkUpdate；onActivityPaused 里 onActivityPause。

- SeedCopier 崩溃 `IncompatibleClassChangeError`：`SeedCopier$1` 需补 `.implements Ljava/lang/Runnable;`。

- AhaPush 与项目 MMKV 版本不匹配（`NoSuchMethodError MMKV.s(String,I)Z` 等）：用 try/catch 包住避免致命。

- `com.block.juggle.datareport.firebase.SFireBaseDataAdapter` ClassNotFoundException 为基座遗留且被捕获，属良性噪声（QA 时不要误判为崩溃）。

### 3.3 More Games 清除（本阶段核心）

现象：主界面 classic 下方第三个按钮、设置弹窗顶部 more games 始终删不掉；点击弹窗后卡 loading。

原因与修法（**必须同时改主 JS 和远程 patch JS，两份结构几乎一样**）：

- 按钮节点名：主界面 `homePage/btn_layout/GameLobbyAddMoreGame`；设置弹窗按钮 key：`enSetupKeys.moreGames` / `SetupBtnItem.state.key==moreGames`。

- 远程 patch 里有一处被写反：`destroyUniverse` 对 GameLobbyAddMoreGame 设了 `i.active = !0`，等于把按钮点亮；要改成 `!1`。

- `bottomList` / iOS `btnList` 必须把 `moreGames`、`share` 一并剔除，否则 patch 覆盖主配置后按钮复活。

- 兜底方案（推荐）：

HomePage 增加 `hideMoreGames()`：递归 node.children，凡 name 含 `MoreGame/moreGame/btn_MoreGames` 一律 `active=false`，在 onLoad/onEnable/render 各调一次。

- Setup 的 render 里先按 `String(key).toLowerCase().indexOf('moregame')` 过滤 state.keys，再 `hideMoreGamesNode()` 递归隐藏。

- `showMiniGameList()` 直接 `return`（断开弹窗/卡 loading 路径）。

- `onClick_moreGames`、`onMoreGameClick`、`isOpenMoreGame`、`onClick_share`、`setShareIconToNative` 全部 no-op。

- 小游戏资源删除（full/lite 两处都要）：

`assets/assets/` 与 `assets/remote_seed/patch/patch/assets/` 下删除：  
`jewel`、`CommonGameEntrance1*`、`CommonGameList*`、`CommonGameListUI2BlockFlowExTrait`、`CommonGameListUI2PixelArtExTrait`、`ChangeMoreGamesDoubleColTrait`、`CampaignAcceptFirstLaunchToMiniGameTrait`、`GameOverShowMiniGameIconTrait`、`JewelGame*`、`MiniGame*`。

- 只删目录不删 manifest 也能启动；如要彻底，可再过滤 `project.manifest.assets` 对应 key（此包 remote manifest 是明文 JSON）。

### 3.4 More Settings 原生弹窗打不开（类缺失）

- 现象：manifest 声明 `org.cocos2dx.javascript.MoreSettingActivity`，但最终 dex 里没有该类，`NativeGame.callMoreSettings` 调不到东西，点开无反应。

- 修复（不依赖 R 类）：

自写 `MoreSettingActivity.java`：`setContentView` 用 `getResources().getIdentifier("activity_more_settings","layout",getPackageName())`；findViewById 同样用 getIdentifier 取 id；Terms/Privacy 直接 `ACTION_VIEW` 打开用户提供链接；顶部 appName 改 `Block Master!`、version 读 PackageInfo.versionName。

自写 `MoreSettingsBridge.java`：`callMoreSettings()`/`callMoreSettings(String)` 用 `Cocos2dxActivity.getContext()` 启动 Activity；context 非 Activity 时加 `FLAG_ACTIVITY_NEW_TASK`。

`javac -bootclasspath android.jar` + 编译桩（Cocos2dxActivity stub）+ `d8 --release --lib android.jar` 打成 classes19.dex。

改 JS `NativeGame.callMoreSettings`：`NativeBridge.send(..., "org/cocos2dx/javascript/MoreSettingsBridge")`（第 4 参指定目标类，默认是 `org/cocos2dx/javascript/AppActivity`）。

- 布局 `activity_more_settings{,_share}.xml` 已删掉 contactUs/share/aboutUs/6 个社交图标/licenses/privacy_preference，只留 title/close/logo/appName/version/terms/privacy。

### 3.5 热更缓存覆盖（本阶段最大的“看似没改成功”坑）

- `install -r` 覆盖安装不会清 `/data/data//files/patch`，旧缓存脚本会覆盖新 APK 里的 JS → 改了半天按钮还在。

- 复现/验证：

```
adb uninstall             # 或 adb shell pm clear 
adb install 
```

- 更进一步：**在 `assets/main.js` 里禁用 patch 搜索路径**，保证运行时强制用 APK 内置（已改好的）JS，而不是 patch 目录/服务器端热更内容：

main.js 顶部原来会把 `patch_temp` 移到 `patch` 并加入搜索路径；改为：遍历 `getSearchPaths()`，凡含 `.../patch` 的都 `splice` 掉再 setSearchPaths。

- 校验：启动后 `bm_boot_marker.txt` 应显示 `settings=src/settings.5731e.js`（走内置 settings，而不是 patch 里 `settings.85c88.js`）。

- 服务器地址参考（存在 main.js / index js / remote cacheList 里）：  
`https://bband1.afafb.com/blockblast/remote/...`、`http://inner-package1.youxi123.com:8820/remote/android/...`、`https://horizon.afafb.com/game/...`。发布前要确认走离线内置而不是拉线上覆盖。

### 3.6 商店覆盖（ps/Play Store）约束

- 现网 `E:\blockh5\build\android_ps\proj\gradle.properties`：`APPLICATION_ID=com.driftsand.game.blockmaster`、`VERSION_CODE=1015`、`VERSION_NAME=1.0.1.5`、`PROP_CHANNEL=ps`。

- 要让玩家能主动覆盖旧版，必须同时满足：

applicationId 完全一致；

新 versionCode > 线上（当前 1015，至少 1016，建议 1100 起）；

与现网同一套 release 签名（`E:/blockh5/config/keystore`，alias=blockmaster，密码见 gradle.properties）——debug 签名传商店装不上。

- Play 上架建议出 AAB；两个变体同包名只能上其中一个，或拆包名。

## 4. QA 清单（本轮实际执行）

- MuMu `127.0.0.1:16384`（adb root）与 TECNO `1291437488049244`：**先卸载/清数据 → 装 v14** → `am start` 主 Activity → `pidof` 存活 → logcat 无 FATAL。

- 直接验弹窗：`am start -n /org.cocos2dx.javascript.MoreSettingActivity`（TECNO 因 exported=false 会 SecurityException，属正常；游戏内部调用不受影响）。

- 日志里 `ClassNotFoundException com.block.juggle...SFireBaseDataAdapter` 为基座遗留良性噪声。

## 5. 复用要点

- 走向过：`stage2_sdk`/`stage2_lite` apktool 工程 + `stage2_rebuild_pipeline.py`/`build_lite.py`/`build_v12..14.py`；patch 脚本在 work 根目录 `patch_bb_remove_moregames_v*.py`、`patch_bb_hide_moregames_v5.py`、`patch_js_moresettings_bridge.py`、`patch_main_js_disable_patch_dir.py`、`patch_more_settings_layouts.py`、`delete_minigame_assets.py`。

- 每次改 JS/资源后必须：改 work 源文件 → 复制到两个 stage 项目 assets → apktool b → merge+sign → 卸载重装 QA。只改 APK 内文件但不重打，等于没改。
