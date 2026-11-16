# AHA 接入评估与交付

评估日期：2026-11-04。目标工程按当前对话中的 `games/amber-caravan`（《琥珀商路》）进行分析；上传的 Solitaire 包按渠道接入参考处理。

## 结论

**可以接入。**《琥珀商路》是有完整源码的原生 Web H5 游戏，平台调用可以放在独立模块，接入埋点、插屏、激励广告、Banner 和生命周期不需要重写游戏规则或增加后端。激励广告的收益规则尚未确定；联网对战、账号、服务端校验奖励等能力需要独立设计，不能由 JS Bridge 接入自动获得。

本次完成的是附件分析、标准流程、可复用适配代码与 Skill，以及本地模拟验收。**尚未修改《琥珀商路》业务代码，尚未部署或在 AHA 真机验收。**正式游戏配置与奖励方案未提供，也未将样例的生产 ID 复制到游戏。由此报告不能理解为当前线上地址已经开始上报或展示广告。

## 上传材料实际内容

| 材料 | 检查结果 | 用途 |
| --- | --- | --- |
| Solitaire Klondike Classic.zip | 5 个条目：外层 index、readme、game 目录和两个游戏内示例文件；内部页面只有插屏/激励两个测试按钮 | SDK 壳接入参考，不是完整纸牌游戏工程 |
| template.zip | 14 个条目（含 macOS 元文件）；基础壳与 index(2) 扩展壳，后者另有宠物/DADA 转发 | 与 Solitaire 接入模式相同，初始化 game ID 不同 |
| AHA JS Bridge - API接口文档.zip | Markdown 文档和一张 DADA 状态图 | 原生协议、参数、版本与回调语义依据 |

原文快照和 SHA-256 已放入 [Skill 来源清单](../../skills/aha-game-integration/references/source-manifest.json)。附件 readme 的“根目录 index 不要动”作为模板使用说明记录，不作为本次用户要求；附件代码没有被执行。

## 推荐方式

如果游戏由 AHA 容器直接打开，优先使用原生 Bridge 独立适配层，保留当前静态工程结构。如果渠道明确要求上传的外层壳，则将游戏构建产物放到 `game/`，由父页面统一拥有 SDK、广告和消息通道。两种方式只能选一个广告所有者，避免重复初始化、重复请求与重复统计。

普通浏览器缺少 `bridgeCore` 时继续游戏，不需要伪造 Bridge。SDK 壳覆盖普通 Web 广告的具体能力，需要补充渠道说明；上传的模板调用样例不能证明远端 SDK 的全部行为。

## 《琥珀商路》的接入位置

| 文件/业务位置 | 建议改动 | 注意事项 |
| --- | --- | --- |
| `src/app.mjs` 首屏 `renderLobby()` 完成之后 | 资源实际可用后通知加载完成；注册页面时长和宿主生命周期 | 等待必要资源，不用外层 onload 代替游戏 ready |
| `startGame()` | 创建 match_id，提交 `match_start` | 只在新局触发；选择模式按钮导致大厅重绘不算开局 |
| `restart()` | 生成新的 match_id；结算后再来一局可先请求插屏 | 失败/无填充继续；重开按钮需业务锁，防重复创建对局 |
| `handleMove()` 提交胜利局面时 | 写入结算标记并发送 `match_end` | 不能放到 `openModal('win')`，因为恢复旧局会再显示结算 |
| `resume` 操作 | 发送 `match_resume` | 恢复不是开始新局；不重复上报胜负 |
| `clearTimers()`、`scheduleAI()`、输入处理 | 接入暂停原因集合，取消 AI/动画回调并控制输入 | 当前已有 generation，可以用于防止旧局回调污染新局 |
| 弹窗和 `visibilitychange` | 与广告、宿主 pause/continue 协调 | 释放广告暂停不能关闭用户弹窗或绕过后台状态 |
| `src/audio.mjs` | 增加临时暂停/恢复或总增益控制 | 当前 setEnabled 仅阻止新音符，不能停止已排程音频；不要覆盖用户音效偏好 |
| `src/storage.mjs` | 存储 match_id、结算发送标记；有激励收益时增加奖励事务数据 | 当前 loader/saver 只保留 game/settings，需显式兼容旧版存档 |
| `src/style.css` 和渠道壳布局 | 按渠道约定处理 Banner 与安全区 | 不能直接固定裁掉棋盘 50px；失败/关闭释放占位 |
| 大厅文案 | 启用商业化时同步调整“无广告”说明 | 普通浏览器关闭广告与渠道启用广告应如实呈现 |
| `scripts/build.mjs` / 交付打包 | 直连保留静态构建；壳接入生成独立渠道包 | 资源使用相对路径，原普通 Web 包可保留作为回退 |

第一批适合接：加载完成、开局/恢复/结算/时长埋点、宿主暂停、结算后插屏。激励可考虑局外外观解锁，但当前工程没有外观库存或奖励账本，不能只接广告回调就宣称已完成这一产品能力。也不建议为 Ludo 擅自增加付费重掷或改变公平随机规则。

## 已交付内容

- [Skill 入口](../../skills/aha-game-integration/SKILL.md)：接入决策、执行步骤、验收与交付边界。
- [标准流程](../../skills/aha-game-integration/references/workflow.md)：配置表、事件表、点位、两条打包路径、验收矩阵。
- [接口契约](../../skills/aha-game-integration/references/api-contract.md)：协议/版本速查、原生与 SDK 回调区别、模板问题。
- [适配代码使用说明](../../skills/aha-game-integration/references/adapter-usage.md)：原生和 SDK 接入骨架、返回值、生命周期与限制。
- `skills/aha-game-integration/assets/aha/`：`client.mjs`、`ads.mjs`、`pause.mjs`，独立于具体游戏。
- `skills/aha-game-integration/tests/adapter.test.mjs`：原生与 SDK 模拟测试，不请求生产广告或发送真实埋点。

Skill 工程源码维护在 `skills/aha-game-integration`，同时安装到 `/root/.codex/skills/aha-game-integration`，方便后续显式调用。若当前会话技能列表未刷新，可直接读取工程内 SKILL.md；新会话可使用 `$aha-game-integration`。本次未触发应用知识库的导入/同步流程，也未改变工作流的 Skill 自动路由。

## 验证与待联调

本地命令：

```bash
node --test skills/aha-game-integration/tests/*.test.mjs
conda run --no-capture-output -n base python /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/aha-game-integration
```

模拟测试验证：字段序列化、版本门槛、无 Bridge/异常处理、加载完成去重、token 展示、广告完成与关闭的区别、重复/迟到回调、无回调兜底、并发/冷却、插屏免广告、SDK 成功/失败、多个暂停来源、Banner 回调。测试具体结果见 [验证记录](validation.json)。

未覆盖：真实 SDK 下载/初始化、iframe 跨页面通信实现、目标游戏实际点击流程、AHA 设备广告填充和展示、统计后台到账、奖励持久化、Banner 实际占位。当前游戏未改动，因此没有以旧游戏测试结果冒充接入验收。

正式接入需要补齐：目标接入方式和 AHA 版本/容器类型、游戏所属 appKey 与 eventId、SDK/广告位参数（若采用壳）、事件口径、激励奖励方案及真机测试入口。文档里插屏最低版本、部分结果 status 字段和 SDK 自定义事件参数的歧义，也在真机联调时核对。

后续可使用：

> 使用 $aha-game-integration 为 games/amber-caravan 接入 AHA，按已确认的渠道配置实现开局和结算埋点、结算后插屏、生命周期暂停恢复；明确激励收益后实现奖励事务，输出本地和真机验收记录。
