# 萌兽方块 · 独立测试验收

## 1. 结论与边界

**本轮自动化验收通过，保留未覆盖范围。** 项目 df0115c4db8c46e69563fd9dc343a6cb；test，attempt=1，非恢复执行。没有修改 src、素材、上游报告、原有构建和测试脚本；仅新增并修订 `scripts/test-audit.cjs`。不自动确认下一阶段或发布。

已独立执行构建、13项规则测试、真实 Chromium 桌面/模拟触屏验收、离线 ZIP 操作及源码 ZIP 解压重建。未发现需要返回代码阶段修复的运行缺陷。实体手机、Safari、全新机器清洁安装和原参考图直接视觉比对未完成，不能以自动化通过替代。

## 2. 依据与设计取舍

开始前完整读取冻结 `casual-game-production/SKILL.md` v1.2.0（f9e955b7b1834518aba9ea71c286ea04636724eb56fbe81fb6cbb96bc33d7d98），以及三份冻结知识 `genre/docs/general.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。实际读取 prototype.md、art.md、art-manifest.json、visual-spec.json、code.md、源码、README 和既有构建/规则/浏览器/打包脚本。

唯一参考相对 ref/：`mcp-inputs/mac-codex/99a6cca2d49fa9163d002045319f920e1b004b09156b98160981beb351b1eafb/animal-tile-art-reference.png`。本轮用 read_reference 定位并读取，仍只返回二进制文本，未直接看见原 PNG，也未得到其工具确认哈希。沿用用户已有真实许可，按调用方核对的视觉描述与正式美术资源核验成品，不重复询问同一限制。

规则以已确认原型为准：经典10×20、七袋、顺时针SRS、500ms接地锁定/15次重置、软降1分/格、硬降2分/格、100/300/500/800乘旧等级、每10行升级、180ms清行、隐藏固化残留/出生碰撞结束。参考5×6阵列不作为玩法。用户指定中文，页面 lang=zh-CN，英文浏览器仍默认中文。刷新仅保存最高分，不保存整局；后台恢复须明确继续。

## 3. 当前 attempt 的真实执行

最终一次补测脚本修改后重新执行全部必需验证：

| 命令 | 退出码 | 结果 |
|---|---:|---|
| npm run build | 0 | 15文件，963575字节，正式素材哈希通过 |
| npm test | 0 | 13/13通过，无跳过 |
| npm run check | 0 | Chromium 153.0.8010.12，桌面/手机/离线/源码重建通过 |
| node scripts/test-audit.cjs post | 0 | 上游不变，17项清单哈希一致，8张正式图实际进入dist，原交付和最终dist一致 |

此前执行 `node scripts/test-audit.cjs pre`，退出0：在原有 check 重新打包前先解压原试玩包并核对15文件一致；原源码包实际解压、独立重建并运行其13项规则测试通过。证据 `evidence/test-baseline.json`、`test-original-source-tests.txt`、`test-original-play/`、`test-original-source/`，避免重新打包掩盖原交付不一致。

最终源码工具指纹 `fb87877752ec79423b0c665b127a63d09d35dab509628eed80b97f61e7054de1`；check记录的src/scripts/tests指纹 `df61b23ec2965858c58a7c90fbeec16d8e74fa8551b7d070944dba73af9a1946`。构建工具SHA256 `09b0717306a50197f2fee72563ef8ffdc44c21899e7210968f8471143c49249f`。最终check后没有重建或修改dist。报告补写不改变运行代码。

## 4. 覆盖结果

- R01–R05：两袋公平性/预览一致、自然重力与长帧上限、墙及固化碰撞、T踢墙/全部候选失败事务、I墙/地板专表、O不变，规则夹具通过。
- R06–R08：虚影与硬降位置、恰固化4格、零距离锁定、软降计分、500ms锁定、15次重置及暂停计时冻结通过。
- R09–R13：单/双/三/四消、同时压缩、旧等级奖励后升级、隐藏格触顶与消行救回、出生碰撞、消行暂停和重开无旧结算通过。
- R14及不变量：非法/损坏/未知版本存档、失败持续提示及成功后清除，4000次随机合法动作检查4格活动块、无重叠、非负分数、等级一致通过。
- 桌面真实按键：开始、左右/旋转/软降/硬降/长按/P、重开确认和取消；从空棋盘9块真实消2行，538分；再制造清行并暂停400ms验证冻结及不重复奖励；实际硬降堆至触顶、结束、再玩和最高分刷新持久化通过。
- 手机模拟真实触点：五按钮、330ms长按、CDP touchCancel、双指旋转及双指硬降仅生成一枚、从空棋盘真实消行、暂停继续通过。Node规划器仅模拟候选，浏览器无棋盘/分数/结束注入。
- 子路径静态服务器访问最终dist，服务自动启动/停止；正常pageerror、console error及外网请求均0。资源中止故障模拟有1条预期 ERR_FAILED，中文错误和重试恢复通过，与正常错误分开记录。
- 禁存储故障模拟仍可硬降得分，持续中文保存失败提示；减少动态环境仍完成真实消行。
- 离线试玩ZIP实际解压后 file://、offline=true，开始、移动、旋转、硬降、重开通过；无CDN、联网配置请求或JS模块加载依赖。

边界旋转夹具、四消、升级等主要由规则层验证，不冒充全部已由真人自然游玩覆盖。失焦恢复使用浏览器内派发blur的故障模拟及规则暂停检查；没有声称实体设备后台生命周期已验收。

## 5. 布局、语言与实际视觉

视口1280×800、390×844、390×700、320×700、844×390通过无横向溢出、棋盘1:2、五按钮至少44px检查。手机棋盘250×500 CSS px，25px格；按钮48px高、8px间距。390×844按钮底约815px，主要操作可见；390×700和320×700需纵向滚动，符合原型允许短屏滚动的取舍。桌面页面约996px高，屏幕按钮需滚动，键盘可直接操作；fullPage截图不表示800px内全部内容可见。

已实际打开最终桌面/手机截图与清行00、07、10帧：深海军蓝稀疏星点、暖奶油圆角动物牌、大眼角色及不同主色可见；活动四格动物统一、虚影暗淡并有虚线边、下一块复用实际牌面。没有串入邻格或使用静态美术预览冒充游戏。手机下一块34px小预览的精细纹理较难辨认，主要靠轮廓/色彩及中文动物名称辅助；保留为体验观察，不声称原图逐像素一致。

实际运行素材：
- I：assets/tiles/I-kingfisher.webp
- O：assets/tiles/O-leopard.webp
- T：assets/tiles/T-owl-card.webp（不是旧候选T-owl.webp）
- J：assets/tiles/J-bear.webp
- S：assets/tiles/S-chameleon.webp
- L：assets/tiles/L-fox.webp
- Z：assets/tiles/Z-rabbit.webp
- 星空：assets/backgrounds/starfield.webp

以上路径相对dist/index.html；17项美术清单当前哈希全部匹配，8张运行图与public原文件逐字节一致。默认中文在en-US及zh-CN环境核对，标题、HUD、首屏教程、五按钮、暂停、重开、结算和错误均中文；键盘P为操作标识，不是切换英文界面。

## 6. 正常速度动画证据

没有修改时钟或加速动画。`evidence/animation.json`、`test-audit.json`记录真实rAF时间、剩余时长、分数、清行索引和逐帧SHA256。最终第一段 `clear-00.png` 至 `clear-10.png`：剩余163.4ms到0，时间3147.9到3314.6ms，分数始终326；可见同一满行淡出及压缩后新方块。审计确认至少三个不同图像帧，rAF经过时间与剩余时长一致。之后11–20帧属于另一次清行，不跨次比较计分。

最终验证录像：`evidence/videos/page@d887ba4aa1c1e057d615a1432e014251.webm`，1876687字节，SHA256 `dbd1da8ecad44ee42dd22b063b9538a7c069289ff3a40734d426f57dea7f34e0`。本轮早一次录像及上游旧录像保留，但不冒充最后一次成功证据。自动化真实记录视频；本报告视觉观察依据连续帧，不宣称已人工全片观看。

## 7. 交付与重建一致性

- 运行入口：`dist/index.html`，15文件展开963575字节，约0.92MiB，小于10MB。
- 离线试玩：`releases/animal-tetris-play.zip`，965301字节，SHA256 `7e358beb6a821c6a2b2c126a9854f529d6b6ff2827eaeb4c59a32f4b3f5bc71c`。解压双击index.html即可玩。
- 源码包：`releases/animal-tetris-source.zip`，5356134字节，SHA256 `f62be82dbe2e81fda6189d8a2cf39ce66d7c87d58b91978909383a633d590792`。最终check内仅重新打包，不改变dist；包包含新增补测脚本与此前上游报告，不包含本报告后补正文。
- 原源码包与最终源码包均实际解压，在evidence下使用Node v22.23.3执行原构建脚本，15文件哈希逐项与最终dist一致。原源码包规则测试也实际通过。未联网执行清洁npm ci；锁文件保留Playwright1.63.0，当前环境浏览器已可用，全新机器安装未验收。

截图：`evidence/desktop-playing.png`、`mobile-playing.png`、`mobile-390.png`、`mobile-320.png`、`game-over.png`、`offline-playing.png`。最终结果数据：`evidence/build.json`、`check.json`、`layouts.json`、`animation.json`、`releases.json`、`test-baseline.json`、`test-audit.json`。

## 8. 失败记录和限制

本轮首次补充post审计退出1：错误地把两次清行的258分和438分当作同一动画比较。实际动画JSON明确存在第一段完成帧及第二次得分，属于补测断言错误，不是游戏重复奖励。仅修正新增test-audit脚本，限定首个完整清行段检查，并在修改后重新执行build/test/check及post，全部退出0；未修改既有测试或放宽游戏规则。

限制：仅Chromium自动化/模拟触屏，未实体手机、iOS Safari或其他浏览器；原参考未直接预览，需调用方比对；未清洁npm ci或全新机器浏览器安装；短屏纵向滚动与微小下一块辨识保留体验取舍；存储、失焦和资源故障属于明确模拟。素材来自美术阶段真实生成和加工，工具未核定商业授权条款，不作商业授权保证。无音频、暂存、T-spin、联网排行榜及跨刷新整局存档，均为原型明确排除。

当前范围验收结束，报告不代替流水线确认，也不自动发布。若后续真机或原图比对发现需改源码/美术，应返回对应阶段修复、重新确认并完整重验。