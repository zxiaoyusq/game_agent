# 风格卡：地中海古典 · 简约圆润 3D 明亮休闲风

技能默认风格 id：`mediterranean-casual-3d`（机读版在 `scripts/styles.json`，改风格改那里，别改 prompt 副本）。

## 一、可直接复制的风格块（正向）

~~~text
风格锚定：轻快明亮的 3D 立体休闲游戏美术。stylized casual mobile game art, chunky rounded volumes, simple clean forms, smooth soft bevels, delicate glossy specular highlights, crisp clean silhouette, soft studio lighting with a warm sunlit rim light, bright and airy, saturated but clean colors, high readability at small sizes, friendly and cute.
材质语言：半哑光塑胶/黏土质感 + 温润黄铜金（brushed warm gold）。不要写实皮革毛孔、不要做旧破损、不要脏污划痕、不要高频噪点纹理。
配色（地中海古典）：陶土红/砖红 #C8563C、深砖红 #9C3B2A、象牙米白 #F4E9D4、暖米 #E6D2AE、橄榄绿 #7C8F45、爱琴海蓝 #2E86C1、深海蓝 #1B4F72、日照金/黄铜金 #E8B04B、白墙暖石 #F7F3EA。整体高明度、中高饱和、通透；暗部与投影一律用暖色（#6B4A3A），不用纯黑或冷灰。
形体与构图：单一主体居中，形体饱满圆润、大色块概括，必要的细节才保留，保证缩到 32~128px 仍能一眼认出是什么。
~~~

## 二、负面块（必须每次都带）

~~~text
严禁：photorealistic 照片写实、hyper-realistic oil painting 厚涂写实、gritty/weathered 脏旧风化、stone carving 石雕质感、medieval grim 中世纪阴郁、dark museum relic 昏暗古董感、dirty dark shadows 脏黑阴影、muddy desaturated colors 混浊发灰配色、high-frequency noise texture 高频噪点、cracks/rust 裂纹锈迹、realistic leather pores 写实皮革毛孔；不要文字、水印、logo、签名、边框、外描边、外发光、投影、地面；不要多个主体、不要拼图/九宫格/分屏。
~~~

> 这条负面块是**针对这类词汇的陷阱**：出现「古典/宗教/地中海/历史」等词时，模型默认会滑向「超写实、风化石雕、昏暗油腻、博物馆古董」的沉重感，与休闲游戏 UI 的轻快语境完全相反。

## 三、配色速查

| 角色 | 色值 | 典型用法 |
|---|---|---|
| 主色 | #C8563C | 封面、屋顶、陶器、主织物 |
| 暗部 | #9C3B2A | 结构线、布料褶皱暗面 |
| 亮色 | #F4E9D4 | 书页、纸张、白墙、浅布 |
| 次亮 | #E6D2AE | 砂岩、次高光 |
| 点缀绿 | #7C8F45 | 橄榄枝叶、植被、装饰纹样 |
| 点缀蓝 | #2E86C1 | 天空、水面、小面积对比色 |
| 深蓝 | #1B4F72 | 冷色暗部（少量） |
| 金属 | #E8B04B | 金饰、徽记、描边、护角 |
| 底色 | #F7F3EA | 留白、白墙 |
| 暖阴影 | #6B4A3A | 所有投影/暗部，代替纯黑 |

## 四、按素材类型的具体指引

| 类型 | 要点 |
|---|---|
| 小图标 / 道具（32~160px 显示） | 形体必须"一眼可辨"：主体占内容框 100%，砍掉次要细节；高光点到为止，靠大色块 + 一枚金属金饰建立精致感 |
| UI 控件（按钮/卡片/徽章） | 圆角统一、斜面柔和、中心区域干净（便于叠加文字）；不要在中心画花纹（NinePatch 拉伸会变形） |
| 角色 / 吉祥物 | 头身比 1:1.5~1:2、圆润四肢、五官极简；服装纹样只取地中海符号（橄榄、波浪、回纹、陶罐） |
| 背景原画（不透明满幅） | 构图同构原图（前景/中景/远景比例保持），细节克制——背景是衬托 UI 的，别抢可读性；用大面积平涂 + 柔和空气透视 |
| 图集 / atlas | **不要整图重绘**：先按原矩形切片单张重绘，再按原始 Rect 逐像素 Repack，最后跑越界检测 |

## 五、一致性检查（批量必做）

- 同一批里：光源方向一致（统一"左上方柔光 + 右后暖色轮廓光"）、金属色一致（同一黄铜金）、暗部色一致（暖棕不用黑）。
- 把已验收图当作 `use_ref` 传给下一张时，务必写「参考图仅用于风格、材质、光照与配色，不要复制其主体造型」。
- 交付前把所有成品拼一张 contact sheet 通看一遍，颜色/光照不齐一眼就能发现。
