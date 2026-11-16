Crazy Knifes AHA SDK 接入包
日期：2026-11-05（Asia/Shanghai）

配置：Crazy Knifes / appKey 5027208。
当前：Crazy Knifes 1.8.5-release，PlayCanvas，42 个模板。
保留前 20 关简化配置，修复第 3 关首次解锁新刀的位置交接。
GA、Banner client/slot/channel 沿用用户提供的 Crazy Knifes.zip。

发布目录结构：
  index.html               外层入口，加载本地 aha-host.js
  aha-host.js              SDK 初始化及广告回调桥接
  game/index.html          实际游戏入口
  game/aha-game-adapter.js  游戏暂停恢复及广告适配
  game/...                 完整游戏资源

使用：把目录整体部署在同一 HTTP(S) 站点，从外层 index.html 进入。
本地可用 Python http.server 指向本目录；请勿双击 HTML 或单独打开 game/index.html 验收广告。
Banner 在底部预留 50px。

已接入的实际玩法：
1. 关卡结算插屏：广告完成或失败后均恢复游戏。
2. 商店广告金币：SDK 返回 viewed 才发放原游戏配置的金币。
3. 通关三倍结算：SDK 返回 viewed 才执行原三倍结算。
4. 广告复活：SDK 返回 viewed 才执行原复活。
SDK 返回取消、无填充、未就绪、SDK 不可用和超时等非成功结果时不发奖励。
广告期间暂停游戏、锁输入并静音，结束恢复此前的暂停及声音设置。
启动和首关加载不等待远程广告服务；加载完成在首关资源与渲染准备后只上报一次。
只有 SDK 在首关就绪时已准备好才尝试启动广告，避免迟到的启动广告打断游玩。

测试广告：正式包默认关闭。与运营确认测试环境后，可在 aha-host.js 的 SDK 配置中，
取消注释 'data-adbreak-test': 'on'。正式交付前再次关闭。
本包没有内置模拟成功、免费发奖或调试切关入口。

验证边界：离线回调测试及浏览器 mock 测试使用测试脚本拦截远程 SDK，
这证明本地接线与回调行为，不代表真实广告展示、收入归属或后台埋点入库已验收。
正式环境仍需运营验收实际广告、GA/平台事件和域名配置。
供应商 SDK 1.8.0.0 的部分无广告兜底弹层也会返回 viewed；本包遵循运营模板的
成功状态契约。viewed 不等同于已独立证明完整观看真实视频，兜底发奖规则需运营与供应商确认。
本次不改变原 Android 包和历史 H5 包，未推送 GitLab 或打发布 tag。
原 1.8.2 基底中的既有已知问题不因本次 SDK 接入而视为全面发布通过。

重建：在 E:\Wilson\Slices Master 下运行：
  node tools/aha-sdk/build-aha.mjs build/Crazy_Knifes_release build/Crazy_Knifes_aha
构建器为保护历史结果，要求输出目录尚不存在；重复构建请使用新的输出目录名。
离线测试：node tools/aha-sdk/test-aha-integration.mjs
提交方式：按运营提供的具体 AHA GitLab 仓库、权限、分支与 tag 规则执行。
