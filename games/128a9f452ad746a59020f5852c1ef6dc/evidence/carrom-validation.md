# E-03：本次真实执行记录

阶段：prototype，只读几何审查。命令均为`node scripts/carrom-geometry-audit.mjs`，没有执行参考游戏。

1. 第一次：exit_code=1。`BL精确直击候选-miss`断言失败：旧检测实际返回true，而样本预期false。原因：L=130.56正好约为三个43.52步长，最后采样触及目标39.168阈值，不能拿该样本证明漏检。仅调整辅助样本，未改原游戏。
2. 第二次：exit_code=0，17项合成断言通过；辅助脚本尝试读取两份ref工作区副本均ENOENT，未能取得完整哈希或全文调用清单。
3. 最终：辅助脚本取消直接参考读取、增加固定BL袋口的普通子漏检样本及出袋段断言后重新执行。exit_code=0：`合成几何断言通过：18项；未执行原游戏；输出 evidence/carrom-geometry-results.json`。

最终执行source_before/source_after均为：
`ac31c20a27ec5d26081527b5fb72e8bfcd7e5a786218a8bf37dbb2ce00182dc0`。
这是run_validation的工作区源码指纹，不是参考JS或单个辅助脚本的文件哈希。仅evidence/carrom-geometry-results.json更新。

最终结果是合成模型的18个样本断言PASS；不包含原候选函数执行、PIXI/planck运行、入袋命中率、真实浏览器、真机或设备性能验证。

本轮没有package.json、可构建游戏工程或dist交付；npm run build、npm test、npm run check未运行，不适用于本轮只读prototype审查，不能记作通过。没有创建虚假构建脚本，也没有迁移引擎、制作美术或产出试玩ZIP。
