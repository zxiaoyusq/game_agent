# 琥珀商路 · Amber Caravan

一款以摩洛哥绿洲商旅为主题的原创 Ludo H5。根据用户提供的 Just Ludo 与 Ludo Superstar 本地包研究重构，融合经典四子归家、吃子解锁快局、策略电脑、同屏对战与自动续局；背景、棋盘、棋子、界面和反馈均为新设计。

线上试玩：[手机与电脑直接打开](https://pagent.ahagamecenter.com/games/amber-caravan/index.html)。部署与后续更新方式见 `workflow/deployment.md`。

## 直接运行

交付中已有 `dist/`。不需要模型、MCP、服务器账号或 Multica；任选一种静态 HTTP 服务即可游玩：

```sh
# 在本工程目录，使用 Python 3 的本地静态服务
python -m http.server 8124 --bind 127.0.0.1 --directory dist
```

打开 http://127.0.0.1:8124 。手机/其他电脑体验可把 `dist/` 上传到自己的 HTTPS 静态站点；所有资源是相对路径。`file://` 直接双击不适合 ES 模块，请通过 HTTP 打开。

游戏资源全在本包，载入后对局无需联网。没有在线匹配；“好友同屏”表示同一设备上轮流操作。存档只属于当前浏览器与域名，换域名不会同步。

## 开始玩

1. 选择「疾风商路」或「经典远征」，选择 2/3/4 人，再选人机或好友同屏。
2. 点击骰子；再点发光的棋子，或点下面的编号按钮。
3. 六点出营；安全星形格免吃；普通格吃掉单枚敌棋。六点/吃子/归家可以再掷，第三个连续六点结束回合。
4. 经典需要四子归家。快局预出两枚，必须吃一子打开归家路线，第一枚精确抵达终点即胜。
5. 顶部「?」查看完整规则，设置可关闭声音或打开快速节奏；暂停、返回大厅、刷新均可继续上次旅程。

## 开发与验证

使用 Node.js 22+（构建/测试）与 Python 3.13（打包）。运行时没有第三方依赖；Playwright 仅用于开发验收。

```sh
npm ci
npx playwright install chromium  # 首次使用且没有对应浏览器时执行
npm run build
npm test
npm run check
npm run serve
npm run release
```

`build` 生成 `dist/index.html`；`check` 启动临时本地服务并真实点击完整对局，不依赖常驻服务。端口默认为8124，可用 `PORT=其他端口 npm run serve` 更改。

`release` 生成：

- `releases/amber-caravan-web.zip`：纯静态网页，上传解压内容即可部署。
- `releases/amber-caravan-project.zip`：完整源码、实际资源、构建、测试、报告及截图。
- `releases/size-report.json`：文件数量、ZIP/展开字节和SHA256；两个包压缩前后均强制不超过10,000,000字节。

开发安装产生的 `node_modules`、两份原始参考ZIP、生图PNG母版和重复发布包不进入交付；完整工程仍包含锁文件，能独立重建，不依赖原包或本机路径。

## 模块与证据

| 文件 | 职责 |
|---|---|
| `src/rules.mjs` | 出营、路径、吃子、锁门、回合、胜负与存档校验 |
| `src/ai.mjs` | 对合法动作评分，不控制骰子 |
| `src/board.mjs` | SVG棋盘、宝石棋子、路径预览与逐格动画 |
| `src/app.mjs` | 界面、输入、随机骰子、暂停/恢复和AI计时器 |
| `src/storage.mjs` / `audio.mjs` | 可靠存储降级与实时合成音效 |
| `workflow/reference-analysis.md` | 两个原包的指纹、规则路径、优点与未知项 |
| `workflow/prototype.md` | 融合规则、新设计差异与验收要求 |
| `workflow/art.md` / `art-manifest.json` | 美术来源、用途与文件哈希 |
| `workflow/visual-review.md` | 原作与新作真实画面对照 |
| `workflow/test.md` | 实际验收结果与边界 |
| `evidence/` | 原作、新作、移动视口、结算截图与浏览器报告 |

## 已知边界

以现代桌面/移动浏览器为目标，已执行的环境以测试报告为准；没有声称已经做过 iPhone/Android 真机验收。移动端的庭院英文是次要装饰，关键状态在玩家牌卡与操作区重复呈现。审美提升有对照评审依据，不等于所有用户偏好都已验证。

所有可玩的模式、AI、规则、资源和音效均在本地，原厂在线匹配、广告、登录、付费、活动排行未迁移，也没有伪造对应入口。
