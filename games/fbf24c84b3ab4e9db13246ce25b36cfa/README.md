# 星点采集

原生 Canvas 2D 单页小游戏：点击青绿色星星五次获胜，支持重开、触摸、鼠标与本局刷新恢复。无需外部运行服务、字体或音频。

## 重建与验证

需要 Node.js 22 或更新版本：

```text
npm ci --ignore-scripts
npm run build
npm test
npm run check
```

Playwright 固定为 1.63.0。浏览器验收需要本地 Chromium，可用 `CHROMIUM_PATH` 指定；否则脚本使用常见系统路径或 Playwright 浏览器。没有浏览器时检查会如实失败。首次安装依赖需要 npm 包源；游戏运行不联网。

`dist/index.html` 是试玩入口，使用任意静态 HTTP 服务托管整个 dist 目录，可放入独立子路径。所有资源相对入口加载。`npm run check` 自行启动隔离静态服务访问最终 dist，随后自动停止；证据在 evidence。手机测试为 Chromium 触摸模拟而非真机。

`npm run release` 在验证后生成 releases 源码包与试玩包，并检查源码包重建一致性；不会修改最终 dist。最终 check 后不要重建或改动 dist。仅供后续代码阶段修复时修改源码，测试阶段不修改上游实现。
