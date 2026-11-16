# 无人值守启动与自愈（autonomous-startup）

范围：`GENERALIZED_PATTERN`。启动/恢复方法可迁移；DADAPET路径、端口、数量、DebugBridge命令只作案例证据，迁移时重新发现。

## 2026-10-14 独立审核：通过范围与部署边界

**PASS：一次真实连接中断后，重新拉起编辑器、MCP和预览，继续完成8项。FAIL：整批任务18成功、3失败。NEEDS_CONTEXT：退出根因、重复恢复和长期稳定性。** 不能把WinError10054单独解释成确定的编辑器崩溃原因。

原始公开工具seq3900证明环境变量污染和干净环境启动；4048证明CDP调用start-server；4104证明仅恢复编辑器/MCP仍因预览未开而失败；4137证明恢复预览后续跑，但CrossEnd仍失败、实际没有重试原项。日志打印“重试本屏”不算重试证据。CreatePet缺引导状态，Setting桥接超时也未解决。

独立读取：Creator/CDP与MCP `cocos://project/info`均返回E:\DADAPET；/health成功；扩展get-server-status为running=true/port=3000。**MCP tool server_status get/port返回7456，查的是Creator预览服务器；MCP transport为3000**。不能把预览端口当MCP URL。tool名和参数用tools/list发现，`project_info`不是该实例的tool；项目身份通过resources/list/read取得。

### 当前脚本的安全与使用范围

旧脚本 `--project E:\WallkikersCocos --check-only` 在CDP/MCP均为DADAPET时仍返回RESULT=OK，已实测反例。审核修正：匹配CDP工程、MCP握手和Resource工程身份；移除全局kill；目标实例还活但CDP不可用时失败退出，交由已授权、已保存状态的受控重启处理；不回退任意CDP页面。支持 `--cdp-port` / `--mcp-port`，只用于harady消息/HTTP契约，Funplay另走自身通道。函数返回True不代表预览或游戏已恢复。

```powershell
# 只读例：端口需从目标实例发现，工程不匹配返回FAIL且不启动/关闭进程
python <skill>/modules/cocos-mcp-channel/scripts/ensure_cocos_mcp.py `
  --project <project> --cdp-port <cdp> --mcp-port <harady-port> --check-only
```

有其他工程占用指定CDP端口就失败退出，先选独立端口。项目正常关闭、人工暂停、离线build转换不触发恢复；启动器本身不是常驻watchdog。编辑器/MCP故障、旧session、预览停止、桥接超时分别诊断，有次数上限与退避，不无限拉起。

**完整恢复配方**：目标进程/工程身份 → CDP正确main.html → 实际扩展get-server-status/start-server → /health → initialize/initialized/tools/list → Resource身份 → 新session → debug_preview start（按当前schema） → 本工程只读桥接/心跳 → 恢复诊断状态 → 重试失败项。

每次记录失败项与完整异常、前后PID/启动时间、root、端口、握手、预览/桥接就绪及重试结果；批处理失败非零，旧截图单列。正式玩法验收使用真实输入，诊断状态恢复不能替代真实一局。启动子进程env过滤ELECTRON_RUN_AS_NODE，NODE_OPTIONS是否过滤按当前配置与报错决定；不改全局系统环境。Windows后台辅助进程Start-Process使用-WindowStyle Hidden。

迁移验收：冷启动、重复调用不产生重复实例、一次目标退出后完整恢复并重试原项、其他工程不受影响、暂停/意图关闭不复活、编辑器与CLI构建不抢写、失败非零。案例没有证明这些全部通过。

证据：`D:\codex_tools\cocos-mcp-audit-20261014\public-tool-*.txt`（公开工具输出与源码快照）；`D:\codex_tools\dsh-cocos-workflow-live-evidence-20261014.json`（独立HTTP/CDP/Resource与哈希）。恢复后8张PNG已独立解码为375×811；只证明有有效产物，不证明视觉正确。

## TL;DR

| 想做的事 | 能不能自动化 | 怎么做 |
| --- | --- | --- |
| 启动 Cocos 编辑器 | ✅ | `Start-Process` + **剔除 `ELECTRON_RUN_AS_NODE`** |
| 拿到编辑器 JS API | ✅ | `--remote-debugging-port=9222` + CDP |
| 启动 MCP 服务（不用人点面板） | ✅ | CDP 里 `Editor.Message.request(pkg,'start-server')` |
| 让扩展面板自动打开 | ❌ | 试过 UI Automation（无原生菜单）与改 `window.json` 布局（多个 id 写法），都不行 → 走 CDP 而非开面板 |
| 编辑器崩溃后接着跑 | ✅ | 崩溃 → 重启编辑器 → 起 MCP → **重开游戏预览** → 重试本项 |

一键入口：`modules/cocos-mcp-channel/scripts/ensure_cocos_mcp.py`（只用于harady；工程身份匹配后才判编辑器/CDP/MCP就绪，不包含预览恢复）。

---

## 1. 坑一：`ELECTRON_RUN_AS_NODE` 污染（最隐蔽，先查它）

### 症状

从 harness 里 `Start-Process CocosCreator.exe --project <proj>` 之后：

- 进程 **900ms 内自己退出**，`Start-Process -PassThru` 明明返回了进程对象
- **退出码 0**（干净退出，不是崩溃）
- 无窗口、无日志、Windows 事件日志里**没有** Application Error
- 不带任何参数启动也一样退

四个现象凑一起很容易误判成"工程坏了 / 许可失效 / 杀软拦截"，从而白查半天。

### 根因

harness 自身若是 Electron 应用（DSH / VS Code / Cursor / Claude Desktop…），
进程环境里带 **`ELECTRON_RUN_AS_NODE=1`**。子进程继承后，Electron 以 **Node 模式**
启动：不建窗口、拒绝 `--project` 这类 GUI 开关。

### 取证方法（一步定性）

把 stderr 重定向到文件：

```powershell
$exe = 'C:\ProgramData\cocos\editors\Creator\3.8.7\CocosCreator.exe'
Start-Process $exe -WindowStyle Hidden -ArgumentList @('--project','E:\PROJ') -PassThru `
  -RedirectStandardError 'err.txt' -RedirectStandardOutput 'out.txt' | Out-Null
```

`err.txt` 里出现：

```
CocosCreator.exe: bad option: --project
```

看到这句就可以直接定位到环境变量，不用再查别的。

### 修法

```powershell
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
Remove-Item Env:NODE_OPTIONS          -ErrorAction SilentlyContinue
Start-Process $exe -WindowStyle Hidden -ArgumentList '--project','E:\PROJ','--can-show-upgrade-dialog','true'
```

Python 里用干净环境启动：

```python
env = {k: v for k, v in os.environ.items()
       if k not in ("ELECTRON_RUN_AS_NODE", "NODE_OPTIONS")}
subprocess.Popen([exe, "--project", proj], env=env)
```

**鉴别口诀**：进程秒退 + 退出码 0 + 事件日志无崩溃 → 先查 `ELECTRON_RUN_AS_NODE`。

---

## 2. 坑二：扩展面板必须人工点（自举死锁）

MCP 服务跑在编辑器进程内。常规流程是"人在编辑器里点开扩展面板 → 服务 start-server"。
harness 想全自动，就得绕过这个点击。

### 两条走不通的路（已实测，别再试）

| 尝试 | 结果 |
| --- | --- |
| **Windows UI Automation 点菜单** | 编辑器窗口类是 `Chrome_WidgetWin_1`，子元素只有 `Chrome Legacy Window` 与 `Intermediate D3D Window`，**查不到 MenuBar**——菜单是 HTML 实现的，UIA 够不到 |
| **改 `%USERPROFILE%\.CocosCreator\editor\window.json` 把面板塞进布局** | 补丁确实被编辑器读取（未被覆盖），但重启后**面板不打开**。试过 `cocos-mcp` 与 `cocos-mcp.default` 两种 id 写法，都不行 |

### 走得通的路：CDP 逃生舱

Cocos Creator 是 Electron 应用。加 `--remote-debugging-port` 启动，就能用
Chrome DevTools Protocol 连到渲染进程执行任意 JS，进而调编辑器的消息 API。

**第 1 步**：带调试端口启动

```
CocosCreator.exe --project <proj> --can-show-upgrade-dialog true --remote-debugging-port=9222
```

**第 2 步**：HTTP 拿 target，挑 `main.html` 那个

```
GET http://127.0.0.1:9222/json
→ [{"type":"page","title":"main.html#...","url":"file:///.../main.html",
    "webSocketDebuggerUrl":"ws://127.0.0.1:9222/devtools/page/XXXX"}]
```

**第 3 步**：WebSocket 发 `Runtime.evaluate`

```json
{"id":1,"method":"Runtime.evaluate",
 "params":{"expression":"<你的 JS>","returnByValue":true,"awaitPromise":true}}
```

**第 4 步**：JS 里先探 `Editor` 在不在，再调消息

```js
typeof Editor !== 'undefined' ? 'HAS_EDITOR' : 'NO_EDITOR'
```

实测 `main.html` 这个 target **有** `Editor`（键：`Message, Package, Panel, ...`）。

**第 5 步**：启动服务（幂等）

```js
var st = await Editor.Message.request('cocos-creator-mcp','get-server-status');
if (!st.running) await Editor.Message.request('cocos-creator-mcp','start-server');
// → {"running":true,"port":3000}
```

Python 侧只需 `requests` + `websockets`：

```python
import requests, websockets, asyncio, json
tl = requests.get("http://127.0.0.1:9222/json", timeout=5).json()
t  = next(x for x in tl if "main.html" in (x.get("url") or ""))
async def ev(expr):
    async with websockets.connect(t["webSocketDebuggerUrl"]) as ws:
        await ws.send(json.dumps({"id":1,"method":"Runtime.evaluate",
            "params":{"expression":expr,"returnByValue":True,"awaitPromise":True}}))
        while True:
            m = json.loads(await ws.recv())
            if m.get("id")==1: return m["result"]["result"].get("value")
```

---

## 3. 坑三：包名要对，否则 `methods is undefined`

同一台机器上可能并存多个同类 MCP 扩展。调错包名的报错很有辨识度：

```
Method does not exist(<pkg>.<method>), The 'methods' of the module is undefined
```

**先查真实注册名**：

```js
var ps = await Editor.Package.getPackages();
ps.filter(p => /mcp/i.test(p.name)).map(p => p.name + ' v' + p.version + ' enable=' + p.enable)
```

该项目观察到以下两个相关包（另有Funplay，不是只有两个扩展；`enable` 都是 `true`、`invalid` 都是 `false`）：

| 包名 | 版本 | 位置 | 能否调用 |
| --- | --- | --- | --- |
| **`cocos-creator-mcp`** | 2.0.2 | `~/.CocosCreator/builtin-extensions/3.8.7/` | ✅ **真正在用**，`toolCount: 64` |
| `cocos-mcp` | 2.8.0 | `<project>/extensions/cocos-mcp-server` | ❌ 方法未注册，调用即报 methods undefined |

**教训**：看到 `methods is undefined` 先查当前包的加载/方法注册和目标包身份；只有证据表明用了错误实现时才换包名。

`cocos-creator-mcp` 的服务管理消息面：

| 消息 | 作用 |
| --- | --- |
| `get-server-status` | `{running, port, toolCount, toolNames[]}` |
| `start-server` | 启动，返回 `{running:true, port:3000}` |
| `stop-server` | 停止 |
| `open-panel` | 开面板（依赖对应包的面板方法；此前失败属于项目级cocos-mcp，不可推断harady open-panel必失败） |

---

## 4. 自愈式批处理（编辑器崩溃不再中断任务）

### 崩溃规律（实测）

DADAPET会话报告连续导航/截图时多次异常退出；2026-10-13/14报告共8次
（分别撑到 9、10、10、8、7、11、2、10 次）。这些是该项目报告，不能断言是Creator硬限制或排除脚本原因。

### 恢复链（缺一环就恢复不了）

```
任务项开始前做健康检查
  └─ 不通 → ensure_cocos_mcp.py（重启编辑器 + 起 MCP）
       └─ ⚠️ 必须再 **重开游戏预览**（debug_preview start）
            └─ 轮询直到游戏侧客户端重新连上
                 └─ 重试本项，而不是跳到下一项
```

**最容易漏的一环**：编辑器重启后**游戏预览也没了**。只重启编辑器 + 服务、不重开预览，
游戏侧客户端不会轮询 MCP，后续命令全部超时：

```
{"error":"Game did not respond within 20000ms. Is GameDebugClient running in the preview?"}
```

### 实测效果

一轮 21 屏的运行态截图任务，第 11 屏时编辑器崩溃：

```
[10/21] OK   DdTask
[11/21] FAIL CrossEnd        ← 编辑器此时崩溃（连接被重置）
     MCP 无响应，尝试自动重启编辑器+服务 ...
       CDP 返回: STARTED {"running":true,"port":3000}
       MCP 已监听 3000 ✓
     预览: {"success":true,"action":"start"}
     已恢复，重试本屏
[12/21] OK   Breed           ← 自动续跑
...
成功 18
```

仅证明一次恢复后续跑；没有证明失败项补齐、恢复耗时上界或长期稳定性。

### 断点续跑

批处理需保存每项结果及构建/状态标识，只有当前批次验证有效的产物可跳过；旧文件存在不算本轮成功。
配 `--redo` 强制重截。

---

## 5. 游戏侧桥接（DebugBridge 模式）

要让 MCP 能"打开某个界面再截图"，需要在**游戏代码**里注册自定义命令。

### 接入

扩展自带客户端脚本，复制进工程（只依赖 `cc`，无外部依赖）：

```
<extension>/client/McpDebugClient.ts  →  <project>/assets/scripts/common/debug/
```

游戏启动时初始化（用独立文件包起来，**默认关、可整体删除**）：

```typescript
import { initMcpDebugClient } from "./McpDebugClient";
const ENABLE = true;                       // 总开关，交付前置 false 或删文件
export function initDebugBridge(): void {
    if (!ENABLE || _inited) return;
    initMcpDebugClient({ mcpBaseUrl: "http://127.0.0.1:3000",
        customCommands: { navigate, pages, closeAll, uistate, enterLobby } });
}
```

`GameApp` 里一行调用（包 try/catch）。MCP 服务未启动时客户端内部静默忽略，对游戏零影响。

### 内置命令（扩展自带，无需注册）

- `screenshot` —— **RenderTexture 抓游戏画面**（返回 dataUrl）
- `click` —— 按节点名点一下

### ⚠️ 命令必须真实反映失败（这条吃过两次亏）

**错误写法**：

```typescript
// 可选链短路时什么都没做，却返回 success —— 外部被骗
await CFW.stage.get(LobbyStage)?.getSystem(ShopSystem)?.openShop();
return { success: true };
```

`CFW.stage.get(LobbyStage)` 为 null（比如游戏还在新手引导阶段）时，整条链静默跳过，
但命令报 `success: true`。后果：**19 张截图里 16 张是同一个画面**，排查代价极大。

**正确写法**：

```typescript
const stage = CFW.stage.get(LobbyStage);
if (!stage) return "LobbyStage 未激活 —— 当前游戏处于新手引导阶段。先执行 enterLobby。";
const sys = stage.getSystem(ShopSystem);
if (!sys) return "系统未注册: ShopSystem";
await sys.openShop();
return null;                                // null = 成功
```

`closeAll` 同理，并且要返回**可校验的计量**：

```typescript
const mgr: any = CFW.uiMgr;
if (!mgr) return { success: false, error: "CFW.uiMgr 为 null，无法关闭 UI" };
const before = mgr._openPanels.size;
mgr.closeAll();
return { success: true, data: { before, after: mgr._openPanels.size } };
```

调用方再校验 `after`，而不是盲信 `success`。

### DADAPET案例诊断/辅助命令（其他项目按自身实现）

| 命令 | 作用 |
| --- | --- |
| `pages` | 返回支持的界面名清单（外部用来确认桥接真的连上了） |
| `uistate` | 当前打开的面板名与数量（诊断堆叠） |
| `closeAll` | 关掉所有 UI，返回 `{before, after}` |
| `enterLobby` | 跳过新手引导直达大厅（**全新预览默认走引导 Stage，不执行它所有大厅界面都打不开**） |
| `navigate {page}` | 打开指定界面 |

### 界面打不开时的排查顺序

1. `pages` 通不通？不通 → 游戏没跑 / 桥接没连
2. 通但 `navigate` 报"LobbyStage 未激活" → 在引导阶段，先 `enterLobby`
3. `navigate` 成功但截图不对 → `uistate` 看有没有堆叠

---

## 6. 截图取景：编辑器截图 ≠ 可对比图

| | 编辑器 prefab 截图 | 运行态截图 |
| --- | --- | --- |
| 内容 | prefab 自身节点，孤立在场景网格上 | **完整成品画面** |
| 宠物 / 背景 | ❌ 不在这个 prefab 里（是独立 prefab） | ✅ 有 |
| 运行时赋值的贴图 | ❌ 显示为品红方块 | ✅ 真实渲染 |
| 与设计稿比例 | ❌ 横向，对不上 | ✅ 同比例 |

**要跟设计稿/效果图逐屏比对，必须走运行态截图。**

### 试过但不可行的路：裁编辑器里的 Canvas 白框

想通过"裁到编辑器场景视图里的 Canvas 边界"来对齐比例。实现后 **42 张只命中 8 张**，
且"命中"的尺寸互相矛盾（`519x1108` vs `87x194`，后者明显是误判）。
画布边框常被 prefab 内容遮挡或被场景网格线干扰。**放弃。**

### 运行态截图的正确姿势

走游戏侧 `screenshot` 命令（RenderTexture 抓画面），得到与设计稿同比例的成品图。
实测手机竖屏工程得 `375x811`（比例 0.462），设计稿 `1080x2400`（0.450），可直接并排。

---

## 7. 坑：`closeAll` 清不掉的界面

**不是所有 UI 都归框架的 `uiMgr` 管。**

实测某个界面（本次是"设置"）不在 `_openPanels` 里：`closeAll` 报
`{before: 0, after: 0}`，但它**明明显示在屏幕上**，并压在后续每一屏背后。

### 兜底做法

把这类界面排到批处理序列**最后**。本次把 `Setting` 移到最后，前面 19 屏全部干净。

### 别用的做法

不要为了清洁而每屏重启预览——虽然状态最干净，但每屏多 ~25 秒，
且预览重启本身是崩溃诱因之一。

---

## 8. 检查清单（复制到任务里用）

无人值守跑 Cocos 编辑器任务前：

- [ ] 正确端口的ensure脚本返回OK且CDP/MCP工程身份一致；不是只查TCP
- [ ] `Editor.Package.getPackages()` 确认在用的 MCP 包名（别猜）
- [ ] 游戏侧客户端已接入且本工程只读心跳有响应（pages是DADAPET案例命令）
- [ ] 批处理每项前做健康检查，崩溃走恢复链（编辑器 → MCP → **预览**）
- [ ] UI 清洁用 `closeAll` 且校验 `after`；清不掉的界面排到最后
- [ ] 要跟设计稿比对的部分用**运行态截图**，不用编辑器 prefab 截图
- [ ] 自定义命令**不得在没做事时返回 success**

---

## 附：本次实测环境

| 项 | 值 |
| --- | --- |
| 编辑器 | Cocos Creator 3.8.7，`C:\ProgramData\cocos\editors\Creator\3.8.7\CocosCreator.exe` |
| MCP 扩展 | `cocos-creator-mcp` v2.0.2（64 工具） |
| 工程 | `E:\DADAPET` |
| CDP 端口 | 9222（临时，仅本机） |
| MCP 端口 | 3000 |
| 退出规律 | 未确认通用阈值与根因，仅该项目多次报告 |
