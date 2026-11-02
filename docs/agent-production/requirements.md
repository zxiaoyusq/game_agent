# 游戏生产工作流与彩球融合项目验收

更新日期：2026-10-18。四阶段均已完成并确认；最终测试运行 `55e9686f786549dca69744c10526547a` 实际重做构建、规则与浏览器检查，最终审计退出 0，`passed=true`、`errors=[]`。下表说明证据及适用范围，未覆盖项保留在文末。

本文件保留该次彩球成品验收时的知识库规模与 Skill 版本。后续跨品类配置、当前知识库及 Skill 演进见 [流程复用记录](reuse.md)，不改写本次运行采用的历史版本。

## 目标与范围

研发工作台采用 **原型定义 → 美术资源 → 代码与集成 → 测试验收** 四阶段。原型定义包括定位、需求、策划和玩法原型；交付与运营不单独设为本轮阶段。后端使用真实 DeepAgents，经本机已登录的官方 Codex 调用 `gpt-6.1-sol`。

真实项目为「彩球融境 · Ball Sort Fusion」，标识 `0a850241a9fc4bee925af55617fead85`，工作区为 `games/ball-sort-fusion`，游戏画面名称为「彩球工坊」。它融合 Guru、HM、Infinite Joy 三款 Ball Sort 的已核实规则、关卡与资源，以官方 Cocos 引擎制作独立 Web/H5 游戏。

知识库增加与美术同级的 Skill 分类，导入公司资料与工程已有两项技能；生产过程新增 Cocos 技能并保留修订记录。原始参考包、用户已有工程修改和历史失败证据均保留。

## 验收矩阵

| 要求 | 已取得的证据 | 状态 |
| --- | --- | --- |
| Skill 分类与完整资料导入 | 9 个技能包、25 个 `SKILL.md` 入口、375 个文件；公司 6 包、原工程 2 包及新增 Cocos 包；原文、源码、支持文档、附件与搜索均有浏览器检查 | 已通过；见 [界面记录](../../logs/workflow-ui-final-review.json) |
| 四阶段界面 | 创建项目、阶段聊天、真实运行状态、报告、产物归属、事件数、预览与移动端布局；无模拟百分比进度 | 最终四阶段完成状态、101 条测试事件、报告和归因均可见；见 [最终界面复验](../../logs/workflow-ui-final-acceptance.json) |
| DeepAgents 与指定模型 | `create_deep_agent`、`FilesystemBackend`、SQLite 检查点；官方 Codex 登录和模型列表核验；模型输出结构化工具意图，实际工具由 DeepAgents 执行 | 四阶段真实调用均已核对；见 [最终审计](acceptance.json) |
| 持久状态与运行生命周期 | 运行、事件、产物及确认保存；真实失败后同检查点恢复；取消实际进程组；同一工作区及父子路径互斥 | 已通过后端回归、独立复验及 [界面生命周期检查](../../logs/workflow-ui-lifecycle.json) |
| 阶段交接与证据门禁 | 已确认上游报告、清单、资源哈希和代码指纹对应归档；上游重跑使下游确认失效；验证后改源码必须重验 | 已通过；见 [后端独立审阅](review.md) |
| 原型定义 | 三款参考、融合规则、100 经典／12 高管／20 迷雾、自由选关、主题、输入与存档约定、验收项 | 已完成并确认；见 [原型报告](../../games/ball-sort-fusion/workflow/prototype.md) |
| 美术资源 | 28 份原始素材：25 PNG 与 3 WAV；每项保留源路径、SHA-256、用途和运行时映射；实际文件及规格已复核 | 已完成并确认；见 [美术报告](../../games/ball-sort-fusion/workflow/art.md)、[清单](../../games/ball-sort-fusion/workflow/art-manifest.json)、[独立复核](art-review.json) |
| 官方 Cocos 引擎 | 正式 3.8.8、固定提交与归档哈希；6340 个源码文件比对；实际构建与浏览器 `cc.VERSION=3.8.8`、WebGL2、活动场景及绘制调用 | 已通过；见 [引擎证据](../../games/ball-sort-fusion/evidence/engine-build.json) |
| 可玩游戏及规则 | 132 关完整解法回放；批量移动、动画、撤销、重开、Worker 提示、加管、存档、数字辅助、音效、三主题与三模式 | 代码及最终测试阶段均通过 9 项规则／存档测试及 26 条浏览器检查 |
| 问题修复与真实输入 | 覆盖当前局确认、节点销毁、迷雾遮蔽、版本与历史校验、命中区、截断历史、存储失败反馈、完成局主题及过期结算均经回归 | 已通过；见 [游戏审阅](game-review.md)、[最终边界](game-review-final-boundaries.md)、[异步与存储边界](game-boundary-review.md) |
| 恢复后重新验证 | 代码运行恢复至 attempt 2，重新执行 `npm run build`、`npm test`、`npm run check`，均退出 0，验证前后与最终源码指纹一致 | 已通过；见 [当前代码报告](../../games/ball-sort-fusion/workflow/code.md) |
| 最终测试验收 | 新测试运行实际读取 Cocos 1.4.2 和公司 Cocos QA 技能，独立重做构建、规则及浏览器检查，复核已有独立证据与未覆盖范围 | attempt 1 三条命令均退出 0，已完成并确认；见 [最终测试报告](../../games/ball-sort-fusion/workflow/test.md) |
| Skill 持续沉淀 | Cocos 技能由 1.0.0 迭代至 1.4.2；真实阶段 `save_skill` 记录原因、前后正文及哈希；源与知识库一致，结构校验通过 | 已通过；见 [技能演化](skill-evolution.md)，1.4.2 原文已在最终界面复验中确认可见 |
| 后端回归 | `python -m unittest tests.test_workflow tests.test_skill_library -q`，覆盖导入、恢复、互斥、交接、确认、取消与写入证据 | 24 项通过；见 [后端说明](../../backend/README.md) 与 [独立审阅](review.md) |
| 可复现构建与运行 | 依赖锁定、官方引擎准备、构建、规则及浏览器命令齐全；浏览器测试自动启动临时静态服务并关闭，不依赖固定开发端口 | 已实现并执行；见 [游戏工程说明](../../games/ball-sort-fusion/README.md) |
| 分发包与最终审计 | Web ZIP 含 39 个文件，逐字节对应最终 `dist`；脚本校验四阶段确认、模型调用、Skill 读取、产物、资源、源码和分发包 | 已通过；[最终审计](acceptance.json) 的 `passed=true`、`errors=[]` |

9 项规则测试包含 132 关解法回放；`npm run check` 会再次执行这些规则测试再执行浏览器检查，不能把同一批测试重复计数。独立边界检查另有 10 项通过、2 项后台冻结未覆盖，不能写成 12 项全部通过。

## 知识库包含的内容

公司资料包括 AI 美术自动化、AI 生图与换皮、游戏逆向与二次开发、外部视觉路由、Spine 动画流水线、ImageGen 角色与 Spine 动画 6 包。其中游戏逆向包有主入口及 16 个子模块。工程原有 APK 工程拆解与资源分析、游戏竞品拆解与融合设计 2 包，本轮新增 Cocos 游戏生产与验收包。

导入内容除 `SKILL.md` 外，还包括参考说明、流程文档、提示词模板、工具和 MCP 服务源码、配置、样例与附件；公司总说明及独立 ZIP 放在「公司资料」中。导入本身只复制和登记资料，不执行包内脚本。常规导入只补缺，并尊重知识库中的删除及已有元数据；明确的 Skill 修订通过发布流程同步，保留前后版本。

## 最终运行与恢复记录

| 阶段 | 当前运行标识 | 当前状态 |
| --- | --- | --- |
| 原型定义 | `9816ef2fbc0742b9977df94b0e31dad6` | 已完成并确认 |
| 美术资源 | `84b18017296a472db5b0a04472598359` | 已完成并确认 |
| 代码与集成 | `5be7ad3a11084952a3af39028c2d1f13` | attempt 2 已完成并确认 |
| 测试验收 | `55e9686f786549dca69744c10526547a` | attempt 1 已完成并确认 |

阶段确认由编排 Agent 依据用户授权、真实报告及独立证据完成，不表述为用户逐项手动签字。执行标识保存在 [会话记录](../../logs/ball-sort-workflow-session.json)，完整事件、快照及 SQLite 检查点位于 `backend/data/workflow/`。

首次原型运行 `a58defd096644d6b80b21ddf78c35487` 暴露 Skill 附件读取限制，修复后从原检查点恢复。原型修订中发现同文件并发编辑竞争，模型回读修复，后端增加每运行 I/O 锁及真实并发回归。当前代码运行遇到原执行步数上限后继续同一检查点，恢复提示显式传递 attempt，执行上限调整为 150；attempt 2 重新构建与验证后才完成，未借用前一次成功放行。

代码 attempt 2 和最终测试 attempt 1 的构建、规则测试与浏览器检查均对应源码指纹 `cd2345379dbd13b880db0eaa8d5ea78492659b9f1af3bba216fc5a54be0a5f45`，每条命令执行前后与最终状态一致。它是验证工具计算的源码、资源、引擎与测试输入指纹，不是 Git 提交。旧代码运行的 8／22、9／24 结果及旧测试运行 `92489d4b393f476a80f1fad62f0b292e` 保留作历史，没有替代当前最终测试。

模型实际工具写入、验证命令产生的变化、引用资源和工作区观察快照分别记录归属。旧原型具有真实成功编辑消息，但没有后续版本才加入的逐次写后哈希，不倒推补造文件作者证明。

## 输入、交付与复核入口

- 环境：Python 3.13.11（conda base）、DeepAgents 0.5.9、Codex CLI 0.162.1、Node.js 22、Playwright 1.63.0 / Chromium 153.0.8010.12。
- 引擎：官方 Cocos Engine 3.8.8，提交 `411f98df047c25902f93440d4b22925c2fb65461`；正式版本核验日期为 2026-10-18，开发分支不作为正式发布依据。
- 关卡：100 经典、12 高管（六层与八层各 6）、20 迷雾；迷雾复用经典棋盘并改变信息可见性，不称为 20 个全新原创棋盘。结构与内容复核见 [内容检查](content-review.json)。
- 资源：Guru 12 张球图、Infinite Joy 12 张球图、HM 1 张试管图与 3 个 WAV；原文件字节保留，运行时缩放和播放。引用资源的来源可追溯，不据此推断商业授权。
- [本地工作台](http://127.0.0.1:15173/)；[实际游戏预览](http://127.0.0.1:8003/api/workflow/projects/0a850241a9fc4bee925af55617fead85/preview/index.html)。这些地址要求本机服务正在运行。
- [Web 分发包](../../games/ball-sort-fusion/releases/ball-sort-fusion-web.zip)；[打包记录](../../games/ball-sort-fusion/evidence/web-package.json)。

完整原始统计来自三款材料的 `analysis/level_summary.json`：Guru 有 18,536 条记录，HM 有 1,016 条记录（1,013 条非空），Infinite Joy 有 16,458 条记录（7,348 个唯一棋盘）。最终选取的 132 关已按实际球序、批量移动语义及合法解法重新验证。逆向材料和方法职责是重建输入，不等于可直接运行的原始源码。

四阶段全部确认后，已在工程根目录执行以下只读审计，退出 0。复核时可再次执行：

```bash
conda activate base
python docs/agent-production/audit_workflow.py
```

脚本只核对已存在的运行与文件，不补写成功状态。[审计结果](acceptance.json) 中 `passed=true`、`errors=[]`，包括当前报告和归档一致、上游交接哈希、当前 attempt 验证指纹、28 份资源、引擎运行时及分发包一致性。[最终界面复验](../../logs/workflow-ui-final-acceptance.json) 另确认四阶段完成、报告与 Skill 1.4.2 可见、真实 Cocos iframe 正常、390 像素视口无横向溢出，页面错误与写入请求均为空。编排 Agent 另打开本轮移动端与浅色设置截图复核可见布局，没有把截图检查解释为真人审美或听感验收。

## 已知验收边界

- 工作流运行于可信本机、单用户、单后端进程。项目脚本使用服务账户权限；当前没有多租户鉴权或进程隔离沙箱，不能把本次验收解释为可直接公开给不可信调用方的生产服务。
- 游戏是官方引擎源码编译的独立 Web/H5 工程；没有 Creator GUI 或 `.scene` 编辑器工程验收，未验证 Android/iOS 原生构建。
- 自动化覆盖 Chromium 的真实页面与模拟视口，没有验证实体手机、Safari、多指硬件或所有长期压力场景。
- 两项后台冻结恢复用例无法在当前无头环境证明真正冻结，明确为未覆盖；已有动画中刷新检查不能替代它们。
- 真人教学效果、迷雾体验、主观美术及音效评价未用自动化结果替代。实际素材、引擎和行为验证通过不等于人类主观试玩已经完成。

## 官方依据

- [Cocos Engine 3.8.8](https://github.com/cocos/cocos-engine/releases/tag/3.8.8)
- [Codex App Server](https://learn.chatgpt.com/docs/app-server)
- [Codex 非交互执行](https://developers.openai.com/codex/noninteractive)
- [DeepAgents 定制](https://docs.langchain.com/oss/python/deepagents/customization)
- [DeepAgents 存储后端](https://docs.langchain.com/oss/python/deepagents/backends)
