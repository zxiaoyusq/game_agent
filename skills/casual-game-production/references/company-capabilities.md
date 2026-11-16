# 公司能力适用范围

本索引连接通用四阶段流程与公司资料，规则与正文以知识库当前版本为准。先通过 `read_skill` 读取相关入口，再用 `read_skill_resource` 按需读取其支持文档；路径相对知识库 `skill/docs/`。跨品类复用的是生产流程、证据记录与交付协议，各品类仍按自己的规则和技术需求验收。

| 任务 | 按需读取的入口 | 使用边界 |
| --- | --- | --- |
| 休闲游戏视觉方向、色彩与界面 | `azure-image2-generation/modules/casual-game-art-style/SKILL.md` | 将形式语言与区域配色、题材分开；以当前项目目标、功能色和用户选择为准，不把历史 V6/V8 当统一标准 |
| 批量美术生产与回填 | `ai-art-automation/SKILL.md`、`azure-image2-generation/SKILL.md` | 轻量索引、代表样、批量生产、累计回填、真实运行验收；按实际可用生图工具选择后端 |
| H5、Canvas 或既有 Phaser 游戏换皮 | `game-reverse-engineering/modules/h5-canvas-reskin/SKILL.md` | 从原型阶段承接方向选择，按阶段读取 intake-and-direction、end-to-end-orchestration 或 pipeline；保留用户选定候选，不顺带修改玩法或布局 |
| Cocos Creator 工程规范与恢复 | `game-reverse-engineering/modules/cocos-project-standards/SKILL.md` | 先确认 Creator 版本和框架身份；CFW 规则只适用于已确认的对应框架，DADA 是案例，独立 Web 不强制企业工程结构 |
| 托管小游戏采集、已有 H5 原版还原与迭代 | `game-reverse-engineering/modules/hosted-minigame-harvest/SKILL.md` | 有输入先核验基线，不重复采集；按需读取 hosted-game-lifecycle、hosted-h5-restoration，目录信息不能冒充可运行成品 |
| H5 包体、加载、低内存优化 | 同上入口的 `references/h5-package-runtime-optimization.md` | 明确成本口径、动态引用、触屏和异步就绪；真实目标平台的数据才能证明优化收益 |

## 游戏参考资料

知识库“公司游戏参考”直接索引 `ref/公司skill整合/AHAgames/`，独立于 Skill 包。新建项目可将指定游戏的 `gameInfo.json` 路径加入参考，再通过 `read_reference` 读取；按问题补充同目录清单，不默认把全部游戏目录送入上下文。

同一页面的“案例研究”索引 `ref/公司skill整合/OneConnectRe/` 等附带资料，可查看和选取单篇研究文档。One Connect 的 Construct 2、关卡、配置、尺寸和性能数字属于该案例；通用流程以对应 Skill 为准。选取文档不等于导入完整游戏、执行来源脚本或复现历史验收。

以当前磁盘检测的包体和商店图片为准：历史 README、CSV 成功字段、旧 Windows `localFile` 路径不能证明本地原包存在；多份清单不一致时记录差异，不用较旧清单截断当前目录。没有原包仍可研究元数据与商店图，但不能据此宣称已检查代码、资源引用、运行效果或完整游戏规则。

## 工程和工具边界

- 现有可执行配置为 Cocos Web、Canvas 2D Web、原生 DOM/SVG/Canvas Web；资料中的 Creator、CFW、Phaser、Godot、真机或 MCP 通道须先核实实际环境与适配情况。
- Cocos 通用规范、框架专属约定与案例数值分开应用；从配置或生成器真源修正问题，不照搬来源工程中直接改派生文件的应急操作。
- 当前生图实现与工具可用性以运行环境为准；源包中的外部 Windows 路径、命令、账号和模型名不是本工程配置。
- H5 换皮的选择和评审由平台提问或自主决策记录承接；资料 HTML 的只读展示不代表工作台表单已回传。未接入的 Python、外部生图或设备工具不得通过读取文档被标记为可用。
- 视觉验收分别记录目标风格、资源契约与真实运行证据。静态示例页、历史截图、可读取的脚本不代替当前游戏的浏览器或设备结果。
