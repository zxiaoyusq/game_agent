# 最小关卡图片与配文编辑器

这是一个无 npm 依赖的本地 HTML 编辑器，适合让美术或内容人员逐关同屏查看原图、配文和出处。

## 接入方法

1. 把整个目录复制到项目的 `working/content-mapping-editor`。
2. 将 `editor.config.example.json` 复制为 `editor.config.json`。
3. 修改项目名、关卡配置、中文文案和图片目录三个路径。
4. 双击 `launch-editor.bat`。

当前适配器识别 Cocos TypeScript 中的 `levelConfigs` 数组、`imagePath/width/height/time` 字段，以及 `quote.N.text`、`quote.N.ref` 文案键。其他 schema 必须先改解析夹具并运行 `py -3 server.py --self-test`，不能直接套用正则回写。

`expected_levels` 设为 `0` 时动态发现关卡数。新增关卡会在编辑器重新载入时出现，页面也会定时检查工程变化。缺配文或出处的新关卡显示“待补全”，不会让整个编辑器卡死。

## 写入保护

- `保存草稿` 只写编辑器目录，不改游戏源码。
- `预览并写入` 先显示新旧差异，确认后才改工程。
- 写入前核对源码 SHA-256，发现外部改动时拒绝覆盖。
- 正式写入前备份关卡表、文案表、草稿和变更报告。
- 只回写图片路径、配文和出处。固定编号、拼图规格、注释及未知字段保持不变。
- 图片只从项目目录读取，不生成或写入占位图。

## 交付门禁

运行 `py -3 server.py --self-test` 后，还要用当前项目执行：全量载入、首末关图片读取、无改动预览为 0、草稿保存、临时夹具写回和备份复验。真正修改项目内容后，继续按 `modules/cocos-qa/references/content-image-mapping-qa.md` 做 Web/APK 与运行时验证。
