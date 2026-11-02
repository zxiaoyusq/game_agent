# BlockMaster / Block Blast 案例专属规则

> **何时读我**：当前包身份/直接基底就是 BlockMaster / Block Blast，或用户明确要求拿这个案例作对照。
> **读完能做到**：拿到该案例的版本基底、材质与 SSS 边界、疑似 bug 的判定条件、真机验收链，并找到对应模块下的案例参考索引。
> **范围**：`CASE_ONLY_BLOCKMASTER`

**范围：`CASE_ONLY_BLOCKMASTER`。** 仅当包身份/直接基底匹配 BlockMaster / Block Blast，或用户明确要求以该案例作对照时才加载本文件；其他项目只参考"怎么证明"的方法，禁止复制任何字面值（见 `references/scope-map.md` 的 `DO_NOT_COPY_LITERAL_VALUES`）。

- 当前直接重打包基底是 Block Blast 10.4.7；9.5.0、六套 AB 采集和旧抓包只作对照。
- 当前已证实的整组材质/表现切换边界是新局和清屏；普通消行不轮换材质。
- SSS 属于连续清屏链，不属于 Replay 或普通新局。
- 原版引导中"手指等待时预消除高亮持续存在"可能是正常设计；只在触摸结束、手势节点退出、动画稳定后仍残留时判 bug。
- Athena、Firebase、Hisavana、Palm/Aha、Banner、奖励/插屏和原厂域名隔离是本项目并列的真机网络验收链。
- `E_BlocksProducer_AnyTouchEnd`、`Eliminate_Effects_Proxy`、`SkinThreeInfo`、`showSSSWhenSkinChange` 等名字只属于该代码基底，其他项目必须重新定位等价 owner。

本文件从根 `SKILL.md` 拆出（8.0.0 路由重构）。案例参考索引：

- `modules/cocos-reverse-engineering/references/android-blockmaster-runtime-effects-ads-regression.md` — 离线运行时回归手册
- `modules/cocos-reverse-engineering/references/android-blockmaster-v35-vendor-isolation-and-real-device-qa.md` — 原厂隔离与真机 QA
- `modules/cocos-reverse-engineering/references/android-blockmaster-v31-ad-resource-and-ui-removal.md` — 广告资源与 UI 移除
- `modules/cocos-reverse-engineering/references/android-blockmaster-moregames-settings.md` — More Games/Settings 清除
- `modules/cocos-reverse-engineering/references/android-jsb-reskin-pitfalls.md` — 换皮+SDK 注入踩坑（V30-V35 前置阅读）
- `modules/gameplay-logic-reverse/references/blockmaster-v123-v124-lifecycle-regression.md` — V118-V124 生命周期回归
- `modules/gameplay-logic-reverse/references/blockmaster-v128-tray-guard-regression.md` — V128 三块保护与 1x1 洪水
- `modules/gameplay-logic-reverse/references/block-blast-case.md` — OFFER_TYPE/Trait 目录/hook 偏移快照

## 后续模式与 Seed 竞态案例

V140–V142 见 `modules/gameplay-logic-reverse/references/blockmaster-v140-v142-mode-seed-regression.md`；模式启用和离线冷启动按任务读取，旧成功日志不能代替当前行为验证。
