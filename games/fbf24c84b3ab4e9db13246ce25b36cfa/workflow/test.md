# 星点采集 · 测试验收

## 结论与阶段边界

本轮为测试阶段，attempt=1，resume=false。独立重新执行构建、规则测试、最终dist浏览器检查及源码ZIP清洁重建，全部退出码0。在已执行的自动化范围内通过，未发现需返回代码阶段修复的缺陷。未修改已确认源码、测试脚本、原型或美术资源；最终 npm run check 后没有修改或重建工作区 dist。源码包的隔离重建仅发生在 evidence/source-rebuild，校验后清理，不影响最终dist。

本报告不代表真机验收、真人体验评价或公网发布完成，不自行推进阶段。自动发布由工作流处理，本轮仅验证目标独立子路径兼容性。

## 依据、参考与设计取舍

实际完整读取冻结入口 `casual-game-production/SKILL.md`，以及全部选定知识：

| 路径 | 冻结SHA256 |
| --- | --- |
| casual-game-production/SKILL.md | f9e955b7b1834518aba9ea71c286ea04636724eb56fbe81fb6cbb96bc33d7d98 |
| genre/docs/general.md | 8d5058f8368fece60ae844b0d40217481746a7d8f0697b8f95cda9d78de64047 |
| framework/docs/web-common.md | 5631072d40b38dfcb641838ceb1836e65d2a9ed07347215f8eb90819e25ceb08 |
| framework/docs/canvas-web.md | ef6ec5c4232be8c692c2ddb567d8353f82266baa5502f96a846ce999d994aad5 |

首次通用品类调用路径末尾误带空格而失败，已用正确路径重新读取成功，未把失败算作读取完成。

实际读取上游 `/workflow/prototype.md`、`art.md`、`art-manifest.json`、`code.md`，规则、页面、样式、输入/渲染源码、视觉配置、构建/浏览器/打包脚本、规则测试及README；发布前另读 `/dist/index.html`。inspect_assets 复核星星、配置和美术预览，哈希均与原清单一致。

用户 references=[]。本轮 read_reference 列出 `ref/`，可见 `BallSort工程拆解_2026-10-01/`、`BallSort竞品拆解_2026-10-01/`、`IAA选品HTML集/`、`skills/`、`公司skill整合/`；这些均非选定参考，未读取正文、未提取或引用。不引入排序关卡求解或第三方素材。

沿用真实已确认的青绿色 #14B8A6、程序化SVG星星与原生Canvas drawImage；五位置固定，前四次命中换位置，第五次唯一胜利，无失败/限时/音效/AI/运行联网。计数、胜利和按钮使用DOM，缩放与规则分离，命中半径32 CSS px不随动画变化。本局存档/恢复为上游既定范围，没有新增产品机制。

## 本轮真实执行

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| npm run build | 0 | 资源哈希校验通过，最终dist为6文件、10435字节，低于10MB |
| npm test | 0 | 5组、5通过、0失败，无跳过 |
| npm run check | 0 | 真实启动Chromium 153.0.8010.12；9组浏览器场景通过；检查服务器自动停止 |
| node scripts/release.mjs | 0 | 实际ZIP提取、CRC校验、离线缓存npm ci --ignore-scripts清洁安装、隔离源码重建及规则测试通过；重建与试玩ZIP逐文件字节一致 |

环境为Node v22.23.3、Playwright锁定1.63.0、无头Chromium。使用现有真实浏览器依赖，未重复安装。浏览器访问本次隔离地址 `http://127.0.0.1:36699/pipeline-star-check-20261109/`，仅服务最终dist入口及包内相对资源；该临时服务已停止，不是线上试玩网址。

三项主验证及打包校验的工具源码指纹前后均为 `f5bee39e60c64acd15a1877f641c1e7f3ea9b3d61950e50b6351746ea593a618`，无源码变化。工具构建指纹为 `75ff4a2d9803fe17264e4765b6694cfedd97f3ba8c593bda8da5b00c175741cd`。脚本按路径及文件哈希计算的dist集合指纹为 `e912426d50d31a560b3affd1149b00cb78dbaae6f7cf549c38004b0ab1a924cd`；browser与release证据一致，单文件详见 evidence/check.json。不同工具口径不可混用。

## 原型验收映射

| 条件 | 本轮检查与结果 |
| --- | --- |
| R1 完整循环与不变量 | 规则验证0–5、count与phase/targetIndex一致；实际鼠标/触摸逐次采集1、2、3、4、5，不注入胜利。固定目标位置均不同且命中真实有效 |
| R2 非法输入 | 鼠标空白、右键、拖出再拖回、动画锁内点击不计数；非主指针与pointercancel为DOM边界模拟，状态不变 |
| R3 胜利与重开 | 胜利后再点保持5，重开清零；手机两尺寸均重开后再次完成整局 |
| R4 旧局事件 | 4/5时按下末目标，Enter重开后释放旧鼠标，新局保持0 |
| R5 布局与调整 | 1280×800桌面；桌面上下文调整为320×568后真实命中下一目标，再返回1280×800保持进度；390×844和320×568手机DPR2。无水平溢出，五位置安全内边距≥40，按钮高度≥44 |
| R6 输入平台 | 鼠标与Chromium touchscreen.tap分别完成核心循环；手机为浏览器设备模拟而非真实手机 |
| R7 动画/减少动态 | 正常rAF、连续录像及实际scale采样通过；reduce媒体模式下无动画等待且再次五次胜利 |
| R8 刷新恢复 | 2/5刷新恢复2；胜利刷新恢复5及胜利文案；重开刷新恢复0 |
| R9 存档异常 | 损坏/版本不兼容安全回退；模拟Storage写失败告警跨等待与后续失败持续；解除故障后的真实写成功清除，刷新恢复3。规则层另覆盖类型及越界 |
| R10 生命周期 | 隐藏/返回为document.hidden及visibilitychange边界模拟，清锁且无自动计数，随后真实鼠标可继续。旧局重开验证见R4；未独立穷举每个动画时刻重开或系统后台 |
| R11 独立路径 | 最终dist在目标slug子路径加载真实SVG/JSON/JS/CSS；正常场景errors=[]，无外部请求。另隔离资源中断，显示重试后恢复可玩，不混入正常场景错误 |
| R12 包重建 | 实际源码ZIP清洁安装、重建、规则测试；重建逐文件一致，试玩ZIP CRC/逐文件一致，展开10435字节 |

美术A1–A6的对应证据为资源加载、三视口及窗口调整、连续录像/rAF、reduce模式、胜利与重开、截图及存储告警。没有把静态预览当作运行画面。存档类型异常和缩放精确关键帧由规则测试覆盖；UI诊断属性只读用于表现采样，不作为规则来源。

## 画面与正常速度动画证据

本次check实际保存7张页面截图（同名文件更新或内容相同）与3段新WebM录像。已有上次3段录像保留，但不作为本次成功依据。

- `evidence/browser/desktop-initial.png`、`desktop-won.png`
- `evidence/browser/mobile-390-initial.png`、`mobile-390-won.png`
- `evidence/browser/mobile-320-initial.png`、`mobile-320-won.png`
- `evidence/browser/storage-warning.png`
- 本次新录像：`evidence/browser/page@8d18500d689d473c5851a9dc3852dd52.webm`、`page@71632575899919d9d5e4252fcca8841e.webm`、`page@865e94841f1277c06648e076c2c00308.webm`。

实际读取桌面初态、390宽初态、320宽胜利图片，青绿色星星完整、深色轮廓可见、计数与重开清晰，胜利文案准确；手机截图为DPR2，截图像素尺寸不等于CSS尺寸。320短屏截图为fullPage：重开可通过正常纵向滚动触达，不声称所有内容都在首屏。

实际读取一段本次WebM文件，工具返回视频内容；本报告不把视频文件读取等同于逐帧人工视觉判读。动画成立依据是源码实际drawImage/rAF、正常时间运行录像与连续采样共同构成，非静态截图或冻结时间：本次 evidence/check.json 记录452.2ms比例0.90，552.3ms约1.059998，618.9ms回到1并保持。采样间隔约16.7ms，符合160ms规格附近完成；采样时间并非动画精确起点，不宣称据此得到精密时长测量。

## 交付与包一致性

- 可玩入口：`dist/index.html`，必须连同包内相对资源以静态HTTP托管，支持 `/pipeline-star-check-20261109/`。
- 试玩ZIP：`releases/star-collection-play.zip`，6条目、11059字节；SHA256 `1b60f7c5cab8bb168da12a0d34d616069e7fc1f4dc652dcf5294f5cf1221f9b3`。
- 源码ZIP：`releases/star-collection-source.zip`，19条目、74243字节；SHA256 `7436e7e0470b09e18e20343830de1a5249181383b7a00116173ae3e47e3475ba`。本次重封装与原代码交付字节一致，保留上游交付，不包含随后写入的本测试报告；测试报告与证据单独交付。
- 结构化证据：`evidence/build.json`、`evidence/check.json`、`evidence/release.json`，均为本次命令真实输出；原 `code-validation.json` 是上游历史记录，不作为本轮验证结果。
- 本阶段新增报告：`workflow/test.md`。

清洁安装实际利用本机npm离线缓存，禁用生命周期，不使用原工程node_modules。首次从空缓存安装、下载浏览器仍可能需要网络；没有执行公网安装或下载，不能把离线缓存成功推论为所有新机器可离线安装。游戏运行本身无外部联网依赖。

## 限制与后续归属

未覆盖真实手机、iOS Safari、Firefox、真人手感与单局时长、真实多指并发/系统后台、逐动画时刻重开、键盘Space的独立浏览器断言、屏幕阅读器实测、公网发布后路径验收。Enter重开、模拟边界和单一Chromium成功不能替代这些范围。

没有调用图片API、独立视觉服务、编辑器、ADB或联网搜索。当前没有公网发布工具，未声称上线目标slug。若后续平台验收发现实现缺陷，应返回代码阶段修复、重新执行三项验证并重新确认；本测试阶段未私自修复或改变上游产物。
