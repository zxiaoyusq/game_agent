# 原型阶段记录：Carrom Freestyle 红棋与罚则依赖复核

## 任务与授权边界

- 项目ID：531d306b87bc430487cc27cdbf2af234；当前工程根目录即该项目工作区。
- 当前阶段：prototype；autonomous=false；用户要求直接交付有依据的只读静态报告。
- 本次工作是既有游戏规则复核，不是创建新游戏或重新定义竞品规则。不修改游戏实现、依赖、资源、HTML、构建或既有测试，不推进美术、代码、测试或发布阶段。
- 面向用户的报告为中文；没有新增或改变玩家界面文案、图片文字或页面语言。后续若授权新默认版本，玩家界面采用English及lang=en；本次不借此要求修改既有HTML。

## 已读参考路径

以下路径相对ref/，均使用read_reference读取：

1. `mcp-inputs/mac-codex/31000435a09f059b10e61a82cd31930e4255c7658fbd6c75bb9d1c487e78178f/Carrom_fallback_current.js`：完整读取至EOF，并定点复核结算核心。
2. `mcp-inputs/mac-codex/080bc7b20fc83732926bfce6785481287f93b63ac97735df9f8eaef7a0a6fb71/disc-rules.js`：全文真实依赖。
3. `mcp-inputs/mac-codex/acfe600b37eac8f3e25c9c670ecdd57d528f43499d851ebbeda4006a28e8692d/freestyle-full.diff.txt`：全文实际仅母球罚则一个hunk。
4. `mcp-inputs/mac-codex/b6eaf03a683f18bb120a4ccf37ff801d0b4f583d7fb5462d2b667d1c2e4f6bca/freestyle-evidence.md`：全文历史摘要，不等同底层日志/录像复核。

已读冻结资料：genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/canvas-web.md。
已读选定技能：game-reverse-engineering/SKILL.md；配套execution-protocol.md、global-rules.md、unknowns-ledger-template.md。子入口modules/gameplay-logic-reverse/SKILL.md工具拒绝读取（未选中），不声称采用正文。

## 原有玩法定义与参考取舍

- 真实模式：mode2 Freestyle；红/白/黑分值50/20/10，任意普通棋给出杆方计分，目标160。
- 核心循环：获得输入权→瞄准与施力→物理运动和扫描入袋→静止后冻结本杆→犯规返场或积分→覆盖/撤红→判终局→续杆或换手。
- 红状态：board→单红非犯规pending；同杆有普通直接covered；pending后同owner非犯规普通覆盖，否则返红并撤旧owner50；covered保持。以上为当前实现，尤其同杆覆盖明确是项目假设。
- 罚则：本杆有子且犯规，全部本杆子返场/无本杆分；仅空队列犯规才调用一般历史罚棋。该罚棋只接受同轮同方全部历史为同色同分普通棋、分数精确匹配，扣/返一颗；混色或含红不罚，不记欠罚。
- 成功失败：先强制完成积分/返场、覆盖或回滚，再判160；pending阻止双方终局，双方均达标取当前actor胜。没有据此编造竞品胜负规则。
- 历史旧版“红50→空杆仍50”属于旧SHA受控桌面样本；不覆盖当前依赖状态机。diff文件名full不代表完整改动。上传正文哈希及历史SHA关联未计算/验证。

## 物理、输入与界面边界

- 真实引擎PIXI + Planck，不是配置建议的原生Canvas重建。本次不迁移引擎。
- 步长1/60，迭代10/10；棋子半径16，friction0、restitution1、linearDamping1.8；入袋距离≤20，trimVelocity在abs(vx)+abs(vy)<0.2时sleep。
- 更新顺序：Tweener/表现→active检查→计时/母球/红/白/黑扫描→timeout postscan flush→物理step。正常结算snapshot与同tick晚扫描存在待复现时序风险。
- 输入窗口沿用当前真实turn和启用flag，出杆/结算期间不得重复出杆；移动touch与桌面mouse待测试。暂停/广告阻塞逻辑tick；table0 Freestyle不递减倒计时，不设不可能的自然超时用例。
- 界面布局不重新设计：只核验原棋盘、母球输入区、双方Freestyle HUD、犯规表现及结果界面对应的状态与提交。没有运行视觉或测量布局，不给臆造像素尺寸。HUD内部value同步，增分label在放大5tick completion后刷新，须区分暂时显示与逻辑分数。
- 验收误差：规则分数、账本/棋数、owner/phase、提交次数容差0；入袋边界19.99/20/20.01精确探测；轨迹重复性暂定位置0.5世界单位/角0.01rad，仅为将来同环境复现建议，不是当前实测或竞品误差。

## 产物与静态验收

- `reports/freestyle-static-review.md`：依据/版本对账、真实符号表、状态图与优先级、29项场景复现矩阵、12项未知台账、直接运行真实依赖的未执行Node断言代码，以及原函数VM/真实Tweener/浏览器物理复现准备规格。
- `workflow/prototype.md`：本阶段记录。
- 静态验收要求：每场景具输入、当前预测、已有证据、未覆盖风险与可执行步骤；当前静态推断、历史隔离模拟、历史受控浏览器与竞品事实分层；完整引用路径和diff实际范围；不改生产、不伪造动态验证。
- 本轮真实验证：参考正文实际读取，完整源至EOF及核心函数调用链静态核对；报告和本记录已使用read_file读回核验。静态核验不是测试运行，后续文字补订也只进行读回检查。
- 未执行：npm run build、npm test、npm run check、Node/VM、浏览器、真机、宿主、竞品实战。未生成dist、素材、源码包或试玩ZIP。本文附代码未保存为独立测试文件、未执行；完整集成/浏览器夹具尚需真实运行资源及后续授权。

## 未闭合事项与阶段停点

重点待证：covered红历史可能令空杆母球犯规免罚；进子犯规不叠历史罚棋；混色免罚/无欠罚；同杆覆盖与终局优先级；正常scan前结算晚事件；终局后active仍更新；真实Tweener及旧sprite/body生命周期。详见报告U01–U12。
不擅自选择待定规则、不编造用户确认、不要求例行阶段确认。交付静态报告后停在prototype；后续需用户真实授权才可补证、修复或进入动态验收。
