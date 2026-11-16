# 萌兽方块

原生 Canvas 2D，中文界面，10×20 经典四连方块。无网络、CDN、运行时模块加载或在线字体。

## 试玩

解压 `releases/animal-tetris-play.zip`，双击 `index.html`；也可以将 dist 放在任意静态服务器子目录。所有脚本与图片均为相对路径。浏览器可能限制 file:// 本地存储，届时界面持续提示但游戏可玩。

← / → 移动、↑ 旋转、↓ 软降、空格硬降、P 暂停。手机或鼠标使用中文屏幕按钮。每消除10行升级；后台或失焦自动暂停，需手动继续；刷新只保存最高分，不恢复整局。

## 重建

Node.js 22+。解压源码ZIP，在根目录运行：

```
npm ci
npm run build
npm test
npm run check
```

Playwright 锁定1.63.0。`check` 优先使用 `/usr/bin/chromium`，亦可通过 `CHROMIUM_PATH` 指定本机Chromium；否则使用Playwright自带浏览器（需预先安装）。浏览器不是源码包的一部分。

`npm run check` 对最终 dist 启动临时静态服务器并自动关闭，覆盖桌面、手机模拟触摸、纯输入消行/触顶、动画序列、本地存储及file://，证据写 evidence/。`npm run release` 仅打包，不修改 dist。

## 结构

- src/rules.js：七袋、SRS、碰撞、锁定与计分
- src/input.js：键盘与Pointer长按、取消和失焦
- src/renderer.js：Canvas牌面、虚影、下一块和清行动效
- src/storage.js：最高分结构验证与失败反馈
- src/app.js：生命周期与中文DOM菜单
- public/assets：美术阶段原始交接，正式构建只复制8张白名单素材
- workflow/：已确认原型、美术与当前代码交接

自制AI素材来源详见 workflow/art.md；工具未核定商业授权条款。没有音频、联网排行榜、暂存、整局刷新恢复。自动验收是Chromium模拟，不代表实体手机验收。
