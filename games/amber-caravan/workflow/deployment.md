# 独立路径部署

部署日期：2026-11-03（Asia/Shanghai）。

试玩地址：<https://pagent.ahagamecenter.com/games/amber-caravan/index.html>

`dist` 的10个静态文件发布到本工程 `frontend/public/games/amber-caravan/`。当前工作台Vite在24681提供静态文件，现有域名入口继续使用原回源。前端以后执行生产构建时，public目录也会自动带入。

使用完整的 `index.html` 链接；当前Vite的目录路径可能回退到工作台首页。没有修改域名、TLS、其他应用的80/81端口，也未重启后端/MCP。

## 后续更新

在游戏工程目录先构建并完成浏览器验收，再执行：

```sh
npm run build
npm run check
node scripts/deploy.mjs ../../frontend/public/games/amber-caravan
```

发布脚本验证源码/构建与浏览器报告及美术清单的SHA256一致，然后准备完整临时目录并改名发布。若已有线上版本，会先保留到 `releases/deployment-backups/<时间戳>/`；失败自动恢复。备份不位于公开静态目录。

## 访问验证

- 10个文件经24681实际服务读取，HTTP200、Content-Type正确、字节与已验收dist完全一致，包含MJS和WebP。
- 公网可达性：用户已明确确认该HTTPS链接能打开游戏。本服务器直连公网域名超时、经其代理也不能完成TLS，因此没有把本机测试冒充公网自动化测试。
- 桌面1440×1000和手机390×844触摸模拟经实际部署入口完成开局、掷骰、落子与刷新续局；实际结果记录在 `evidence/deployment-results.json`，不是实体手机自动化测试。
- 工作台首页仍为原应用、`/api/health` 返回200、未带令牌的MCP初始化仍返回401。
