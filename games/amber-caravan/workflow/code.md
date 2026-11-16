# 实现与交付

运行入口：`dist/index.html`。使用相对资源路径，可放入任意静态HTTP服务子目录；无需工程后端、模型服务、MCP、账户或CDN。

```sh
npm ci
npm run build
npm test
npm run check
npm run serve
npm run release
```

- `rules.mjs`：不包含DOM/计时器/随机入口，返回新状态；输入与规则读档校验。
- `ai.mjs`：对合法动作评分，无法修改骰子。
- `board.mjs`：纯显示坐标、矢量材质与逐格动画；不会提交规则结果。
- `app.mjs`：页面/弹窗/输入、系统公平骰子、唯一AI计时器与代际取消。
- `storage.mjs`：局面版本和规则验证、浏览器存储读写降级。
- `audio.mjs`：仅在用户交互解锁后播放音效。
- `scripts/build.mjs`：静态文件构建与10MB检查。
- `scripts/serve.mjs`：开发预览和测试共用的隔离静态服务。
- `scripts/package.py`：完整工程和纯网页两种ZIP，按压缩前后双重10MB门禁出包。

运行时无第三方库；唯一开发依赖是锁定版本的 Playwright。源码保持可读、不混淆。重新构建不需要原始两个ZIP或图片生成工具。

浏览器测试只能读取 `window.amberCaravan.snapshot()`，没有改局、跳关或强制胜利接口。完整局测试可为系统随机源提供固定种子以便复现，所有对局动作仍经实际页面点击、正式规则和AI。详细实际覆盖与运行证据见 `test.md`。

不提供联网匹配、广告、商城、服务器云存档。这些不是本次融合目标，界面没有假入口。浏览器存档是本设备本域名的进度，不会跨机器同步。
