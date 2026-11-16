# 按需检索提示词模板

只有需要通用场景模板时读取；不要求每次先遍历模板库，不把模板全文送给模型。休闲游戏优先使用 [美术指导模块](../modules/casual-game-art-style/SKILL.md)。

## 提示词模板库（2026-09-15 内化自 gpt-image-2）

休闲游戏美术任务优先读取 [风格指导模块](../modules/casual-game-art-style/SKILL.md)，通用 UI 样机模板不得擅自增加货币、HUD、角色或改变原游戏布局。

> 本模板库原属独立技能 `gpt-image-2`（来源 ConardLi/garden-skills v1.0.3），2026-09-15 内化合并进本技能，原技能已移除。

**位置**：`references/prompt-templates/` —— 17 大类 / 93 个模板 + 1 个方法论文档 `prompt-writing.md`。

**核心原则：先检索模板，再写 prompt。** 只读最贴近的 1~2 个模板文件，**不要一次性读整个目录**。

### 模板索引

1. **学术配图 Academic Figures** --- 9 个  (目录 academic-figures/)
   - graphical-abstract
   - mechanism-diagram
   - method-pipeline-overview
   - multi-condition-comparison
   - neural-network-architecture
   - publication-chart
   - qualitative-comparison-grid
   - research-overview-poster
   - scientific-schematic
2. **素材与道具 Assets & Props** --- 2 个  (目录 assets-and-props/)
   - game-screenshot-mockup
   - retro-skeuomorphic-icons
3. **头像与人设 Avatars & Profile** --- 5 个  (目录 avatars-and-profile/)
   - character-grid-portrait
   - cultural-portrait-series
   - sticker-set
   - style-transfer-selfie
   - themed-3d-icon
4. **品牌与包装 Branding & Packaging** --- 6 个  (目录 branding-and-packaging/)
   - beverage-label-design
   - brand-identity-board
   - character-merch-board
   - cosmetic-packaging
   - full-mascot-brand-doc
   - mascot-brand-kit
5. **编辑工作流 Editing Workflows** --- 5 个  (目录 editing-workflows/)
   - background-replacement
   - local-object-replacement
   - object-removal
   - portrait-local-edit
   - product-retouching
6. **网格与拼贴 Grids & Collages** --- 5 个  (目录 grids-and-collages/)
   - ad-banner-multi-grid
   - anime-pitch-board
   - banner-grid-2x2
   - lookbook-grid
   - mixed-style-multi-panel
7. **信息图 Infographics** --- 6 个  (目录 infographics/)
   - bento-grid-infographic
   - comparison-infographic
   - hand-drawn-infographic
   - kpi-dashboard-infographic
   - legend-heavy-infographic
   - step-by-step-infographic
8. **地图 Maps** --- 5 个  (目录 maps/)
   - food-map
   - illustrated-city-map
   - itinerary-day-trip-map
   - store-distribution-map
   - travel-route-map
9. **肖像与角色 Portraits & Characters** --- 5 个  (目录 portraits-and-characters/)
   - character-sheet
   - founder-portrait
   - pose-reference-sheet
   - professional-portrait
   - virtual-host
10. **海报与战役 Poster & Campaigns** --- 8 个  (目录 poster-and-campaigns/)
    - banner-hero
    - biomimetic-concept-poster
    - brand-poster
    - campaign-kv
    - character-catalog-poster
    - editorial-cover
    - lineup-comparison-poster
    - vintage-editorial-infographic
11. **产品视觉 Product Visuals** --- 6 个  (目录 product-visuals/)
    - ecommerce-marketing-board
    - exploded-view-poster
    - lifestyle-product-scene
    - packaging-showcase
    - premium-studio-product
    - white-background-product
12. **场景与插画 Scenes & Illustrations** --- 4 个  (目录 scenes-and-illustrations/)
    - concept-scene
    - healing-scene
    - minimalist-mood-scene
    - picture-book-scene
13. **幻灯片与视觉文档 Slides & Visual Docs** --- 4 个  (目录 slides-and-visual-docs/)
    - dense-explainer-slides
    - educational-diagram-slide
    - policy-style-slide
    - visual-report-page
14. **分镜与序列 Storyboards & Sequences** --- 8 个  (目录 storyboards-and-sequences/)
    - anime-key-visual
    - character-relationship-diagram
    - cinematic-storyboard-grid
    - four-panel-comic
    - manga-spread-page
    - process-photo-board
    - product-tvc-storyboard
    - recipe-process-flowchart
15. **技术图 Technical Diagrams** --- 7 个  (目录 technical-diagrams/)
    - er-diagram
    - flowchart-decision
    - mind-map-tech
    - network-topology
    - sequence-diagram
    - state-machine
    - system-architecture
16. **字体与版式 Typography & Text Layout** --- 2 个  (目录 typography-and-text-layout/)
    - bilingual-layout-visual
    - title-safe-poster
17. **UI 样机 UI Mockups** --- 6 个  (目录 ui-mockups/)
    - chat-interface-scene
    - landing-page-case-study
    - live-commerce-ui
    - product-card-overlay
    - short-video-cover-ui
    - social-interface-mockup

### 模板工作方式

1. 从上面索引找到最贴近的分类目录；
2. 定位到具体模板文件，只读该文件；
3. 模板里的 `{argument ...}` 表示可替换参数；
4. 用户明确给的值直接填入；模板标了 `default` 的可用默认值；缺失信息会显著影响结果时主动询问；
5. 用户说「你随机生成」时，可在模板允许范围内合理随机化。

> ⚠️ 模板里的 JSON 是**提示词结构模板**，**不是 API 请求体模板**。最终交给 `scripts/gpt_image.py` 的是「渲染后的 prompt 字符串」——可以是拍平的 JSON，也可以是结构化自然语言段落，按模板原样使用。

### 何时先读方法论文档

先读 `references/prompt-templates/prompt-writing.md`，当：
- 还没决定怎么构造 JSON 模板
- 需要判断哪些字段该问、哪些可默认、哪些可随机
- 需要把新案例抽象成可复用模板

### 询问规则（禁止笼统地问「你想要什么风格」）

按模板字段精确提问，例如：
- 直播 UI 模板缺主体 → 问「主播是谁？用真人照片、名人名字、人物描述，还是完全随机生成？」
- 缺商品信息 → 问「商品名称是什么？价格是否指定？评论和礼物内容要我自动补全吗？」

### 与生图流程的衔接

以下脚本例子仅适用于已选择外部后端的任务；原生工具任务返回总入口并使用原生工具。准备好prompt后：
- **无参考图** → `python scripts/gpt_image.py --prompt "<渲染后的prompt>" --size auto`
- **有参考图** → 追加 `--ref`
- **需要透明底**（图标/贴纸/素材/可叠加元素）→ 追加 `--background transparent`，检查退出码（3=未达标）
- **要大幅提升精度** → 追加 `--tier advanced`
- **换皮类**（编辑工作流 + 要求保持 alpha/尺寸不变）→ 走上方「换皮模块」的 reskin 管线，不要直接调脚本硬贴
