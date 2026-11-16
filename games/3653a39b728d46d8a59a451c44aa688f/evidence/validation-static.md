# 本轮静态核查执行记录

项目3653a39b728d46d8a59a451c44aa688f；prototype；attempt=1，恢复执行。本文件记录工具真实返回，不是浏览器或游戏验收。

## 最后一次脚本修改后的验证

1. `node scripts/audit-static.mjs`：exit_code=0。
   输出：清单321项；加载表297条；实测图像15项；被覆盖声明的缺路径2条；有效加载表缺路径0条。未执行游戏。
   有效对象键295个；原JS研究副本哈希经断言核对。
   source_before/source_after：`f6dfa4f51865b52c662c5f51d7c23b15a7f79e05a295643dac785c035885be67`。
   changed_paths：workflow/resource-inventory.json（研究报告产物）。
2. `node scripts/record-archive-metadata.mjs`：exit_code=0。
   输出：本地逐文件证据覆盖321条资源；实测哈希15条；未回填306条。
   source_before/source_after同上。
   changed_paths：evidence/archive-metadata-coverage.json。

两条命令均在本次恢复后、最后一次脚本修改之后执行。此后仅补写报告和evidence，未更改脚本、研究资源或任何dist。

## 失败与处理

迁入全量哈希时，初版record-archive-metadata.mjs尝试读取 `/conversation_history/d608e15991a84190bee1545c02d77238.md`，真实Node返回ENOENT、exit_code=1，指纹78ab23fdef995b6de5ed8c9a4639a7ef9ae6eea1f3518ca7afa37e06165a169e前后相同。原因：工具会话文件可读不表示Node执行环境同一路径可读。没有越界找其他目录，没有重复相同失败操作，没有伪造元数据恢复；改为实际清单覆盖率核对，成功记录如上。**306项独立清单哈希回填仍是缺口**，不能用改后成功退出声称原目标全量完成。

FNT参考读取/提取被工具拒绝，字体页与字距未核对；代表图像读取无可见多模态画面，未目视、未测alpha边界。文件头测宽高不是视觉验收。

## 不适用/未执行

这是用户限定的隔离历史资料分析，不是代码或测试阶段，无游戏工程、package.json脚本接口或dist。未跑npm run build、npm test、npm run check，不以原创静态脚本替代它们；未运行原游戏，不访问网络，不进行截图、触控、帧率、离线刷新或真机验收。没有新发布包。
