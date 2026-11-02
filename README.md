# 游戏 Agent 系统

后端使用 FastAPI，运行在 Conda `base` 环境；前端使用 Vue 3 和 Vite。

## 游戏生产工作流

研发工作台使用四阶段：**原型定义 → 美术资源 → 代码与集成 → 测试验收**。
项目、运行、事件、产物快照和确认状态保存在后端；任务由 DeepAgents 实际执行，模型通过本机官方 Codex 登录调用 `gpt-6.1-sol`。
启动前按 [后端说明](backend/README.md) 安装依赖并检查 `codex login status`。当前执行服务按可信本机、单后端进程运行，具体执行边界见后端说明。

- [目标与验收依据](docs/agent-production/requirements.md)
- [四阶段最终审计](docs/agent-production/acceptance.json)
- [Skill 迭代记录](docs/agent-production/skill-evolution.md)
- [Cocos 游戏工程](games/ball-sort-fusion/README.md)
- [跨品类复用与知识组织](docs/agent-production/reuse.md)

工作台选中的 Skill 来自知识库“Skill”分类；每个运行保留实际读取的版本哈希。只有真实产物及所需检查通过后，阶段才进入评审确认；重新运行上游会使下游确认失效。

知识库中的“Skill”与美术等模块同级，已导入公司 6 包、工程原有 2 包及新增 Cocos、通用休闲游戏生产包，共 10 包、26 个技能入口、376 个文件。界面可搜索、阅读技能与支持文档、查看脚本源码和下载附件；导入资料不会执行包内脚本。

另有“游戏品类”和“技术框架”两类知识：7 份品类指南、4 份技术指南。新建项目选择品类和技术方案，可查看基础资料并补选知识；实际运行冻结配置、正文与哈希，按所选品类制定验收。当前执行接口覆盖 Cocos Web 和 Canvas 2D Web，完整成品验收案例仍为 Ball Sort；其它引擎须先适配构建和运行能力，不能仅凭文档收录视为支持。

当前 Ball Sort 项目提供 [本地游戏预览](http://127.0.0.1:8003/api/workflow/projects/0a850241a9fc4bee925af55617fead85/preview/index.html) 和 [Web 分发包](games/ball-sort-fusion/releases/ball-sort-fusion-web.zip)。游戏使用官方 Cocos Engine 3.8.8，共 132 关；四阶段已完成并确认，最终审计通过，后端 24 项、游戏规则／存档 9 项、浏览器 26 条检查通过。验证范围及未覆盖项见上方验收依据。预览地址依赖本机后端服务，独立运行及重新构建按游戏工程说明操作。

## 前置条件

- 已安装 Conda、Python 和 Node.js。
- 后端依赖已安装在 Conda `base` 环境中。
- 前端依赖已安装；首次启动时脚本会自动执行 `npm install`。

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
