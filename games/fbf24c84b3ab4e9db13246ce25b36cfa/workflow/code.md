# 星点采集 · 代码与集成交接

## 阶段与依据

本轮为代码阶段，attempt=1，resume=false。实现与本阶段真实验证完成；未代替后续独立测试阶段确认，也未执行公网发布。

实际读取：已确认的 `workflow/prototype.md`、`workflow/art.md`、`workflow/art-manifest.json`、美术预览、真实 SVG、视觉配置和已有核验脚本；完整读取本轮冻结的 `casual-game-production/SKILL.md` 与 `genre/docs/general.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。冻结哈希见上游原型表格。

参考路径：用户 `references=[]`。通过 read_reference 列出 `ref/`，目录含 BallSort工程拆解_2026-10-01/、BallSort竞品拆解_2026-10-01/、IAA选品HTML集/、skills/、公司skill整合/；均非选定参考，未读正文、未提取、未引用。没有引入排序或消除玩法。

用户已真实确认青绿色。本轮通过 inspect_assets 复核三个上游美术文件，哈希均与清单一致；未改上游原型或资源。SVG 和配置实际进入 dist，预览仅随源码交接，不进入试玩包。没有图片API生成、第三方素材授权声明或音效。

## 实现与设计决策

- 原生 Canvas 2D，非 Cocos；打开即开局，一个页面、一个星星，前四次命中换位置，第五次唯一胜利，重开随时可用。
- `public/rules.js`：独立规则、版本化存档校验、安全区域位置映射、固定半径命中与缩放曲线；状态提交不依赖 DOM 或动画。
- `public/app.js`：图像与配置加载、DPR绘制、Pointer Events 输入和生命周期。仅主指针/鼠标左键，按下和释放都命中且同局才提交；拖出、取消、动画锁内输入不补点；重开取消旧输入。
- 缩放为真实 requestAnimationFrame，160 ms，0.90→1.06→1.00，分段 ease-out-cubic。减少动态效果即时可点；隐藏取消活动指针并停止表现，返回清除动画等待锁。
- SVG 使用 drawImage 等比绘制为56×56 CSS像素，半径32命中区与动画独立；40像素安全内边距；手机高360、桌面420、最大宽480，DPR上限3；短屏正常滚动。
- 标题、计数、胜利提示为 DOM 文本；重开为语义按钮，Enter/Space及焦点样式可用。Canvas不是唯一文字信息来源。
- 本局 localStorage 保存 `{version:1,count,targetIndex,phase}`；校验版本、类型、范围与相互不变量。刷新恢复游戏中和胜利态；损坏/过期回到新局。写失败告警持续保留，直到真正写成功；读取受限不阻止游戏。无账号、云存档、随机难度或外部运行请求。
- 资源失败可见诊断与重试。构建直接复制 public，所有路径相对 `dist/index.html`；真实验证路径 `/pipeline-star-check-20261109/`。

主要逻辑附中文注释；代码标识为英文。运行依赖只有浏览器原生能力；开发验收依赖固定 Playwright 1.63.0，锁文件已交付。

## 产物

| 路径 | 用途 |
| --- | --- |
| `dist/index.html` 及同目录相对资源 | 完整可玩构建，6个文件，展开10435字节，远小于10MB |
| `public/index.html`、`style.css`、`app.js`、`rules.js` | 页面、响应式布局、输入/渲染和独立规则源码 |
| `public/assets/star.svg`、`visual-config.json` | 复用并实际集成的已确认美术文件 |
| `package.json`、`package-lock.json`、`README.md` | 固定构建/测试接口、依赖锁定和清洁重建说明 |
| `scripts/build.mjs`、`check.mjs`、`release.mjs`、`tests/rules.test.mjs` | 真实构建、规则测试、Chromium集成验收与ZIP打包/重建检查 |
| `releases/star-collection-source.zip` | 精简源码包，含源码、锁文件、脚本、测试、上游交接与本报告；不含node_modules、dist或参考源码 |
| `releases/star-collection-play.zip` | 试玩包，根入口index.html，仅含已验收dist的6个文件；11059字节 |
| `evidence/build.json`、`check.json`、`release.json`、`code-validation.json` | 逐文件哈希、真实结果、正常帧采样及包重建日志 |
| `evidence/browser/` | 7张实际截图和3段正常速度WebM录像 |

## 本次真实验证

所有源码/资源修改完成后执行以下命令，全部退出码0；没有通过后修改或重建最终 dist。后续仅补写报告/证据并重新封装源码包。

| 命令 | 实际结果 |
| --- | --- |
| `npm run build` | 上游美术清单逐文件SHA256校验通过，构建6文件/10435字节 |
| `npm test` | 5组、0失败：五次唯一胜利/重开、全部有效进度恢复、损坏及越界拒绝、三尺寸安全边距/命中、缩放关键帧 |
| `npm run check` | 实际启动Chromium 153.0.8010.12，Node v22.23.3；9组浏览器集成场景通过；隔离静态服务器结束自动关闭 |
| `node scripts/release.mjs` | 真实ZIP生成/逐项CRC校验、实际提取源码、离线缓存 `npm ci --ignore-scripts --offline` 清洁安装、提取源码重建与规则测试通过；与最终dist逐文件字节一致；试玩ZIP字节一致 |

浏览器覆盖：1280×800鼠标完整循环、窗口改为960×720；390×844和320×568、DPR2手机真实浏览器触摸输入分别两局。验证空白、右键、拖出、动画期间点击、旧局释放、胜利后点击、重开键盘操作；2/5、胜利、重开刷新恢复；损坏和旧版本存档、写失败持续提示与恢复可写；减少动态效果与资源故障重试。常规场景控制台错误、失败请求、外部请求均为0。资源故障测试单独注入并解除，不将预期失败请求伪报为常规错误。

取消、多指主标志、隐藏/返回和存储异常使用明确标注的 DOM/API 边界模拟，不声称为真实多点触屏或系统后台行为。核心胜利均由实际鼠标/触摸操作达成，未注入计数或胜利。

### 视觉与动画证据

- `desktop-initial.png`、`desktop-won.png`：桌面初态与胜利。
- `mobile-390-initial.png`、`mobile-390-won.png`、`mobile-320-initial.png`、`mobile-320-won.png`：手机两尺寸初态与胜利，fullPage包含短屏滚动下的重开按钮。
- `storage-warning.png`：真实页面的模拟存储失败持续告警。
- `evidence/browser/page@6e4c422b89dc5c519ec1739fc8dbe2aa.webm`、`page@d3a25f9f306de22d48488ae77be6e98b.webm`、`page@c9b26bd800b8a9169486b392e0627021.webm`：三上下文正常运行连续录像；动画未加速、未冻结或替换时间。
- `evidence/check.json` 的 animationFrames 为正常rAF采样：观察到0.9、1.0599999附近峰值及回到1，非静态峰值截图。已读取桌面初态及320宽胜利截图，实际星星青绿色、轮廓完整、文本与重开清晰，无明显裁切。

### 指纹与一致性

- 三项主验证的工具源码指纹前后均为 `f5bee39e60c64acd15a1877f641c1e7f3ea9b3d61950e50b6351746ea593a618`。
- 构建脚本按package/public/scripts/tests排序计算的源码集合SHA256：`fe350582597d61c5d3a211cdf114f1c4840ece21328dd641f1551993c29ef534`；与工具口径不同，详见 evidence/build.json 文件列表。
- 工具构建SHA256：`75ff4a2d9803fe17264e4765b6694cfedd97f3ba8c593bda8da5b00c175741cd`。
- 构建/浏览器/打包脚本按路径及单文件哈希计算的dist集合SHA256：`e912426d50d31a560b3affd1149b00cb78dbaae6f7cf549c38004b0ab1a924cd`，三份证据一致；报告与源码ZIP变化不改变运行构建。
- 星星SHA256：`7344a233421e96ed041f7a12fef32efc37e679707d6b32157e1e201d52035d53`；视觉配置：`84c9b8b3bcb69b9d7f09175e8cfc7e8cb1f44596d395a388ac546d7d39e54d0d`。
- 试玩ZIP SHA256：`1b60f7c5cab8bb168da12a0d34d616069e7fc1f4dc652dcf5294f5cf1221f9b3`。源码ZIP最终大小、条目数与哈希以加入本报告后重封装生成的 evidence/release.json 为准，避免报告自引用哈希。

## 验收条件与边界

原型 R1–R12、美术 A1–A6 均有本阶段对应自动化证据；R2多指/取消、R9存储异常、R10隐藏返回为边界模拟，非设备级证据。R12源码包实际提取重建及试玩包一致性通过。后续测试阶段必须独立重新执行 `npm run build`、`npm test`、`npm run check`，不能只引用本轮日志，且不修改上游源码或资源。

未覆盖：真机/iOS Safari/Firefox/真人手感与单局时长主观评价、真实多指并发和系统后台、外网发布后验证。本轮只交付可部署构建及独立子路径兼容性，不声称已经上线目标slug，不自行推进下一阶段。开发清洁首次安装通常需要npm源或离线缓存及可用Chromium；试玩运行不联网。没有调用编辑器、ADB、搜索或独立视觉服务。
