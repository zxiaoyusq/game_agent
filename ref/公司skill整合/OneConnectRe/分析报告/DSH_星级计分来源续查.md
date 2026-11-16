# 竞品单关星级计分来源：定向追踪

请在已核对哈希的 Tile Connect v1.19.9 arm64 包上继续离线追踪，不操作 MuMu、不使用多模态视觉、不修改 One Connect 工程和已有 goal。

现已知 `ScoreStarProgress.ModifyScore` 被 `JudgeControl.CreateStar`、`TimeFlyStar` 等调用；请以完整调用链和直接反汇编为依据，追踪这些调用的 `delta` 来源、数值、与配对数、连击、剩余时间、倒计时奖励和道具的关系。区分逐次加分与结算时飞星，列出可由静态代码确定的比较和计算式；若字段或间接调用无法确认，明确列为未知。复核评分阈值基准 B 的真实类型和值来源，不把字段偏移一致当成闭环。

请在 `E:\codex_apk_work\竞品拆解\tile connect\07_程序与配置拆解\` 交付带包哈希、RVA、原始汇编、可复跑工具和证据等级的报告及机器可读表。不要开发内购或直接改项目。
