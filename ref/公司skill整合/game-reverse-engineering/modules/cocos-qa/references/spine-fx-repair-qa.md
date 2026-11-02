# Spine FX 修复与跨端 QA（GENERALIZED_PATTERN）
> **何时读我**：Spine 特效错色/错图/不播/遮挡，评价字或点赞异常
> **读完能做到**：按源数据、Atlas、引擎、宿主、产物五层定位问题，修好颜色格式、加权网格与 Atlas 边界，接对触发与层级，再用 fresh-profile Web、真机与 APK 包内数据三层复验
> **范围**：`GENERALIZED_PATTERN`

适用于 Cocos Creator 中评价字、点赞、庆贺 Emoji、光效等 Spine 出现错色、错图、不播放、
完成点崩溃、尺寸失真或被 UI 遮挡。具体资源名、数量、比例和坐标必须按当前项目重新取证。

## 1. 先分层定位

1. **源数据层**：确认源 Spine 版本、二进制/JSON 是否完整、动画名、skin、slot、attachment、
   weighted mesh 顶点与权重。
2. **Atlas 层**：逐页读取物理 PNG 宽高，对比 atlas `size` 和每个 region 的 bounds/rotate；
   页面声明尺寸与物理图不一致时，UV 会在 Web/native 表现成错图或越界。
3. **引擎层**：确认项目 Cocos 使用的 Spine runtime 版本；不要把旧 `.skel` 字节流直接交给
   不兼容 runtime。转换后二次验证，不能只以“JSON 能解析”作为成功。
4. **宿主层**：确认真正触发 owner、parent 坐标系、sibling、scale、动画名、loop、声音与回收。
5. **产物层**：Web 缓存、构建中间资产、APK 打包副本必须与工作区逐个对比。

## 2. 数据修复门禁

- Spine JSON 的 `color`/`dark` 使用 runtime 接受的裸十六进制串；若工具误写成 `#RRGGBBAA`，
  要在备份后批量移除前缀。逐文件统计修改位置，并断言修复后不存在残留 `#`；不要顺手改变
  `Perfect_Frame.png` 等已验收原图。
- 二进制转 JSON 时，weighted mesh 的 `vertices` 不能只保留首个顶点。按 Spine 加权顶点编码
  遍历每个逻辑顶点：读取 boneCount，再读取每组 boneIndex/x/y/weight；断言游标恰好落在数组
  末尾、boneIndex 有效、权重和近似 1。截断常导致 native SIGSEGV 或 Web wasm 越界/null function。
- 不直接信任 atlas 的页面 `size`。读取 PNG IHDR 获得物理尺寸；若声明页不同，按轴缩放
  region 的 xy/size/orig/offset 等坐标，`rotate:90` 要交换占用轴后再做边界断言。最终每个 region
  必须满足物理页内 `x>=0,y>=0,x+w<=W,y+h<=H`。
- 动画列表优先从 `SkeletonData.getRuntimeData().animations` 读取；它可能是数组，也可能是
  名称到动画对象的映射。不要只读 `SkeletonData.animations[0]`，否则大量骨骼停在 setup pose。
- 每个被改 JSON 留原位或集中备份，并做“仅允许字段”差异：颜色修复不得改变骨骼/关键帧，
  Atlas 修复不得改变原图像素，格式头修复不得偷偷改动画内容。

## 3. 运行时接线

- 触发规则从原作代码/元数据恢复：谁触发、何时触发、是否首胜/零提示、动画名、声音名、
  loop 与持续时间必须各有证据。资源存在不等于原作会在该位置播放。
- 先做“资源职责矩阵”，区分首胜徽记、通用祝贺 Emoji、横幅、评价字、彩纸等独立层。除非原作
  代码明确互斥，不要把 `firstWin ? firstwin : congratulations` 当作当然逻辑；首胜常是“首胜层 +
  通用祝贺层”同时播放。只见彩纸或徽记而不见 Emoji，优先检查触发分支是否错误地二选一。
- 缩放按“源作者画布到当前设计画布”的比例起步，但最终值必须按**该骨架自己的可见 bounds**
  校准：读取 setup pose/runtime bounds 的宽高，先计算 `s=min(目标占屏宽/boundsW, 目标占屏高/boundsH)`，
  再乘完整父链 world scale 检查最终占屏尺寸。不同骨架即便来自同一作者画布，也不得共用 scale；
  宽横幅评价字、近方形 Emoji、局部点赞的可见边界完全不同。记录 `bounds × nodeScale × parentScale`
  与宿主卡片/画布的占比，再用 0/300/750ms 截图校准，避免只看节点 scale 数字。
- 一个反馈只有一个 owner，声音只播一次。结算评价字与局内完成光不能各自再播放同一评价动画。
- 已烘焙宿主优先：`find-first` 取得节点，重置旧 Tween/UIOpacity，恢复 Skeleton enabled/paused，
  clearTracks 后 setAnimation。结束时将 baked host `active=false`，不要 destroy；运行时新节点才销毁。
- Cocos Creator 3.8.x JSB 中，Prefab 里“初始 inactive 且已直连 SkeletonData”的宿主可能出现
  数据、动画名、透明度和变换均正确但完全不出图：原生组件反序列化时持有资源，渲染对象却未初始化，
  再赋同一资源又会被相等判断短路。仅在 native 播放前执行一次 `skeletonData = null`，再绑定原
  SkeletonData，然后 clearTracks/setAnimation；Web 不做此重绑。必须以早期帧实机画面验证，
  `_instance`/`_renderData` 等 Web 私有字段在 JSB 上为空不能单独作为失败证据。
- 某些 Cocos Web/特定转换资产在 non-loop 完成回调处不稳定时，可仅在浏览器把底层设为 loop，
  根据真实动画时长在首轮完成前主动淡出并两阶段停用；native 保留真实 loop 语义。这个兼容分支
  必须有复现用例，不能全局套用固定毫秒数。
- 需要压过最终弹窗的庆贺/Emoji 放在弹窗根级独立 Overlay；局部评价字仍放在照片/成功弹窗
  坐标系。层级 QA 同时断言 parent 和 sibling，不能只看“节点 active”。
- 多层庆贺按从后到前顺序播放：背景/首胜层先入栈，Emoji 最后入栈，并在每次播放后将其设为
  Overlay 的最后 sibling。根级 Overlay 自身也必须是弹窗根节点的最后 sibling；只调整 Overlay
  内部顺序，无法压过 Overlay 外的最终弹窗。
- 加载、挂载或动画名异常时回退经过批准的静态 Sprite；禁止程序绘制“临时字/色块”冒充正式 UI。

## 4. Web QA（每轮使用新 Profile）

1. 关闭旧 Chrome，删除或归档本轮 profile，再启动构建；旧 Service Worker/CacheStorage 会制造
   “源码没生效但画面通过”的假阳性。
   Windows 上还要先查 TCP excluded range；固定端口被系统保留时，Python/Node HTTP server 会立即
   退出而 Chrome 仍能截出错误页。探针必须先验证 server 存活与首页 HTTP 200，随后断言 `System`、
   `cc.director.getScene()` 可用；出现 `System is not defined`/`cc is not defined` 时本轮所有截图无效。
2. 探针记录：资源加载结果、runtimeData 骨骼/动画数、实际动画名、节点 parent/sibling/scale、
   首次与二次播放、回收后宿主是否仍存在、console error/unhandled rejection。
3. 用真实操作触发，不只在控制台手工 new 组件。评价字至少覆盖完美/非完美；点赞覆盖正确归位；
   庆贺覆盖首次与非首次通关。
   首通场景必须同时断言首胜宿主与祝贺 Emoji 宿主 active，且两者不是用条件表达式二选一。
4. 对高对比文字/徽章做像素分类：目标色像素应超过阈值，污染色为 0 或在批准容差内；截图与
   统计 JSON 同时保存。颜色统计只证明渲染结果，不能替代层级和触发规则。
5. 至少跑设计比例、较高与较矮比例；检查 FX 尺寸、中心、裁切和 UI 遮挡。
6. 自动淡出的结算 FX 要在弹窗出现后约 0/300/750ms 连拍，不能只截数秒后的静止结算页。节点
   active、动画名正确只证明“调用发生”，最终 PASS 仍需画面中看到 Emoji 主体而非仅有彩纸；
   同时保存根级 sibling/parent dump，证明它确实覆盖最终弹窗。

## 5. MuMu/真机与 APK 数据级 QA

- 安装前核对 adb endpoint、包名、ABI、version、签名与 APK SHA-256；只操作当前项目包。
- 冷启动后按“首页 → 功能弹窗 → 闯关真实触发 → 通关结算 → 相册详情”逐屏截图，抓取同时间段
  logcat，断言无 Spine crash/wasm/native error、无重复声音、无卡死。
- 至少打一局不用提示的真实完美局；如果自动脚本交换拼图，记录棋盘 bounds 与实际交换序列，
  不用直接改存档替代触发。
- 解压最终 APK 内目标 SkeletonData/atlas/PNG，重复颜色、网格、Atlas 边界与动画名验证，并和
  Web 构建/工作区做哈希或语义 diff。工作区通过而 APK 失败，优先查 Cocos/Gradle 陈旧缓存。
- 报告逐项 PASS/FAIL，证据必须可定位到脚本、JSON、截图、logcat 与 APK；唯一未覆盖的手工项
  要明确列缺口，不得用静态分析代替真机画面。

## 6. 最小自动断言清单

- 全部目标 JSON 可解析；颜色格式残留 0；备份与目标一一对应。
- weighted mesh 游标/骨骼索引/权重和合法；atlas 所有 region 在物理页内。
- 每个已接入 `Fx.play(parent, group)` 在 parent 下有唯一 baked host，SkeletonData 非空。
- 首次/二次播放均显示；回收不 destroy baked host；console/logcat 崩溃 0。
- 庆贺 Overlay sibling 高于最终弹窗；局部评价字高于照片与结果徽记。
- 首胜层与通用祝贺 Emoji 同时可见；Emoji 为 Overlay 最后 sibling；早期帧能看见主体而非只见粒子。
- native 初始 inactive 的 baked Skeleton 做 null→data 唤醒后能出图；同一资源 Web 不受影响。
- fresh-profile Web、设备实机、最终 APK 包内数据三层结论一致。
