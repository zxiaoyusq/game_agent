# Landing log
> **何时读我**：记录本项目 QA 里程碑与偏差时
> **读完能做到**：看懂每轮里程碑的实际结果、与预期的偏差、回填动作和验证方式，并把新的 QA 结论按同一张表继续往下追加
> **范围**：`GENERALIZED_PATTERN`

| 日期 | 阶段 | 实际结果 | 与预期偏差 | 回填动作 | 验证 |
|---|---|---|---|---|---|
| 2026-09-05 | 怀旧时光拼图 Spine FX 修复与 QA | 评价字/点赞/相册/结算 FX 恢复跨端渲染；颜色、网格、Atlas、动画名、回收与层级均形成门禁 | JSON 可解析仍可能错色；加权网格截断会跨端崩溃；旧 Chrome profile 会造成假阳性；局部 sibling 无法压过最终弹窗 | 新增 `spine-fx-repair-qa.md`，把资产→运行时→Web→设备→APK 证据链固化 | fresh-profile Web 像素分类与 console、MuMu 真实触发截图/logcat、APK 包内 JSON/atlas 数据复验 |
| 2026-09-05 | 首胜结算 Emoji 触发/层级回归 | 根级 Overlay 已正确仍只见彩纸；定位为首胜徽记与祝贺 Emoji 被错误写成二选一 | `active=true` 和 sibling 正确不证明用户看到了目标主体；晚截图会错过自动淡出 | 增加资源职责矩阵、首胜双层同时播放、Emoji 最后入栈、0/300/750ms 连拍门禁 | fresh-profile Web 同时命中两宿主，早期帧看到完整 Emoji 覆盖最终弹窗；设备端按同节奏复验 |
| 2026-09-06 | JSB 烘焙 Spine 初始禁用唤醒 | Web 正常、native 节点/动画/透明度/坐标均正确但 Emoji 不出图；null→SkeletonData 重绑后原生 300ms 帧完整显示主体 | 同值赋值会被 SkeletonData setter 短路；JSB 的 Web 私有渲染字段为空不是可靠失败信号 | 增加 native-only 烘焙宿主重绑规则与早期帧实机门禁 | MuMu 真实通关：重绑前只见彩纸，重绑后完整 Emoji 位于结算弹窗最上层；Web fresh profile 无回归 |
| 2026-09-06 | 关卡图片与剧情配文映射审计 | 全量编号、图片和语言键结构通过后仍发现开篇图片与文案语义不符；逐图人工判断不能被索引检查替代 | `imageIndex == level`、键数量完整和构建通过只证明结构，不证明画面主题、配文和出处一致 | 新增 `content-image-mapping-qa.md`，固化三联审计、可回写编辑器、白名单回写和产物级复验 | 结构报告单列 PASS；语义状态保留 `PENDING/FAIL/PASS`，修改关卡用同屏截图与 Web/APK 提取值复核 |
| 2026-09-06 | 可扩展关卡内容编辑器 | 530 关真实数据可在无依赖 HTML 中同屏预览；首版加载层被 CSS 覆盖且浏览器请求了全部大图，视觉 QA 后修复 | 原生 `hidden` 可被组件 CSS 覆盖；仅写 `loading=lazy` 不足以保证大列表按需请求；固定关卡数会阻断后续扩关 | 沉淀 `assets/content-mapping-editor/`；增加 `[hidden]` 强制规则、IntersectionObserver 缩略图窗口、动态关卡发现、缺键待补全、10 秒安全同步与写回追加键 | Python 自检覆盖中文路径/草稿/预览/备份/原子写回/新键追加；真实工程载入 530/530、映射缺口 0、首末图可读、无改动预览 0；浏览器首屏只请求可视区图片 |
| 2026-09-08 | Cocos 精修构建与 Web/MuMu 回归 | 结算 Spine 按可见 bounds 缩小后占屏正常；三类背景运行态比例与原图一致；签到领取/防重复/关闭异常 0；MuMu 四屏目标错误 0 | 仅按作者画布比例会让近方形 Emoji 过大；旧探针端口落入 Windows excluded range 后仍生成空白 PNG；旧审计硬编码过时 JSON 长度/ABI 造成假 FAIL | 增加 bounds×世界缩放校准、端口/HTTP/System 启动门禁和“审计常量必须有当前权威依据”规则 | fresh-profile Web 记录实际 scale/parent/sibling、背景 source/runtime 尺寸与 Widget；Gradle SUCCESS、APK `13886/0/True`、MuMu Streamed Install 与目标错误 0 |
