# 原型定义：Freestyle 红棋覆盖竞品证据与源码核对报告

## 1. 任务背景与核对范围

- **核对目标**：聚焦 **Freestyle 模式红棋覆盖（Queen Cover）** 单一机制，核对两份证据文档与 D201 游戏代码。
- **核对范围与文件**：
  1. `mcp-inputs/mac-codex/d8e1a0b421927f19767297d450a93cd464bb49b6e9a14e3de5635afd05a3a196/freestyle-local-evidence.md`（本地竞品录像抽样与操作记录摘要）
  2. `mcp-inputs/mac-codex/826cb9adc09939cacd457460640d8c22f08c88ef59a0b085260c0008a478a5d2/three-mode-evidence.md`（三模式规则页面与当前代码对照）
  3. `mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js`（D201 项目代码）
- **客观原则声明**：严格区分本地作者转述与本轮未提供的原视频文件；本轮未获得任何实际 MP4/PNG 视频流，不得也不声称亲眼见过实机或视频。不修改游戏代码、不修改界面。

---

## 2. 证据锚点清单（逐文件提取）

### 2.1 freestyle-local-evidence.md 中的证据锚点
- **锚点 1（离线传玩 Freestyle Disc Pool 盘面无红子）**：
  - 位置：`freestyle-local-evidence.md:1–25`
  - 内容：转述 MuMu 竞品（19.6.0 / 1491）在断网传玩模式下截取的 24 枚棋子为黑 12、白 12，**未见红子（Queen）**。顶部虽然有红白黑图标与数字，但作者明确指出“顶部的红色图标不能直接视为盘面已有红子或已知分值”。
- **锚点 2（联网 Delhi Freestyle 开局有红子）**：
  - 位置：`freestyle-local-evidence.md:9–15`
  - 内容：转述联网 Delhi Lounge Freestyle 开局显示 9 黑、9 白及中心红子（红 50、黑 10、白 20）。
- **锚点 3（红棋覆盖相关视频证据缺失声明）**：
  - 位置：`freestyle-local-evidence.md:50–55`
  - 内容：作者明确说明“不能将此盘面当作 Carrom 红球覆盖证据”、“必须补采进白子、进黑子、同杆多子、红色图标含义和目标临界结算的视频，再决定最终规则”。文档后续所有实测仅针对黑子进袋（+10）、白子进袋（+20），**没有任何一段录像或截图完成了 Freestyle 红棋进袋及其覆盖/返场的实际触发**。

### 2.2 three-mode-evidence.md 中的证据锚点
- **锚点 4（竞品 Freestyle 规则页面文案）**：
  - 位置：`three-mode-evidence.md:9–15`（模式规则表格）及截图引用 `../03_运行证据/模式调研_Freestyle规则.png`
  - 内容：竞品规则页面中明确写道：“**每种球分值不同，红球入洞需覆盖，先到目标分数获胜；入洞续杆，未入或犯规结束回合。**”
- **锚点 5（当前项目本地 Freestyle 规则素材文案）**：
  - 位置：`three-mode-evidence.md:14` 及引用素材 `tut_05_screen_design.png`
  - 内容：本地 Freestyle 规则图描述了分值、目标分、续杆和犯规换手，**明确没有列出红球覆盖**。
- **锚点 6（静态代码分析指出的高优先级风险）**：
  - 位置：`three-mode-evidence.md:18–26`
  - 内容：文档指出当前代码 `game.js:4833–4845` 在 Queen 进袋时设置 `_0x4268e2=true`，并在 mode 2 放入本杆收集数组 `_0x31089b`；而在回合判定 `game.js:3159–3169` 进入 mode 2 分支后立即将 `_0x4268e2=false`，并在 `3170–3277` 对棋子直接计分。文档指出这存在“红球未覆盖也计分或不返场”的高风险，但注明“尚未通过实际红球入袋→未覆盖→换手的试验，不能宣布已经确认缺陷”。

### 2.3 D201 源码（carrom-current-d201.js）中的证据锚点
- **锚点 7（Freestyle 状态初始化与 Queen 状态机变量）**：
  - 代码行/位置：全局变量区及 `_0x5480e3()`（重启/开局重置函数）
  - 核心定义：
    - `_carromFreestyleQueenState = {phase: 'board', owner: null};`
    - `_carromFreestyleHistory = [];`
    - `_carromQueenClearedThisShot = false;`
    - `_0x4268e2 = ![];`
- **锚点 8（结算入口与暂定覆盖逻辑：`_0xbdafb3` 中的 mode 2 分支）**：
  - 代码位置：`carrom-current-d201.js` 结算函数 `_0xbdafb3()`
  - 核心逻辑：
    1. 统计当前杆进袋：
       ```javascript
       let _carromQueenShot = {
         actor: _0x209883 ? 'player' : 'opponent',
         foul: !!_0x530863,
         queen: _0x3daed1.some(function (disc) { return disc._type === 0; }),
         ordinary: _0x3daed1.filter(function (disc) { return disc._type === 1 || disc._type === 2; }).length
       };
       ```
    2. 进袋给分机制：若红棋进袋（`_carromQueenPrecredited`），立即计入分值（`_0x1c2aac[0]` 即 50 分）并压入 `_carromFreestyleHistory`；
    3. 调用规则状态机决策：
       ```javascript
       var queenDecision = window.CarromDiscRules.freestyleQueen(_carromFreestyleQueenState, _carromQueenShot);
       if (queenDecision.returnQueen && !_carromReturnFreestyleQueen(queenDecision.revokeOwner)) return;
       if (queenDecision.state.phase === 'pending' && _carromQueenShot.queen) queenDecision.state.points = _0x1c2aac[0];
       _carromFreestyleQueenState = queenDecision.state;
       ```
    4. 红棋返场与扣分回退实现（`_carromReturnFreestyleQueen`）：
       若判定需返场（`returnQueen`），从 `_carromFreestyleHistory` 查找历史记录并扣减已加的 50 分，重新生成 Queen 放回桌面中心（`_0x4efd2a` 坐标）。
    5. 残留旧分支清理：
       ```javascript
       if (_0x4268e2 && !_0x5ebd99) {
         (_0x52e61d(), (_0x4268e2 = ![]));
         if (_0x209883) _0x4d3bf1 -= 0x32;
         else _0x41f634 -= 0x32;
         ...
       }
       ```
    6. 代码注释标注：“`// Provisional Freestyle policy: competitor edge cases need runtime evidence.`”（临时 Freestyle 策略：竞品边界情况需要运行时证据）。

---

## 3. 核对结论分类

### 3.1 确认项（Confirmed）
1. **规则页面文案存在明确冲突**：
   - 竞品 Freestyle 规则页面（截图 `../03_运行证据/模式调研_Freestyle规则.png`）明确记载“**红球入洞需覆盖**”。
   - 本地前端规则展示图（`tut_05_screen_design.png`）中**完全没有红球覆盖要求**。
2. **D201 代码已实现 Freestyle 红棋覆盖状态机（provisional 阶段）**：
   - D201 并非完全缺失红棋覆盖，而是通过 `window.CarromDiscRules.freestyleQueen`、`_carromFreestyleQueenState`、`_carromFreestyleHistory` 和 `_carromReturnFreestyleQueen` 实现了“先预给分、待下一杆覆盖验证；若未覆盖则返场并扣减 50 分”的状态转移逻辑。
3. **分值体系在同场馆（Delhi Lounge）一致**：
   - 竞品 Delhi Lounge Freestyle 与当前代码/界面一致：红 50、白 20、黑 10，目标分 160。

### 3.2 冲突项（Conflicted）
1. **规则展示 vs 规则代码**：
   - 当前项目的玩家规则引导/教程素材 `tut_05_screen_design.png` 向玩家传达的信息是“无覆盖要求直接计分”，而 D201 底层代码却引入了 `freestyleQueen` 状态机与返场扣分机制，存在玩家认知与代码结算的不一致。
2. **竞品离线传玩 vs 竞品联网 Delhi 盘面**：
   - 竞品离线传玩 Freestyle Disc Pool 盘面仅有 24 枚黑白棋，**无红棋**；而联网 Delhi Freestyle 盘面为 9 黑 9 白 1 红。离线模式下无红棋即不存在红棋覆盖；联网模式下有红棋且规则页声称需覆盖。两者在竞品内部属于不同入口规则分支。

### 3.3 未知 / 不可判定项（Unknown / Indeterminate）
1. **竞品 Freestyle 红棋进袋及覆盖的真实运行表现（无法判定）**：
   - 证据文档转述的所有本地录像中，**均未记录到任何一次红棋进袋后的下一杆覆盖或未覆盖实机过程**。
   - 本轮未提供任何实机视频流或原视频文件，不能声称亲眼见过。
   - 竞品是否确实在 Freestyle 运行态执行了严格的红棋返场、扣分、同杆覆盖、犯规返场机制，仍属于**不可判定项**。
2. **`window.CarromDiscRules.freestyleQueen` 的外部具体实现细节（不可判定）**：
   - 在 `carrom-current-d201.js` 中，该规则函数挂载在外部 `window.CarromDiscRules` 上，其内部状态转移表、同杆普通球是否可覆盖、母球犯规时红球返场顺序等边界实现未内联在当前单个 js 文件中。
3. **竞品在未覆盖返场时的计分时机（不可判定）**：
   - 竞品是“进袋暂不加分，覆盖成功才加 50”，还是 D201 采用的“进袋先加 50，覆盖失败再扣 50”，因缺乏真实视频及对局网络包证据，目前无法判定。

---

## 4. 文件与代码位置索引表

| 检查维度 | 文件路径 | 行号 / 位置 | 证据状态 | 核心内容与结论 |
|---|---|---|---|---|
| 竞品离线盘面无红棋 | `freestyle-local-evidence.md` | 第 1–25 行 | 作者转述证据 | 离线传玩 Freestyle 盘面识别 24 子（黑 12、白 12），无红棋 |
| 竞品规则页要求覆盖 | `three-mode-evidence.md` | 第 11–15 行 | 截图转述证据 | 竞品规则页明确载明“红球入洞需覆盖” |
| 本地教程未提覆盖 | `three-mode-evidence.md` | 第 14 行、素材 `tut_05_screen_design.png` | 本地资源证据 | 当前项目规则素材省略了红球覆盖说明 |
| D201 红棋状态机定义 | `carrom-current-d201.js` | 全局定义及 `_0x5480e3` | 源码事实 | 定义 `_carromFreestyleQueenState`，初始化为 `{phase:'board', owner:null}` |
| D201 红棋覆盖判定与返场 | `carrom-current-d201.js` | `_carromReturnFreestyleQueen` 与 `_0xbdafb3` 内结算分支 | 源码事实 | 实现了临时状态机驱动的 Freestyle Queen 覆盖、未覆盖扣分返场 |
| 竞品实机覆盖视频 | 无（未提供） | 无 | 缺失 | **无原视频提供，不可判定真实竞品运行态表现** |

---

## 5. 原型定义阶段结论与后续建议

1. **维持代码与界面不修改**：本轮明确指令为仅核对证据与代码，不要写游戏、不要修改界面。因此不对 D201 做任何代码和资源改动。
2. **原型决策建议**：
   - 待后续获得竞品红棋进袋、覆盖成功、未覆盖返场、同杆入袋等完整连续视频或抓包证据后，再明确是否需要同步更新教程素材 `tut_05_screen_design.png` 与对齐 `CarromDiscRules.freestyleQueen` 状态转移边界。
