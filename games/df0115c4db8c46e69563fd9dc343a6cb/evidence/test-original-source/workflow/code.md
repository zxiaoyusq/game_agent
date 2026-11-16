# 萌兽方块 · 代码与集成交接

## 1. 范围与依据
- 项目 df0115c4db8c46e69563fd9dc343a6cb，当前 code，attempt=1、非恢复执行。仅完成代码阶段及其必要自验，不代替独立 test 阶段确认，不自动发布。
- 工作前完整实际读取冻结 `casual-game-production/SKILL.md` v1.2.0，以及 `genre/docs/general.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。未扩充未选Skill。
- 实际读取并保留上游 `workflow/prototype.md`、`workflow/art.md`、`workflow/art-manifest.json`、`workflow/visual-spec.json`。既有美术脚本、素材与报告未修改。
- 唯一参考相对 ref/ 路径：`mcp-inputs/mac-codex/99a6cca2d49fa9163d002045319f920e1b004b09156b98160981beb351b1eafb/animal-tile-art-reference.png`。本次 read_reference 返回PNG二进制文本，未直接看见原PNG；沿用用户已回答许可，依据调用方核对描述和已确认美术资源制作，不编造原图视觉确认或原图哈希。
- 实际打开美术手机预览及最终浏览器桌面/手机截图。八张正式运行素材均由 inspect_assets 重新清点，SHA256逐项匹配上游清单，总934122字节。使用自制AI资源的来源沿用 art.md，工具未核定商业授权。

## 2. 实现与设计决策
- 原生Canvas 2D，不加载Cocos、框架或伪造引擎。中文界面、`html lang=zh-CN`，不随浏览器语言切换。
- `src/rules.js`：10×20可见区加2隐藏行；七袋Fisher–Yates；七类四连方块；顺时针SRS及I专表/O不变；软降+1/格、硬降+2/格；接地500ms、最多15次有效重置；同时消行、180ms动画冻结输入；100/300/500/800×旧等级；每10行升级；自然速度1000ms×0.8^(等级-1)，最低100ms；隐藏固化残留或出生重叠结束。
- `src/renderer.js`：状态驱动Canvas绘制、DPR封顶2、棋盘保持1:2；正式256牌按16,16,224,224采样，以0.16格圆角clip隐藏不透明外角；活动色边、0.18图像虚影加虚线；固化不压暗；下一块复用牌面；深蓝棋盘独立遮底，星空背景cover。清行动效前60ms轻闪、后120ms淡出、每行6微粒；减少动态不闪不粒子，保持规则时序。
- `src/input.js`：键盘方向键、Space、P；左右150ms后每60ms重复、最后按下优先；Pointer捕获、取消、多指策略；只用一条Pointer输入链，避免鼠标/触摸重复；硬降100ms保护防多指穿透，硬降后清理旧长按；DOM按钮支持键盘原生激活。
- `src/app.js`：开始、暂停、继续、再玩；活跃局重开确认；隐藏/失焦自动暂停、显式继续；帧delta上限100ms，后台不补算；不提供注入棋盘/分数接口，只有只读 `window.tetrisSnapshot` 供诊断。
- `src/storage.js`：最高分JSON版本与安全整数验证；损坏/未知版本不崩溃；读写失败持续提示并保留内存纪录，真实成功写入才清除。刷新回待开始，仅保留最高分；按原型不做跨刷新整局恢复。
- 中文首屏规则、HUD、菜单、错误与Canvas无障碍名称；手机五个按钮带图标和中文。390px棋盘250×500 CSS px，即25px格；按钮48px高、间隔8px。390×844主要玩法与按钮在屏内；390×700、320窄屏、横屏及桌面高度不足允许纵向滚动，无横向溢出，不裁去按钮。桌面1280×800完整页面约996px高，需滚动访问屏幕按钮，键盘无需滚动即可操作；最终桌面截图为fullPage，不冒充800px内全部可见。

## 3. 构建与离线交付
- `scripts/build.cjs` 清洁生成dist，普通script本地文件；视觉JSON编译为常量，不fetch配置、无ES模块/CORS运行时依赖、不用CDN或在线字体。
- 构建只复制8张白名单图，特别使用 `T-owl-card.webp`，不包含旧T候选、母版、QA、静态预览、workflow或研究源码。
- `dist/index.html` 为唯一入口，包内相对资源均可用；共15文件、**963575字节（约0.92MiB）**，展开小于10MB。
- `scripts/archive.cjs` 真实ZIP存储模式/CRC32；`scripts/release.cjs` 仅打包，不重建或修改dist。包名：
  - `releases/animal-tetris-play.zip`：解压双击index.html即可玩，965301字节。试玩内容SHA256 `7e358beb6a821c6a2b2c126a9854f529d6b6ff2827eaeb4c59a32f4b3f5bc71c`。
  - `releases/animal-tetris-source.zip`：src、脚本、测试、锁文件、README、上游素材与报告，保留可重建源码。最终包尺寸和SHA256以 `evidence/releases.json` 为准；本报告补写后重新打包源码，运行代码和dist不变。
- README含 `npm ci`、三条验证命令与浏览器依赖说明。Playwright锁定1.63.0；prepare_web_runtime在package存在后真实成功安装。没有承诺源码包自带浏览器。

## 4. 本attempt最终真实验证
最后一次源码/验收脚本修改后重新执行，均退出0：

| 命令 | 真实结果 |
|---|---|
| `npm run build` | 15文件，963575字节；运行素材哈希校验通过 |
| `npm test` | 13/13通过，覆盖R01–R14组合用例及随机不变量 |
| `npm run check` | Chromium 153.0.8010.12真实运行最终dist，桌面/手机/离线/源码重建通过 |

- 最终工具源码指纹：`f553a5174357d44c440f804dee6e6c0d95074f874c34b204cbd8a4a2d377e1a8`（验证时整个工程源输入）。报告和evidence补写不属于运行代码修订。
- check额外记录src/scripts/tests内容指纹：`8447a21b8e6ac8be1557da2168cfd302cc01560f6a3a12d22bbf7a75265a8e95`。
- 最终构建工具SHA256：`09b0717306a50197f2fee72563ef8ffdc44c21899e7210968f8471143c49249f`；逐文件哈希见evidence/build.json及check.json。check前后dist逐项哈希不变；验收后不重建或修改dist。
- 最终重复check桌面从空棋盘纯键盘规划10块，真实消2行、672分（七袋随机使每轮分数不同）；再真实制造消行、P暂停400ms、核对剩余动画/奖励冻结、继续后无重复结算；真实硬降堆至触顶、结束与再玩；最高分刷新持久化、重开确认/取消；左右长按、旋转、软降、暂停、失焦恢复。
- 手机真实浏览器模拟触摸使用Pointer/CDP输入，五按钮、长按330ms、touchCancel、多指旋转及双指硬降恰生成一块；从空棋盘真实触点消行、暂停恢复。
- 视口1280×800、390×844、390×700、320×700、844×390；棋盘比例1:2、按钮≥44px、无横向溢出。默认中文在en-US和zh-CN浏览器均核对。
- 正常速度rAF连续Canvas截图及WebM视频，没有改时钟或加速动画。动画JSON记录180ms剩余时间逐帧下降和清行完成，分数不重复；另在减少动态环境真实消行。
- check自行启动隔离端口本地静态服务器、访问 `/nested/game/index.html` 子路径，最后自动停止；正常控制台/pageerror及外网请求均0。
- 实际解压试玩ZIP、校验CRC及哈希，`file://`且browser offline=true真实开始/移动/旋转/硬降/重开通过，无网络依赖；不需要额外单文件HTML。
- 实际解压源码ZIP，在独立 `evidence/source-rebuild` 使用当前Node执行其原构建脚本，重建文件哈希与最终dist逐项一致。没有联网重新执行npm ci，清洁依赖安装仍待独立验收复核。
- 禁存储环境真实硬降后持续中文失败提示，仍可玩。人为中止T资源请求后显示中文错误，取消拦截点击重新加载恢复；该预期网络错误单列记录，不计作正常控制台错误。

## 5. 失败记录与修复
- 首次prepare_web_runtime因尚无package.json被拒；写入真实package后重试成功。
- 首次规则R08断言失败：测试夹具在14次合法操作后锁定计时被重置到0，错误期待1ms固化。补充最后一次重置后的499ms推进后复测通过；未放宽500ms规则。
- 首次check超时：脚本使用不存在的快照API名 `animalGame`，实际工程为只读 `tetrisSnapshot`；修正验收读取和加载就绪条件，并避免向规则只读getter赋值。诊断浏览器尝试不存在的/usr/bin/chromium失败，使用实际Playwright Chromium后看见正确首屏；最终check自动选择可用浏览器。
- 补充硬降释放旧输入，防旧长按影响下一块；补充全页、活动块可见截图和消行暂停用例后重新执行全部三条命令。最终无未解决验证失败。`evidence/check-failure.json` 保留初次失败溯源，最终成功以check.json为准，旧视频亦不能当作最终成功。

## 6. 实际产物与证据
- 运行入口：`dist/index.html`；源码：`src/`。
- 离线试玩和源码包：`releases/animal-tetris-play.zip`、`releases/animal-tetris-source.zip`。
- 验证脚本：`tests/rules.test.cjs`、`scripts/build.cjs`、`scripts/check.cjs`、`scripts/archive.cjs`、`scripts/release.cjs`。
- 最终证据：`evidence/check.json`、`build.json`、`layouts.json`、`releases.json`、`animation.json`及其中帧索引对应的`clear-*.png`。目录保留前一成功轮次同构建截图，最终动画以JSON所列帧为准，不通配混用旧帧。
- 最终画面：`evidence/desktop-ready.png`、`desktop-playing.png`、`mobile-390.png`、`mobile-playing.png`、`mobile-320.png`、`game-over.png`、`offline-playing.png`。
- 最终连续视频：`evidence/videos/page@646f32d2fca20995973ae7b208d1372c.webm`。截图与视频是真实页面，不使用美术静态预览冒充试玩。

## 7. 限制与下游验收
- 本轮是代码阶段自验，不创建独立workflow/test.md、不自动确认或推进测试/发布。
- Chromium模拟桌面/手机，不代表实体手机、iOS Safari、Android Chrome或其他浏览器验收；没有Creator、ADB、外部视觉服务或联网采集。
- 原PNG无法直接预览，最终画面须供调用方与原图比对；不能宣称原图逐像素匹配、用户新视觉确认或商业授权保证。
- 不实现上游明确排除的音频、暂存、T-spin/连击、联网排行榜与跨刷新整局存档；无整局存档并非恢复失败。
- 错误/存储测试为明确隔离的故障模拟；普通核心循环全部来自真实输入，Node规划器只模拟候选，不向浏览器注入棋盘、得分或假结束。
- test阶段应只读重新运行build/test/check并核验最终ZIP和语言、真机范围及清洁安装；若发现需改代码/美术，应返回对应阶段修复。
