# 需求理解（生图前的需求分析与规格化）

> 来源：GameArtAgent（`E:\Gameprogram\PLAYFORGE-全套-2026-08-05\美术AI自动化生产`）的 intake / concept_analyze / spec_split 三阶段提炼。
> 目标：把用户模糊的"帮我做套美术"变成**有据可查、可校验、可直接生图**的资产规格。

## 1. 需求三通道扫描（intake）

不凭感觉列需求，从三个来源收集证据：

| 通道 | 内容 | 限制 |
|---|---|---|
| 策划文档 | .md / .txt / .rst，文件名含 需求/策划/美术/资产/plan/brief/spec/design/art 优先 | 最多 5 份、每份 6000 字符截断 |
| 工程源码图片引用 | 5 种正则提取（`src=`、`url()`、`drawImage()`、`loadImage()`、含 icon/btn/bg/sprite/ui 关键字的路径） | 最多 30 文件；过滤 http/https/data: 外链 |
| 已有美术文件 | 列出 .png/.jpg/.webp/.svg 相对路径 | 最多 120 个；已有资产标注"已有"不重生成 |

忽略目录：node_modules/.git/dist/build/raw_generated/processed/delivery/review 等。

## 2. 需求提炼 LLM 模板

System（直接可用）：

```
你是一位资深游戏美术需求分析师。根据用户提供的策划文档、工程源码图片引用、已有美术文件，
提炼美术资产需求清单。
要求：
- 每条需求是一个具体资产（UI 控件 / 图标 / 底图 / 特效 / 字体等），简明 ≤60 字
- 直接输出 markdown 无序列表，每条以 "- " 开头
- 不要输出标题、不要解释、不要编号段落，只输出列表
- 若信息不足，基于通用手游给出 8–15 条常见需求
```

User 拼接：`### 文档：{名}` + `### 源码图片引用` + `### 已有美术文件`，每类最多 50 条。

**解析铁律**：只认列表项（`- ` `* ` `+ ` `1.` `1)`），解析不到 → 返回空 → 用兜底清单（"主开始按钮/顶部资源条/底部导航栏/设置按钮/通用面板底图/金币图标/…"）。**下游只依赖列表行，标题段落一律忽略**——所以产出物必须保持"需求=列表项"格式。

## 3. PROJECT_BRIEF.md 产物格式

```markdown
# PROJECT_BRIEF.md
- **项目名称**：xxx
- **模式**：换皮 / 新建
- **风格说明**：xxx（若有）

## 用户提供的美术效果图
- path/to/concept.png

## 工程源码图片引用
- assets/ui/btn_start.png

## 美术资产需求清单
- 主开始按钮
- 顶部资源条
```

## 4. 效果图控件拆分（concept_analyze）

有参考效果图时，用视觉模型把"一张图"拆成"独立可复用资产"，而非整张重绘。

### 优先级（三层）

1. **required_ui**：所有可见可复用 UI —— 按钮/面板/tab/进度条/资源计数/图标/气泡/滑块/艺术字。全选 selected=true。
2. **key_scene**：完整可复用场景主体（角色/建筑/交互装置），**最多 8 个**。
3. **scene_group**：整体环境层，**最多 1 个**，grouping=`scene_environment_layer`。

### 硬规则

- **禁止**把花/草/石头/围栏段/阴影/纹理碎片等小装饰拆成独立资产
- 全屏背景只能 category=`background` 且 **selected=false**（小面板背景/按钮背景允许生成）
- 图上没有可见 UI 结构时返回空 controls，停止拆分（别把场景插画硬拆）
- **不凭空发明图上看不到的 UI**

### JSON 契约（必须严格遵守）

```json
{
  "coordinate_space": {"width": 750, "height": 1334},
  "controls": [{
    "name": "ui_play_button",
    "bbox": [200, 400, 600, 260],
    "category": "button|icon|panel|progress|text_label|background|character|pet|building|prop|decorative",
    "priority": "required_ui|key_scene|scene_group",
    "reuse_reason": "可独立复用的原因（中文）",
    "grouping": "standalone|scene_environment_layer",
    "selected": true,
    "usage": "用途（中文）",
    "has_text": false, "text_content": "", "text_type": "art|program|unknown",
    "confidence": 0.95
  }]
}
```

- `coordinate_space`：声明 bbox 所在像素空间，必须与真实画布一致；或 0-1000 归一化 + `"normalized": true`。**省略或与实际不符 → 整个响应被拒**
- bbox 整数、左上角原点、不越界
- required_ui 排在最前

## 5. 需求 × 控件双向核对（reconciliation）

识别结果与需求清单做**子串匹配**（大小写/首尾空白归一），三分类：
- **matched**：控件名或文字与需求互为子串
- **extra**：识别了但需求没提（提示需求遗漏）
- **missing**：需求提到但没识别到（提示拆分遗漏）

missing 必须回补或人工确认，不能静默带过。

## 6. 资产规格 ASSET_SPEC.json（生图的唯一依据）

每资产一条，核心字段：

| 字段 | 说明 |
|---|---|
| `source` | `concept_art`（从效果图 crop 出参考）/ `generated`（纯文本生图）/ `imported`（已有素材）。**三种来源互斥**，concept_art 必须带 source_bbox/source_image/reference_crop |
| `width`/`height` | 目标精确尺寸；concept_art 类 = 控件实际像素 |
| `transparent` | 是否透明底（决定后处理走透明/不透明分支） |
| `category` | background/building/character/decor/prop/fx/ui/icon/path/pet |
| `text_layers` | 文字分层：`type=art`（美术字，随图生成）vs `type=program`（程序字，交付 README 清单，不做进图里） |
| `size_basis` | 尺寸依据：concept_bbox/concept_bbox_scaled/imported_native/user_override |

**文字分离原则**：可变的数字/文本（等级、数量、货币值）标 program，让程序用代码渲染；固定的艺术字标 art。

## 7. 生图 prompt 组装（image_gen）

- 纯生成：`style_prompt_base + 资产描述`，尺寸默认 1024x1024
- 参考图编辑（concept_art 类）：**edit 模式**，prompt 固定追加后缀
  `"... match the reference image style, regenerate on solid magenta background #FF00FF"`
  品红底约定与后处理色键抠图配套（见 image-postprocess.md）
- 编辑尺寸按规格宽高**向上取整到 16 的倍数**

## 8. 任务模板（90% 场景免手写配置）

| 模板 | 跳过阶段 | 特殊参数 | 后技能 |
|---|---|---|---|
| 三消图标 | concept_gen/analyze | 256x256 | multi_res, engine_pack |
| 关卡背景 | concept_analyze | 2048x2048, transparent=false | seamless_tile_check |
| 道具图标 | concept_gen/analyze | 128x128 | uniform_margin, multi_res, engine_pack |
| UI 按钮组 | 无 | 全流程 | nine_slice, multi_res, engine_pack |
| 换皮迁移 | concept_gen | style_similarity=0.8 | — |
