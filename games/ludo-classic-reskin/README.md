# LUDO · 原版贴图与动画版

Canvas 2D 手机/桌面竖屏游戏；经典四枚全归家、快速首枚归家，2/3/4席人机或同屏。保留已确认原版纹理与纯规则核心，不含登录、广告和外网运行依赖。

## 运行与验证

需要 Node.js 22+、npm；浏览器检查使用 Chromium。

```sh
npm ci
npm run build
npm test
npm run check
```

`check` 自动启动/关闭最终 dist 静态服务器。可用 `CHROMIUM_PATH` 指定已安装的 Chromium；否则按系统路径及 Playwright 路径查找。Playwright 固定 1.63.0，Prettier 固定 3.6.2。格式化使用 `node scripts/format.mjs`，仅格式化表现层与新增工程/测试文件，跳过五个复用核心和全部已确认美术文件。

试玩入口 `dist/index.html`，需由静态服务器访问。可独立挂载于 `ludo-classic-reskin/`，所有资源为包内相对路径、无CDN。正式源码/试玩ZIP位于 `releases/`；旧版包保存在 `releases/initial-code/`。浏览器证据写入 `evidence/`。

## 操作

点击当前玩家骰子，随后点棋子或底部编号；键盘 Tab、Enter/Space 可操作语义按钮。动画默认开启，设置可选择减少动态/静音。暂停、切后台、重开会取消演出；刷新恢复已提交局面，不重复掷骰/落子。图片未加载齐时开始与继续禁用，失败可刷新重试。

## 结构与范围

- `src/rules/rng/ai/storage/lifecycle.js`：授权复用纯核心，来源见 `design/reuse-baseline.json`。
- `src/assets/map/timeline/render/main.js`：纹理装配、15×15映射、时间轴、Canvas渲染及输入协调。
- `scripts/`：构建、CRC ZIP、资源白名单、浏览器自然轨迹与生命周期验收。
- `tests/`：规则完整对局及同seed逐条重放。

源码包只带重建所需资源、清单、设计和依赖声明；不包含凭据、node_modules、商业参考引擎、美术生产脚本或一次性迁移器。参考资源商业授权由提供方核实；浏览器模拟视口不代替Android/iOS真机测试。本交付属于代码阶段，未部署发布。
