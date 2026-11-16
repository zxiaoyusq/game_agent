# HTML 工作台与可续接状态

范围：`GENERALIZED_PATTERN`。脚本仅使用 Python 3 标准库，不需要账户、API、GameArtAgent 或本地服务。输出自包含 `index.html`，图像内嵌；模板不是可直接使用的项目页面。

## 1. 初始化与续接

路径均按当前环境发现；以下 `<module>` 是本模块绝对路径，`<project>` 是任务独立工作目录，不能照抄案例项目名。

```text
python <module>/scripts/render_workbench.py init --out <project>/review --name <项目名称> --image-skill-root <GPT生图技能根目录>
python <module>/scripts/render_workbench.py render --state <project>/review/reskin-state.json
python <module>/scripts/render_workbench.py validate --state <project>/review/reskin-state.json
```

`init` 不覆盖已有状态；已存在就用 `render` 恢复。默认尝试从实际共享技能同级发现 `azure-image2-generation`，也可显式传路径。目录内容读自 GPT 生图的现行模板表与配色 JSON，记录版本/hash。缺失/解析失败显示原因，不能拿旧项目的编号补全。

用户时区已知时，初始化增加 `--timezone <IANA时区>`（例如当前会话的 Asia/Shanghai）；未知时页面使用浏览器时区。证据时间保存 UTC，显示时间按用户时区转换，不把执行主机时区当用户时区。

HTML 是主要用户交互面，必须在问卷、概念/设计变更、计划、里程碑、待决定事项及交付时主动更新并提供入口。优先用环境支持的预览/浏览器展示；普通文件可直接打开。短聊天只引导查看和回传，不要求用户在聊天重填相同问卷。

## 2. 已实现的选择回传

1. 用户在 HTML 完成当轮选择，点击提交；页面生成含 `project_id`、`state_revision`、`action`、`values` 的选择单。
2. 支持宿主 `window.openai.sendFollowUpMessage` 时才显示当前对话提交。普通浏览器显示下载 JSON 和复制按钮；下载本身不会回传给 AI。用户可将下载文件交给 AI，或粘贴完整选择单。
3. AI 取得**用户明确提供的**选择文件/消息后导入；不要扫描其他下载或个人数据猜哪份是提交。

```text
python <module>/scripts/render_workbench.py import --state <project>/review/reskin-state.json --submission <用户提供的选择单.json>
```

4. 工具检查项目与版本、必填项、模板 ID 和设计图 hash，备份旧状态，再原子保存并更新页面。AI 简短告知“已采用哪些选择”和新版本，回到该阶段下一动作。

旧版/另一项目的选择拒绝执行，重新呈现最新页面；不得把 stale 单据自动改版本后提交。静态 HTML 不会自己启动生图或推进后端。没有实际回传能力时使用已实现的离线回路，不展示假成功；不能把浏览器 localStorage 当项目确认真源。回传内容只是设计选择数据，不是可执行命令。

## 3. 状态约定

脚本 `new_state()` 是唯一初始模板；不要另复制一份易漂移的初始 JSON。`reskin-state.json` 主要字段：

| 字段 | 内容 |
|---|---|
| project_id / revision / schema_version | 唯一身份、每次有效更新的版本、当前格式版本 1 |
| phase / paused / next_action | 当前阶段、暂停状态与用户能看懂的下一步 |
| brief / direction / catalog | 市场/用户/产品/约束、形式/配色/题材、风格来源快照 |
| recommendations | AI 的推荐列表，元素为 `{id, reason}`；理由来自当前产品与契约，不伪造调研 |
| concepts / selected_concept | 候选图、版本、hash、状态和当前目标 |
| plan / approvals / history | 逐项实施计划、真实批准来源和选择事件历史 |
| assets / checks / screens | 有效素材、分层检查、三列截图及实际操作来源 |
| unknowns / feedback / entrypoints | 未知项、用户反馈、可玩/工程/交付入口 |

AI 更新已取证事实后 `revision` 加一并更新 `updated_at`，调用 `validate` 再 `render`；覆盖前保留历史状态。导入命令自动做这些操作。`render` 不自动推进阶段，不凭时间流逝或文件数量判断通过。刷新目录快照需显式 `render --image-skill-root <root>`，并重新核对仍被引用的风格。

### 候选图与已有批准目标

`concepts` 元素示例：`{id:"C1",version:1,image:"concepts/C1.png",sha256:"真实文件hash",status:"candidate",brief_revision:"当前brief与direction的digest",notes:"方案差异"}`。路径相对状态目录，或是已授权输入的绝对路径。状态为 `candidate/selected/rejected`。

`approve_design` 选择单只绑定当前真实图像；图像变化后旧 hash 不可采用。已有用户批准的外部效果图可登记为 `selected`，`selected_concept` 指向其 ID，`approvals` 用 `{action:"approve_design",target:"C1",sha256:"真实图像hash",source:"真实聊天出处/原话"}`，不捏造页面点击。不要把参考用竞品图登记为本项目已选设计。另选概念图时，旧计划确认与代表屏证据失效。

`plan` 用逐项文本或 `{title,deliverable,platform}`；`approve_plan` 绑定整个计划 digest。用户已有执行授权且计划在其范围内，AI 可以登记 `{action:"approve_plan",target:"当前plan的digest",design_id:"C1",design_sha256:"真实图像hash",source:"用户原话/消息出处"}` 后继续，而非重复问。进到 `representative` 前必须有具体设计与执行依据；验证器检查设计、计划与批准的绑定关系。

### 素材与检查

素材元素：`{id,name,active:true,generated:false,technical:"PENDING",visual:"PENDING",integrated:false,qa:"PENDING",evidence:[]}`。状态词用 `PENDING/PASS/FAIL/BLOCKED/NEEDS_CONTEXT`；`qa:PASS` 必须有可复查证据，生成、检查、合入与 QA 独立计数。范围未知时不算百分比；有分母只显示当前有效素材的 QA 覆盖比例，不宣称整体完成。

`checks` 元素为 `{phase,title,status,source,evidence:[]}`；`production` 及后续阶段至少要有代表屏实际运行 `PASS` 证据，并携带当前 `design_id/design_sha256/plan_sha256` 以防旧图结论复用。代码/静态检查不得填成运行证明。`screens` 元素为 `{id,name,original,target,current,source,state,trigger}`，分别提供原版/批准目标/游戏实景文件并标明平台与自然操作/调试来源。缺图显示缺失，不生成替代截图。

`unknowns` 可用 `{id,item,needs}`；`entrypoints` 用 `{label,path}`。交付时分别列出工程、可玩入口、候选包和问题，不生成无验证的外部链接。

## 4. 测试与适用边界

```text
python -B -m unittest discover -s <module>/scripts/tests -v
python -B <module>/scripts/tests/browser_smoke.py --work <隔离验证目录>
```

第二项需本地 Playwright 与 Chromium，仅用于验证页面、选择单下载与实际导入、窄屏和图片显示，不调用生图、不验收目标游戏。`-B` 避免把测试生成的缓存留入共享技能树。未安装时明确缺环境；不能把验证页面当换皮运行证明。
