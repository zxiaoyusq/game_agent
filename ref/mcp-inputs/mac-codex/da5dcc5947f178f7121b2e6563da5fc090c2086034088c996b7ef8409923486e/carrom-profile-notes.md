# 对手资料代表屏效果稿 v1

参考：项目当前 Delhi 对局截图与竞品 Delhi 对局截图。目标是研究匹配、对局及结算中同一离线对手的可辨识资料；本稿仅用头像和名字示意，未合入游戏，不证明运行效果。图像生成同时改变了棋盘尺寸和部分装饰，违反保留棋盘结构的约束，因此只采纳顶部头像视觉方向，不可直接作为整屏替换资源；后续控件必须在原尺寸与原坐标下单独制作并核验。昵称示例不是联网或真人身份声明。

## 控件草稿

`opponent_control_source.png` 为参考旧结算头像边框生成的单个灰度人物控件草稿，尚未处理为 156×156 目标成品，也未校验像素边界、原游戏 tint、匹配/局内/结算一致性及实际显示。不得直接替换游戏素材；仍需生产满足原文件契约的资源并在实际运行中验证。游戏工厂审查 `23765b26bb7746929b5573839902f371` 第一次因连接错误失败，已恢复第二次运行。

`opponent_control_156.png` 是将控件草稿按原资源尺寸制作的 156×156 预览件，透明角 alpha=0，文件 27,467 字节；原 `results_opponent_profile.png` 为 954 字节，直接替换会显著增加该素材本身的字节。预览件边框占比也与原图不完全一致。当前发现结算/匹配素材与局内 `avatar_silhouette_cha01` 为不同路径；不能只替换一个就宣称同局头像一致。该预览未合入，需核实各场景颜色叠加、压缩后实际 ZIP 增量及受控浏览器显示，再决定具体素材方案。

局内人像已另行制作 `opponent_portrait_112.png`，压缩样本 `compressed/opponent_portrait_112.webp` 为 2.71 KiB；结算头像压缩样本 `compressed/opponent_control_156.webp` 为 3.78 KiB。两张压缩前后对比见 `compressed/portrait_comparison.png` 和 `compressed/comparison.png`，已在实际像素尺寸查看。它们仍是测试件，未计算合入 ZIP 的最终差异或验证 tint、颜色状态与运行时兼容性。

源码显示局内左右两侧均通过 `_0x3020e6` 创建并共用 `avatar_silhouette_cha01`，直接替换此文件会同时改变玩家和对手。匹配/结算又使用独立头像及胜利状态图，因此需要先核对状态引用与分支，再使对手侧独立选用对应素材；不能仅凭尺寸相同就覆盖原素材。

局内临时预览 v2：在测试 HTTP 响应中将对手头像选择改为 cha02，并修正进入对局时覆盖纹理的赋值；仅临时替换资源，不写入正式游戏。截图 `E:\AIlab\CarromClashMasterRe\evidence\头像临时预览V2_击球后截图.png` 显示对手画像、玩家原剪影及击球后棋局；灰度版本与效果稿的彩色视觉不一致，因此继续生成彩色人像。新 `opponent_portrait_color_112.png` 和 `compressed/opponent_portrait_color_112.webp`（约 3.47 KiB）仍是未合入候选；匹配/结算彩色同一角色、状态图及实际运行还需验证。

彩色匹配/结算候选：`opponent_control_color_156.png` 及对应 WebP；对手获胜状态草稿 `opponent_win_color_156.png`。后者在 156 像素下外框下方仍可见红色杂点；`opponent_win_cleanup_attempt.png` 为再次生成的清理尝试，外框外依然存在红色残留，判定未通过，不可合入。后续需要按原框透明轮廓进行精确清理，并验证局内、匹配和结算角色一致与状态色。

胜利头像后处理：对 `opponent_win_color_156.png` 先验证 y=145..155 无 alpha>20 的有效主体，再将该区域清为透明以去除弱透明杂点，得到 `opponent_win_clean_156.png`；按头像框范围裁切并缩放得到 `opponent_win_fitted_156.png`，压缩样本 `compressed/opponent_win_fitted_156.webp` 约 6.55 KiB。此处理改变了生成稿的外框占比以接近原资源，但不等于与原图边界逐像素一致；尚未在胜负界面、移动设备或宿主运行验收，不得称正式通过。

彩色临时预览：`tests/opponent-profile-color-preview.probe.cjs` 仅在 HTTP 响应中替换对手头像资源及两个对手侧纹理引用，不改正式游戏。桌面截图 `evidence/头像彩色预览_匹配中.png` 与 `evidence/头像彩色预览_击球后截图.png` 分别显示匹配和局内为同一角色、玩家仍为原剪影、局内完成击球。两张是一次桌面模拟，不证明结算、不同分辨率、AHA 宿主或触控验收。

受控胜局结算预览：`tests/opponent-profile-win-preview.probe.cjs` 使用临时响应替换头像，注入最后一枚棋的布置并完成受控胜局，`evidence/头像彩色_受控胜局返回.png` 显示对手普通状态头像与匹配、局内为同角色。脚本首轮因为引导标记仍开而中断；视觉复跑移除了引导断言，截图背景可见引导层残留，因此不能作为自然引导或完整胜局验收。金币 50 及刷新存储在该次受控运行中观察到，但不能替代宿主验收。

## 开发版合入与验证

已将彩色局内人像以独立资源 `development/assets/avatars/opponent_local.png` 加入加载表（文件实际为 WebP），原玩家剪影保留；匹配/普通结算和对手胜利状态分别替换 `development/assets/result/results_opponent_profile.png`、`results_opponent_profile_win.png`（实际 WebP）。局内构造和开局重置两个位置仅将对手侧指向新纹理，避免双方共用头像或进入局内后被旧纹理覆盖。原代码和两张旧结算图备份在 `evidence/backups/20261113_opponent_profile/`。

正式源码 SHA-256 `09cc050bc26a3f81480b1818fe28df6068ace2cae7e59721832500cc845430c9`；109 项脚本测试通过。非临时替换的桌面浏览器加载开发版、进入 Delhi、完成一次击球，`evidence/头像正式合入_击球后截图.png` 显示对手彩色头像和玩家原剪影；匹配、胜利、败局的同角色预览此前使用临时响应资源，败局为直接注入界面、胜局为受控布棋且引导层残留，不能视为正式版自然完整胜负复验。截图与触控、移动端、AHA 均需后续验证。

按同一固定时间与压缩参数合成开发目录 ZIP：4,031,003 → 4,043,912 字节，+12,909 字节。不是正式分发包，也未实测加载或设备帧耗时；WebP 内容沿用项目已有同扩展名资源的浏览器加载方式，目标宿主兼容性仍待验。

正式文件复验：`tests/opponent-profile-integrated-match.probe.cjs` 在本地 HTTP 直接读取合入资源，`evidence/头像正式合入_匹配中.png` 显示匹配中为新对手头像；`tests/opponent-profile-integrated-win.probe.cjs` 使用正式资源和受控末棋布置，`evidence/头像正式_受控胜局返回.png` 显示胜局对手头像。两脚本均退出码 0；胜局测试放宽了引导状态断言，截图背景可见引导层，故不能视为自然引导/完整胜局通过。临时响应注入的败局状态图另有截图 `evidence/头像彩色预览_注入败局.png`，它只是直接调用结算界面的视觉测试，不是正式版自然败局。
