# One Connect DSH 交接入口

- 日常省量巡检：`& 'C:\Program Files\Python312\python.exe' -X utf8 tools/dsh_status_compact.py --changes`。只输出会话运行、队列、目标或公开消息序号等有变化的会话；无变化时无输出。首次运行建立观察基线并显示当前状态。观察状态保存在 `analysis/dsh_handoff/observed-status.json`，与人工审核游标独立；观察不代表已审核，删除观察文件只会重建基线。
- 发现 `new_message: true` 后按需使用 `--session reverse --unread` 或 `--session art --unread`；核查交付文件和证据后再确认审核序号。仅在确有新交付、阻塞或纠偏时展开完整记录或发指导，运行中且正常推进时不重复派工。

- 状态检查：在项目根目录运行 `& 'C:\Program Files\Python312\python.exe' -X utf8 tools/dsh_status_compact.py`。默认只显示状态、队列、观察与审核序号及有无未审核消息；需要调查时加 `--full` 查看最多 300 字符的最新消息。重复检查不会自动视为已审核。
- 定向增量检查：`tools/dsh_status_compact.py --session reverse --unread`（或 `art`），只输出审核游标后的最近 12 条消息、每条最多 300 字及截断标记；结果保存在对应 `*-unread.json`，不覆盖最新状态快照。`unread_may_be_truncated=true` 表示可能遗漏更早消息，或消息标记 `truncated=true` 时，应按游标查看完整公开记录。游标为空时从序号 0 开始；不要把截断片段当成完整审核。
- 实际审核消息和相关证据后，运行 `& 'C:\Program Files\Python312\python.exe' -X utf8 tools/dsh_status_compact.py --ack reverse --seq <message_seq>`（美术用 `art`）。必须与最新快照序号一致；只记录明确审核，不可倒退。检查只取最新一条公开消息，存在多条未审核消息时须按需查看完整历史，不能凭片段确认全部内容。
- 完整快照固定在 `analysis/dsh_handoff/reverse-latest.json` 和 `analysis/dsh_handoff/art-latest.json`，每次覆盖；需要审计细节时再查看。历史快照、回执和证据不自动删除。
- 具体交付写入 `analysis/dsh_handoff/<任务名>.md`：简明列状态、基线、结论、证据路径、验证范围、未知和下一步；以完整清楚为准，不为满足机械字数反复压缩。大型证据放原位置并从摘要链接，不复制大段日志。旧报告保留原路径，不要求搬迁。
- 统一路径：固定状态为 `analysis/dsh_handoff/{reverse,art}-latest.json`，下一条指导为 `{reverse,art}-next.md`，回执分别保存在 `{reverse,art}-deliveries/`。发送时使用已授权的 `dsh_session.py send --message-file`，按需验证回执；复用指导文件前保留回执，避免重复投递。
- 指导正文和回执遵守 `dsh-guidance`，保留原始 requestId 与送达验证；不因为状态检查重复派工。运行中或排队的工作先等待，停工且有明确任务时再派发。
- 快照的 `last_seq` 仅表示观察到的记录，并不代表已审核；读取结果后需结合具体文件和回执核实，不能自动推进 reviewedSeq。截断的消息必须按需查完整快照。
- 不改变既有工作分工、暂停状态、项目分支或 HTML 约束；视觉拼接由主代理对照用户批准的效果图复核。
