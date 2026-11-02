# Android Cocos JSB 游戏启动卡 Loading 排查手册

> **何时读我**：Cocos JSB 安卓包启动后卡在品牌页/Loading，不崩不 ANR 进程照跑，或怀疑入口文件与 settings 哈希、白屏黑屏时读我。
> **读完能做到**：用文件标记插桩把 JS 引导链断点定位到具体环节（settings 哈希错配、require 命中的空模块缓存、HEK 解密失败），再用 getStringFromFile + eval 绕过缓存修复并清装验证。
> **范围**：`GENERALIZED_PATTERN`

范围：`GENERALIZED_PATTERN`。复用启动链定位方法，不复制 BlockMaster 路径、marker、settings 哈希或加密结论。

场景：Cocos Creator 2.4.x JSB 原生 Android 游戏（常见于带热更 assets + 加密壳的手游），启动后**永久停在品牌页/原生 loading**，不崩溃、无 ANR、进程存活、GL 持续渲染。  
来源：BlockMasterPro（Block Blast 9.5.0 换皮）实战排查。10.4.7 基座新增踩坑（真机 ART/桥接改道/SDK 注入）见 `modules/cocos-reverse-engineering/references/android-jsb-reskin-pitfalls.md`。，从"卡 loading"定位到"JS 引导链静默中断"并修复的全过程与踩坑清单。

## 一、排查决策树（按此顺序，每步取证后再进入下一步）

1. **网络假设**：先怀疑热更服务器/DNS（多版本共卡时尤其如此）。设备端 `ping`/`curl` 主域名 + frida 原生钩 `getaddrinfo`/`connect`（spawn 90s），看 DNS rc 与 connect 是否悬挂。

2. **显示管线假设**：GLThread 卡 `eglSwapBuffers→dequeueBuffer→waitForFreeSlotThenRelock` **≠ 死锁**（见踩坑 4）。同实例同时取证（debuggerd 栈 + frida egl 计数）。

3. **Surface 门控假设**：HOME→回前台切换，看 nativeInit/JS 标记是否恢复。

4. **JS 加载/求值假设**（最常见根因区）：引擎读了 main.js 但 JS 引导链静默中断。

## 二、JS 引导链断点定位法（核心方法）

### 2.1 文件标记插桩（唯一可靠的观测手段）

**关键前提：`jsb.fileUtils.writeStringToFile` 的参数顺序是 `(content, fullPath)`——content 在前！**（写反了不报错、静默失败，且第一次"成功"的错觉会让你误判。）正确写法：

```js
var _bmwp = jsb.fileUtils.getWritablePath();
var _bm = function(n, x) {
var t = String(Date.now()) + (x ? (' ' + x) : '');
try { jsb.fileUtils.writeStringToFile(t, _bmwp + 'bm_' + n + '.txt'); } catch (e) {}
};
_bm('top_ran');   // 放文件最顶部
```

- `console.log` **不落 logcat**，一切观测必须写盘。

- 顶层 `setInterval` 轮询当前场景名（`cc.director.getScene().name`）写盘——能区分"引擎活着但无场景"与"整条链死了"。

- 把整个原版 main.js 包进 `try{...}catch(e){_bm('fatal_error', String(e))}`，**异常文本会直接告诉你断点**。本例抓到的签名：`TypeError: Cannot read properties of undefined (reading 'debug')` —— 即 `boot()` 里 `settings.debug` 时 `window._CCSettings` 未定义。

### 2.2 引导链各环节的插入点

| 环节 | 插入位置 | 标记内容 |
|---|---|---|
| 文件被求值 | main.js 最顶部 | top_ran |
| settings 各候选 require | v8TryRequire 的 catch 分支 | 异常文本 `req_fail` |
| settings 成功 | require 返回后 | `typeof window._CCSettings` |
| boot() 入口/出口 | window.boot 调用前后 | pre_boot / boot_throw |
| 模块加载 | loadScript 的 cb 回调 | cb_ok / cb_err(异常文本) |
| 场景加载 | loadScene 回调 | scene_ok(场景名) / scene_err |

### 2.3 典型断点与对应根因

- 无任何标记 → main.js 未被求值：检查引擎实际加载的是哪个文件（**files/patch/main.js 优先于 APK assets/main.js**，改错文件=白干）。

- 标记停在 settings 阶段、`_CCSettings` undefined：

热更 patch 目录**哈希/版本错配**：main.js 引用 `settings.c9e81.js` 而磁盘只有 `settings.3a3e3.js`（远程热更把文件换名/删除）；

- settings 文件是 `HEK:` 头加密块且解密失败（空内容被 require 静默吞掉）；

- require 命中**已缓存的空模块**（引擎早期预加载失败后缓存了布尔占位符，后续 require 直接返回、不执行文件）。

- **绕过 require 缓存的可靠修法**：直接 `var raw = jsb.fileUtils.getStringFromFile(name); if (raw && raw.indexOf('_CCSettings') !== -1) { eval(raw); }` —— getStringFromFile 走文件层（HEK 透明解密、返回明文），eval 后 `_CCSettings` 必被设置。

- settings 版本选择：**优先加载与磁盘 assets 匹配的版本**（看 project.manifest 的 version 与 main/mainTraits 的 hash 后缀），错配虽能过场景加载，但可能在后续原生玩法初始化时崩。

## 三、修复套路（卡 loading 类问题）

1. 用明文修复版覆盖 `files/patch/main.js`（历史验证：**明文 JS 可直接被执行**，无需 HEK 重加密）。

2. settings 用明文替换（从之前的 getStringFromFile 导出 dump 或本地解密后回填），并改 main.js 为 2.3 的直接 eval 加载。

3. 注意热更更新器会重新下载覆盖修复文件——修复需考虑钉死热更状态（删/改名 project.manifest 或等版本对齐），否则修复会被冲掉。

4. 文件 push 后 `chmod 666` + `chown` 应用 uid（先 `stat` 原文件确认 uid，不要照抄文档里的）。

## 四、踩坑清单（按踩坑顺序）

1. **writeStringToFile 参数顺序是 (content, path)**。写反不抛异常、静默失败；且 catch 逻辑不能依赖"写失败会抛异常"——cocos 的文件 API 失败返回 false 不抛，别用 try A 失败再 try B 的模式（A 会"成功"地失败）。0 字节的 epoch 时间戳文件是原生层的心跳，别与你的标记混淆。

2. **console.log/console.error 不落 logcat**。所有 JS 侧断言必须写盘；别用 logcat grep 判断 JS 行为。

3. **改对文件**：引擎优先执行 `files/patch/main.js`（热更目录），不是 APK `assets/main.js`。在 A 文件插桩却观察不到时，先确认引擎到底执行哪个。

4. **waitForFreeSlotThenRelock ≠ GL 死锁**。单次 debuggerd 栈快照看到它只是双缓冲背压瞬态。判定死锁必须同实例同时取证：frida 钩 `eglSwapBuffers` 计数（正常 120 次/秒、pending 12、无 ≥100ms 阻塞）与栈快照对照；线程 state=S 且 CPU 时间增长 = 活着。**单栈快照断言死锁是本案例最大误判。**

5. **AAssetManager 的 .jsc 打开只是优先探测**：引擎先试 `main.jsc`（不存在）再回退 `main.js`。看到 `.jsc` 打开记录不等于它在执行，先查文件是否真实存在。

6. **HEK 加密文件与明文混用**：引擎文件层对 `HEK:` 头文件透明解密、对明文直接执行。明文替换可行；但 require 的模块缓存可能吞掉解密失败的 settings（见 2.3）。

7. **frida 在 houdini 翻译进程上 Java 桥不可用**（`Java is not defined`）：x86_64 模拟器跑 arm64 应用时，改用纯原生钩子（Interceptor），hook libc 时枚举所有含 libc/houdini 的模块逐个挂。

8. **apktool 重打包的 smali_assets 陷阱**：解码后 `smali_assets/` 里嵌套的 `audience_network/classes*.dex` 树会和顶层类一起被 smali 进 assets.dex → "has already been interned"。修法：删掉整个 smali_assets 目录、把原 APK 的 `assets/audience_network/*.dex` 二进制原样放回 assets/。

9. **多包并存冲突**：两个包都声明 `c.g` 等混淆 authority 会 INSTALL_FAILED_CONFLICTING_PROVIDER；同包名换 APK 必须先 uninstall。

10. **改包名前先想清楚**：原生崩溃可能与包名相关（加密壳/路径依赖），A/B 验证要单变量——v7（无 SDK、旧包名）能进游戏 vs v8/v9（SDK/新包名）崩，才能隔离变量。

11. **subagent 失败要换模型/自查**：派发子任务返回空结果时，先确认子 agent 用的模型是否符合要求（出现过子 agent 用错模型导致空回报）。

12. **多版本共卡优先怀疑共享环境/外部服务**，别先归因自己的改动；但修复推进后出现的**新**崩溃（如场景加载后原生 SIGSEGV）要立刻 A/B 回退定位（本例：v7 可正常进游戏 → 新崩溃是后续改动的回归）。

## 五、证据采集命令速查

```powershell
# 线程栈（root 下）
adb shell debuggerd -b <pid> > threaddump.txt
# 同实例 egl/资产追踪（frida spawn，脚本见 loading_diag 归档）
frida spawn + Interceptor hook eglSwapBuffers / AAssetManager_open / open / openat / getaddrinfo / connect
# 文件标记检查
adb shell "ls /data/user/0/<pkg>/files/ | grep bm_; cat .../bm_*.txt"
# 墓碑对比
adb shell "ls -t /data/tombstones/ | head -5"
# 心跳文件（原生启动进度）
adb shell "ls /data/user/0/<pkg>/files/ | grep -E '^[0-9]{9,}'"
```
