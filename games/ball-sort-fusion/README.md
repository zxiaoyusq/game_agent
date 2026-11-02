# 彩球工坊

已完成的 Cocos Web/H5 彩球分类游戏。100 个经典关卡、12 个长管挑战（6 个六层、6 个八层）、20 个隐藏球关卡，所有交付关卡都有逐步回放通过的合法解法。支持连续同色批量移动、抛球动画、音效、撤销、重开、Worker 提示、辅助空管、浏览器进度存档、数字辅助与 3/6 星解锁主题。

## 直接运行

当前工作区已经构建好 `dist/`，可直接使用 HTTP 静态服务运行：

```bash
cd /root/dev/game-agent/game_agent/games/ball-sort-fusion
npm run serve
```

打开 [本地游戏](http://127.0.0.1:8123)。后端集成可将 `dist/` 挂载为静态目录；它不依赖 API、账户或远程模型，模型只参与生产流程。

## 构建与验收

使用 Node.js 22+、npm、curl、tar 和系统 Python。引擎构建采用官方 Cocos Engine 3.8.8 源码与官方 `@cocos/ccbuild`；不是 `cc` 兼容层，也不是自制 Canvas 游戏。实际画面由 Cocos 的 Scene、Camera、Canvas、Graphics、Sprite、Label、Tween 与输入系统绘制；音效由 Cocos AudioSource 播放。

```bash
npm ci --ignore-scripts
npx playwright install chromium
bash scripts/setup-engine.sh
npm run build
npm run check
```

`npm test` 为快速规则与存档测试；`npm run test:browser` 会自动启动随机端口的临时只读静态服务，通过真实 Chromium WebGL2 和鼠标点击验收，结束后关闭服务。也可以使用 `GAME_URL=http://127.0.0.1:8000/具体预览路径/ npm run test:browser` 验收后端实际预览地址。

源码缓存默认位于 `~/.cache/cocos/cocos-engine-3.8.8`，可以通过 `COCOS_ENGINE_PATH=/自定义路径 bash scripts/setup-engine.sh` 指定。`COCOS_ENGINE_ARCHIVE` 可以单独指定源码压缩包位置。直接执行 `COCOS_ENGINE_PATH=/已安装的源码 npm run build:engine` 也支持自定义路径，不要求源码父目录存在压缩包；缺少压缩包时证据中的 tarball 哈希记为 `null`；没有实际 Git HEAD 或匹配的官方归档证明时，提交 ID 也记为 `null`。

如需重新抽取关卡与参考素材，在仓库保留 `ref/BallSort工程拆解_2026-10-01` 的前提下执行 `node scripts/prepare-reference.mjs`。它会重新逐关回放验证并生成来源清单。

## 固定引擎与已验证的构建路径

2026-10-18 联网查询 [Cocos 官方下载页](https://www.cocos.com/creator-download) 与 [官方最新正式 Release](https://github.com/cocos/cocos-engine/releases/latest)，正式发布版本为 **3.8.8**。默认开发分支上的其他版本号不作为稳定发布依据。

- 官方标签：`3.8.8`。
- 固定提交：`411f98df047c25902f93440d4b22925c2fb65461`。
- [官方源码压缩包](https://codeload.github.com/cocos/cocos-engine/tar.gz/refs/tags/3.8.8) SHA256：`8af14ad3f861b9edd1d90c928a676ccaec4d9ec6d0bce42f56c59c9b3a82afa5`。
- 已实际构建的官方构建器：`@cocos/ccbuild 2.3.23`；完整依赖固定在 `scripts/engine-package-lock.json`。
- 独立源码必须先运行官方 `build:debug-infos`，否则会报无法解析 `DebugInfos`。构建脚本已自动执行该生成器。
- 2D Web 包必须显式包含 `legacy-pipeline`，否则真实 Cocos 会报 1223/1222，Canvas 无法取得 Batcher2D。已修复并通过浏览器验收。
- 独立运行时没有 Creator 导入数据库，因此注册官方测试夹具中的 2D Effect 元数据，并根据同版本官方 Shader 展开 Uniform 和 2D GLSL。出处与 SHA256 位于 `evidence/shader-sources.json`，生成脚本为 `scripts/prepare-effects.mjs`。

这里交付的是**官方引擎源码编译的独立 Web 游戏工程**，目前支持 Web/H5。没有使用 Creator GUI，没有 `.scene` 编辑器场景文件，也未验证 Android/iOS 原生打包；不能把这个目录描述为已通过 Creator 编辑器打包的项目。

## 三款参考的实际融合

完整来源、SHA256、用途与加工记录见 `evidence/source-manifest.json`，并见 `evidence/fusion-design.md`。三款原始工程都是 Unity，规则与场景重建为 Cocos：引用反汇编的静态方法职责不等于恢复或移植完整原始源码。

- Guru：96 个经典关卡及原始解法、12 种玻璃珠材质；参考 `TubeData.CanImport` 与 `TopBallSameCount` 的职责，使用纯函数规则重写。
- HM：6/8 层高管关卡及原始解法、玻璃管材质、点击/移动/满管 WAV；参考 `LevelSprite.UndoMove`，通过完整局面快照实现撤销。
- Infinite：4 个开场关卡、12 种主题球材质、隐藏球设计；参考异步 Hint 职责，由离线 Worker 求解。

Guru/HM 的标准化关卡是**管口到管底**，加载时必须倒序；本项目数组统一为管底到管口。连续同色球必须批量移动，才能完整回放原始解法。原图像素和 WAV 内容保留，仅在 Cocos 中缩放与控制播放音量。

## 验收证据

`evidence/engine-build.json` 保存引擎构建信息、最终 cc.js SHA256、实际 Git HEAD 或归档逐文件比较结果（本例 6340 个源码文件匹配，仅排除明确替换的依赖锁）；`evidence/level-validation.json` 保存 132 关解法回放结果；`evidence/browser-validation.json` 保存实际引擎版本、活动场景、WebGL2 设备、draw call 与浏览器验收结果。对应截图包括经典、六层、八层、迷雾、结算、浅色主题、390×844 移动端和 1440×900 宽屏。

操作开始前先提交完整逻辑局面与存档，动画只显示临时快照。按钮在动画期间锁定。存档逐字段校验，损坏的索引、进度、球数、容量或历史不会导致启动崩溃，恢复时显示中文反馈。重复通关按关卡 ID 更新最佳成绩，不重复发星。
