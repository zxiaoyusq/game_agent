# 机器人路径首尾与目标接触改造：原型定义

## 0. 交付边界与证据等级

- 项目：eca000da775d45feb4e8ae507d15e54a；当前阶段：prototype；恢复执行：attempt 2。
- 本文是设计交付，不是逻辑补丁、可试玩原型或游戏安全证明。没有修改参考源码、创建运行工程、生成美术、执行源码、构建、单测或浏览器验收。下文数值算例是手推预期，绝不是已通过的测试。
- autonomous=false；无已确认的上游决策。本文方案是工程建议，未冒充用户确认，也不推进下一阶段。
- 唯一参考（相对 ref/）：`mcp-inputs/mac-codex/342e46b75c9b2c5023756b13d1ec1939c2ac83880659ec45de17c126dec118ad/Carrom_clearance_342e46b7.js`。已分页阅读至 `_0x3f3a` 字符串表及文件结尾；恢复时补读先前大块读取的间隙。偏移是字符定位，不作为稳定行号；实现时以本文函数名和调用实参定位，先生成机械调用清单核对。
- 已读取冻结资料：`genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。
- 已读取技能：`game-reverse-engineering/SKILL.md`；配套执行协议、全局证据规则、未知清单模板。采用 owner 定位、证据分级、最小改动、未知闭合和真实运行才可判定的做法。未选中的 gameplay-logic-reverse 子入口读取受限，未采用其未读正文；后续专项逆向可补选。
- 当前输入是 PIXI 渲染、Planck 物理的既有 H5 JS，不是 Canvas 2D 原生项目。本文只定义独立几何逻辑及既有 AI 接入，不换引擎、不加载 Cocos、不宣称原工程符合 canvas-web 构建约定。若下一阶段要求实际迁移引擎，必须重新确认范围/选型；不能为满足标签私自重写游戏。

## 1. 玩法、状态、界面及参考取舍

### 1.1 保持的核心循环

玩家在基线放置 striker → 瞄准并选择力度 → 发杆 → 固定步长模拟棋子碰撞/反弹/入袋 → 按模式及 queen cover 规则结算 → 保持回合或交给对手。AI 对称参与，但先搜索直接、反弹和一层组合计划，再提交一杆。

本任务只提高 AI 的候选几何可信度。保留四角袋口枚举、既有力度计算、hDot 排序、普通/自由模式目标选择、queen 结算、墙体/袋体、皮肤、玩家操作和计分逻辑。拒绝把任务扩展为全棋盘物理求解、无界组合搜索或美术换皮。

### 1.2 成功/失败的两个层级

- 路径成功：完整闭区间无非法碰撞；指定目标是正确末端的首次合法接触；所有阶段及连接点有效。`clear` 仅表示这项静态几何条件成立。
- 路径失败：第三棋挡路、目标提前接触、背面/切离命中、末端穿透、起点进入重叠、非法/过期身份、无有效移动或阶段衔接错误。
- 游戏成功：仍由原规则 owner 处理真实入袋、清盘、queen cover、胜负和奖励；路径成功不等于这一杆必进袋，也不得提前更新计分。
- 无合法路径：有界 fallback 重试后进入既有无杆结算，不强发一杆、不冻结回合、不增加奖励、不跳过 queen cover。

### 1.3 物理与输入窗口

- 坐标契约：本文 x/y 是 body 世界坐标乘 `_0x541423=100` 的搜索单位，简称 WU。渲染缩放、设备像素比、CSS 尺寸不能参与半径计算。
- 原 `_0x49d791` 在更新棋/袋检测后执行 `world.step(1/60,10,10)` 并 clearForces；`_0x4bf21a` 累加 ticker delta，`while(accumulator>1)` 消耗一步。保持现状，不因几何改造改变步长、求解次数或积分顺序。
- 玩家输入只在原来的放置/瞄准状态可用；物理运动、AI Tween、结算、暂停/广告期间不增开输入窗口。
- AI 搜索需要有效、同回合的静止棋盘快照；最终提交前读 body 坐标（不要用可能落后一帧的 sprite 坐标），确认棋盘仍静止、对象和 fixture 有效。移动中不可用静态检测承诺安全。
- 原搜索延迟约500ms；AI 瞄准结束后约500ms 发杆，约2300ms 后进入后续处理。它们是调度延迟，不是碰撞容错；保留原回调隔离和结算等待机制。

### 1.4 布局与英文文案

不新增玩家界面：棋盘居中，四角袋口，原有顶端回合/得分区域，底部基线滑条及力度/瞄准操作，原有暂停和结算面板。本文只用文字描述布局，没有声称检查贴图实际呈现。

游戏默认 English；后续 H5 入口设 `html lang="en"`，不随中文浏览器切换。推荐可访问文案：`Carrom`、`Your Turn`、`Opponent's Turn`、`Move the striker along the baseline.`、`Drag to aim and set power.`、`Release to shoot.`、`Paused`、`Resume`、`Restart`、`You Win`、`You Lose`。无路径不弹技术错误，正常显示下一回合。开发诊断可用中文，但调试层默认关闭且不计入玩家文案。旧贴图中有英文字符串线索，不等于已核验所有文字素材。

## 2. 静态取证：缺陷及真实几何

### 2.1 检测 owner `_0x3ea989(start,step,angle,length)`

它将玩家棋、对手棋、queen 合并扫描；`steps=floor(length/step)`，不足一步立即返回 false。投影点夹到 `[step,steps*step]`，采样点也从第1步开始；返回“是否阻挡”，没有 moving/target 身份。

近似判定为：

```
end = floor(length / step) * step
along = clamp(dot(disc - start, u), step, end)
sample = clamp(round(along / step), 1, steps) * step
sampleRadius = step * 0.9
gapRadius = min(sampleRadius, step / 2 + 16)
blocked = distance(disc, samplePoint) < sampleRadius
       || distance(disc, projectionPoint) < gapRadius
```

因此首尾的中心轨迹域没有完整覆盖：`[0,step)`、截断末点到真实终点、所有 `length<step`。注意这不是“这些区域任何棋都不会检到”：旧采样圈可能覆盖其中一部分，但存在可复现漏检。

不能简单扩展范围：moving 自身和合法目标目前靠盲区被避开；补齐后若仍无身份，就会挡住自己/目标。也不能叠加保留旧大采样球作为兼容检测，否则误挡依旧。

### 2.2 fixture 半径，而非图像/搜索半径

|对象/证据|真实半径 WU|搜索旧值|影响|
|---|---:|---:|---|
|普通棋、queen：`_0x54e9a5` 内 `_0x5ca3cc`，`Circle(16/100)`|16|`_0x3ce1ab=15`|棋-棋真实接触距离32，而旧组合偏移30|
|striker：`_0x13fb80` 实例 `_0x27e1b4`，局部 `34*0.8` 再乘0.8创建 Circle|21.76|`_0x133600=21.76`|striker-棋真实接触距离37.76，而旧 contact 偏移36.76|

- coin 路径旧 step=30，两个检测阈值均27，低于真实32。
- striker 路径旧 step=43.52：sampleRadius=39.168，大于真实37.76；gapRadius=37.76。可误挡离轨迹38.5的棋。
- `_0x23a7dc(point,distance)` 是放置重叠判断，无身份；候选生成部分传36.76，最终过滤/fallback传37.76，也不一致。
- 必须同时改路径检测与 contact 构造：`H = center(target) - outgoingUnit * (radius(moving)+radius(target))`。不是仅把检测阈值调大。放置阈值统一真实37.76和同一容差契约，但不顺带扩大基线。
- 身份必须对象引用：两普通组 id 各从0开始，跨组 id 重复；queen 不一定有相同 id 契约。不能用 id、坐标或颜色排除。
- 删除 body 的棋由活动快照清理；若快照中有非有限坐标/无法识别半径，则 fail closed 为 invalid，而不是无声跳过障碍。

### 2.3 已定位调用与生命周期

四个袋口搜索函数各4次调用，共16处：`_0x52106f`、`_0x25af2a`、`_0x521eef`、`_0x30849b`。原签名为 `(destination,candidates,checkOutgoing,outputArray?,parentOutgoingAngle?,carriedDistance?)`。

直接候选通常枚举最多7个基线解，反弹4个，并受 hDot 改进条件和 break 控制。当 best<=0.5 且没有 outputArray 时才调用自身一次组合搜索；有 outputArray 就不再递归。因此应维持一层组合，不做无界递归。

候选只有 `{pos,dir,speed,hDot,dist}`，未保存 target 或 segments。出射向量与入射向量评分用 `abs(dot)`，背后命中也可能高分：必须先有向合法性过滤，不能指望现有排序消除它。

`_0x50a0ff` 生成并过滤/排序候选；`_0x3d12d7` fallback 仅随机目标、寻找空基线、指向目标中心，不检查路径；`_0xd6b627` 保存棋盘快照后进入 `_0x4662ac` 放置 Tween，`_0x223471` 瞄准/随机角度误差，`_0x4b3cc6` 最终一次提交。当前最终仅查棋盘快照/基线/放置，不查实际带误差路径。

原 `game.test()` 在 `_0x47e567(true); return` 后的搜索/发杆代码不可达，不能当有效验收入口。

## 3. 建议接口：身份化、闭区间、可诊断

这是接口定义，不是已集成代码。

```ts
type Point = { x: number; y: number };
type SegmentSpec = {
  key: string;
  phase: number;
  kind: 'pocket' | 'target' | 'railIn' | 'railOut';
  start: Point;
  end: Point;
  moving: object;
  movingRadius: number;
  target: object | null;
  expectedContact: null | {
    center: Point;       // moving 在首次接触时的中心，不是表面点
    outgoingUnit: Point;
  };
};
type PhaseScene = {
  discs: ReadonlyArray<{ ref: object; center: Point; radius: number }>;
  departureRefs: ReadonlySet<object>;
};
type PathResult = {
  status: 'clear' | 'blocked' | 'invalid';
  reason: string;
  blocker: object | null;
  firstDistance: number | null;
  contactCenter: Point | null;
};
// checkSegment(spec, scene, tolerance) -> PathResult
// validatePlan(plan, snapshot) -> PathResult
```

- 公开候选字段保持不变，追加私有 `_carromPathPlan`：版本、目标引用链、分段、阶段姿态、起点接触来源、快照/turn。引用可在内存保存，不写进 LocalSave、不 JSON 序列化或打包进玩家存档。
- scene 由活动 body 快照构造，按对象引用去重；每次阶段变更有独立 pose overlay，不改真实 body。
- 只对 `disc.ref === spec.moving` 排除自身。所有其他棋均检查，target 也必须参与首次碰撞求解。
- moving/target 不能相同，target 必须在该阶段存在；target 段必须有 expectedContact，非 target 段不得带末端目标豁免。
- 半径由唯一 adapter 读取已核实的圆 fixture；版本未知时可用上述已取证常量且校验类型。不得按 sprite 大小、skin、step 或猜测 id 得到半径。
- 不引入全局 ignore 数组、不允许 `ignoreAllNearStart/End`。起点接触许可仅作用于某阶段明确的 departureRefs，且仍执行分离判定。
- 旧 `_0x3ea989` 可作为局部布尔 adapter，返回 `result.status !== 'clear'`；迁移后所有调用必须传完整身份，不给旧签名偷偷推断目标的后备通路。保留 structured result 供回归诊断。

## 4. 几何定义及误差

### 4.1 第三棋：完整圆扫掠

令 A=start，B=end，D=B-A，L=|D|，u=D/L。对障碍圆中心 O，真实有效半径 R=rm+ro：

- 最近点距离：`s=clamp(dot(O-A,u),0,L)`，`dmin=|A+s*u-O|`，覆盖两个端点的圆帽。
- 严格间隙大于容差才 clear；第三棋在中途/末端的切触也当 blocked，避免同一时刻多体接触排序不确定。它不能借 target 规则获准。
- 候选可能阻挡时再求首次接触：`q=O-A`，`p=dot(q,u)`，`h²=|q|²-p²`，若有圆交集，则 `sEnter=p-sqrt(max(0,R²-h²))`、`sExit=p+sqrt(...)`；取闭段 `[0,L]` 中最早交点。起点已在圆内须先走起点规则，不将负根夹0后当合法目标。
- 按最早接触距离记录 blocker；多个接触相差不超过位置容差，第三棋优先拒绝，不能按遍历顺序挑 target。
- 无需沿段采样，短段与长段用同一算法；仅用最近点判定无法证明目标接触先后，target 段必须求根。

### 4.2 目标：不是永久忽略，而是局部预期首次接触

target 段 clear 需要同时满足：

1. 起点不在 target 内部；L 有效。求得该 target 的首次进入根在本段末端，`|L-sEnter| <= contactWindow`，且首次接触的 moving 中心距 expectedContact.center 不超过 contactWindow。
2. B 到 target 中心的距离满足 `|distance(B,O)-R| <= positionEpsilon`，穿透超过 positionEpsilon 直接拒绝；不能因为“距末端很近”就原谅1或2 WU的旧 contact 穿透。
3. 令 `n=(O-H)/R`（moving 指向 target 的碰撞法线），入射 `dot(u,n)>directionEpsilon`，且 `dot(n,expectedOutgoingUnit)>0`。重建 H 时 n 应与预期出射一致；用于发杆误差复核时要求其角差在下述上限内。
4. 没有更早的第三棋，也没有同窗口的多体第三棋。不得允许穿过 target 后到远侧终点，不得允许反弹前段先碰该目标。

contactWindow 只用于浮点/接触点匹配，不改变圆半径，不是删除末尾0.25 WU轨迹。合法 target 在末端表面接触允许，不延伸 moving 轨迹进入其中心。

### 4.3 起点接触、零段与非法输入

- moving 自身始终按引用排除。
- 初始重叠超过 positionEpsilon（包括第三棋、target）为 blocked；原放置/棋盘状态另作诊断，不自动推开棋。
- 起点恰好接触第三棋：仅当该引用在此阶段 departureRefs，`dot(A-O,u)>=-directionEpsilon` 且沿段最小距离不低于 `R-positionEpsilon` 才允许离开。切向外离也允许；朝圆内部必须拒绝。有限直线中这可验证距离单调不减，不用跳过前几像素。
- 普通初始棋贴靠可由快照认证后加入 departureRefs；既有碰撞后的前驱棋由阶段衔接认证。不得把终点接触许可自动继承为下一段的全局忽略。
- rail 连接点仅允许墙碰撞这一既有事件，任何附近棋仍检查；第二段没有无条件起点豁免。
- `L<=lengthEpsilon` 做静态端点重叠检查以提供 blocker；即使空点无阻挡，射击计划也返回 invalid/zeroLength，不当成有效击球。零段不能满足 target 命中；短但非零段照常求根。
- 非有限点/方向/半径、半径<=0、缺 target、失效对象、阶段不连续，均 invalid。旧入口若仍收 length，则负数 invalid，不能 floor 后误当 clear。

### 4.4 建议容差（待真实运行标定，不是物理参数变更）

|量|建议初值|用途|
|---|---:|---|
|positionEpsilon|0.01 WU|浮点径向误差；不吞掉1/2 WU旧穿透|
|contactWindow|0.25 WU|首次接触距离与预期中心匹配|
|lengthEpsilon|0.000001 WU|退化段识别|
|directionEpsilon|0.000001|单位向量点积/切离判定|
|发杆接触法线与计划出射的角差|0.005 rad|误差复核上限，仍不保证袋内动态成功|
|原快照变化阈值|1 WU|保留原重规划触发；小于1 WU也必须按当前 body 重建路径|

所有位置比较使用 WU；平方量比较要正确换算，不能直接给 d² 加0.01。建议通过 R±positionEpsilon 构造阈值，目标真圆求根另判距离容差。微小负的 h²/判别式仅在数值容差内夹0，明显负值不得制造交点。

## 5. 逐调用点迁移表

符号：S=striker 引用（21.76），C=当前候选棋引用（16），T=递归父目标引用（16），P=袋点（无 disc 身份）。普通层 destination=P；递归层 destination=父目标接触中心，必须随 context 传 T。C/所有障碍均使用各自 fixture 半径。表中 target 的括号给出半径，不以括号代替真实引用。

|编号/owner|原起终点定位|moving / target|迁移后起终点与半径|
|---|---|---|---|
|UL-1 `_0x52106f` 出射|`_0x5bf2f1`→destination|C / 普通null，递归T(16)|center(C)→P，或→center(T)-out(T)*32；rm16|
|UL-2 直接|`_0x2c664d`→`_0x445ac0`|S / C(16)|B→H(C,S)，H=C-out(C)*37.76；rm21.76|
|UL-3 反弹前|`_0x3442b5`→`_0x5b4aca`|S / null|B→R，下墙；rm21.76；C是正常障碍|
|UL-4 反弹后|`_0x5b4aca`→`_0x445ac0`|S / C(16)|R→H(C,S)；rm21.76|
|UR-1 `_0x25af2a` 出射|`_0x5ccf72`→destination|C / 普通null，递归T(16)|center(C)→P或父contact；rm16，组合R32|
|UR-2 直接|`_0x259ced`→`_0x549a1b`|S / C(16)|B→重建H(C,S)，R37.76；rm21.76|
|UR-3 反弹前|`_0x38960c`→`_0x8ead75`|S / null|B→R，下墙；C不能提前碰|
|UR-4 反弹后|`_0x8ead75`→`_0x549a1b`|S / C(16)|R→重建H(C,S)，R37.76|
|LL-1 `_0x521eef` 出射|`_0x401fea`→destination|C / 普通null，递归T(16)|center(C)→P或父contact；rm16，组合R32|
|LL-2 直接|`_0x41e2cf`→`_0x10f68c`|S / C(16)|B→重建H(C,S)，R37.76|
|LL-3 反弹前|`_0x1590c9`→`_0x2fcc90`|S / null|B→R，右墙；C是正常障碍|
|LL-4 反弹后|`_0x2fcc90`→`_0x10f68c`|S / C(16)|R→重建H(C,S)，R37.76|
|LR-1 `_0x30849b` 出射|`_0x42b5f4`→destination|C / 普通null，递归T(16)|center(C)→P或父contact；rm16，组合R32|
|LR-2 直接|`_0x296671`→`_0xb71b68`|S / C(16)|B→重建H(C,S)，R37.76|
|LR-3 反弹前|`_0x226e70`→`_0x2cc74c`|S / null|B→R，左墙；C是正常障碍|
|LR-4 反弹后|`_0x2cc74c`→`_0xb71b68`|S / C(16)|R→重建H(C,S)，R37.76|

这些行都不再用旧 step 作为半径。checkOutgoing=false 不能免除最后 validatePlan 的出射检查。直接段的 B、反弹段 B/R 和 H 改为当前有效 body 几何计算；不能改了 H 却复用旧角度、dist、镜像反弹点。保留原枚举次序、hDot阈值和评分主体，只用有向合法性作前置过滤，距离按新几何重新计算。

墙中心轨迹连接点按原 board 和边框26构造：上两袋用 `R.y=board.y+board.height-26-21.76`；左下用 `R.x=board.x+board.width-26-21.76`；右下用 `R.x=board.x+26+21.76`。R 不是袋口/目标棋，需镜像法解有限墙段内反射点，确认未落在角袋开口/非墙区域；墙袋真实边界验收仍待完整运行工程。

### 5.1 四个递归入口及 context

|owner|旧递归 destination 局部变量|必须新增传递|
|---|---|---|
|`_0x52106f`|`_0x4191c3`|父T引用、out(T)、T后续段、阶段context|
|`_0x25af2a`|`_0x592de6`|同上|
|`_0x521eef`|`_0x2b4a5f`|同上|
|`_0x30849b`|`_0xf51964`|同上|

建议第7个私有 context 参数，保持前6个旧参数角色。递归 destination 从 `T-out(T)*30` 改成 `T-out(T)*32`。递归 candidates 排除 `C===T` 的自组合，目标T保留在障碍scene中；不能因T是父目标就从所有段删除。

实际计划顺序应为：S→H(C,S)（或S→R→H）→切换moving为C，C→H(T,C)→切换moving为T，T→P。父层先验出射只是粗筛，拼成计划后再按阶段复核全链。

### 5.2 阶段姿态：避免组合的另一类误杀

只传身份仍不够：在检查 T→袋时，如果仍把 C 放在其击前坐标，可能错误挡路；反之永久忽略C会漏掉前驱障碍。

设计用只读 pose overlay：S在击中C时的中心更新为H(C,S)，C在击中T时更新为H(T,C)，T开始出射时仍为原中心。T→P 阶段中C仍是障碍，只在起点已认证的切离接触上给 departureRefs 许可；S也按其最近已知接触中心保留在该阶段scene。C出射阶段同理保留S的接触姿态。不能因moving切换就把上一moving永久删除。

这是“前驱停在接触点”的轻量几何近似：没有证明碰撞后的S/C会静止，斜击余速、同步运动可能产生不同障碍位置。本文既不以击前坐标伪造完整组合判定，也不宣称该近似覆盖动态多体。几何上合法的组合保留进入候选；其动态可接受性必须用真实Planck回归闭合。若要求绝对动态安全，需另立仿真预测范围，不能在本任务偷偷加重型求解器。

## 6. fallback、最终提交与无路径

### 6.1 fallback `_0x3d12d7`

保留其随机目标/空基线搜索策略和既有 `_carromFindOpenBaseline()`，但保留选中目标对象T。不能仅 `{pos,dir}` 指向中心后发杆。

对B到T中心的方向v构造首次表面接触中心 `H=T-v*37.76`，创建S→H target段；fallback不承诺进袋，expectedOutgoingUnit=v。扫描全部第三棋及目标首次接触。每个已有随机/扫描候选用同一合法性检查；有界找不到则返回null。候选长度不得负/零；离目标近但合法的短段不能因不足step而漏检。

基线寻找与路径寻找须分开计数；不要增加无上限随机 while。建议每次 fallback 最多检查32个路径候选（预算建议，不是旧代码事实）；保持原最终同turn最多2次重试，超过或无候选走既有无杆路径。正常四角候选被几何拒绝时，fallback仍不能绕开完整检查。

### 6.2 最终 `_0x4b3cc6` 的稳定提交边界

在设置shotTurn/调用shoot之前，保留所有原guard并增加：

1. 旧round/turn一致、尚未提交、棋盘活动对象/fixture有效且静止。
2. 对象引用核对和当前body快照；已有 `_carromAiBoardChanged` 对引用、组、缺失、重复、非有限和大于1 WU差异的检查保留。未超过1也按当前坐标重建H/R/整条计划并查放置和路径，不直接接受旧几何。
3. 最终实际角度（含随机误差）与实际pos求射线和反弹点。若从接口角度到shoot角度存在PI转换，必须通过真实速度/输入测试核实，不凭符号名猜方向。验证实际首碰是计划target，接触点在contactWindow内且法线出射角差<=0.005rad；所有后续阶段重建后再检查。
4. 误差策略建议：保留随机误差来源，最多4个样本逐个验证；都不合法时试零误差同一计划；仍不合法则有界重规划/原2次fallback机制。把最终批准的error保存在候选且只使用这一值，瞄准Tween后不再次随机。严格接触约束可能削弱旧随机“失手率”，必须记录候选/误差接受率及胜率变化；这属于本路径修复的明确工程建议，不是已确认的难度改版。
5. 只有最终clear才设置shotTurn并一次shoot。路径invalid/blocked沿用重试及无杆结算，不能让旧回调再发杆。

反弹误差不能仅旋转第一段却保持旧R/H：重新求墙交点、反射方向及target首碰。不合法镜像/开口反弹直接拒绝。这个复核只验证几何计划，不预测摩擦、旋转、墙恢复系数和进袋概率。

### 6.3 queen 与一次结算

无路径、非法参数、重试耗尽保持原分支：普通 queen 待cover (`_0x5d148e===1 && _0x4268e2`) 或自由模式 `queen.phase==='pending'`，记shotTurn并设 `_0x5ebd99=false`，调用 `_0xbdafb3(turn)`；其他情况 `_0x5e7a5f()` 交回玩家。不可统一直接跳回合。

保留round/turn/settledTurn/shotTurn/retryTurn/retryCount、Tween/定时器回合捕获和一次提交guard。重开、退出、广告返回后的旧回调不得用新棋盘身份继续提交。

## 7. 可复现假数据：手推规格，未执行

统一 moving 在A，rm=16（S用21.76）；非S障碍/target半径16。u沿A→B，expectedContact=B，除背撞例外出射+n为(+1,0)。每例独立scene，moving引用M必须加入scene以核验自排除；target用独立引用T，普通障碍O。未说明 departureRefs 的例子为空。坐标可整体平移至棋盘内部，几何预期不变；这些不是原版残局截图。

|编号|数据 WU|手推预期与覆盖|
|---|---|---|
|G01 首段|A(0,0),B(90,0),O(-10,20)，旧step30|新blocked，起点距22.36<32；旧最近第1点距44.72>27而漏检|
|G02 尾段|A(0,0),B(59,0),O(75,20)，旧step30|新blocked，尾端距25.61<32；旧末点30距49.24>27而漏检|
|G03 短段|A(0,0),B(5,0),O(20,25)，旧step30|新blocked，末端距29.15<32；起点约32.016不重叠；旧steps0直接false|
|G04 真实半径|A(0,0),B(90,0),O(45,30)|新blocked，30<32；旧最近采样/投影距离>27漏检|
|G05 旧大采样球误挡|S:A(0,0),B(130.56,0),O(43.52,38.5)，无target|新clear，38.5>37.76+0.01；旧样点39.168阈值blocked|
|G06 合法目标棋|A(0,0),B(68,0),T(100,0)|clear；R32，首碰s68正好末端、n(+1,0)；M自身不挡|
|G07 合法striker目标|S:A(0,0),B(62.24,0),T(100,0)|clear；R37.76，首碰62.24|
|G08 旧contact穿透|S:A(0,0),B(63.24,0),T(100,0)|blocked；末距36.76，穿透1；不能靠target豁免放行|
|G09 组合旧contact|A(0,0),B(70,0),T(100,0)|blocked；穿透2，首碰68；改成68恢复合法|
|G10 目标提前/穿过|A(0,0),B(168,0),T(100,0)|blocked；first68，不是末端；不能全局ignore T|
|G11 背面命中|A(200,0),B(132,0),T(100,0)，expectedOutgoing(+1,0)|blocked；接触n(-1,0)，背离出射；abs(dot)仍可能1|
|G12 第三棋抢先|A(0,0),B(68,0),T(100,0),O(50,0)|blocked；O首碰18早于T68|
|G13 末端第三棋切触|A(0,0),B(68,0),T(100,0),O(68,32)|blocked；O于末端切触，不能借T许可通过|
|G14 起点向外离开|A(0,0),B(60,0),O(-32,0)，departureRefs={O}|clear；初距32且沿段递增；若未认证许可则blocked|
|G15 起点切向离开|A(0,0),B(60,0),O(0,32)，departureRefs={O}|clear；距离sqrt(s²+32²)不减，不进入|
|G16 起点进入|A(0,0),B(60,0),O(32,0)，departureRefs={O}|blocked；初接触后进入，许可不等于排除|
|G17 起点已有穿透|A(0,0),B(60,0),O(-31,0)，departureRefs={O}|blocked；1WU初穿透不修正、不忽略|
|G18 近目标有效短段|A(67,0),B(68,0),T(100,0)|clear；首碰距1，不按step早退|
|G19 零段|A=B(0,0)，无障碍/或O(20,0)|无障碍invalid/zeroLength；有O为重叠诊断，均不可发杆|
|G20 非有限/负长度|A.x=NaN；或半径0；或旧length=-1|invalid，布尔阻挡adapter返回true|
|G21 跨组同id|M.id=0、O.id=0但不同对象；O(45,0)，A(0,0),B(90,0)|blocked；只有M引用排除，不按id过滤O|
|G22 同坐标不同对象|M(0,0)，另O(0,0)|blocked；不能按坐标排除O|

分段/生命周期补充规格：

- C01 一层合法组合：S初始(-100,0)，C(0,0)，T(100,0)，袋点P(200,0)。S→(-37.76,0)，C→(68,0)，T→P。阶段2 S在(-37.76,0)为认证离开接触；阶段3 C在(68,0)为认证离开接触。静态计划预期clear，旧自组合 `C===T` 必须invalid。Planck真实动态/袋点有效性未验证。
- C02 组合父目标提前碰撞：把S→C路线改为途经T的路径；入射段target仍C，T必须普通障碍，不因递归父引用被忽略。
- C03 前驱再次成为障碍：第三阶段 moving=T，A(100,0),B(0,0)，scene C在(68,0)。预期blocked，因为T向前驱内部运动；换moving不永久ignore C。
- B01 反弹连接：S A(0,0)→R(80,0)→H(80,80)，C(80,117.76)，O(80,-30)。在不校验墙的纯分段假数据中，第一段末端距30<37.76应blocked，第二段同样查起点。这是连接附近棋不可开盲区的断言，不是声称该直角折线是原墙合法反射。
- B02 反弹前目标早碰：同A/R，C(60,0)，第一段target=null。应blocked；把C只放到第二段target名单不等于第一段忽略C。
- B03 合法镜像反弹无障碍：在完整工程取真实有限墙、镜像解R，生成S→R→H；两个闭段同时clear且法线反射有效才保留候选，需真实fixture测试，不使用B01折线充当物理验收。
- L01 原候选全部blocked且fallback全部blocked：不shoot，最多2次原重试后结算；普通模式无queen待cover正常交玩家。
- L02 同L01，但普通queen待cover/自由queen pending：调用原cover失败结算恰好一次，确认queen回置/phase按原规则处理。
- L03 搜索后T移走/删除body/同id替换为新引用：最终invalid或重规划；旧plan不能引用新对象冒充旧T。
- L04 搜索后位移0.5WU：旧snapshot可能未触发changed，但最终重建几何仍执行；位移2WU触发原重规划。
- L05 error使第一段先撞O或错过目标：拒绝该error；换零error或原有界重规划；只能批准最终验证过的error一次。
- L06 重开/退出/广告返回：旧round/turn回调零次发杆，新回合只提交一次，重复结算调用不重复奖励。

建议实现时把G系列做数据驱动单测，B/C做validatePlan单测，L系列用注入状态与真实浏览器事件验证。随机测试固定种子，覆盖旋转/平移不变性、端点交换对第三棋阻挡的对称性（target有向性不要求对称）、R±epsilon、长段与1e-5短段。失败输出种子、快照、引用标签和firstDistance，以复现而不是只输出PASS。

## 8. 最小改动范围与性能预算

### 8.1 后续代码阶段允许的最小补丁集合

1. 新增纯几何checker、半径adapter、phase scene/plan validator（尽量局部命名 `_carrom...`，中文解释注释）。
2. `_0x3ea989` owner及16处实参迁移；四函数只新增context、真实contact构造、受影响角度/dist/R重算、有向候选过滤与私有plan。保持搜索阈值/遍历/递归深度。
3. 四个自身递归入口传父引用与后续段，拼接后阶段复核；消除自组合。
4. 放置检测调用统一真实接触半径及相同容差；不改玩家拖条、墙、袋、计分。
5. fallback保留目标、检查首碰、有限候选/无路径；候选筛选、`_0xd6b627`快照/plan交接、`_0x223471`error固定、`_0x4b3cc6`提交前复核。
6. 新增单测/集成/浏览器验收脚本及证据输出，默认关闭几何调试叠层。

不整文件反混淆、不替换PIXI/Planck、不修改规则owner、皮肤/资源、广告/存档模块；参考研究源码不当作新构建代码。实施前备份目标源码并记当前SHA256，逐hunk对照；交付有效diff与可回退版本。当前阶段没有执行以上修改。

### 8.2 性能设计与测量

- 单段扫描N个活动圆：O(N)，无按长度/step的循环。最近点快速拒绝，用平方距离；仅可接触对象求平方根和首碰。活动棋引用去重及半径快照每次搜索一次，不在每个checker里concat三个数组。
- 单层候选近似4袋×N×(最多7直接+4反弹)，每计划2~3段；检测成本约O(N²)。一层组合最坏带来额外N枚父/中间棋枚举，可能O(N³)，不能声称“换成闭段后整体恒定时间”。保留原阈值/提前break，不扩大深度。
- 最终复核只有获选计划的有限段，O(N×段数)。scene overlay只更新少量pose，可用Map/复用数组，避免每候选深克隆整棋盘和跨回合引用泄漏。
- 建议性能门槛（尚未测）：单段p95<=0.1ms；19枚活动棋搜索p95<=16ms、组合压力p95<=32ms；若主线程长任务超过50ms则失败并考虑时间分片，而不是静默截断并强发fallback。具体设备须声明，桌面结果不能代替低端手机。
- 每个快照记录候选数、四类拒绝原因、checker调用数、圆测试数、根计算数、直接/反弹/组合比例、fallback率、zero-error率、搜索耗时p50/p95/p99。分别记录包体、加载、内存、目标设备；当前均未测。

## 9. 回归与验收计划（未执行）

### 9.1 几何及行为门槛

- 16处机械调用清单与本文逐项对齐，禁用漏参旧入口；所有target有引用，moving切换正确；不能残留15构造的物理contact或旧sample大圈。
- G/B/C合成数据实际执行且断言全部满足；记录数值误差，不把target合法接触判blocked、不因同id误排第三棋。
- 固定残局/固定随机种子对比原版和补丁：可说明的差异是首尾阻挡恢复、真实半径阻挡恢复、旧过大采样误挡解除、背撞剔除和错误contact修正。若合法直接/反弹/组合在无第三棋情况下消失，必须逐例诊断，不能用“更保守所以正常”掩盖。
- 回合/cover/罚杆/奖励同规则基线一致；无候选不挂起、不强发，不重复提交；保留原一层组合及目标模式选择。
- 搜索静态clear只代表几何通过。真实Planck记录每步body坐标、速度、首碰引用、墙碰位置和入袋事件；首碰应与计划一致，进袋成败及偏差另计。

### 9.2 物理、输入与浏览器

相同seed、力度、pos、dir、最终error，在1/60固定步上运行；以30/60/120Hz渲染驱动和模拟慢帧/暂停/恢复进行相同输入复测。不要为了通过改原物理步长。

建议动态判定：首碰对象/接触顺序完全一致；不同渲染节拍同输入下固定物理步事件顺序一致；中心位置差初始预算<=0.5WU（须报告原版稳定性和实际最大值），若超预算定位ticker accumulator/更新顺序而非放宽几何半径。墙/袋恢复系数、摩擦、休眠和角袋碰撞以真实fixture为准。当前入袋逻辑是中心到袋点<=20触发，要分别验“路径到袋点没有棋阻挡”和“真实物理入袋”，不能把点目标当半径16的棋。

真实浏览器验收应启动本地静态服务器，访问最终dist，覆盖桌面与手机视口：菜单→开局→基线真实拖动→瞄准力度→释放→AI一杆→无路径/queen结算→暂停恢复→重开；检查console/pageerror、默认英文和中文locale仍英文，输出截图、事件序列和JSON证据到evidence，并自动停止服务器。单参考JS与模拟PIXI stub运行不能冒充这项验收。

### 9.3 构建/发布要求与本轮状态

后续真正代码/测试阶段必须在最后一次源码/资源修改之后以及每次恢复attempt重新执行：`npm run build`、`npm test`、`npm run check`。check必须访问最终dist、真实启动Chromium验证；失败修复后全部重验，验证后不再重建/修改dist。试玩只能读取dist/index.html及相对资源，展开<10MB；源码和试玩ZIP写releases，证据写evidence。

本轮仅prototype，无package.json/可运行工程，未执行这些命令，未引用上一attempt旧日志当通过；没有dist、releases、截图或测试PASS。本文写入后的文件回读仅证明报告可读，不证明几何实现/游戏已验收。

|验收项|当前结论|实际证据|
|---|---|---|
|参考全文静态阅读、核心owner/16调用/fixture定位|PASS（仅静态取证）|本轮及恢复前合法reference读取结果，函数/实参锚点|
|原型设计、分段接口、调用迁移、假数据规格|设计交付|本文；未集成未执行|
|机械调用计数/AST穷尽证明|BLOCKED|未执行源码分析脚本；16处为静态定位清单|
|npm构建/单测/check|BLOCKED|当前只有参考JS，无完整运行工程；本阶段未执行|
|真实Planck、多体组合、墙袋、英文贴图、手机性能|BLOCKED|没有真实浏览器/目标设备证据|
|完整游戏安全验收|BLOCKED|不得从手推算例或路径clear推出安全|

## 10. 未知清单与闭合路径

|编号|缺口/影响|已有证据|闭合方式/状态|
|---|---|---|---|
|U01|完整运行依赖、入口、资产和版本未提供，无法构建原版|单JS引用PIXI、Planck、Howler、GameSnacks、CarromDiscRules、CarromLocalSave等；部分实现/适配在JS内但不构成完整工程|后续集成提供/核验完整H5；BLOCKED，不要求本轮用户为报告补包|
|U02|canvas-web标签与参考PIXI/Planck不一致|真实Application/Circle/world.step证据|本报告保持分析既有工程；只有实施引擎迁移时需request_user_input确认选型/范围；NEEDS_CONTEXT|
|U03|机械全调用计数及字符串旋转映射未执行|全文读到字符串表；16处路径调用逐项静态定位|实现前生成AST/文本清单、原签名调用全部校验；BLOCKED，未声称动态解码或机器穷尽证明|
|U04|墙体/角袋有效有限区间和各皮肤对齐尚未动态核验|原R公式、board变量及袋中心约(61,362)/(579,362)/(61,886)/(579,886)的静态线索|完整工程body fixture/袋点定义精确复核及镜像墙事件日志；BLOCKED；上述近似袋点不作为本方案硬编码|
|U05|组合前驱余速/碰撞后pose并非停在contact|阶段overlay明确近似，原评分非完整物理解|真实Planck固定步组合回归；如要求动态绝对保证另立预测仿真范围；BLOCKED|
|U06|随机error过滤可能影响失手率/AI胜率|原存在约±0.05..0.1rad随机扰动；本设计严格合法性过滤|固定seed统计误差/候选接受率、回合与胜率对比；BLOCKED；本文不是用户确认难度变化|
|U07|英文界面/贴图、触控/慢帧和内存/加载没有验收|原字符串有英文文案，未读取真实完整资产|dist浏览器中文locale、桌面/手机输入及资源核验；BLOCKED|
|U08|几何容差与Planck实际接触slop/版本匹配未标定|真实半径和固定1/60已取证|运行记录fixture、接触法线、首次碰撞及R±epsilon；BLOCKED；不得把0.01当引擎真实slop|

## 11. 交付记录

实际产物：`/workflow/prototype.md`，唯一新增设计文件。参考源码保持未修改；没有美术/源码包/试玩ZIP。报告包含设计决策、参考路径、接口与16处迁移、边界假数据、性能及真实验收计划。本轮针对连接错误恢复读取并完成文档交付，不把中断前的工作或未经执行的计划当验证成功。
