# 游戏 Agent 系统

后端使用 FastAPI，运行在 Conda `base` 环境；前端使用 Vue 3 和 Vite。

网站统一通过登录后的全流程工作台创建和执行游戏项目，首页提供「全流程工作台」「知识库管理」
和「产出游戏」入口。旧版独立策划、美术、研发和运营页面及其专用接口已移除。
全流程仍共用模型调用、图片生成和知识库服务，已有项目记录与游戏文件保持原样。

## 游戏生产工作流

研发工作台使用四阶段：**原型定义 → 美术资源 → 代码与集成 → 测试验收**。
项目、运行、事件、产物快照和确认状态保存在后端；任务由 DeepAgents 实际执行。网页在创建项目及运行阶段时都可以选择「API Key 网关」或「Codex CLI（服务器登录）」。API 默认模型为 `gpt-6.1-sol`，也可选工程白名单中的 Claude、DeepSeek；Codex CLI 当前适配 `gpt-6.1-sol`。两种来源不自动回退。
启动前按 [API Key 全流程说明](docs/agent-production/deepagents-api-workflow.md) 配置服务器网关和密钥。当前执行服务按可信本机、单后端进程运行，具体执行边界见后端说明。

- [目标与验收依据](docs/agent-production/requirements.md)
- [四阶段最终审计](docs/agent-production/acceptance.json)
- [Skill 迭代记录](docs/agent-production/skill-evolution.md)
- [Cocos 游戏工程](games/ball-sort-fusion/README.md)
- [跨品类复用与知识组织](docs/agent-production/reuse.md)

工作台选中的 Skill 来自知识库“Skill”分类；每个运行保留实际读取的版本哈希。只有真实产物及所需检查通过后，阶段才进入评审确认；重新运行上游会使下游确认失效。

新运行默认由后端结合项目品类、技术框架、阶段与明确任务选择 Skill，工作台和 MCP 共用同一规则。界面显示原因和能力限制，可人工补充、排除或切为手动选择。运行开始时冻结入口及同包文本，Agent 按需读取，结束时核对完整正文与版本哈希；恢复继续使用原快照。品类差异由品类知识承接，Creator、采集、生图等文档不会自动安装或启用其外部工具。详见 [Skill 调用与自动选择](docs/agent-production/skill-routing.md)。

知识库中的“Skill”与美术等模块同级，截至 2026-11-11 收录公司 6 包及工程 5 包，共 11 包、31 个技能入口、492 份文件。本次同步 H5 换皮 2.0、托管小游戏生命周期 1.4 及相关参考，并将平台适配规则更新到休闲生产 Skill 1.3。界面可搜索、阅读正文、查看图片和脚本源码；HTML 示例可静态预览本地配图。Skill 页提供“检查来源更新”和显式同步，更新前备份旧正文，保留自定义标题、摘要、标签与已删除状态；正常启动只补新文件。

知识库的“公司游戏参考”独立读取 AHAgames，支持搜索、品类与本地包筛选、游戏详情和商店图查看；新建项目可直接选择其资料路径。当前目录为 74 款游戏、370 张商店图片，其中 2 款有本地原包、72 款缺包；页面以实际磁盘为准，并显示历史清单数量差异。“案例研究”还提供 OneConnectRe 等资料的单篇阅读与引用，远程 MCP 参考索引同步可见；案例工程不作为 Skill 整包导入。导入和浏览不执行包内脚本、不触发远程采集。

另有“游戏品类”和“技术框架”两类知识：8 份品类指南、5 份技术指南。新建项目选择品类和技术方案，可查看基础资料并补选知识；实际运行冻结配置、正文与哈希，按所选品类制定验收。当前执行接口覆盖 Cocos Web、Canvas 2D Web 与原生 DOM/SVG/Canvas Web。《琥珀商路》已使用工程 API Key / `gpt-6.1-sol` 完成原生 Web 棋盘游戏四阶段生产、测试及发布：[直接试玩](https://pagent.ahagamecenter.com/games/amber-caravan-api/index.html)，[配置、网页操作和真实验证记录](docs/agent-production/deepagents-api-workflow.md)。其它引擎须先适配构建和运行能力，不能仅凭文档收录视为支持。

当前 Ball Sort 项目提供 [本地游戏预览](http://127.0.0.1:8003/api/workflow/projects/0a850241a9fc4bee925af55617fead85/preview/index.html) 和 [Web 分发包](games/ball-sort-fusion/releases/ball-sort-fusion-web.zip)。游戏使用官方 Cocos Engine 3.8.8，共 132 关；四阶段已完成并确认，最终审计通过，后端 24 项、游戏规则／存档 9 项、浏览器 26 条检查通过。验证范围及未覆盖项见上方验收依据。预览地址依赖本机后端服务，独立运行及重新构建按游戏工程说明操作。

## 前置条件

- 已安装 Conda、Python 和 Node.js。
- 后端依赖已安装在 Conda `base` 环境中。
- 前端依赖已安装；首次启动时脚本会自动执行 `npm install`。

## 产出游戏

首页点击「产出游戏」即可选择并运行已有作品，支持搜索、页面内试玩、重新运行和新窗口打开。目前可玩作品包括彩球融境、两个琥珀商路版本，以及上传的箭头解谜、疯狂飞刀、经典接龙。Checkers Pocket 上传目录仅有广告测试模板，作为待补全条目保留，不提供伪造的游戏入口。切换游戏、结束试玩或返回首页会关闭原游戏窗口。

目录由后端实时读取 `games/<游戏目录>/dist/index.html` 与 `frontend/public/games/<游戏目录>/index.html`，同名产物去重并优先运行已分发版本；工作流记录或 `games/<游戏目录>/game.json` 补充游戏名称和品类。显式导入但缺少运行包的条目显示原因并禁用运行；未产出构建的普通需求项目及公司参考包不自动加入。新增 Web 构建后刷新列表即可查看，无需维护前端固定清单。

接口为 `GET /api/produced-games`，游戏资源限定在 `/api/produced-games/{id}/play/{资源路径}`。实现与浏览器验收说明见 [产出游戏验收](docs/produced-games/verification.md)。

## 启动

### 本地模式

仅供当前服务器本机访问，前端默认监听 `127.0.0.1:15173`：

```bash
./start.sh local
```

启动后访问：

- 前端：`http://127.0.0.1:15173/`
- 后端文档：`http://127.0.0.1:8003/docs`

### 域名模式

前端默认监听 `0.0.0.0:24681`，通过固定域名对外提供服务：

```bash
./start.sh domain
```

启动后访问：

- 前端：`http://pagent.ahagamecenter.com/`
- 后端文档：`http://127.0.0.1:8003/docs`

不传参数时默认使用域名模式：

```bash
./start.sh
```

域名模式要求入口代理或负载均衡将 `http://pagent.ahagamecenter.com/` 的请求转发到服务器的 `24681` 端口，且该端口未被其他服务占用。DNS 记录只解析地址，不配置端口转发；若直接通过域名连接服务器，需访问 `http://pagent.ahagamecenter.com:24681/`。

## 停止

```bash
./stop.sh local     # 停止本地模式
./stop.sh domain    # 停止域名模式
./stop.sh all       # 停止所有本项目进程
./stop.sh           # 等同于 ./stop.sh all
```

## 自定义端口或 Conda 环境

默认后端端口为 `8003`。可在启动时覆盖后端端口、前端端口或 Conda 环境：

```bash
CONDA_ENV=base BACKEND_PORT=8004 FRONTEND_PORT=15174 ./start.sh local
CONDA_ENV=base BACKEND_PORT=8004 FRONTEND_PORT=8080 ./start.sh domain
```

前端会自动将 `/api` 请求代理到当前设置的 `BACKEND_PORT`。

## 日志

运行日志位于 `logs/`，按启动模式区分：

- `logs/backend-local.log`、`logs/frontend-local.log`
- `logs/backend-domain.log`、`logs/frontend-domain.log`
