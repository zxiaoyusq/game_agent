# AHA Games：三区本地化换皮 AI 生图规范

版本：1.0 · 日期：2026-10-21 · 状态：可用于风格打样与提示词组装，尚未经样张及当地用户验证。

本文件用于后续批量美术生产。当前交付是设计规范与提示词，不包含已生成素材、可直接运行的图集或已完成的游戏换皮。

## 目录

1. [目标、范围与使用方式](#1-目标范围与使用方式)
2. [全局生产契约](#2-全局生产契约)
3. [南亚：彩绘集市](#3-南亚彩绘集市)
4. [尼日利亚：当代社区小店](#4-尼日利亚当代社区小店)
5. [东南亚：社区街市](#5-东南亚社区街市)
6. [六款游戏的主题映射](#6-六款游戏的主题映射)
7. [提示词组装与完整示例](#7-提示词组装与完整示例)
8. [批量生产与文件管理](#8-批量生产与文件管理)
9. [验收与常见失败修正](#9-验收与常见失败修正)
10. [文化参考与未确认事项](#10-文化参考与未确认事项)

## 1. 目标、范围与使用方式

### 1.1 已确定的目标

- 完整重制六款游戏的美术，玩法、代码和交互规则保持原样。
- 风格要有当地生活和工艺辨识度，不能只给原有国际休闲风换一组颜色。
- 以一套生产技术规范承载三组美术方向，不在第一阶段承诺制作十八套完整游戏。
- 地方属性优先通过场景、材质、货品、容器、店面、彩绘和织物表现。
- 保持手机小尺寸下的轮廓、玩法状态和操作信息清楚。

六款原游戏：

| ID | 原名（仅用于资产追踪） | 主要类型 |
|---|---|---|
| 77413 | One Connect | 配对图标与棋盘 |
| 77924 | Candy Crush | 消除棋子、障碍、特效与界面 |
| 94215 | Bubble Shooter GO | 泡泡、发射器、轨迹与特效 |
| 93876 | Tidy Master | 商品、容器、货架与收纳状态 |
| 78388 | Classic Billiard | 球台、球杆、球体与运动界面 |
| 82251 | Just Ludo | 棋盘、骰子、棋子与桌游界面 |

### 1.2 三组的角色

用户提供的 2026-10-10 单日 H5 用户占比：巴基斯坦 15.31%、印度 13.86%、孟加拉国 4.20%；尼日利亚 9.04%；菲律宾 5.00%、印尼 4.03%。

| 风格组 | 涉及国家 | 占比合计 | 制作定位 |
|---|---|---:|---|
| SA | 巴基斯坦、印度、孟加拉国 | 33.37% | 第一套完整主题的优先候选 |
| NG | 尼日利亚 | 9.04% | 独立方向打样，不代表整个非洲 |
| SEA | 菲律宾、印度尼西亚 | 9.03% | 共用制作基础，国家元素分别设计 |

合计 51.44%。这是用户量驱动的制作分组，不是审美偏好调查；不能把单日用户占比解释为风格效果或营收预测。三组也不是发行规则：国家未知的用户、其他国家和中东市场不自动套入其中。

### 1.3 快速使用顺序

1. 选择游戏与原始资源，记录真实用途、尺寸、轮廓、视角和状态。
2. 选择一个地区风格包，以及适用的国家元素包；一次生成不混用多个国家包。
3. 从该地区色板挑选当前资产真正需要的颜色，通常 2—4 个主色即可。
4. 按“通用画法＋地区风格＋国家元素＋资产主体＋原资源契约”组装提示词。
5. 出代表样张，通过风格与几何检查后，建立母版，再扩展同类资产。
6. 生成后校验并修正尺寸、透明度、图集关系与颜色；提示词无法保证这些数值精确成立。

若只制作一套首发资源，建议先采用 SA 的现代彩绘集市方向；PK/IN/BD 各保留一张国家化概念样张供比较。没有确定国家主题之前，使用 SA_BASE，避免随意混入某国专属图案。

## 2. 全局生产契约

### 2.1 共享的是画法与技术规范

| 项目 | 统一要求 |
|---|---|
| 画法 | 清楚的手绘形体、简化块面、有限笔触、适量体积；不是照片、写实 PBR 或厚重油画 |
| 线条 | 外轮廓简洁，局部轻描边；线粗按最终显示尺寸调整，不直接规定所有资产同一像素值 |
| 材质 | 木、彩绘金属、搪瓷、织物、陶器、竹藤等有区分；小图标减少颗粒细节 |
| 光照 | 普通单体优先左上柔光；球体、台球、旧动画已有光向时继承原方向 |
| 体积 | 普通物件可轻微立体化；纯平 UI 保持平面；不能强制所有资源改成等距三维 |
| 装饰 | 有地方辨识度的细节放在背景、边框与容器；棋盘操作区保持干净 |
| 镜头 | 继承原图；正视图、顶视图、侧视图与斜视图分别建母版 |
| 角色 | 非必要不增加新角色；必须替换原角色时保留动作结构与原点，服饰和肤色按具体人物设计 |
| 特效 | 简化花瓣、纸屑、闪光等可以承载主题；范围、时序和命中含义保持原样 |
| 文字 | 非文字素材默认无文字；已有烘焙文字资源需单列，不能因“no text”而漏掉本地化文字 |
| 质感 | 当代、整洁、有生活气息；不把当地生活默认画成破旧、贫困或旅游纪念品陈列 |

以下数字都是设计起点，不是已测出的最优参数：背景装饰细节约占可见区域 10%—20%；操作区装饰尽量控制在 0%—5%。最终以原场景构图、目标手机显示和玩法可读性为准。

### 2.2 三个层级分别控制

| 层级 | 固定项 | 可变化项 |
|---|---|---|
| 技术层 | 资源 ID、命名契约、图集 rect、画布、锚点、骨骼、帧序、碰撞观感 | 仅在现有资源契约容许范围内重绘 |
| 游戏层 | 颜色所对应的类别、牌点、骰点、球号、四方路径、特殊物件状态 | 表面材质、边缘装饰、合理的物件造型 |
| 文化层 | 选定地区/国家包及样张风格 | 店面、背景、包装、器物、纹样、日常货品 |

**地区色板只用于装饰与非功能色。** 泡泡、糖果、Ludo、台球等承担规则信息的颜色，先从原资源建立 ID→颜色/形状映射；不能为了套色板擅自更换、合并或漏掉颜色类别。需要明显换色时，应先证明不破坏原玩法识别与引用契约。

### 2.3 通用正向关键词块：GLOBAL_RENDER_v1

```text
production-oriented 2D mobile game art, clear hand-painted shapes,
clean readable silhouette, simplified color planes, restrained brush texture,
gentle form shading appropriate to the original asset,
consistent edge treatment, contemporary well-kept everyday setting,
readable at the original in-game display size,
match the provided reference camera and composition
```

这个块只规定画法，不加入集市全景、人物、建筑或整套配色。不要把背景描述复制进每一个独立图标。

### 2.4 通用排除关键词块：GLOBAL_EXCLUDE_v1

适用于普通背景、道具与非文字 UI；文字资产另行处理。若后端没有独立负向输入字段，把这些约束改成提示词内的自然语言要求，不能当作通用 API 参数。

```text
photorealism, cinematic depth of field, heavy oil paint texture,
muddy low-contrast colors, excessive micro-patterns, busy gameplay area,
unrequested characters, collage of multiple cultures, tourist souvenir collage,
copied commercial logos, recognizable licensed characters,
watermark, fake writing, invented calligraphy, unintended readable text,
cropped object, duplicated object, inconsistent lighting
```

按任务追加，而不是所有图片机械粘贴：

- 透明单体：`background scenery, floor plane, cast ground shadow, checkerboard pattern, opaque white backdrop, glow halo`。
- 纯背景：`foreground UI, gameplay tokens, score labels, buttons, text baked into the reserved gameplay area`。
- 固定布局重绘：`new layout, moved controls, changed board geometry, extra slots, changed object count`。
- 地方元素：排除本次未选的国家、节庆和宗教图像；不需要把所有宗教名称写进每条提示词。

### 2.5 必须继承的原资源契约

- 图片宽高、alpha 模式、透明留边、可见包围盒、枢轴与旋转方向。
- 九宫格可拉伸区域、图集裁切与旋转、子图坐标、帧名称。
- 动画帧数、帧序、骨骼与挂点；涉及位移的特效不改变可见运动含义。
- 牌面 ID、配对 ID、泡泡半径、瓶口/槽位、台球球袋、棋盘路径与骰点。
- 所有状态：普通、按下、禁用、选中、命中、消失、失败、胜利等，以原包真实状态为准，不自行虚构新状态。

AI 生成图先作为候选；精确裁切、重排、图集回写、色值修正、文字排版需要确定性后处理。整张随机生成的新图集不能直接覆盖原图集。

透明要求需要同时落实到后端设置：使用内置 `image_gen` 时，透明单体设置 `transparent_background: true`，不透明背景设置 `false`；不能只在提示词里写“transparent”。其他后端按其真实能力配置，并检查最终文件 alpha。

## 3. 南亚：彩绘集市

### 3.1 风格卡 SA_PAINTED_BAZAAR_v1

**一句话方向：现代街头小店，搭配手绘彩绘工艺的花卉边框、彩色木作和搪瓷容器。**

区别于原国际休闲风的关键：减少统一塑料玩具质感，增加手刷漆边缘、彩绘器物、实体店面、食品托盘和布棚。地方感来自可识别的生活物件与工艺，而不是给所有按钮挂一圈装饰。

| 项目 | 设计关键词 |
|---|---|
| 形状 | 简化花瓣、叶片、卷草、波浪边、圆角矩形、彩绘金属板轮廓 |
| 材质 | 彩绘木、亮面搪瓷、局部镜面点缀、拉丝金属托盘、棉布棚、暖色灰泥 |
| 场景 | 当代甜品铺、街边水果摊、整洁杂货柜台、社区庭院、街区台球室 |
| 光照 | 暖日光、柔和阴影；金属只用少量清楚的高光 |
| 图案 | 花叶边饰、少量圆点与短条纹；图案集中在外框、盒边、棚布和器物边缘 |
| 情绪 | 热闹、亲切、手作感、日常生活；不是宫廷、奢华婚礼或宗教庆典默认场景 |

### 3.2 配色板

以下色值为原创设计提案，不是“南亚官方配色”或用户偏好统计。

| 角色 | 名称 | HEX | 用途 |
|---|---|---|---|
| 主色 | 彩绘青蓝 | `#168E9B` | 主界面外框、柜台、非功能按钮底 |
| 辅色 | 花卉洋红 | `#C84678` | 花卉纹样、盒边、局部强调 |
| 暖强调 | 金黄 | `#E6AD32` | 奖励装饰、金属边、小面积高光 |
| 次强调 | 珊瑚橙 | `#DE6A45` | 店铺点缀、容器和少量背景物件 |
| 中性亮 | 奶油白 | `#FFF1D8` | 棋盘承托、面板、留白 |
| 中性暖 | 陶土 | `#B96E4D` | 盆器、墙面、背景木作暖部 |
| 暗部 | 深蓝墨 | `#243D55` | 轮廓、暗部与信息承托 |
| 高光 | 暖白 | `#FFF9EF` | 搪瓷与糖点高光 |

建议分配：奶油白/暗部等中性承托约 60%，青蓝主色约 25%，洋红/金黄/橙色等强调约 15%；这是界面与场景的面积起点，不用于规定每个棋子的颜色。

### 3.3 地区通用关键词 SA_BASE

```text
contemporary South Asian neighborhood bazaar-inspired game art,
hand-painted floral enamel edging, colorful painted wood,
warm cream plaster, simple cotton awning, clean metal trays,
teal and cream foundations with restrained magenta and golden accents,
stylized everyday shop objects, decorative detail confined to the edges,
original non-ceremonial ornament, uncluttered gameplay center
```

### 3.4 国家元素包：每次只选一个

| 包 | 适合的元素 | 英文追加词 | 应限制的使用方式 |
|---|---|---|---|
| PK_PAINTED_METAL | 参考巴基斯坦卡车彩绘的花叶、扇形边缘、彩绘金属面板与点状反光装饰 | `Pakistani truck-painting-inspired floral metalwork, simplified painted petals, scalloped painted metal trim, small reflective dot accents` | 不把卡车、人物肖像、文字口号自动加到所有资源；不抄现成作品整幅构图 |
| IN_SHOP_CRAFT | 现代印度街区甜品铺；彩绘木柜、金属甜点托盘、素色棉布、简单花叶店招装饰 | `contemporary Indian neighborhood sweet-shop styling, painted wooden counter, clean metal sweet trays, cotton awning, original simple floral shop ornament` | 不以某一地区店面代表整个印度；首版不默认加入神像、节庆圣物、宫殿、婚礼布景 |
| BD_RICKSHAW_FLORAL | 参考达卡人力车彩绘的花叶、风景色块与明快手刷边缘，用于背景板/器物外框 | `Dhaka rickshaw-painting-inspired floral panels, bold hand-painted flower and leaf shapes, colorful painted shop board, simplified brush-painted edges` | 文化参考限达卡来源，不能宣称代表全部孟加拉国；不把运输工具强行画成游戏主棋子 |

PK 与 BD 的彩绘来源分别见 [R1](#r1) 与 [R2](#r2)。IN_SHOP_CRAFT 是根据日常店铺题材提出的原创组合方向，并非某种覆盖印度所有地区的传统艺术流派；食品和城市细节需按目标国家/城市继续取证。

### 3.5 可用物件词库

| 类别 | 中文候选 | 英文关键词 |
|---|---|---|
| 水果 | 芒果、番石榴、香蕉、石榴、椰子；仅作为候选货品，不声称各国专属 | `mango, guava, banana, pomegranate, coconut` |
| 甜点形态 | 螺旋糖点、圆球甜点、切块奶糖、装盒小点；具体食品名称由已确认参考补足 | `spiral sweet, round syrup sweet, square milk sweet, boxed small sweets` |
| 容器 | 彩绘搪瓷罐、金属托盘、陶杯、编织果篮、纸盒 | `painted enamel tin, clean metal tray, clay cup, woven fruit basket, paper sweet box` |
| 装饰 | 简化花叶、彩绘木边、棉布遮棚、无字店招、手刷墙面 | `simplified floral edging, painted wooden trim, cotton awning, blank painted shop sign, brushed plaster wall` |

词库是可选主体，不是一张图里必须出现的清单。单体素材每次只指定一个主体；食品选择不暗示宗教认证或成分承诺。

### 3.6 禁止漂移与完整参考提示词

常见漂移：阿拉伯宫殿、满屏宝石、大片金色、混合多国国旗、宗教图案、婚礼舞台、欧美糖果城堡、过密传统纹样、仿文字笔画。

```text
Create a decorative shop-counter frame for a 2D mobile game.
Use clear hand-painted shapes and a contemporary South Asian bazaar direction.
Apply original simplified floral enamel edging to painted teal wood,
with warm cream inner panels and small golden accent dots.
Keep the central panel plain and empty for the existing game content.
This is the SA_BASE direction: do not add country-specific symbols.
Follow the provided frame reference exactly for canvas, border thickness,
inner opening, cutouts and transparent areas; add no new protruding decoration.
No text, no people, no complete shop scene, no collage of countries.
Output a single isolated frame with a true transparent background.
```

## 4. 尼日利亚：当代社区小店

### 4.1 风格卡 NG_NEIGHBORHOOD_MARKET_v1

**一句话方向：整洁的当代社区商店，用彩绘木作、金属容器、少量靛蓝织物形成地方感。**

区别于南亚：减少细密卷草和镜面点饰，采用更大的色块、方格、条带与织物边缘。文化参考有具体出处，但不把一个族群的纹样当成尼日利亚所有人的统一标识。

| 项目 | 设计关键词 |
|---|---|
| 形状 | 清楚的矩形货架、粗细有节奏的条带、少量方格和圆点 |
| 材质 | 彩绘木、干净金属罐、搪瓷器物、织物边饰、编织篮、平整墙面 |
| 场景 | 当代社区杂货铺、街角小店、水果柜台、运动俱乐部、庭院桌游 |
| 光照 | 清楚日光，暖亮部与偏蓝阴影；避免泥黄色滤镜 |
| 图案 | 自创几何条带；需要明确约鲁巴工艺参考时才选 NG_YORUBA_ADIRE 包 |
| 情绪 | 当代、活跃、亲切、有经营感；不默认草屋、荒野、野生动物或历史部落场景 |

### 4.2 配色板

| 角色 | 名称 | HEX | 用途 |
|---|---|---|---|
| 主色 | 深靛蓝 | `#263A73` | 外框、织物边、较大承托面 |
| 辅色 | 活力橙 | `#E8843C` | 木柜点缀、少量奖励与按钮装饰 |
| 次色 | 叶绿 | `#2F8F62` | 店面局部、日用品包装 |
| 次色 | 晴空蓝 | `#64AFC8` | 窗框、局部背景与亮色物件 |
| 中性亮 | 棉布奶油 | `#FFF3DB` | 面板、标签留白、棋盘承托 |
| 中性暖 | 暖陶土 | `#B76B4A` | 背景墙、容器与木作暖部 |
| 暗部 | 深蓝灰 | `#263347` | 轮廓、阴影、信息区域 |
| 高光 | 棉白 | `#F7F4E8` | 织物亮部、金属点光 |

建议分配：中性亮/暗承托约 60%，靛蓝约 25%，橙绿蓝强调合计约 15%。靛蓝用于外框时要保证功能物件与背景分离，不能直接把整块玩法底板压成深色。

### 4.3 地区关键词 NG_BASE

```text
contemporary Nigerian neighborhood-shop-inspired game art,
well-kept painted wooden shelves, clean enamel and metal containers,
large confident color blocks, simple original geometric edging,
indigo and cream foundations with restrained orange and green accents,
small woven storage details, lively everyday urban community setting,
clear object separation, uncluttered gameplay area
```

### 4.4 具体工艺元素包 NG_YORUBA_ADIRE

Àdìrẹ 是尼日利亚西南部约鲁巴文化中的靛蓝防染布工艺参考，来源见 [R3](#r3)。该元素包可用于特定主题的少量布艺和边饰，不自动代表全尼日利亚，也不替代对实际目标受众的验证。

```text
Yoruba adire-inspired indigo resist-dye textile accents,
original simplified dot-and-grid cloth pattern,
soft irregular dye edges, restrained blue-and-cream textile edging
```

应用位置：棚布、桌垫边、布袋、面板外侧软装。图标中央、骰点、球号和主要按钮识别图案不叠加染布花纹。若没有明确选用约鲁巴工艺的设计意图，使用 NG_BASE 的原创几何边饰即可。

### 4.5 可用物件词库与禁漂移

| 类别 | 中文候选 | 英文关键词 |
|---|---|---|
| 货品 | 水果、香蕉类货品、饮品、盒装日用品；形态需与选定参考一致 | `fresh fruit, plantain or banana chosen from reference, original drink carton, household goods box` |
| 容器 | 金属罐、搪瓷盆、编织篮、无品牌包装袋 | `clean metal tin, enamel bowl, woven basket, original unbranded product pouch` |
| 店面 | 彩绘木柜、简洁货架、遮棚、无字招牌、布艺桌垫 | `painted shop counter, simple shelving, awning, blank signboard, cloth table runner` |

不要使用：`generic tribal African style, safari, savanna village, tribal masks everywhere, kente as a Nigerian national pattern`。避免以其他国家/群体的特定工艺替代所选来源；来源未核实的“非洲符号”不要直接交给模型自由拼接。

### 4.6 完整参考提示词

```text
Create one isolated enamel storage tin for the Tidy Master reskin.
Use clear hand-painted 2D game-art shapes and the NG_BASE direction.
The tin has a cream body, an indigo lid, one broad orange color band,
and a small original blue-and-cream geometric border.
Show a contemporary everyday shop object, clean and well maintained.
No brand, no label text, no people, no shop background, no ground shadow.
Match the provided original tin reference in silhouette, camera, lid height,
visible bounding box, anchor placement and all transparent margins.
Output exactly one object, fully visible, on a true transparent background.
Do not turn the object into a cultural souvenir or add a mask motif.
```

## 5. 东南亚：社区街市

### 5.1 风格卡 SEA_NEIGHBORHOOD_STALL_v1

**一句话方向：热带社区里的小店与街市，用清楚的棚架、编织、木作和现代生活货品承载地方元素。**

SEA 是生产基础包，不是单一文化。PH 和 ID 必须独立选择国家元素，不能把印尼 Batik、菲律宾招牌与其他国家建筑拼在一张图里。

| 项目 | 设计关键词 |
|---|---|
| 形状 | 开放式售货窗、横向棚檐、木柜、简洁篮筐、植物剪影 |
| 材质 | 彩绘木、竹藤类日常编织、棉布、简洁金属、局部磨砂塑料 |
| 场景 | 当代社区小店、街边水果/饮品摊、带遮棚的桌游角、运动休闲室 |
| 光照 | 明快日光或清楚的店内暖光；首版不依赖重霓虹和复杂夜景 |
| 图案 | 共用包采用原创条带/编织节奏；国家特定纺织图案只进入对应包 |
| 情绪 | 日常、清爽、热闹但有秩序；不默认海岛度假酒店或旅游景点拼贴 |

### 5.2 配色板

| 角色 | 名称 | HEX | 用途 |
|---|---|---|---|
| 主色 | 海青 | `#158F9C` | 店面外框、非功能 UI 与柜体 |
| 辅色 | 珊瑚红 | `#F06B55` | 遮棚、局部商品与强调 |
| 暖强调 | 芒果金 | `#E9B84A` | 小面积边饰与亮部 |
| 次色 | 叶绿 | `#4B8A4C` | 少量植物和店面点缀 |
| 中性亮 | 椰奶白 | `#FFF2D9` | 面板、留白、台面 |
| 中性暖 | 竹木褐 | `#B78B5B` | 木作、编织与背景容器 |
| 暗部 | 深青墨 | `#244B49` | 轮廓与清楚的结构阴影 |
| 高光 | 柔白 | `#F7FCF2` | 瓷器、包装与泡泡高光 |

建议分配：中性承托约 60%，海青约 25%，珊瑚红/芒果金/叶绿合计约 15%。不得把这组配色称为菲律宾或印尼共同的传统配色。

### 5.3 地区关键词 SEA_BASE

```text
contemporary tropical neighborhood-stall-inspired game art,
painted wooden counters, simple awning shapes, everyday woven storage,
clean modern shop fixtures, warm cream and teal foundations,
restrained coral and mango-yellow accents,
fresh daylight, simplified practical objects,
clear silhouettes and an uncluttered gameplay center
```

### 5.4 国家元素包

| 包 | 具体落点 | 英文追加词 | 使用边界 |
|---|---|---|---|
| PH_NEIGHBORHOOD_STORE | 菲律宾社区 sari-sari 小店的售货窗、罐装零食、无品牌小袋货品、彩绘店面与棚檐 | `Filipino sari-sari neighborhood-store-inspired counter, orderly small original product packets, snack jars, painted window frame, simple awning` | 参考实际小店构图，减少遮挡玩法的栅格；默认不摆烟酒，不生成商业品牌；店名另排版 |
| ID_STALL_BATIK_ACCENT | 当代印尼街边小店，木作与编织；可选少量 Batik 工艺启发的原创日常花叶纹样 | `contemporary Indonesian neighborhood-stall styling, painted wood and woven containers, optional original batik-inspired everyday floral cloth accent` | Batik 的具体图案可能有身份/仪式含义；只选已确认适合日常用途的参考，不让模型生成所谓“神秘图腾” |

PH 的小店形态可参考菲律宾贸工部门资料 [R5](#r5)；ID 的 Batik 工艺背景见 [R4](#r4)。这些来源证明题材/工艺存在，不证明当地玩家一定偏好该设计。

### 5.5 可用物件与禁漂移

| 类别 | 中文候选 | 英文关键词 |
|---|---|---|
| 货品 | 芒果、椰子、香蕉、简单饮品、原创包装零食；按国家参考筛选 | `mango, coconut, banana, original drink container, unbranded snack packet` |
| 容器 | 编织篮、竹木托盘、金属饮品罐、玻璃零食罐 | `woven basket, bamboo or wooden tray, metal drink container, clear snack jar` |
| 店面 | 无字售货窗、彩绘木台、遮阳棚、简化植物 | `blank shop window frame, painted wooden counter, sun awning, simplified greenery` |

避免：把东南亚默认画成巴厘岛度假村；把多个国家的寺庙、文字和服饰混在一起；默认加中国式灯笼和仿汉字；用霓虹夜市遮盖游戏主体；以海滩椰树代替所有地方辨识。

### 5.6 完整参考提示词

```text
Create a decorative background for a 2D mobile puzzle game.
Use SEA_BASE with PH_NEIGHBORHOOD_STORE: a contemporary Filipino
sari-sari-inspired shop frontage, orderly original snack jars,
a painted teal wooden counter, a restrained coral awning,
warm cream surfaces and a few everyday woven storage accents.
Match the supplied original background composition and perspective.
Keep the supplied gameplay exclusion mask plain and low contrast;
place shop details outside that mask and outside existing UI safe areas.
No people, no logos, no readable labels, no score display or game pieces.
Do not add Indonesian batik, other countries' monuments or religious imagery.
Render the requested full opaque background canvas with no transparent holes.
```

## 6. 六款游戏的主题映射

### 6.1 三组完整映射

本表是可选的主题扩展路线，不是要求立即生成十八套完整素材。首批先选一组，完成代表样张和一个完整关卡/流程的替换验证。

| 游戏 | SA 彩绘集市 | NG 当代社区小店 | SEA 社区街市 |
|---|---|---|---|
| One Connect | 集市货品配对：水果、简化甜点、彩绘罐与小器物 | 社区商店配对：水果、饮品、搪瓷器物、原创包装 | 小店货品配对：水果、饮品、零食罐与编织容器；PH/ID 道具分别选 |
| Candy Crush | 甜品柜台消除：奶糖/果糖形态、金属托盘和彩绘柜台 | 社区甜点铺：原创糖点、零食罐与靛蓝/橙色店面 | 街市甜品摊：水果糖点、木柜与国家对应布饰 |
| Bubble Shooter GO | 彩绘屋檐下的泡泡游戏：花叶框、彩绘发射器、清楚圆球 | 社区庭院泡泡：彩绘木框、少量织物边、原创玩具发射器 | 遮棚街市泡泡：彩绘木/竹木外观、海青棚檐，PH/ID 装饰独立 |
| Tidy Master | 杂货/甜点铺收纳：罐、盒、托盘、果篮 | 当代小店收纳：商品袋、罐、篮、柜台；按具体参考做包装 | PH 社区小店收纳，或 ID 街边小店收纳；不共用国家特定标签 |
| Classic Billiard | 街区台球室：彩绘木台沿、简洁店面与少量花叶软装 | 现代社区台球俱乐部：靛蓝/奶油墙面、彩绘木与少量布艺 | 社区运动休闲室：彩绘木、简洁棚架/窗框，避免把台球台做成竹编玩具 |
| Just Ludo | 庭院桌游：彩绘木棋盘外框、棉布桌垫、简洁庭院 | 社区桌游角：木作、原创几何布垫；可选约鲁巴工艺主题 | 棚檐下的家庭桌游：木作、日常编织桌垫，按国家选边饰 |

### 6.2 每款的正向关键词与不能改变的部分

#### One Connect · 77413

```text
one clearly identifiable everyday market object per tile,
bold distinct silhouette, restrained local material detail,
consistent camera and scale within the same tile family,
clean edge, generous shape separation, matching pair identity preserved
```

- 每个配对 ID 只绑定一种新物件；同 ID 的全部状态保持同一造型。
- 不同 ID 不使用“同形不同花纹”作为唯一差异，先确保轮廓可辨。
- 若原棋子是纯平面，采用平面图标；原资源有斜视角时才沿用斜视。
- 生成纯图标时不带摊位、托盘组合、文字、手或人物。

#### Candy Crush · 77924

```text
original stylized sweet game token,
distinct category silhouette, simple appetizing form shading,
local sweet-shop material cues, consistent visual mass,
preserve original functional color and special-token distinction
```

- 配色表不能覆盖原来的功能颜色映射。
- 普通块、条纹/特殊块、障碍与破坏状态分别列清单，原包存在什么就覆盖什么。
- 蜿蜒食品造型要简化成适合原碰撞观感的体积，不外伸到相邻格。
- 本轮原游戏名仅作追踪，正式标题、角色和宣传图采用原创方案。

#### Bubble Shooter GO · 94215

```text
single perfectly round bubble game token,
preserve the original radius and category color,
clean glossy highlight in the reference lighting direction,
restrained decorative detail, readable special-bubble symbol
```

- 地方纹样主要放在背景、发射器、外框；普通球面不铺密集花纹。
- 不把圆球变成花瓣形、椭圆、器皿或多件组合。
- 命中、爆炸、轨迹、替换球和技能状态的尺寸与信息意义保持一致。
- 玻璃感泡泡可以有内部半透明，但画布外侧仍应真透明；须实测 alpha。

#### Tidy Master · 93876

```text
single contemporary neighborhood-shop product,
original unbranded packaging, locally grounded container materials,
clear front silhouette, clean separable edges,
match the original shelf-slot and drag-footprint contract
```

- 货品要能贴合原槽位和拖拽轮廓；宽高、开口、盖子、支撑面不能随意改。
- 包装身份由色块/图标表达；非文字资产不生成品牌和仿文字。
- 所有摆放、遮挡、完成状态均按原资源覆盖；“换了展示图”不等于全状态已换。

#### Classic Billiard · 78388

```text
top-down billiards asset matching the original camera,
precise pool-table geometry, readable ball numbers and stripe distinction,
restrained local painted-wood decoration on non-playing surfaces,
clean felt, professional recreational-club atmosphere
```

- 顶视图示例仅适用于原图确实顶视的资源，球杆/头像等单独跟原图。
- 台面、球袋、库边与瞄准区域保持原样；地方装饰布置在外围和背景。
- 球号和条纹必须准确：球体底图与数字分离处理，仅在原引擎已支持分层时采用分层；原来一体烘焙则按原方式精确重绘。
- 不能把整张球台和 UI 生成成新的布局。

#### Just Ludo · 82251

```text
top-down family ludo board decoration,
original four player colors and path layout preserved,
restrained local painted-wood or textile accents outside the paths,
clean board cells, clearly readable dice dots and pawn silhouettes
```

- 红黄蓝绿四方及原顺序、路径、安全格、起终点保持一致。
- 地区色板只进入棋盘外框、桌布、背景和非规则 UI。
- 不因语言方向为 RTL 而镜像棋盘、移动路径或手势。
- AI 不负责自由重画骰点与棋盘格数；优先保留/确定性重绘功能区域，在指定蒙版内生成装饰。

## 7. 提示词组装与完整示例

### 7.1 推荐结构

```text
[任务：生成/参考重绘/单一局部编辑]
+ [GLOBAL_RENDER_v1]
+ [一个地区包：SA_BASE / NG_BASE / SEA_BASE]
+ [零或一个国家/工艺元素包]
+ [当前资产唯一主体与真实用途]
+ [当前资产用到的2—4个主色，功能色以原资源为准]
+ [真实镜头、材质、光照]
+ [原画布、可见轮廓、锚点、留白与UI安全区约束]
+ [对应资产类别的输出要求]
+ [GLOBAL_EXCLUDE_v1的相关项与当前任务特定排除项]
```

地区关键词只是文字速记，不是模型已认识的风格 LoRA。实际提交时展开完整关键词，并附带已确认的母版或参考图。不要只向模型输入 `SA_BASE`。

### 7.2 生产工单字段

每个资产一条，字段值必须来自真实清单。此处不是某个工具的 API schema。

```yaml
asset_id: 与原资源或自建映射表一致的稳定ID
game_id: 六款之一的数字ID
original_resource: 真实原图/图集子图/原配置路径
asset_type: background / isolated_prop / ui_frame / token / effect_frame / text_image
style_version: 例如 SA_PAINTED_BAZAAR_v1
country_pack: 例如 PK_PAINTED_METAL；无国家包时填写 NONE
state_id: 原资源中存在的状态名
canvas_px: 从原资源读取的宽与高
alpha_contract: transparent / opaque / 原资源要求
reference_image: 已存在的原资源或已确认母版路径
geometry_mask: 需要锁定操作区时使用的真实蒙版路径
functional_color_id: 不适用时填写 NONE；适用时绑定原映射
positive_prompt: 完整展开的提示词
exclusions: 本资产适用的排除项
output_raw: 本次生成原图的计划路径
output_processed: 尺寸/alpha/颜色处理后的计划路径
qa_status: 尚未生成 / 待检 / 通过 / 返工
```

未知宽高、锚点和引用路径不能用猜测值进入正式批次；应列入待取证项。创意概念图可以另设规划画幅，但不得将其冒充原位可替换素材。

### 7.3 单体透明素材通用模板

```text
Create exactly one [SUBJECT] for [GAME AND REAL ASSET ROLE].
[EXPANDED GLOBAL RENDER BLOCK]
[EXPANDED REGION BLOCK]
[OPTIONAL ONE COUNTRY / CRAFT BLOCK]
Use [SELECTED DECORATIVE COLORS] on non-functional surfaces only;
preserve [ORIGINAL FUNCTIONAL COLOR IF APPLICABLE].
Match the supplied reference in camera, silhouette, proportions, lighting,
visible bounding box, anchor placement and transparent margins.
Keep decoration within the original silhouette and preserve [CRITICAL FEATURE].
No readable text or logo, no second object, no hand, no scene, no floor plane,
no cast ground shadow, no cropping, no checkerboard or opaque backdrop.
Output one isolated object on a true transparent background.
```

模板中的方括号必须替换为实际内容后再提交，不能把字段名原样送去生图。

### 7.4 背景通用模板

```text
Create a full opaque background for [GAME / SCENE].
[EXPANDED GLOBAL RENDER BLOCK]
[EXPANDED REGION BLOCK]
[OPTIONAL ONE COUNTRY BLOCK]
The scene contains [TWO OR THREE CONCRETE LOCAL EVERYDAY CUES].
Match the reference perspective, camera height and architectural scale.
Keep the supplied gameplay and UI exclusion masks plain, low contrast and empty.
Place cultural decoration along [EXACT NON-INTERACTIVE EDGES / AREAS].
Use [SELECTED BACKGROUND COLORS], keep functional game colors out of this task.
No gameplay objects, buttons, scores, readable shop text, people or logos.
Fill the complete requested canvas; no transparent holes and no vignette
that hides existing interactive content.
```

### 7.5 UI 边框通用模板

```text
Redraw only the decorative material of the supplied [UI FRAME].
Use [REGION AND OPTIONAL COUNTRY STYLE] with [SELECTED COLORS AND MATERIAL].
Preserve the exact outer canvas, inner opening, corner radii, border thickness,
cutouts, nine-slice safe areas and transparent regions shown in the reference.
Place one restrained local ornamental cue on the non-stretching edge only.
Keep the label area blank; add no lettering, pictograms or new controls.
No changed layout, no new protrusions, no extra panel, no background scene.
Output the isolated frame with the original alpha contract.
```

九宫格安全区是技术约束。即使提示词写了 preserve，仍须测量原图与输出，不以模型“看起来一致”代替校验。

### 7.6 六条可直接打样的提示词

以下示例不含未知的假尺寸。用于独立概念打样时可直接输入；用于正式原位替换时，必须同时提供对应原图和已核实的尺寸/蒙版。HEX 仅作生成引导，最终色值需后处理核验。

#### A. SA / PK · One Connect · 彩绘搪瓷罐图标

```text
Create one closed-lid enamel storage tin icon for a matching-pairs
mobile game. Use clear hand-painted shapes, a bold simple silhouette,
restrained brush texture and gentle form shading.
Apply Pakistani truck-painting-inspired simplified flower and leaf edging
to the tin's painted metal surface: teal #168E9B, cream #FFF1D8,
small magenta #C84678 petals and golden #E6AD32 accent dots.
Keep most of the central body plain and the silhouette easy to identify
at the original tile size. Match the supplied original token reference
for camera, visual mass, anchor and transparent margins.
Exactly one object, no scene, no text, no logos, no vehicle, no person,
no flag, no ceremonial imagery, no ground shadow.
True transparent background; keep the entire object visible.
```

#### B. SA / IN · Candy Crush · 原创甜点棋子概念

```text
Create one original sweet-shop game token shaped as a simple rounded
square milk sweet, with a single clear top surface and restrained
appetizing form shading. Use a contemporary Indian neighborhood
sweet-shop direction and a clean hand-painted 2D mobile-game finish.
Match the provided original token's silhouette envelope, camera,
visual mass, anchor and transparent margins.
Preserve its original functional category color; do not recolor the
category to match a regional palette. Add only a tiny cream-colored
surface accent that remains readable at the original display size.
No plate, no tray, no other sweets, no shop scene, no text or logo,
no ceremonial ornament, no extra protruding garnish.
Exactly one isolated token on a true transparent background.
```

如果该原 ID 的功能色无法与“奶糖”外观合理协调，改用同色果糖造型；不能牺牲功能色去追求食品写实。

#### C. SA / BD · Bubble Shooter GO · 背景

```text
Create a full opaque decorative background for a bubble-shooter mobile game.
Use clear hand-painted shapes and a contemporary neighborhood-shop setting.
Frame the side edges with Dhaka rickshaw-painting-inspired original
flower-and-leaf painted panels, warm cream plaster and restrained teal wood.
Use small magenta and golden accents only on the decorative edges.
Match the supplied original background perspective and composition.
Keep the supplied bubble-field, aiming-path and HUD exclusion masks
plain and low contrast, with no overlap from flowers or architecture.
No bubbles, no launcher, no game UI, no text, no people, no vehicle,
no flags or ceremonial imagery. Do not create a full busy street scene.
Fill the full canvas with no transparent holes.
```

#### D. NG · Tidy Master · 当代小店商品

```text
Create exactly one original unbranded household-goods carton for a
shop-organizing mobile game. Use clear hand-painted 2D forms and the
visual language of a contemporary Nigerian neighborhood shop.
The carton uses cream #FFF3DB, indigo #263A73 and one broad orange
#E8843C accent band with a small original geometric product symbol.
Keep the carton clean, practical and easy to distinguish from round tins.
Match the original carton reference in shape, camera, proportions,
folds, anchor, shelf-slot footprint and transparent margins.
No readable label, no commercial brand, no mask or safari motif,
no scene, no other product, no person, no ground shadow.
One fully visible object on a true transparent background.
```

#### E. SEA / PH · Classic Billiard · 外围环境概念

```text
Create only the non-interactive decorative surroundings for a 2D
billiards-game background. Use a contemporary Filipino neighborhood
recreation-room direction: a painted teal wooden wall panel,
a simple coral awning seen at the outer edge, and small everyday
woven storage details placed away from the playing area.
Use clear hand-painted shapes, restrained shading and warm cream highlights.
Match the supplied original room perspective and camera exactly.
Preserve the complete table, rail, pocket, aiming and HUD exclusion mask:
do not draw, move or cover any part of those functional regions.
No characters, no shop lettering, no scoreboard, no flags, no religious
imagery, no Indonesian batik and no tourist-landmark collage.
Produce a full opaque background; keep the original gameplay contrast.
```

这里生成的是环境候选，不是可以直接覆盖球台整图的文件；合成时严格依照实际分层或蒙版处理。

#### F. SEA / ID · Just Ludo · 棋盘外围装饰

```text
Redraw only the decorative outer wooden frame and tabletop surround
of the supplied top-down ludo-board image. Use a contemporary Indonesian
neighborhood tabletop direction, clear hand-painted shapes and restrained
original batik-inspired everyday floral cloth accents on the outer surround.
Use warm cream #FFF2D9, bamboo brown #B78B5B and teal #158F9C;
do not apply this decorative palette to player colors or rule markings.
Preserve the original canvas and top-down projection exactly.
Leave all four player areas, colored paths, grid cells, safe spaces,
start and finish regions and any existing dice or text unchanged.
No new symbols inside the paths, no changed grid count, no extra pawn,
no fake writing, no ceremonial pattern and no architecture.
Match the supplied original image's alpha contract.
```

只有已确认用途与图案来源的日常纹样才进入正式版本；未确认时将 Batik 句替换为 `a plain woven cloth accent with an original simple floral border`。

### 7.7 局部修正模板

```text
Edit only [PRECISE REGION / ELEMENT] in the supplied approved image.
Change [SPECIFIC MATERIAL / MOTIF / COLOR ISSUE] to [EXACT TARGET].
Preserve every other object, the camera, composition, lighting,
canvas size, geometry, functional colors, transparent areas,
reference silhouette and all existing readable text exactly.
Do not redesign the asset or add cultural details outside the edit mask.
```

用于实际修改时需要提供原图和明确编辑范围。不能用“其他不变”代替逐项核对输出。

## 8. 批量生产与文件管理

### 8.1 分阶段生产

| 阶段 | 建议产出 | 通过条件 |
|---|---|---|
| 0 原资源取证 | 六款资源契约、功能色映射、图集/动画/状态清单 | 真实引用与尺寸可追踪；未知项单列 |
| 1 地区方向打样 | 3 个地区各一张主要场景概念图；建议选择同一游戏与同一构图比较 | 地方元素清楚、国别不混、玩法区域干净；尚不代表可直接替换 |
| 2 首发地区母版 | 一组配对图标、一个 UI 框、一张背景、一组球体/特殊状态、一张台球或 Ludo 外框样板 | 代表不同材质和镜头的样张已确认，缩小后仍清楚 |
| 3 首个完整游戏 | 菜单→开始→游玩→失败/胜利→重开所需的全套实际引用美术 | 全状态覆盖、技术契约和运行效果通过，再承诺后续工期 |
| 4 扩展六款 | 沿各游戏已确认母版生产，保留单一地区版本 | 每款独立检查，不能仅凭第一款通过就宣布其余通过 |
| 5 地区/国家扩展 | 更换已规划的地方元素和对应宣传素材 | 根据实际发行需要扩展；不自动生成全部组合 |

批量生图前先确认代表性样张。未确认时可以继续整理清单和工单，但不能把未定风格整批扩散。这里没有默认开启生图任务，也没有产生图像费用估算。

### 8.2 用参考图固定风格

- 参考分两类：原资源负责几何与功能约束，已确认母版负责画法与材质。
- 原始文化参考应记录来源；先提炼为原创风格样张，不把博物馆藏品或艺术家整幅作品直接裁切成游戏图案。
- 同一个资产族使用同一组母版、相同镜头、光向、边缘处理与同版提示词。
- 有随机种子或固定参数能力时记录它们，但不把“同一 seed”当一致性的保证；跨模型也不能直接复用其含义。
- 文生图拿到母版后，后续优先在支持的参考重绘/编辑路径上延展，减少反复纯文字抽样造成的风格漂移。
- 生成时固定模型版本与可用参数；本文件不预设某一后端支持不存在的参数。

### 8.3 建议目录与命名

以下是后续新建生产目录的规划，不表示这些文件夹已经存在。原游戏包与原始素材不直接覆盖。

```text
art_production/
  manifest.csv
  references/
    original_geometry/
    cultural_sources/
    approved_style/
  SA_PAINTED_BAZAAR_v1/
    SA_BASE/
    PK_PAINTED_METAL/
    IN_SHOP_CRAFT/
    BD_RICKSHAW_FLORAL/
  NG_NEIGHBORHOOD_MARKET_v1/
    NG_BASE/
    NG_YORUBA_ADIRE/
  SEA_NEIGHBORHOOD_STALL_v1/
    PH_NEIGHBORHOOD_STORE/
    ID_STALL_BATIK_ACCENT/
```

每个实际生产分支下按 `game_id/raw`、`game_id/processed`、`game_id/qa`、`game_id/delivery` 分开。

输出命名建议：

```text
77413_SA_PK_tile_原ID_normal_v001_raw.png
77413_SA_PK_tile_原ID_normal_v001_processed.png
93876_NG_BASE_prop_原ID_normal_v001_processed.png
82251_SEA_ID_frame_原ID_normal_v001_processed.png
```

其中“原ID”必须替换为映射表中的真实稳定 ID；正式覆盖时按原工程需要恢复准确文件名或图集名，不能把工作文件名直接当加载路径。

### 8.4 每批记录

- 资产与原资源的对应关系、国家/工艺包、样张版本、模型标识、提示词版本。
- 原始输出、处理后输出、尺寸、alpha、功能色检查结果、内容哈希。
- 普通/特殊/禁用等状态覆盖情况，原图集页和子图对应关系。
- 文化来源、原创改写方式、尚待当地语言或文化复核的项。
- 返工原因、替换历史、压缩前后文件和正式交付版本。

### 8.5 后处理与下游同步

1. 透明单体等比适配原可见范围，不拉伸；不擅自裁掉原透明留白。
2. 检查真 alpha，清理白边、色边、棋盘残留和地面阴影；半透明物件另检。
3. 按原映射校正功能色、球号、骰点和必须准确的文字。
4. 按原图集的子图坐标、旋转/裁切规则回写；逐帧验证动画与状态。
5. 对正式交付素材做适合原格式的压缩；检查颜色与透明度有没有变化。
6. 更新实际项目引用的素材，以及相关压缩版本、宣传素材和预览页。
7. 若预览 HTML 内嵌了旧图，重新打包对应内嵌图；只更改磁盘 PNG 不算预览已同步。
8. 记录本次实际完成的验证类型；文件检查、图集检查与真实运行检查分别报告。

### 8.6 多语言与不改代码的边界

- 地区资源版本不是语言版本：同一国家可能需要多种语言，同一语言也可能服务多个国家。
- 普通装饰图默认不烘焙文字；文字由原系统已有机制处理。
- 原本就是含字图集/烘焙按钮且不能改代码时，按其现有加载方式制作准确的语言版本；不能自行假设可以新增文字层或语言切换。
- 阿语/乌尔都语的连写、RTL、标点与数字混排需要真实字体和原运行环境验证；AI 生成仿文字不能替代翻译排版。
- 没有国家切换能力时，按独立包体或发行平台已有配置使用资源。不能为了套本规范偷偷新增地区判断或加载代码。

## 9. 验收与常见失败修正

### 9.1 可执行验收表

| 检查项 | 通过标准 | 不通过时 |
|---|---|---|
| 地区风格 | 按选定包能看出一致的生活题材/工艺语言；不是只有颜色不同 | 增加一个具体器物/材质线索，减少泛化风格词 |
| 国家边界 | 一个资产/场景未混入未选国家的特定符号 | 删除混入的纹样和建筑，固定国家包 |
| 文化层级 | 小图标有一个足够的地方线索；背景在非玩法区体现两三个具体线索 | 不给所有物体强加纹样，按资产尺度调整 |
| 原布局 | 原尺寸、槽位、边缘、锚点、路径和 UI 安全区一致 | 回到原图参考与蒙版，逐项测量修正 |
| 玩法识别 | 类别、点数、球号、特殊状态清楚且与原映射一致 | 先修复功能信息，再处理装饰 |
| 小尺寸可读 | 在游戏真实显示尺寸下仍能快速区分；不只放大看漂亮 | 降低纹样密度，增大色块与轮廓差异 |
| 材质统一 | 同族图标、UI、背景的笔触与光照相容 | 使用同一母版进行局部编辑 |
| 透明 | 模式/alpha符合契约，无假透明或脏边；透明留白准确 | 后处理修复并重新检查 |
| 状态覆盖 | 原有全部有效状态有对应新资源 | 补齐状态，不能用普通态替代所有状态 |
| 本地化文字 | 翻译准确、字体可用、无仿文字、无明显溢出或混排错误 | 使用可校对文字与确定性排版，在原运行环境重测 |
| 全量替换 | 有实际引用资源清单与覆盖记录；商店与预览同步 | 补齐漏项，明确未完成部分 |
| 可运行性 | 启动、游玩、失败/胜利、重开及相关 UI 场景可重复验证 | 不以图片文件检查代替运行通过 |

任何关键玩法信息、几何或语言可读性不通过，都不能因“地方感更强”而接受。

### 9.2 失败修正短语

| 现象 | 提示词修正与实际动作 |
|---|---|
| 仍像原国际糖果风 | `replace generic plastic surfaces with painted enamel, wood and the selected everyday shop materials`；同时换具体器物/店面参考，不只追加国家名 |
| 纹样过密 | `use one broad ornamental band only, keep the remaining surface plain`；缩小检查 |
| 画成文化大杂烩 | `use only the selected country pack; remove every unselected country-specific motif`；明确列出本图应移除的元素 |
| 像旅游纪念品 | `contemporary practical everyday product, not a souvenir display`；换日常物件参考 |
| 显得破旧贫困 | `clean, well-maintained contemporary shop materials, no distressing unless present in the approved reference` |
| 图标多了场景 | `exactly one isolated object, no shop, no shelf, no person, no floor`；剪除背景后仍需检边缘 |
| 装饰遮住操作区 | `confine ornament to the supplied outer-edge mask; leave the gameplay exclusion mask empty`；按蒙版合成 |
| 全套画法漂移 | 不继续加形容词；回到已确认母版，用参考编辑并固定同版提示词 |
| 球/棋子尺寸变化 | `match original silhouette and visible bounds` 仅是引导；后续必须测量与回归 |
| 包装上出现假字 | `original simple graphic label, no letters or numbers`；必要时擦除后准确排字 |

## 10. 文化参考与未确认事项

### 10.1 来源与用途

下面的资料用于确认文化/生活题材的来源，不是审美效果、商业转化或发行许可的证明。本文配色、形状简化、主题组合和提示词均是本次设计建议。

<a id="r1"></a>
**R1 · 巴基斯坦彩绘工艺**：[Smithsonian Folklife：The Festival’s Pakistani Painted Truck Keeps on Truckin’](https://festival.si.edu/blog/pakistani-painted-truck)。用于 PK 包的彩绘金属与花卉边饰参考；不直接复制作品或随意移用文字内容。

<a id="r2"></a>
**R2 · 孟加拉国达卡彩绘**：[UNESCO：Rickshaw Painting: A Colourful Heritage of Bangladesh](https://www.unesco.org/en/articles/rickshaw-painting-colourful-heritage-bangladesh)。用于 BD 包的手刷花叶与彩绘面板参考；地域来源明确，不等于全国统一风格。

<a id="r3"></a>
**R3 · 尼日利亚 Àdìrẹ**：[V&A：Africa fashion: cloth of a continent](https://www.vam.ac.uk/articles/cloth-of-a-continent-africa-fashion)。其中 Àdìrẹ 部分说明约鲁巴文化中的靛蓝防染布，用于 NG_YORUBA_ADIRE 的选配布艺参考。

<a id="r4"></a>
**R4 · 印尼 Batik**：[UNESCO：Indonesian Batik](https://ich.unesco.org/en/RL/indonesian-batik-00170?RL=00170)。用于理解日常用途与特定象征/仪式用途的差别；不能仅凭“batik”关键词任意复制纹样。

<a id="r5"></a>
**R5 · 菲律宾社区商店**：[菲律宾贸工部门：Starting a Business — Sari-Sari Store](https://dtiwebfiles.s3.ap-southeast-1.amazonaws.com/wp-content/uploads/Starting-a-Business-Sari-Sari-Store.pdf)。用于 PH_NEIGHBORHOOD_STORE 的社区小店题材参考；具体店面与包装仍需按实际参考原创设计。

<a id="r6"></a>
**R6 · 印度题材与工艺检索入口**：[Incredible India：Delhi](https://www.incredibleindia.gov.in/en/delhi)、[Exquisite Crafts](https://www.incredibleindia.gov.in/en/exquisite-crafts)。用于后续选择具体城市的甜品铺、街市和工艺参考；不把一个城市当作全国代表。

### 10.2 已知与未知

已知：六款游戏的初筛资源规模、用户提供的一日国家占比、三组制作方向与用户要求的玩法/代码不动边界。

仍待确认：

1. 首发采用 SA_BASE 还是一个国家主题，实际发行语言与地区分发方式。
2. 六款完整有效资源、远程依赖、隐藏状态、内嵌包与图集契约；此前选型静态扫描不代表全量制作清单已完成。
3. 每条生产工单的原尺寸、引用、视角、锚点、功能色与输出格式。
4. 当地人员对具体食品、器物、店面与所选工艺纹样的辨识和语义反馈。
5. 代表性样张、目标手机上的可读性、真实运行效果与实际制作成本。

本文件的生成模板可直接用于打样；正式批量执行前，先填入真实资产契约并确认母版。没有执行图像生成、资源合入或运行验收时，不把这些步骤记为已完成。
