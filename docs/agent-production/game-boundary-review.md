# 游戏功能边界独立验收

结论：12 项定向检查中，10 项通过，0 项确认的游戏失败，2 项后台冻结用例因环境不支持而未覆盖。本次不能表述为全部通过。

实际预览：http://127.0.0.1:8003/api/workflow/projects/0a850241a9fc4bee925af55617fead85/preview/index.html。

运行时：Cocos 3.8.8 / WEBGL2。本次测试及最终截图复核期间，记录的运行源码与资源输入哈希均未变化。

| 用例 | 状态 | 验证内容 |
| --- | --- | --- |
| R09-control | 通过 | 未改变棋盘时真实提示合法，只高亮、不自动移动 |
| R09-move | 通过 | 过期 Worker 结果未改变当前局面、步数、高亮或反馈文案 |
| R09-undo | 通过 | 过期 Worker 结果未改变当前局面、步数、高亮或反馈文案 |
| R09-add | 通过 | 过期 Worker 结果未改变当前局面、步数、高亮或反馈文案 |
| R09-restart | 通过 | 过期 Worker 结果未改变当前局面、步数、高亮或反馈文案 |
| R09-mode | 通过 | 过期 Worker 结果未改变当前局面、步数、高亮或反馈文案 |
| I02-freeze-resume | 未覆盖 | 无头Chromium接受Page.setWebLifecycleState但未产生freeze/resume事件；独立空页面对照仍为visible，600ms内定时器从1增至31，未证明真实冻结。不能据此判定游戏失败或通过。 |
| I02-freeze-refresh | 未覆盖 | 无头Chromium接受Page.setWebLifecycleState但未产生freeze/resume事件；独立空页面对照仍为visible，600ms内定时器从1增至31，未证明真实冻结。不能据此判定游戏失败或通过。 |
| S03-write-failure-move | 通过 | 操作可继续，未保存反馈在操作结束后仍可见 |
| S03-write-failure-undo | 通过 | 操作可继续，未保存反馈在操作结束后仍可见 |
| S03-write-failure-add | 通过 | 操作可继续，未保存反馈在操作结束后仍可见 |
| S03-write-recovery | 通过 | 关闭设置后警告保持，真实写成功后才清除；完整局面和辅助状态保存，刷新后历史仍可逆 |

## S03 修复前证据与修复后结果

修复前实际 API 预览中，启动后令存档 setItem 抛 QuotaExceededError，再正常点击首关 0→3：步数为1、棋盘已变、存档原文不变，反馈却为“很好，继续给每种颜色找到自己的位置”。随后读取该构建 main.mjs 的 SHA-256 为 `1d1da7e5c4a859d072a262083d889e17353ad024740bd6ad4d0f2bb52da8b36f`。历史失败保留在 JSON 的 prior_findings 中。

修复后，移动、撤销、加管操作结束后均保留未保存警告。设置内切换声音失败时，弹窗底部和关闭后的主界面均有警告；已实际检查截图中的文字。恢复可写并成功保存后，警告消失，刷新恢复完整局面及辅助管，连续撤销仍可用。

- 主界面写失败截图：`logs/game-boundary-storage-failure.png`。
- 设置内警告截图：`logs/game-boundary-settings-open-warning.png`。
- 设置关闭后警告截图：`logs/game-boundary-settings-closed-warning.png`。
- 成功保存后截图：`logs/game-boundary-storage-recovered.png`。

## 未覆盖的 I02 后台范围

当前无头 Chromium 接受冻结协议调用，但没有产生 freeze/resume 事件。独立空页面对照中，页面仍为 visible，600ms内定时器继续运行；因此无法证明实际进入后台或冻结。本次把两个相关用例标为未覆盖，而非游戏缺陷，也未伪造可见性事件。已有动画中刷新检查不能替代真实设备后台恢复，后者仍需支持该生命周期的浏览器或设备环境。

## 方法与可追溯记录

脚本位于 `logs/game-boundary-review.cjs`，结果与动作保存在同名 JSON。所有玩法操作均为真实指针点击；状态接口仅只读。Worker注入只延迟原生求解结果，不修改结果。存储注入只模拟setItem异常，没有注入棋盘或通关。输入检查逐项核对实际API文件与源文件SHA-256，并记录测试前后及最终视觉复核后的哈希。未修改游戏源码、测试、已确认报告或工作流状态。
