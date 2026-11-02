# Cocos Web 技术配置

状态：当前可执行配置，已有排序案例验证。适用于需要 Cocos 场景、节点、组件、精灵、输入或音频能力的 Web 项目；每个新品类仍需完成自己的规则和体验验收。

## 已验证的本地依据

`games/ball-sort-fusion` 使用官方 Cocos Engine 3.8.8、真实 Scene/Camera/Canvas/Graphics/Sprite/Label/Input/AudioSource 和 WebGL2。引擎获取与构建脚本为 `scripts/setup-engine.sh`、`scripts/build-engine.cjs`，依据在工程 `evidence/engine-build.json` 及根项目 `docs/agent-production/acceptance.json`。

3.8.8 是该案例固定的已验版本，不是永久“最新版本”。用户要求最新时重新核实官方正式 release 并固定版本/提交/归档哈希，再验证工具链；不从开发分支版本字段推断正式发布。

## 实现与交付

遵循 `framework/web-common.md` 的三条命令、`dist/index.html` 和四阶段报告/资源清单契约。按需求选择节点和资源组织，不要求复制 Ball Sort 工程，也不要求同样的关卡、撤销、Worker 或模块拆分。

- 用真实引擎能力实现；手写一个名叫 `cc` 的替代对象、只导入类型或展示版本文字都不是引擎身份凭证。
- 保存实际源码来源、版本和构建后运行时哈希，在运行页面核对引擎版本、活动场景及实际渲染；身份记录与当前产物一致。
- 将纯玩法规则与节点表现分开；主题或布局重绘不重复结算。移除子节点不自动等于销毁对象，按实际 API 清理节点、事件与异步回调。
- 用重复真实操作检查节点或内存是否持续增长；调试工具持有的对象应释放，避免误判。
- 以实际画布到 CSS 像素比例校验输入和触控范围，不只看设计分辨率。

## 能力边界

当前案例是独立官方引擎 Web/H5 工程，不含 Creator GUI 工程或 `.scene` 编辑器资产，也没有原生包验收。需要 Creator 编辑器、Android/iOS、小游戏平台或新的物理组件时，先补相应构建/运行适配与目标平台证据，不能从 Web 测试通过推导其他平台通过。

`cocos-game-production` Skill 提供 Cocos 专项方法；品类规则从当前项目选择的品类知识读取，Ball Sort 案例只按需参考。
