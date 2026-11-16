# 代码阶段验收证据索引

本attempt最终三项真实验证：`npm run build`、`npm test`、`npm run check`均退出0；这是code阶段自验，不是下一test阶段确认。验证完成后只增加交接文档，不改源码、资源、dist或交付ZIP。

## 验收条件及覆盖

| 条件 | 已执行证据 | 边界 |
|---|---|---|
| 保留原版十字棋盘、四色圆营地、亮面棋子、原骰序；仅有限背景换皮 | build.json的58件白名单及逐件SHA；screenshots/B01-menu.png、mobile.png、frames；两份上游manifest | 不等于逐件白/深底人工视觉验收；箭头位置采用确认原型，差异见workflow/code.md |
| 经典/快速、2/3/4席、终点、安全、吃子和奖励规则正确 | rules-summary.json；10组单测；18完整规则对局 | 不穷举所有随机局 |
| 玩家通过自然输入可完成游戏 | browser-summary.json、trajectories.json、screenshots/quick-result.png、screenshots/classic-result.png | 快速4人同屏与经典2席人机使用seed1；三席验证轮转 |
| 默认正常动画可见且不是静态替代 | animation-pixels.json、animation-events.json、连续frames与video/page@9b1e7b9a380b0a396394bbc0a579b8df.webm | 五类骰/走/吃/归家/胜利均有时序、ROI像素变化证据；不声称原引擎逐帧一致 |
| 演出不重复提交；暂停、刷新、重开和后台可靠取消 | lifecycle.json、visibility.json | 覆盖dice/walk/capture及后台AI；真实trusted标签隐藏，非伪造hidden事件 |
| 手机布局与触控、键盘辅助可用，无控制台错误 | browser-summary.json、mobile.png；真实Chromium153.0.8010.12 | 320/360/390手机模拟视口与DPR1/2；不是物理手机、多浏览器或听感验收 |
| 最终dist相对资源、展开小于10MB，源码可重建 | build.json：1,283,838字节；packages.json：sourceEntries85、distEntries71、rebuildIdentical=true | 实际解包构建并比较逐件SHA；无部署或发布 |

## 失败与复验

首轮check退出1，`browser-failure.json`保留CDP profile清理ENOTEMPTY记录。等待Chromium进程退出并有界重试清理后，最终三命令均实际重新通过。历史失败不删、不解释为首轮成功。

最终源码指纹：`48e8d1dc437225ec0aa333a49faf6d7b701b85d55e8af0dca7966096e5d5ae10`。
最终构建指纹：`9f73d6c9f420dda5ad35eafbbb0e45595c8124886393b47a43f063c1a17d03e5`。

交付、来源、上游冻结SHA与完整限制见`workflow/code.md`。音频实际接入及容错不等于人工听音；商业授权未独立核实。等待审阅，不自行确认或推进阶段。
