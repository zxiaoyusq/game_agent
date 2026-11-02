# 彩球融境 · 本轮测试验收报告

日期：2026-10-18；测试阶段，attempt=1，resume=false。本轮独立重跑现有自动化通过，等待编排/用户验收，不自行确认阶段。

## 依据与归属

实际读取cocos-game-production/SKILL.md（1.4.2）、game-reverse-engineering/modules/cocos-qa/SKILL.md及配套ball-sort-fusion.md、web-qa.md；技能保持1.4.2，无新增通用修复经验。历史Windows、Blockudoku、Creator2.4和原生路径只借鉴验收结构。

参考通过read_reference读取ref/BallSort工程拆解_2026-10-01/交付说明.txt、ref/BallSort竞品拆解_2026-10-01/彩球分类头部产品拆解与融合设计报告.md前段及目录。实际读取/workflow/prototype.md、art.md、art-manifest.json、code.md和旧test.md；/evidence/engine-build.json、source-manifest.json（完整分段）、level-validation.json、final-independent-boundary-summary.json；package、build-web脚本、规则测试及浏览器测试必要段。

复用其它工程制作Agent已有游戏、关卡、素材与引擎产物，本轮执行验证并更新本报告。未修改src、tests、scripts、package、原始素材、已确认报告或manifest；未从零生成游戏或重新编译引擎。设计决策沿用已确认原型：连续同色批量移动、满管同色完成、可选高管/迷雾、事务撤销及可靠恢复；测试阶段不改实现以保留上游确认。

## 本轮真实命令与指纹

本次通过run_validation串行执行，三条均退出0，未借用旧运行成功。

| 命令 | 退出码 | 实际结果 |
| --- | ---: | --- |
| npm run build | 0 | 当前public/src及已有引擎产物打包至/dist |
| npm test | 0 | 9项规则/存档测试通过，失败、跳过、取消均0，132关解法完整回放 |
| npm run check | 0 | 再跑9项单测及26条真实Playwright Chromium检查，通过 |

三次命令source_before/source_after共六值一致：`cd2345379dbd13b880db0eaa8d5ea78492659b9f1af3bba216fc5a54be0a5f45`。这是工具源码工作区指纹，非Git提交。build/test的changed_paths为空，check仅列evidence/code-memory-regression.json；其它证据由脚本本轮实际写出，内容相同不代表未执行。验证后仅更新报告。

运行时为Chromium153.0.8010.12、cc.VERSION3.8.8、Director场景“彩球工坊”、活动Cocos画布、WEBGL2、drawCalls42。现有脚本采用Linux Node随机端口临时只读服务、无头Chromium及ANGLE/SwiftShader，finally关闭服务与浏览器。未使用历史固定端口夹具。

引擎身份引用上游engine-build.json：提交411f98df047c25902f93440d4b22925c2fb65461，归档SHA256为8af14ad3f861b9edd1d90c928a676ccaec4d9ec6d0bce42f56c59c9b3a82afa5，运行时SHA256为c5dbfbd9008357af024539cb96071774d8d9809a5a1d3850b88389f7ac8fa1a0，上游记录6340文件匹配。本轮核对记录与实际运行版本，未重新下载、逐文件验源或编译引擎。

## 内容、资源及检查范围

关卡边界为经典100、高管12（容量6/8各6）、迷雾20，共132。本轮单测实际读取levels.json，逐步验证全部交付解法合法、最终满管同色、颜色守恒及总数132。levels.json实际枚举SHA256为905b102f516bc9c73612988dec8a68bd7b86de3f566b771f5510a77b6a3e9adb。Guru/HM采用已确认方向转换与批量规则；Infinite Joy解法来自本工程求解，非原包自带。

本轮inspect_assets核对28份原始素材与art-manifest/source-manifest逐项哈希相符：Guru12张、Infinite Joy12张、HM1张PNG及3份WAV。关卡、配置与截图不计入28项。未生成AI图片或加工素材，来源可追溯不代表商业授权。HM管图实际用途及非等比适配沿用art报告，保留source-manifest旧描述差异。

9项单测覆盖：132关解法；批量容量与非法移动；完成判定及偏离路径求解；未知版本隔离；合法相邻事务链；500条截断链；截断边界经撤销/保存恢复/继续操作及非法输入拒绝；损坏JSON恢复；缺球、超容量、坏历史及辅助状态拒绝。

26项浏览器完整清单见/evidence/browser-validation.json，本轮已完整回读。覆盖真实引擎运行、覆盖确认、迷雾遮蔽、坏档恢复、节点回收、动画中刷新、移动/撤销/加管、Worker当前局面提示、持久化、三模式代表关通关、幂等奖励、主题/符号、移动端布局与44CSS像素目标、截断历史、设置边缘点击、写失败持续反馈、完成局主题与过期结算、宽屏截图。主页面errors=[]、failedRequests=[]，即已监听的pageerror/console error/requestfailed均为0；隔离边界context的pageerror亦为0。隔离context没有单独监听requestfailed，不能扩大零失败请求的统计范围。宽屏“无变形”是脚本标签，实际仅采样并截图，不替代模型视觉验收。

## 重点缺陷回归与本轮证据

- 遮蔽、覆盖确认、未知版本、相邻合法历史：均本轮check重跑；迷雾同色未满管底球无Sprite且仅问号，覆盖取消保留棋盘，未知会话/篡改历史拒绝恢复。异常存档注入仅用于恢复测试。
- 节点回收：/evidence/code-memory-regression.json，0/200/400次真实点击的堆为9730080/11004092/10929304字节，Node65/70/70、试管4/4/4、无parent节点3/8/8。稳定段未线性增长，不能据此声称全局无泄漏。
- 设置重叠：/evidence/code-target-regression.json，两视口同层目标无重叠，3个开关各4边真实点击仅改目标字段；360×640声音/数字中心y380/428、高44、间隔4，原点(180,401)有效；390×844对应y487/539、间隔8。
- 截断撤销持久化：/evidence/code-history-regression.json，三次撤销刷新后步数/历史数500/499、499/498、498/497，boundary.moves=1、extra=true；themePreserved=true，继续移动后moves499/history498，再撤销刷新恢复。500条合法历史是恢复夹具，后续动作真实指针执行。
- 存储失败持续反馈：/evidence/code-boundary-regression.json，正常启动后隔离模拟setItem失败，移动、撤销、加管、设置、主题重绘五类操作均保持未保存警告和旧存储原文；实际写入成功才清除，刷新恢复额外管与设置。
- 完成局主题与旧结算：同一boundary证据及测试断言，以真实解法/指针完成前三关，默认主题重绘等待900ms仍保留设置；完成局刷新正常结算且奖励幂等，解锁主题及快速导航无旧结算覆盖。最终classic.index=3、completed=3、theme=1、won=false、overlay=false；realPointer/realSolutionCompletion=true，errors=[]。

本轮产物：重新打包/dist/，更新/workflow/test.md；浏览器脚本重新输出上述五份JSON及/evidence/classic-desktop.png、classic-win.png、challenge.png、challenge-eight.png、mystery.png、hint.png、settings-light.png、mobile.png、mobile-eight.png、wide-desktop.png和code-*回归截图。已回读浏览器、内存、边界及目标/历史必要段。截图由测试实际生成，本模型未作视觉审美验收，待编排Agent另行打开检查。

## 其它Agent补充与限制

/evidence/final-independent-boundary-summary.json明确归属编排与独立审查Agent，不算本模型本轮执行。其记录补充：动画期间10入口锁定；真实前6经典及2/3/5/6主题阈值与重复奖励；三模式末关通关回首关；真实Worker延迟结果在移动/撤销/加管/重开/切模式后丢弃，共6例；运行期写失败4例；132个ID及结构颜色、前20经典等价性审查，迷雾复用经典棋盘改变可见性。这里只引用汇总，未打开其中工程外docs原报告；main_sha256为2e0e0df11a131d124c624d56d210765afacbb4bd3de20e52cb025186d78ccc8f，该单文件指纹与本轮工作区指纹口径不同。

两个后台冻结恢复用例因无头Chromium无法证明真正冻结，明确未覆盖，不标通过。未验证Creator原生包、Android/iOS打包、实体手机、Safari/Firefox、硬件GPU差异、多租户企业部署、长期压力或完整GPU/原生内存；模拟视口和鼠标不代表实体触屏所有手势。未亲自看图、试听或完成人类迷雾体验、教学效果、审美/透明边缘/跨主题颜色语义验收；资源商业许可仍未证明。

本轮既有自动化通过，未发现需退回代码阶段的阻塞；独立性指重新执行和核对现有测试，不代表另写一套独立测试或所有需求全面通过。保留上游确认，提交编排/用户验收，不伪造阶段确认。
