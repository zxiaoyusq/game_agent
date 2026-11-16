# 萌兽方块 · 美术资源交接

## 范围与证据
- 项目 df0115c4db8c46e69563fd9dc343a6cb；当前仅 art，attempt=1。复用并保持 `/workflow/prototype.md` 原文不变；没有现成游戏源码，未推进代码或测试阶段。
- 中文界面明确采用 `zh-CN`；所有图片无烘焙文字，预览中文标题、HUD与控制通过DOM绘制。没有引入音频、在线字体或第八类方块。
- 工作前完整读取全部四份冻结Skill入口：casual-game-production、ai-art-automation、casual-game-art-style、azure-image2-generation；完整读取三份冻结知识 general.md / web-common.md / canvas-web.md。按需读取 ui-runtime-delivery.md 与 design-system.md。执行方法采用本轮真实工具，不使用文档中的外部CLI、Python、Creator或ADB。
- 开始实际 `inspect_assets(paths=null)` 结果空；根目录仅有上游workflow。最终再次inspect_assets取得清单17项当前SHA256。
- 唯一原参考相对 ref/：`mcp-inputs/mac-codex/99a6cca2d49fa9163d002045319f920e1b004b09156b98160981beb351b1eafb/animal-tile-art-reference.png`。本轮read_reference实际读取仍仅返回PNG二进制文本，工作区无可读图片映射，不能把它当作已看见或作为工具参考输入。本轮没有原PNG的工具确认SHA256。
- 沿用用户已真实补充的许可：若远端仍无法直接查看，按调用方核对的原图描述制作预览供调用方比对；无需重复询问同一限制。原图724×1000、5×6阵列等信息来自用户补充，而非本轮视觉观察。参考仅负责动物牌与星空风格，棋盘仍经典10×20。

## 设计决策
采用浅暖奶油白厚圆角牌、暖金灰细边、柔阴影，大头大眼幼崽与细彩色内边。动物有柔渐变和绘本式毛羽体积光，背景深海军蓝稀疏微光星点，棋盘用独立不透明暗蓝底退后，网格细弱。母版细节丰富但小尺寸以大眼、耳/喙/尾形和主色辨识；不同动物不随机换类。

| 类型 | 动物 | 正式路径（工作区） | 功能色 |
|---|---|---|---|
| I | 蓝橙翠鸟 | public/assets/tiles/I-kingfisher.webp | #49adf1 |
| O | 金黄斑点幼豹 | public/assets/tiles/O-leopard.webp | #eab643 |
| T | 紫猫头鹰、米白胸 | public/assets/tiles/T-owl-card.webp | #ad79e2 |
| J | 暖棕熊 | public/assets/tiles/J-bear.webp | #c08756 |
| S | 翠绿变色龙、盘尾 | public/assets/tiles/S-chameleon.webp | #6ac35b |
| L | 橙狐狸、白胸 | public/assets/tiles/L-fox.webp | #f69941 |
| Z | 粉耳白兔 | public/assets/tiles/Z-rabbit.webp | #eea6c4 |

同块四格、已固化格与下一块复用同一动物图片。固化牌不额外压暗，防止24px识别受损；活动块加类型色1 CSS px边线和轻柔亮影；虚影0.18透明度加同色虚线，不作为实体。主操作按钮金黄/深蓝字，次按钮蓝底/奶油字，同家族12px圆角；触控命中区至少44px、间隔至少8px。字体系统中文，无字体文件与联网依赖。

## 真实生成与加工
本轮实际调用工程图片API三次，返回provider=openai-image-api、model=gpt-image-2，质量high。未猜测其他模型或授权条款，没有复制用户原图像素。
1. `masters/owl.png` 1024×1024：提示独立正面紫猫头鹰幼崽、米白胸、大眼高光、浅奶油圆角方牌、暖金灰细线、紫内边、纯深海军蓝外底、无文字/配件/棋盘。无参考图片。SHA256见清单。
2. `masters/animal-six.png` 1536×1024：实际输入本轮owl.png作为唯一画风参考；提示严格3×2、每格512×512，依次翠鸟/幼豹/熊、变色龙/狐狸/兔；奶油同族牌面、各类细功能色内边、纯深蓝外底、动物完整。不是用户原PNG参考改图。
3. `masters/starfield.png` 1024×1536：无输入参考；提示海军蓝、安静中心、稀疏蓝微光星点，不含月亮/银河/动物/方块/UI/文字。

七张正式WebP均256×256，无损等比处理。T使用完整1024母版缩小；其余按六个512×512单元裁切，坐标依次 (0,0)、(512,0)、(1024,0)、(0,512)、(512,512)、(1024,512)。裁切全部在1536×1024内，不旋转、不拉伸、不截断动物。

背景 `public/assets/backgrounds/starfield.webp` 为768×1152（2:3），由1024×1536等比缩小；这是适应实际生成画幅的常规技术决策，原型768×1536仅建议值。显示使用cover居中等比裁边，不按棋盘1:2强拉伸。

### 透明度与采样契约
- process_art_image实际报告所有256牌面为65536不透明像素，透明/半透明像素为0，alpha范围255…255；背景同样全不透明。没有真实透明外边距，也没有执行抠底，不作相反声明。
- 用 `drawImage(image,16,16,224,224,x,y,cellSize,cellSize)` 采样，各牌有效奶油边约占90%以上；在目标格用半径 `0.16*cellSize` 的roundRect clip隐藏深蓝角部，不按颜色阈值去底。开启imageSmoothing；类型外边线由程序绘制。这是可用的非透明技术方案，不是透明PNG替代。
- 正式T路径为 **T-owl-card.webp**。早期试裁 `public/assets/tiles/T-owl.webp` 保留为非交付候选（48,48,928,928），未进入正式清单与预览；下游禁止通配复制该文件。
- 原始母版、qa样张、previews均保留追溯，但不进入dist。

## 预览与尺寸检查
- 入口 `/assets/art-preview.html`：静态HTML/CSS、相对路径中文DOM HUD与按钮示意；没有玩法脚本、网络资源或可点击游戏按钮。
- `/public/assets/previews/mobile-board.png`：390×700，10×20、24px格；活动猫头鹰T、落点虚影、下一块幼豹O及底部动物堆叠。棋盘范围x=75…314、y=112…591。
- `/public/assets/previews/desktop-board.png`：720×740，30px格；同构图，布局容器可由下游在桌面居中扩展，不把整张图拉成可玩棋盘。
- `/public/assets/previews/size-sheet.png`：420×130，第一排24×24、第二排30×30七动物真实派生样张；`public/assets/qa/` 保留14个单张PNG。
- 上述棋盘PNG由 `/scripts/art-preview.cjs` 将正式WebP经process_art_image派生样张与实际背景母版确定性合成，不是AI整屏图，不是浏览器试玩截图。背景使用母版同源图而非最终WebP解码；不声明与最终Canvas逐像素一致。
- 实际read_file查看过三张AI母版、初版手机/桌面预览、原尺寸拼图：动物角色与主色符合映射，裁切没有邻格串入，24px外轮廓和大色块可区分，兔子眼睛和粉耳、猫头鹰紫色、变色龙盘尾保留；幼豹斑点/毛羽纹理在24px部分消失属正常缩小，不以这些微细节作为唯一辨识手段。最终背景采样改为cover后须在下游浏览器再核验全屏呈现。

## 验证结果（本attempt真实执行）
执行 `node scripts/art-preview.cjs` 两次均exit_code=0；最后一次在所有合成脚本、HTML与visual-spec修改后执行：
> 美术文件检查通过：14张尺寸样张，2张棋盘预览回读一致，运行素材共934122字节。未执行游戏或浏览器验收。

最后一次实际检查：PNG解码、14样张尺寸、1536×1024图集及6裁切界限、7类映射、8正式资源存在非空、中文预览lang及图片相对路径、预览编码/解码像素回读一致、素材字节预算。证据 `/evidence/art-file-check.json`。17项清单哈希来自随后inspect_assets，不借旧日志。

8张运行图总计 **934122字节（约0.89MiB）**；这是素材预算，不是最终dist大小验收。源码/玩法尚未生成，未运行npm run build、npm test或npm run check（这些归代码和测试阶段），未安装Playwright，未做浏览器/真机/离线试玩操作。

一次owl-24样张写到assets/previews被process工具拒绝（工具仅允许public/assets），随后更正为public/assets/qa/owl-24.png并实际成功；无悬而未决加工失败。没有用被拒绝路径宣称产物。

## 下游集成与动画规格
交接 `/workflow/visual-spec.json`。路径值相对未来dist/index.html，仅复制七牌与星空8张图到dist/assets，不通配复制public。配置应编译为常量/内嵌，不在file://下fetch JSON；用本地Image加载后drawImage，保持加载失败中文提示。Canvas规则/输入/渲染分离，不用本静态构图行数组冒充可玩逻辑。

消行保持上游180ms：前60ms最大0.25透明度奶油柔光，后120ms淡出；每行至多6个微小粒子、寿命≤180ms，不晃动棋盘。prefers-reduced-motion下取消闪光/粒子，时序180ms后直接提交新棋盘；暂停冻结动画，重开使旧会话回调失效。当前仅规格，不存在已运行消行动画或序列验收。

下游验收条件：
1. 10×20保持1:2，390及320px宽/桌面实际Canvas中七类主色、外轮廓可读，24px时不额外内缩；DPR缩放不改规则格。
2. 活动、固化、虚影、下一块真正引用正式七牌路径，特别不能误用T早期候选；星空背景使用正式WebP且cover不拉伸。
3. 中文标题/HUD/按钮/暂停/结算/错误和aria，html lang=zh-CN，英文浏览器仍默认中文。
4. 正常速度180ms消行与减少动态偏好分别验证并保存连续证据，静态美术预览不能代替动画证据。
5. 真实桌面键盘与手机Pointer点击完成玩法，资源加载失败可诊断；离线file://、最终dist小于10MB由后续真实构建与check检验。

## 来源与限制
资源为本轮生成和确定性加工的自制交付，不导入用户参考像素、外部IP标志或署名。API使用及商业授权条款未由工具核定，不作“已获商业授权”保证；用户原参考版权也未由本轮认定。

原参考仍未能直接视觉核验，预览需供调用方与原图比对；这不等于本轮已取得用户视觉确认。当前交接的是**真实素材包和静态构图**，尚未合入可玩游戏；最终集成、浏览器语言/触控/动画、真机及离线试玩验收均待后续阶段。本轮未创建dist或releases、不声称有试玩ZIP，不代替流水线确认、不自行推进下一阶段。

实际主产物：`workflow/art.md`、`workflow/art-manifest.json`、`workflow/visual-spec.json`、`assets/art-preview.html`、清单所列真实资源与`evidence/art-file-check.json`。

清单写入后补充执行 `node scripts/art-manifest-check.cjs`，本attempt退出码0：17项全部实际非空、path/sha256/usage/source均为非空字符串、当前文件SHA256逐项匹配，无重复路径。脚本只读资源，不重写预览；证据为 `/evidence/art-manifest-check.json`。
