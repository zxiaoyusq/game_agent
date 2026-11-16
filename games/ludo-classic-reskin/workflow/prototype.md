# LUDO · 原版贴图与动画版：原型定义

阶段：prototype；attempt=1。仅定义规格，不确认、不发布、不写游戏实现。

## 1. 范围与决策

这是原版结构优先的轻换皮：Superstar 主视觉，Just 补充棋子/骰子材质与动作。保留标准 15×15 十字棋盘、红绿蓝黄功能色、四角圆营地、亮面立体棋子、上下头像/骰子座及紧凑竖屏。只编辑低风险背景小装饰或标题；中文程序字、通用 LUDO 标识，移除旧品牌、广告及商业入口。禁止圆形棋盘、北非题材、网页大卡片、整屏 AI 棋盘及大风景背景。

本局循环：掷骰 → 展示骰子结果 → 从合法棋子中选择 → 逐格移动/吃子/归家演出 → 留席加掷或下一席 → 第一位达到目标者结算 → 再来一局。无金币成长、在线匹配、商业道具、限时失败或完整排名。局时未实测，不承诺分钟数。

技术：原生 Canvas 2D 纹理/图集；规则、输入、渲染和时间演出分离，少量 DOM 语义按钮承担键盘与辅助触控。原 Cocos 包仅静态研究/提取，不运行商业 SDK，不加载 Cocos，也不编写通用引擎。最终独立路径 `ludo-classic-reskin/`，不覆盖原游戏。

## 2. 既有核心是唯一规则真源

已实际读取 `design/reuse-baseline.json` 和全部 `src/{rules,rng,ai,storage,lifecycle}.js`。清单记录上游 API Key / gpt-6.1-sol、run `f4dcc9b6e1de48c4a30af42ff1d2be24` 的来源与 SHA256；这些是引用基线，不是本轮新产物或本轮测试通过证据。

| 决策 | 固定规格及已读接口 |
|---|---|
| 席位 | `ownersFor`：2席 `[0,2]`、3席 `[0,1,2]`、4席 `[0,1,2,3]`；至少一位真人。人机默认首席真人其余 AI，同屏全部真人；席位顺序轮转，首席由既有 RNG 选择。|
| 经典 | `classic`：每队4枚，初始全为 `progress=-1`；4枚全部到56者胜。|
| 快速 | `quick`：每队2枚，首枚进度0、另一枚-1；先有1枚到56者胜。没有吃子解锁归家或绕圈锁门。|
| 路径 | 公共环52格；单棋子公共进度0…50，51…55为5格私道，56为终点，共57个在盘进度。不要把“57进度”写成终点57。|
| 合法走法 | `targetProgress`：只有6能出营，出营仅到0，不再前进6格；在盘加骰子，必须≤56，超点不能选；已归家不能动。|
| 安全格 | `SAFE=[0,8,13,21,26,34,39,47]`，四起点与四星格；私道也安全。安全格可异色共存。|
| 叠子/吃子 | `legalMoves` 只检查最终普通公共格，敌方全部叠子回营；同色可叠、不组成路障，经过敌子不吃、不阻挡。私道不交叉吃子。表现偏移不得改变格号。|
| 回合奖励 | `bonusReasons`：6、吃子、归家任一理由留席加掷一次，多个理由不累计；胜利优先、无额外掷骰。无合法动作直接换席，即使掷到6。|
| 连六 | 第3个连续6保留在 `lastEvent.dice` 中并跳过，不撤销此前移动。非6或换席重置，动画不得重新抽点。|
| 状态/事务 | `awaitRoll → awaitMove → awaitRoll/finished`；ROLL可因无路或三连6直接换席。`dispatch` 同步一次提交移动、吃子、奖励、胜利和轮转，`revision`每成功动作+1。|
| RNG/AI | 原样复用 `mulberry32-v1` + `bounded` 拒绝采样、`freshSeed/seedFromSearch`；不重新设计公平随机。AI原样 `chooseMove`，只选合法动作，不消费或窥视未来 RNG。|

保持 `createMatch/dispatch/makeAction/legalMoves/cellId` 及动作结构不变。代码阶段只做项目独立命名：`MATCH_KEY=ludo-classic-reskin:match:v1`、`SETTINGS_KEY=ludo-classic-reskin:settings:v1`；`rulesVersion` 在 rules创建与 storage校验两处同步换为 `ludo-classic-reskin-1`，拒绝旧项目档，不迁移旧页面/题材文字。中文旧“商队”错误提示改“玩家”，不改规则或接口。本轮不编辑上述源码。

## 3. 十字坐标契约（设计映射，不是原包格号的直接拷贝）

棋盘坐标 `(row,col)` 从左上0开始，向下/向右递增。公共 `P[0…51]` 按以下有序表；绝对格号来自 `cellId(owner,progress)`，不得再用圆形角度推导：

```text
 0…12: (13,6),(12,6),(11,6),(10,6),(9,6),(8,5),(8,4),(8,3),(8,2),(8,1),(8,0),(7,0),(6,0)
13…25: (6,1),(6,2),(6,3),(6,4),(6,5),(5,6),(4,6),(3,6),(2,6),(1,6),(0,6),(0,7),(0,8)
26…38: (1,8),(2,8),(3,8),(4,8),(5,8),(6,9),(6,10),(6,11),(6,12),(6,13),(6,14),(7,14),(8,14)
39…51: (8,13),(8,12),(8,11),(8,10),(8,9),(9,8),(10,8),(11,8),(12,8),(13,8),(14,8),(14,7),(14,6)
```

| owner/颜色/营地 | 出营点 | 私道51…55 | 56终点（三角内） |
|---|---|---|---|
| 0 蓝/左下 | P0=(13,6)，向上 | (13,7),(12,7),(11,7),(10,7),(9,7) | (8,7) |
| 1 红/左上 | P13=(6,1)，向右 | (7,1),(7,2),(7,3),(7,4),(7,5) | (7,6) |
| 2 绿/右上 | P26=(1,8)，向下 | (1,7),(2,7),(3,7),(4,7),(5,7) | (6,7) |
| 3 黄/右下 | P39=(8,13)，向左 | (7,13),(7,12),(7,11),(7,10),(7,9) | (7,8) |

`progress<=50` 用 P[(13*owner+progress)%52]；51…56用所属私道/终点，内部格号52…75不作为P下标。公共P51真实存在，但蓝棋子由P50进入蓝私道，不能再绕P51；其他队同理。星标放P8/P21/P34/P47，起点箭头放P0/P13/P26/P39，不得把星号当唯一安全格。

营地占四角6×6区；基准棋子中心/底座位置为左上 `(2,2),(2,4),(4,2),(4,4)`，其它角列或行+9。最终按原营地纹理四个圆孔作局部标定，保持处于同一角区、不改路径。格中心 `x=boardX+(col+.5)*cellSize`、`y=boardY+(row+.5)*cellSize`；棋子底座锚到格中心，图集 trim/offset 先还原再绘制。静态棋盘若有内边框，先确定有效网格内矩形再映射，不能把整张外边框当225格。

## 4. 布局、资源和演出

详细契约见 `design/visual-baseline.md`，运行门禁见 `design/acceptance.md`。主场景一屏包含棋盘、当前骰子、玩家头像与紧凑棋子选择条；桌面等比居中，不新增左右仪表盘。默认正常动画；“减少动态”为用户选项。演出只读已提交结果、先存后播，动画结束只解锁不再次派发动作。刷新不重掷、不重播已提交旧动作；隐藏/暂停/重开取消旧演出及AI，返回按已提交局面继续。

## 5. 本轮真实证据与参考取舍

参考根 `ref/公司skill整合/AHAgames/`，简称 S=`94034_Ludo_Superstar/Ludo_Superstar.zip`、J=`82251_Just_Ludo/Just_Ludo.zip`。两份 gameInfo已通过read_reference读取。ZIP只分页定位和局部读取，没有整包解压/运行。

| 证据 | SHA256 / 实际读取范围（字符，左闭右开） | 采用与排除 |
|---|---|---|
| S ZIP | `9ec528932dff7b8ee0dff125aa57cc4663e1419435c7143dcef4533d3d3646b7` | 主视觉与动作依据 |
| J ZIP | `190f2525f6b18b7104b5ee5fe28eb91d52996b2d73c9a4b2e8f73311be72de55` | 补充材质/动作依据 |
| S `www.hnyigegame.com/Ludo_Superstar/game/scripts/assets/main/index.a298e.js` | `5fce66c3a08c152c3b3a05957862b8d164c84e82136abea07145336bfde91762`；0…21000、125000…141000、236000…254000 | canChessWalk/getWalkPathArray证明6出营、精确终点；playChessWalkAnim移动与scale、playBeEatenAnim逆路回营。MapGrid原包只吃单枚，锁门/火箭/护罩/LuckManager改概率等全部不移植，项目仍用已有核心吃敌叠子。|
| J `www.volcanoh5game.com/Just_Ludo/assets/main/index.js` | `3334a9a60e060753ae65d2c89ab51376d5cfcd72f614efbe2c9ab9d3dd7d4c0f`；60500…86000 | canWalk、playWalkAnim、playBeEatenAnim与出营；保留动作质感，不带幸运调整与商业逻辑。|
| S `game/loading/assets/resources/import/0c/0c67ce8ea.b217e.json`（以上S主机路径前缀） | `759c137bf862a76d6ae487daa0f7817dcd03cda7587d7e10ac7e45713eda9c08`；全文6193字符 | dice_anim=0.833333s、30fps，0…0.8s共25个非负时间关键帧；另有-0.133333预置关键帧，不误作首播放帧。|
| S resources目录 | `game/loading/assets/resources/config.0bf53.json` 哈希 `400b7586462e8b88a8066bc32aba935edc4b2ffbf82af5e5b24cb6a08801b66b`；0…11000、33000…46671 | paths/UUID/packs/version连接语义名与实际native资源；非全部配置审计。|
| J resources目录 | `assets/resources/config.json` 哈希 `54cda02a5b1d70075ae8790923397194569a0c431fe820ace735e31144e60be9`；全文 | original1图集、棋子/骰子Prefab与音效路径定位。|

两张预览已通过read_file实际查看：`reference-assets/original-super-preview.png`（SHA256来源记录为 `6d59c85086cafd2920fe0d70c45c8ffc8cfdec0876f8018ffa8baaef596542bb`）与 `original-just-preview.png`（`8c60cd75cc5332c6d6df92d0e732f4ab87ece2b35082129da3265df11d29931f`）。源与帧序见已读 `reference-assets/preview-provenance.json`：分别原preview.gif第13/17帧，只作视觉对照，不是棋盘素材或本轮运行截图。

已读冻结 Skill完整入口：casual-game-production、ai-art-automation；配套已读 company-capabilities 与 ui-runtime-delivery；已读四份冻结知识 general、board-games、web-common、canvas-web。美术明确走复用/局部API编辑，不套默认新题材风格。下轮美术应显式补选 `azure-image2-generation/SKILL.md`（AI生图与素材换皮）及 `game-reverse-engineering/modules/h5-canvas-reskin/SKILL.md`（H5Canvas换皮）；它们不在本轮冻结选择内，本轮未自行扩读或声称采用其全文。

## 6. 产物、核验及限制

本轮新产物仅 `workflow/prototype.md`、`design/visual-baseline.md`、`design/acceptance.md`；已有src与预览未改动。真实完成的是文件/图片读取、ZIP局部代码和资源配置核对及规格书面一致性检查。

未执行npm run build/npm test/npm run check：当前是原型阶段且没有package.json、页面、脚本或dist；不存在本轮运行通过、动画截图或包体通过结果。下游必须在最终源码/资源修改后真实执行三条验证，check只访问最终dist且验证后不改dist。未生成图片、未提取运行资源、未商业授权核验、未运行参考引擎/SDK、未真机验收；原包素材为用户提供库来源，不凭“公司素材”推定外部商业授权。

两次参考条目读取失败如实记录：骰子配置最初误用 `game/assets/resources/import/...`，纠正为 `game/loading/assets/resources/import/...` 后全文读取成功；`loading/.../0b931a73e.89ff3.json` 不存在，未据此声称读取成功，头像/提示特效精确native定位交给美术阶段。以上不是规则实现缺陷，也不把文档计划当实现完成。
