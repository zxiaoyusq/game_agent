# 基于运行观测的算法本地复现

> **何时读我**：哥哥要在本地把一坨跑得起来的原版脚本复现出来，或碰到"本地跑不通、日志对不上、补了环境还是差一处"的卡点，问该按什么顺序取证和补环境时。
> **读完能做到**：按 Observe → Capture → Rebuild → First divergence 四步建立可复现的本地回放：先锁定真实执行入口与 owner，采样时只读 hook 并保留无调试基线，只补实际观测到的依赖，差异定位到第一处不一致后用同一夹具单变量回放验证。
> **范围**：`GENERALIZED_PATTERN`

范围：`GENERALIZED_PATTERN`。适用：Cocos JS/JSB/Web 的出块、配置解析、解码和离线机制移植。浏览器与 JSB 环境分别取证。

## Observe → Capture → Rebuild → First divergence

先确认真正执行入口、脚本/bundle 哈希、触发动作和实际 owner。浏览器可用 request initiator/xref；JSB 优先真实 bridge、资源 loader、eval/heap 链，不套用浏览器专用工具名。

采样保存输入、输出、调用顺序、配置快照、时间来源、RNG 状态、存档/缓存依赖和异步提交边界。Hook 先只读；断点可能改变计时、生命周期和超时，要保留无调试基线。采样前后存档原字节备份/哈希/finally 恢复。

本地环境仅补实际观测到的依赖，不能用一套虚构的 window/document/navigator/jsb 令脚本“跑起来”。时钟、RNG、I/O 等由夹具显式注入；引擎调度/动画/广告结算不假装已经还原。

遇到差异，定位第一处不一致的输入、分支、调用或状态写入；每次只改变一个有因果依据的补环境决策，再回放同一夹具。长脚本按业务函数拆，不全局替换异常处理或清空缓存掩盖根因。

## 完成条件

正常、失败、边界、多轮状态转移与采样输入回放一致；未知依赖明确保留。玩法需检查 RNG 推进次数、候选分布和原版保护器触发率。固定输入下输出相等不代表完整游戏还原；重新接入原生命周期后做真机流程回归。

来源：逆向AI.zip `js-reverse/SKILL.md` 的 Observe/Capture/Rebuild/Patch/DeepDive 流程；包内专属 MCP 名称、签名生成场景和自动补环境规则不直接移入游戏工程。来源见 [合并记录](../../../references/minimaxh3-absorption.md)。
