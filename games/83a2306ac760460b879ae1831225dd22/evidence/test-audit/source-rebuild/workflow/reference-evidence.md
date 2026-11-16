# 参考证据与研究边界

## 身份和读取

主参考：`ref/公司skill整合/AHAgames/94034_Ludo_Superstar/gameInfo.json`、同目录`Ludo_Superstar.zip`；补充：`ref/公司skill整合/AHAgames/82251_Just_Ludo/gameInfo.json`、`Just_Ludo.zip`。两份元数据已读取，两包均用ZIP工具分页列完索引，仅按需读取代码与提取素材，未执行参考源码。

|包|ZIP字节|条目/展开字节|SHA256|
|---|---:|---:|---|
|Superstar|5213177|651 / 6773526|`9ec528932dff7b8ee0dff125aa57cc4663e1419435c7143dcef4533d3d3646b7`|
|Just|3327654|195 / 5525803|`190f2525f6b18b7104b5ee5fe28eb91d52996b2d73c9a4b2e8f73311be72de55`|

以下`S/`代表Superstar包内`www.hnyigegame.com/Ludo_Superstar/`，`J/`代表Just包内`www.volcanoh5game.com/Just_Ludo/`，不是外网访问证据。

|真实member|研究输入或字段|member SHA256|
|---|---|---|
|S/game/scripts/assets/main/index.a298e.js|`/reference-inputs/superstar-main.js`；Tools、MapGrid、Chess、PlayerInfo、GameScene|`5fce66c3a08c152c3b3a05957862b8d164c84e82136abea07145336bfde91762`|
|J/assets/main/index.js|`/reference-inputs/just-ludo-main.js`；快局、走法、奖励、吃子、暗改骰子|`3334a9a60e060753ae65d2c89ab51376d5cfcd72f614efbe2c9ab9d3dd7d4c0f`|
|S/game/loading/assets/main/config.a298e.json|MapInfo入口pack映射|`9577827f68660eaaa1dbaa4bc37e9e17289c75232f6f6e7e141c140af02de5eb`|
|S/game/loading/assets/main/import/0b/0be10531e.a5010.json|`/reference-inputs/superstar-map-entry.json`；MapInfo|`939a9d1fda59358fd9c388cd19e6e13bb0febd3eebdcc75b0f4e74ecf77a7393`|
|J/assets/main/import/0b/0b5e1c6b1.json|MapInfoFour；与主参考的路径、安全格、门一致|`ec520675982c9b3c6c99742f18fcbad8f9f5f562e9050a56c12346fad24032f5`|
|S/game/assets/main/import/09/09d798ff2.89558.json|`/reference-inputs/superstar-scenes.json`；Game_grass布局节点，皮肤由运行动态替换|`443de521a57ca18e5982203bcb82e54535b79256f6af1e27ce35fe6ec5b554ad`|
|S/game/loading/assets/resources/config.0bf53.json|`/reference-inputs/superstar-resources.json`；逻辑资源名→UUID→pack/native|`400b7586462e8b88a8066bc32aba935edc4b2ffbf82af5e5b24cb6a08801b66b`|
|S/game/loading/assets/resources/import/0b/0b0754561.b16fd.json|`/reference-inputs/superstar-skin1-frames.json`；骰子六面、棋子、旋转trim|`f29f427236703e9498d821db0e00322c2e09ad70ed5ca194efd3fc370ff60771`|
|S/game/loading/assets/resources/import/0f/0f000441e.f6f55.json|`/reference-inputs/superstar-skin3-0-frames.json`；十字棋盘、红黄营地、安全星|`578a950e708b5ad497df00e052c340b6f340b73d8d3e6387b2efa1563f0b9d2b`|
|S/game/loading/assets/resources/import/04/04afb2abe.9a5b4.json|`/reference-inputs/superstar-skin3-1-frames.json`；紫背景、蓝绿营地|`9fb15d9f975f1a6547b8d729347596227e559d202ceead884f12ef410c0f22cb`|
|S/game/loading/assets/resources/import/0c/0c67ce8ea.b217e.json|`/reference-inputs/superstar-dice-animation-pack.json`；dice_anim与滚动帧|`759c137bf862a76d6ae487daa0f7817dcd03cda7587d7e10ac7e45713eda9c08`|
|S/game/loading/assets/resources/import/53/53aa3cf5-0207-4d1f-8c26-3ec42aceb070.b9150.json|原版Dice prefab，220×220、非trim显示，引用dice_anim|`c3b790a926db78dec815fceaae7b5a839995dd719b44d3da3b06bd2d0b85aa23`|

Superstar压缩代码读取字符区间：0–6000、45000–63000、85000–127000、128000–146000、154000–176000、192000–206000、211000–219500、220000–240000；不是全文审计。Just重点行：1233–1240（两子预置）、1721–1742（合法移动及indexOf缺口）、1753–1865（动作结算）、1961–2089（走子与吃子动画、精确终点）、5118–5165（奖励与轮转）、5198起（模式胜负）、10168–10176（单敌子吃子）、12920–12935（连续六点暗改）；地图pack读取0–20000字符并复核8500–11500。场景重点行：69–109及340–397（schema）、529–1080（格子）、1081起（Canvas）、营地棋子段、1247–1257（mapNode/组）、1692–1720（玩家信息）、1776–1889（底图/营地/终点）。

## 已观察的真实图像

全部使用多模态read_file观察，inspect_assets取得实际文件哈希：

|研究图|包内native（S/game/loading/assets/resources/后）|字节 / SHA256|实际观察|
|---|---|---|---|
|`/reference-assets/superstar-skin1.png`|native/8d/8d3956e8-a178-443d-91c2-bf2d36409e71.116ce.png|125874 / `ebecd53c16c8a929a4f884e7f35ec3945f50ebcf65037589912b5087da93dbc1`|含原版白灰立体骰子及亮面四色棋子，也混有其他皮肤；不是所有帧都属original|
|`/reference-assets/superstar-skin3-0.png`|native/94/940d8ae4-6774-4e81-bb4c-8d8fed54226c.5d699.png|229924 / `6f47a04372be65f5afdaa5bb991217c1ebe5a55a3d125c06efa0c547575d6dbb`|原版奶油白格、中央四色箭头、红黄营地与运行棋子，混有海滩等皮肤|
|`/reference-assets/superstar-skin3-1.png`|native/51/5115ecbc-d727-4655-84ac-e700038972d5.b2713.png|9904 / `ded0443028225d1e3375d597850856a2abaa364fbca2249600eb95b6e1a5c72c`|原版紫色斜菱纹背景及蓝绿营地|

这是图集静态证据，不是原版运行截图。图像工具能显示图片，但未用文件头解析器确认实际编码、像素尺寸与alpha通道；黑色显示空区不等于黑底或透明度通过。美术阶段必须确认magic/MIME、alpha、裁切方向与边缘。不声称已取得授权：素材来自用户提供的研究包，外部发布许可需权利方核验。

## 规则证据和取舍

- 两包MapInfo/MapInfoFour一致：52外环+24归家格，4条normal/terminal、安全格8个、门4个；见board-contract.json，禁止把76称外环长度。
- 营地仅6出营，到起点一次；已完成棋子不可走。原版门关闭时normal循环；开门后terminal数组，精确点数。
- Just `getBeEatenChess`仅落点在进入前恰好一敌子时返回目标，安全格分支不吃；多子格免吃，未在合法走法中看到堆叠封路判断。本作采用不封路、多子免吃并写清规则，不套用其他Ludo变体。
- `onPlayerOptCompleted`胜负优先，吃子/归家保留回合；`setTurnPlayerIndex`骰子6保留回合，OR而非奖励队列叠加。
- 连续六点：源码是第四次候选6被改非6，不是常见三六罚停；Just还含首局AI不给6逻辑。本作拒绝暗改、皮肤buff、Luck、新手操纵，骰子独立均匀，无连续六惩罚。
- 快速解锁边界：某子在normal最后格而全队开门，原版terminal.indexOf可能失败。本作按绝对格逐步衔接，下一步正常回本席起点，下一次到门前再进归家道；不瞬移、不凭空提前归家、不永久失去合法动作。这是健壮性修正，不是已实测原版行为。
- 用户真实回答：**“首版统一首名结束；快速保留吃子解锁并扩展所有席位配置”**。本作经典2/3/4席首位四子归家结束；快速每席两子起点、两子营地、吃子永久全队开门、首子归家结束，适用同屏任意真人/AI。原版四人经典/Local争前二结束及Local无快速的限制不复现。

## 摇骰配置

dice_anim UUID `f6kjjXV1JHZYGKAZZnJ+2a`位于0c67ce8ea pack，时长0.8333333333333334秒、sample=30；spriteFrame关键帧-0.13333333333333333、0、1/30、2/30…24/30。负时间是预滚关键帧，不应再增加总时长；正常呈现使用0–0.8的25次换帧，完成时显示已确定的1–6结果面。存在独立“合成_00000…00024”滚动帧和dice0；不能以六点面循环冒充原版滚动帧。配套pack保留每帧UUID引用及trim/offset，后续须沿resources映射到各native，按clip引用顺序还原，不能按文件名排序。

## 真实检查结果与限制

本阶段成功：双包索引及关键源码/配置阅读、字段交叉核对、三张研究图逐项提取/观察/哈希清点、用户规则冲突确认。个别猜测路径读取返回不存在，包括dice UUID独立文件和game/assets的0c67 pack；均未作为成功证据，已通过loading pack定位dice_anim。不做整包解压、不加载参考Cocos。

本阶段未执行npm run build、npm test、npm run check：没有游戏工程，当前仅原型定义，不能把文档研究称为构建/测试通过。未运行浏览器、联网采集、Creator、ADB、真机或发布；未生成AI图、未裁出集成素材、未合入代码。所有reference-inputs禁止打入dist。后续动作见prototype.md。
