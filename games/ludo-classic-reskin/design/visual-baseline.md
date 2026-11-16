# 原版视觉与资源复用基线

本文件为原型规格，以下运行路径均为计划；本轮没有提取、生成或合入资源。

## 1. 画面基准与布局

实际看过 `reference-assets/original-super-preview.png`：暗紫菱形低对比底、近满宽棋盘、红左上/绿右上/蓝左下/黄右下、浅圆营地、立体亮面棋子，上方与下方骰子座及小头像。Just预览的蓝底、粗金边、大品牌标题和四周大头像不整体移入；仅作为棋子高光、骰子厚度与动作补充，不抢占棋盘面积。

逻辑场景默认360×600，等比完整展示；棋盘有效15×15网格内矩形 `(12,126,336,336)`，格22.4单位（外框在其外侧少量留边，加载实图后标定）。顶部0…44放小LUDO/设置入口，44…118放红、绿玩家头像/骰子座；棋盘126…462；470…544放蓝、黄头像/骰子座；550…594放紧凑合法棋子编号条/一句状态。四席仅激活当前座骰子按钮，其余显示静态座；两席蓝下方、绿上方，缺席营地仍保持原版结构。

手机按 `min(可用宽/360,可用高/600)` 等比缩放，扣除安全区；320×568、360×640、390×844一屏同时看完整棋盘和可掷骰子，不滚动寻找操作。桌面1280×800保持同一场景等比居中、两侧仅底色，不改成后台布局。矮屏优先压缩空隙/标题、保棋盘与骰子，不拉伸纹理。CSS画布、内部DPR（建议封顶2）与指针坐标用同一变换。

主骰子、设置、重开及编号选择按钮最少44×44 CSSpx（缩放后仍需达标）。棋子贴图本身不能普遍达到44px：支持棋盘自然点子，同时在底部提供最多4个44px语义编号按钮，使用同一合法动作；相邻或叠子有歧义时不得扩大相互覆盖命中区后随机选。编号条是贴近HUD的小控件，不是网页大卡片。Tab/Enter/Space可操作，状态有中文aria-live，音效可关闭、首交互解锁。

## 2. 已定位资源 → 计划运行引用

前缀约定：SZIP=`ref/公司skill整合/AHAgames/94034_Ludo_Superstar/Ludo_Superstar.zip`；SJ=`www.hnyigegame.com/Ludo_Superstar/game/`。JZIP=`ref/公司skill整合/AHAgames/82251_Just_Ludo/Just_Ludo.zip`；JJ=`www.volcanoh5game.com/Just_Ludo/`。表中的帧来源是已读普通ZIP条目，不是运行文件。由config的UUID、native版本和packs静态解析实际PNG；哈希/尺寸/alpha未实测时不填写假值。

| 原路径 / 帧 | 计划运行路径 → 用途 | 处理与已知契约 |
|---|---|---|
| SZIP `SJ loading/assets/resources/import/0f/0f000441e.f6f55.json`，skin3-0.plist / `original_img_center_blue` | `public/assets/original/super-board-atlas.png` + `super-board-frames.json` → 棋盘底与中心 | imported，保留；rect[1445,1187,586,585]、originalSize586×585、offset0。需实看native确认底图是否已含营地/标记，避免双画。不是skin_original_board商店缩略图。|
| 同上 `original_img_base_bg_hong/huang` | 同一原图集 → 红/黄圆营地 | imported，保留；233×233、rect[1405,1774,233,233]/[1640,1774,233,233]。蓝/绿对应实际帧待美术局部定位，不能擅自用新图替代。|
| 同上 `original_img_wujiaoxing`、`original_img_sanjiao_*` | 同一图集 → 四星安全格和四色起点箭头 | imported，保留；星27×26；红/黄15×17、蓝/绿17×15。移除barrier显示，不用其15×33贴图暗示锁门。|
| SZIP `SJ loading/assets/resources/import/0b/0b0754561.b16fd.json`，skin1.plist / `original_img_chess_*` | `public/assets/original/super-token-dice-atlas.png` + frames.json → 四色棋子 | imported，保留高光和软alpha；蓝32×53（rotated）、红32×52（rotated）、绿/黄33×53。蓝rect[894,298,32,53]、红[949,298,32,52]、绿[932,117,33,53]、黄[897,117,33,53]，offset0。按原尺寸还原，底座锚到格中心，不把整图中心当底座。|
| 同上 `original_dice_points_1…6` | 同一原图集 → 最终骰子点数，不决定随机 | imported；采样104×106、originalSize220×220、offset[4,3]。六个rect按点数为[1198,390]、[1304,390]、[1221,115]、[1324,1]、[1312,223]、[1327,109]，宽高均104/106；不得抹掉trim空白再误用旧锚点。|
| SZIP `SJ loading/assets/resources/import/0c/0c67ce8ea.b217e.json` / dice_anim | `public/assets/original/super-dice-frames/` + `dice-animation.json` → 真实翻面序列 | imported；0…24号合成帧，originalSize220×220，逐帧rect与offset不同；dice0原Size200×200。由clip引用关系还原顺序，不按包条目/JSON存放顺序排序；不纳入负时间预置帧作为播放帧。|
| S config `ZiYuan/cmn/img_game_my_bg` / `img_game_other_bg` 与PlayerInfo相关头像 | `public/assets/original/super-hud/` → 上下座框和小头像 | imported；已定位语义路径，具体native/头像帧、尺寸/alpha/锚点美术阶段解析与视觉核验。只选实际离线库文件，不联网补头像；缺少可复用头像如实报告，不假装已提取。|
| S config `Music/roll_dice`、`chess_walk`、`chess_be_eaten`、`chess_arrive_terminal`、`settlement_win` | `public/assets/audio/{roll,step,capture,home,win}.mp3` → 对应动作音效 | imported，首选S；roll真实native为 `SJ assets/resources/native/f0/f08dedb0-3c9e-4f7b-b58b-9ebf05f7c389.ed0db.mp3`，step=`.../a8/a889c8f7-f51b-405e-9030-9328fba1b580.521b7.mp3`，capture=`.../a2/a2ce3d23-f7c7-4ad7-a2be-f6253f365ffd.28ae1.mp3`，home=`.../f1/f1064f67-47ba-479e-997e-844354533849.5bd25.mp3`，win的精确native成员尚未定位，需逐件确认不猜路径。|
| JZIP `JJ assets/resources/import/0e/0e9b645a7.json` / original1.plist；texture UUID=`68DmCYgNJIuLOlzCesMAFa`，已列native `JJ assets/resources/native/68/680e6098-80d2-48b8-b3a5-cc27ac30015a.png` | `reference-assets/just-original1.png`；必要补充时 `public/assets/original/just-original1.png` + frames.json | imported，主要材质校准/备用，不混用两套锚点。营地236×236，棋子originalSize34×56（红采样34×54且rotated），dice2…6采样96×96、originalSize150×150、offset[-5,-9]；dice1在其它pack，未核对不猜。|
| S原版低对比紫底装饰/标题母版（精确native待美术定位） | `public/assets/reskin/{background-detail,title}.png` → 小装饰/中性LUDO标题 | 仅局部API编辑，标api-edited；底色与格局不换题材。先读取真实母版、API传reference_paths、保持输出尺寸/alpha/锚点；标题不烤中文动态HUD。若原底仅程序底色，可直接保留程序底与实际纹理，仅编辑标题，不能生整屏图。|
| 原版落点圈/terminal或success必要特效（S config已定位Prefab/Animation/terminal/Terminal、settlement/success/Success） | `public/assets/original/effects/` + effect-frames.json → 落点/归家/胜利 | 优先imported少量真帧；禁止整套表情/商店动画包。所需闪光/彩纸运动可Canvas轻量程序化补充，标procedural；不能称API图片或伪造源帧。|

已读图集配置SHA256：S skin1 `f29f427236703e9498d821db0e00322c2e09ad70ed5ca194efd3fc370ff60771`；skin3-0 `578a950e708b5ad497df00e052c340b6f340b73d8d3e6387b2efa1563f0b9d2b`（已读0…8500/9861字符）；J original1 `b7dc298a89ed2b550516133a6a4c4989ac6fe4f9a5b001e9a9b7062c0ea152a4`全文。S skin2 pack已读全文，仅商店板缩略/皮肤预览，不作为游戏主板替代。

## 3. 美术阶段交接门禁

实际采用已选AI美术自动化工作法，补选AI生图与素材换皮、H5Canvas换皮入口；排除默认新题材风格模块。只用工程图片API `generate_art_image` 和真实参考图编辑，不走Codex登录、其它Key或外部CLI；本轮未生成。

美术开始先inspect_assets。只提取选定native和研究配置，不整包解压、不执行参考脚本；素材下public/assets，研究代码只能reference-inputs且不进dist。最终 `workflow/art-manifest.json` 必须非空真实资源清单，每件path、实际sha256、usage、source，并记录imported/api-edited/procedural分类。另补原ZIP成员→原帧→运行文件→渲染用途的逐件映射；本表不能冒充完成清单。

对每件实测宽高、RGBA/alpha统计、透明边缘白/深/实景对照，保留rect、originalSize、offset、rotated、capInsets、锚点与帧序。不重排图集，不未经授权trim/旋转素材；Canvas采样旋转帧需明确解旋转。派生JSON仅是Canvas资源适配，不称Cocos原生图集。API原始输出、参考哈希、提示词、局部编辑范围、后处理与正式文件哈希均保留。高风险功能资源全部保留，无整屏生图校准步骤。原库授权状态未独立核实，来源如实写用户提供参考库。

## 4. 真实时间动画（下游必须实现）

| 演出 | 正常速度规格 |
|---|---|
| 骰子 | 默认833ms（允许600…900ms），30fps原帧序翻面，叠加小幅弹跳/落座；终帧显示dispatch的lastEvent.dice，包括三连6/无路时。动画纹理不能选择骰子结果。|
| 移动 | 每格110ms（允许90…130ms）；按from到to逐格走，营地→0只一跳。每段弧线h约0.25…0.4格，缩放建议1→1.15→1；底座阴影与落点圈120…180ms反馈。原S移动是0.2×速度并放大至1.8，另每段间隔0.1s；本项目采用更克制幅度与无额外100ms停顿，是明确的表现取舍，不声称逐帧原样移植。|
| 吃子 | 落点先80…120ms碰撞/闪圈，再按被吃棋子在提交前的进度逆向逐格回到0，再回原营地；逆路每段30ms，末段100ms easeOut。敌叠子全部演出、可同步退回，不改规则。|
| 归家 | 最后一跳到对应三角终点，300…450ms局部闪光/落点反馈，已归家棋子小范围整齐叠放或计数，不覆盖其它色终点。|
| 胜利 | 归家后800…1200ms克制彩纸，500ms内开始可见；结束显示Canvas结算与44px“再来一局”语义按钮，不显示金币/广告奖励。|
| 提示 | 当前头像边框及合法棋子1.2…1.6s呼吸，alpha/scale变化克制，不持续大圈旋转；减少动态时停止呼吸、瞬时对齐已提交状态，规则不变。|

TaskGate继续管理AI；表现新增小型rAF时间轴与演出epoch（不是重写引擎）。成功动作先同步提交/保存一次，再用提交前后只读快照播；busy期间棋子/骰子/AI锁住，设置/暂停/重开仍可操作。隐藏或暂停取消时间轴和音效并立即对齐已提交结果，不后台补播；恢复后调度恰好一次下一步AI。重开换matchId/epoch、清理旧帧/计时器；刷新加载合法存档，不根据lastEvent重发或重播旧动作。长帧不无限补绘逐格，恢复按取消策略处理。只读动画事件见验收规格。
