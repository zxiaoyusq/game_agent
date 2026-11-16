# 归档.zip 游戏导入记录

来源：用户上传的 `归档.zip`。每款游戏的 `import-manifest.json` 记录原始归档 SHA-256、目录名和实际导入文件数。

| 上传目录 | 游戏库名称 | 状态 | 目录 |
| --- | --- | --- | --- |
| Arrow_Out_Puzzle_Lite | 箭头解谜 · Arrow Out Puzzle Lite | 可运行，Cocos 2.4.15 | `games/arrow-out-puzzle-lite` |
| Crazy_Knifes | 疯狂飞刀 · Crazy Knifes | 可运行，PlayCanvas 1.69.2 | `games/crazy-knifes` |
| Solitaire_Klondike_Classic | 经典接龙 · Solitaire Klondike Classic | 可运行，Phaser | `games/solitaire-klondike-classic` |
| Checkers_Pocket | 口袋西洋跳棋 · Checkers Pocket | 待补全游戏内容 | `games/checkers-pocket` |

Checkers Pocket 过滤 `.git` 和 macOS 附带项后只有 4 个文件：外层 `index.html`、`readme.md`、`game/index.html` 和 `game/index.js`。内层页面仅含“点击模拟插屏调用”和“点击模拟激励调用”两个按钮，没有棋盘、规则或资源。目录保留该条目并说明原因，未将广告测试页包装成可玩的西洋跳棋，也没有另造游戏替代。补齐真实运行包后会自动恢复运行按钮。

## 导入方式

- 原始有效文件保存在各游戏的 `source/`，未执行 `init_zy.sh` 或其他附件命令，未复制 `.git`、`.DS_Store`、`__MACOSX`。
- 三款完整游戏的 `game/` 整体复制到 `dist/game/`，保留相对路径、引擎、关卡、美术与音频；没有替换或改写玩法脚本。
- `dist/index.html` 与 `browser-host.js` 是本工作台的浏览器入口，替换运行版本的渠道广告外壳。原始外壳仍在 `source/index.html`，可以追溯。
- 浏览器入口不加载渠道广告或统计 SDK，不留空 Banner 条；仅处理同源且来自本游戏 iframe 的固定消息。广告不可用立即走失败回调，不阻塞主流程、不伪造激励完成。纸牌原本依赖激励广告的 Hint / Undo 在本预览环境不能通过观看广告获得，正常发牌和接龙可用。
- 后端允许 `.ccm`、`.plist` 等包内引擎资源，继续禁止工程私有文件、隐藏路径、目录穿越和符号链接。各游戏 `game.json` 只补充展示信息，不能指定任意外部运行地址。
- 游戏实际画面用于封面，保存为 `evidence/desktop-lobby.jpg`。游戏库以完整运行入口决定是否可玩，列表总数与可玩数量分别显示。

## 复现与验收

一次性导入脚本（目标目录已存在时拒绝覆盖）：

```bash
conda run --no-capture-output -n base python scripts/import_archived_games.py /路径/归档.zip
```

运行包原始内容和校验记录分别见各目录的 `source/`、`dist/`、`import-manifest.json`。验证命令在仓库根目录执行：

```bash
PLAYWRIGHT_MODULE=/tmp/bubble-ui-check/node_modules/playwright/index.mjs node frontend/scripts/check-imported-games.mjs
PLAYWRIGHT_MODULE=/tmp/bubble-ui-check/node_modules/playwright/index.mjs node frontend/scripts/check-produced-games.mjs
```

上传游戏检查通过真实网页按钮进入游戏库，再在内嵌窗口使用真实指针输入：箭头移出、飞刀跳跃、纸牌发牌。引擎状态只读用于断言，不注入局面或直接调用移动/通关函数。验收记录为 [imported-results.json](imported-results.json)，图片位于各游戏 `evidence/`。验证范围是浏览器加载和核心输入，不等于全部关卡通关、真实广告或 AHA 真机验收。
