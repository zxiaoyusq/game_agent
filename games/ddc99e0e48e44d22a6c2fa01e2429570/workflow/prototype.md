# Freestyle 规则图替换契约与效果稿核对报告

## 1. 原素材与资产契约核对
- **原始素材**: 真实文件 `mcp-inputs/mac-codex/945f81aa5e020112e0ffcbbbf3953fd1ce5a0e0666373b1a2cc4b0ee2de6b096/tutorial-original.webp`。
  - **元数据分析**: 实际编码为 WebP，虽引用名以 `.png` 结尾，尺寸 `477×707`，Alpha 非零区域 `(46,57)-(432,665)`。
  - **源码证据**: `carrom-current-d201.js` 中存在 `tut_05_screen_design` 的引用路径 `assets/tutorial/tut_05_screen_design.png`。该资源通过 `PIXI.TextureCache` 等机制加载。
- **候选效果图**: `freestyle_rules_mockup.png` (视觉参考) 与 `freestyle_rules_candidate_unverified.png` (待核对候选)。
  - **核对结果**: 候选 `freestyle_rules_candidate_unverified.png` 尺寸 `1030×1527`，比例、内容边界与原始资产 `477×707` 不一致。
  - **替换风险**: 候选图像包含重绘标题与文案，直接覆盖将破坏原有布局定位与文本适配；需重新校准几何与文本坐标。

## 2. 运行验收评估
- **布局逻辑**: 游戏规则对话框通过 `_0x14d186` 类定义，`this._items` 存储布局组件。素材加载与布局坐标受 JavaScript 逻辑直接控制。
- **验收路径**: 
  1. **备份**: 必须保留原始 WebP 文件，严禁在未测试的情况下直接替换。
  2. **制作**: 生成符合 `477×707` 规范的候选图，确保透明边界与原始 assets 坐标匹配。
  3. **测试**: 在 Canvas 2D 运行环境下通过 `npm run check` 启动本地静态服务器，自然操作进入规则页，核实文案显示完整性与布局漂移情况。
  4. **宿主/包体**: 确认资源哈希变更后包体大小影响及宿主环境渲染的一致性。

## 3. 结论与执行计划
- **严禁**: 不得将 `freestyle_rules_candidate_unverified.png` 直接覆盖现有游戏资源；不得修改源码以硬编码新尺寸。
- **行动**: 待美术阶段处理图像尺寸对齐，并在 code 阶段集成测试。
- **现状**: 项目已完成资产元数据核实与源码逻辑定位，目前未发现异常卡死或阻碍测试的非法引用。

---
*记录: 原始素材编码为 WebP，实际引用存在路径后缀偏离。该评估基于静态资源解析与运行时代码静态分析，未执行真实游戏环境 UI 截图比对。*
