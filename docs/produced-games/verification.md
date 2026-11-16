# 产出游戏验收

首页原「产出沉淀」改为带真实数量的「产出游戏」按钮。游戏库按实际存在的 Web 构建列出作品，支持搜索、选择、内嵌运行、重新运行、结束试玩、新窗口打开和返回首页。封面使用对应工程已有验收截图。

首批目录中有三个可运行版本：

- 彩球融境 · Ball Sort Fusion：`games/ball-sort-fusion/dist`。
- 琥珀商路 · Amber Caravan：`frontend/public/games/amber-caravan`。
- 琥珀商路 · API 全流程验证：`frontend/public/games/amber-caravan-api`。

随后从用户上传的 `归档.zip` 添加箭头解谜、疯狂飞刀、经典接龙，并保留缺少游戏本体的 Checkers Pocket 条目。目前合计 7 项、6 款可运行，详见 [上传包导入记录](archive-import.md)。

游戏运行资源由后端提供，开发模式经 Vite 的既有 `/api` 代理访问；生产部署仍需保留 `/api` 反向代理。目录不要求工作流四阶段全部确认，只要求已存在 Web 运行入口；有入口不代表该游戏已经完成正式验收。

## 验证命令

```bash
cd backend
conda run --no-capture-output -n base python -m unittest tests.test_produced_games -v
cd ../frontend
npm run build
```

浏览器检查使用可用的 Playwright，服务默认位于 `http://127.0.0.1:24681`，可用 `APP_URL` 覆盖。若 Playwright 不在前端依赖中，用 `PLAYWRIGHT_MODULE` 指向已安装的 `playwright/index.mjs`：

```bash
PLAYWRIGHT_MODULE=/tmp/bubble-ui-check/node_modules/playwright/index.mjs node frontend/scripts/check-produced-games.mjs
```

此命令在仓库根目录执行。输出 [浏览器结果](browser-results.json) 及桌面、手机截图。成功用例读取真实目录和运行包，通过正常按钮和指针操作游戏，不注入胜利或局面；列表失败和空状态单独使用网络替身。

后端测试覆盖：工作区与分发目录去重、新增产物发现、无构建项目排除、工作流元数据与损坏记录、已分发版本优先、相对资源 MIME、入口 HEAD 请求、封面白名单、私有文件及路径/符号链接越界拒绝。

浏览器检查覆盖：首页数量和入口、完整列表、搜索和无匹配状态、三款游戏真实开局/操作、旧 iframe 销毁、新窗口打开、390px 布局与游玩、目录失败恢复、空列表与返回首页。游戏规则本身未修改，本次没有重复执行所有游戏的完整通关测试。
