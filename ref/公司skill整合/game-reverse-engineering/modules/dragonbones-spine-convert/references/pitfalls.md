# 踩坑记录与经验（DB → Spine 3.8 + QA）
> **何时读我**：把 DragonBones 转成 Spine 3.8 时 / 真实 Spine 打开报曲线值无法转成 float / 要核对 4.x 与 3.8 的曲线格式差异 / 转换后要批量验证产物
> **读完能做到**：把 4.x 数组曲线无损改写成 3.8 四字段，拿到可用的 3.8 查看器，按判据批量跑验证，并处理跨页同名区域、PNG 补边和 DB 到 Spine 的映射细节
> **范围**：`GENERAL_DEFAULT`

## 1. 曲线格式：最大的坑（4.x 数组 vs 3.8 四字段）

### 现象
- 真实 Spine 3.8.99 打开时报：`SerializationException: Error reading animation: N → Value cannot be converted to float: array`（`SkeletonJson.readCurve` 对数组直接 `asFloat()`）。
- 影响面：101/116 组、13452 处曲线（该游戏案例）。

### 根因
- Spine 4.x JSON：`"curve":[x1,y1,x2,y2]`（贝塞尔 4 控制点数组）。
- Spine 3.8 JSON：`"curve":<数字>` + 可选 `"c2"/"c3"/"c4"` 四字段（3.8.99 `readCurve` 反编译确认：`setCurve(frame, curve, getFloat("c2",0), getFloat("c3",1), getFloat("c4",1))`）。
- 转换器最初把 DB 三次贝塞尔控制点直接写成数组 → 3.8 编辑器拒绝。

### 致命陷阱：JS 运行时会“静默吞掉”
- spine-ts 3.8.75 的 `readCurve` 不做类型检查，把数组塞进曲线槽位 → 插值变 NaN，但不抛异常。
- 因此“JS 全量加载 116/116 通过”是假绿；只有真实 Spine 能暴露问题。
- **结论：QA 必须包含真实 Spine（查看器/编辑器）打开这一步。**

### 修复
- 无损改写：`[a,b,c,d]` → `"curve":a,"c2":b,"c3":c,"c4":d`。
- Java 3.8.99 与 JS 3.8.75 两端都认，动画曲线保真。
- 已在 `db2spine.py` 内建 `fix_curves()`，转换时自动完成。
- 修复后复核指标：全量 0 处数组残留，`c2` 字段数 == 修复前数组数。

## 2. 真实 Spine 3.8 获取
- 官方试用版 Launcher 只装最新版（实测仅 “Latest 4.3.x”，无 3.8 选项）。
- 3.8 编辑器仅付费用户可在 Launcher 选 Other… 输入 `3.8.99` 下载；官方服务器已移除旧版试用包。
- 免费官方 3.8 工具 = **Skeleton Viewer 3.8.99**（JAR，需 Java 9+）：
  `https://esotericsoftware.com/files/sv/skeletonViewer-3.8.99.jar`
  - 命令行直接打开：`java -jar skeletonViewer-3.8.99.jar <xxx.json>`（json 与 atlas/png 需同目录同名）。
- 第三方“3.8 中文版”多为魔改/汉化包，来源与安全性自行评估。
- 4.x 编辑器可打开 3.8 工程预览（试用版不能保存/导出），可作为补充验证。

## 3. 批量验证的判据
- 每个文件：`java -jar viewer <json>`，等 4 秒。
- PASS = 进程存活（窗口正常）且 stderr 为空。
- 失败时 stderr 会打完整堆栈（如曲线报错），抓前 300 字符入报告 CSV。
- 116 组全量约 8 分钟；先 `-Limit 3` 冒烟。

## 4. 图集相关
- **跨页同名区域**：DB 图集多页存在同名 SubTexture（本案例 14 组，如 `resources_encourage_ske` 44 个重复、`ShowSSSWhenSkinChangeTrait_gameplay_pfxyd_ske` 151 个）。
  - Spine 按名称解析、取第一个匹配页（先到先得），与游戏内 DB 运行时一致；若第二页裁剪尺寸不同，预览可能有细微差异。
  - 需精确还原时在 Spine 编辑器中手动改名拆分。
- **PNG 补边到 2 的幂**：部分原始贴图逻辑高度 < 实际高度（本案例 7 组）。转换时必须按真实 PNG 尺寸写 atlas `size:`，UV 才不受影响。
- **多页预览**：`preview.html` 仅内嵌首页贴图，其余页按同目录相对路径加载；不要单独移动 png。

## 5. DB → Spine 映射要点（已逐项核对游戏运行时）
- 坐标系：DB y-up（yDown=false），`rotation = skY`，`skew = skX - skY`，正角为逆时针。
- Spine：`rotation = skY`，`shearX = skX - skY`，`scaleX/Y = scX/scY`。
- slot color / colorFrame 为 0-100 百分制 → Spine 0-255 十六进制。
- 图集区域 offset = `(-frameX, frameHeight - height + frameY)`（已用原生 Spine 验证）。
- mesh uvs 为区域相对（top-left origin）→ Spine regionUV 翻转 v。
- ffd：DB offset 为 float 索引，vertices 为增量 → Spine deform 直接映射。
- zOrder：[slotIndex, offset, ...] 对 → Spine drawOrder offsets。

## 6. 其他
- DB 的 `boundingBox` 等非贴图附件未输出（该游戏皮肤主要为 image/mesh）；若目标游戏有 boundingBox/path，需要扩展转换器。
- `index.json` 为总清单；预览总页 `index.html` 引用各组 `preview.html`。
- 转换器默认路径硬编码在文件顶部（`SRC`/`OUT`/`LIB`），新项目用 `--src/--out` 覆盖，`LIB` 需手动改。
