---
name: vision-device-testing
description: Use when 要对 Android 游戏或应用执行可重复的真机视觉测试：使用 ADB、逐步截图、OCR、图像基线、UI dump、设备信息与 Logcat 证据，并给出 PASS、FAIL、BLOCKED 或 NEEDS_CONTEXT 验收结论。普通构建、浏览器 QA 或仅生成效果图不走本模块。
---

# Android 真机视觉验收

## 执行卡（先用这张卡，再读正文）

**我管什么**：Android 游戏/应用的可重复真机视觉验收——ADB、逐步截图、OCR、图像基线、UI dump、设备信息与 Logcat 取证，最后给出 PASS/FAIL/BLOCKED/NEEDS_CONTEXT 结论；普通构建、浏览器 QA、只出效果图不走本模块。

**第一步做什么**：先定位可用管线（用户给出路径 → 环境变量 `VISION_DEVICE_PIPELINE` → 工作区 `vision-device-pipeline` → 已知安装路径），确认它有 `bin/dispatch-task.zsh`、`bin/run-device-test.zsh`、`bin/accept-task.zsh`，且 `adb devices` 里有已授权设备；缺任一直接判 `BLOCKED`。

**做完怎么算完成**：
- [ ] 独立任务目录已建，`TASK.md` 与 `scenario.json` 按 `modules/vision-device-testing/references/scenario-schema.md` 填齐
- [ ] 每步截图 + OCR + UI XML + 设备元数据 + 结果 JSON + Logcat 全部落盘到 attempt 目录
- [ ] 坐标取自设备实际截图分辨率，未假定方向或像素密度
- [ ] 采集全程遵守 `modules/vision-device-testing/references/collection-boundaries.md` 负面清单
- [ ] 结论只用 PASS/FAIL/BLOCKED/NEEDS_CONTEXT 之一，并附任务目录、结果文件、实际 attempt 目录与具体证据
- [ ] 任务自带的独立 `VERIFY.sh` 已跑过

**红线（不可违反）**
- 模拟器只能做阶段回归，真实结论必须在真机；没有已连接且已授权的 ADB 设备时不得通过，也不得把启动截图测试描述成完整流程通过。
- 管线缺失、缺脚本或设备未授权 → 结论必须是 `BLOCKED`，不得模拟执行或声称通过。
- 状态词只有 `PASS`/`FAIL`/`BLOCKED`/`NEEDS_CONTEXT` 四个，不许自造"基本通过""疑似通过"。
- 采集负面清单：凭据、Cookie、授权头、原始网络体与用户隐私不采集、不留存、不入报告；意外落入证据集要立即剔除并记录。
- 视觉基线缺失即不得通过；基线只能从人工确认的已知良好构建建立，测试过程中不得静默覆盖。
- Logcat 出现 `FATAL EXCEPTION`、`ANR in`、`Fatal signal`、`SIGSEGV`、`Abort message:` 即 FAIL；视觉模型不得覆盖确定性失败。

**卡住时按顺序读**：
- 字段或场景写不对 → `modules/vision-device-testing/references/scenario-schema.md`
- 不清楚该采什么、或采到了敏感数据 → `modules/vision-device-testing/references/collection-boundaries.md`
- 结论定不下来 → 正文「验收规则」与「状态」两节

全局五步循环与六条铁律见 `references/execution-protocol.md`。

用于需要 Codex 定义测试流程、收集证据并作最终验收判断的 Android 游戏真机测试。普通构建、浏览器 QA 或仅生成效果图不走本模块。

## 运行管线发现

本模块描述验收合同，不自带设备执行脚本。执行前按顺序查找可用管线：

1. 用户明确提供的管线路径；
2. 环境变量 `VISION_DEVICE_PIPELINE` 指向的目录；
3. 当前项目或 Codex 工作区中的 `vision-device-pipeline`；
4. 已知安装路径 `/Users/imac/Documents/Codex/vision-device-pipeline`。

可用管线应提供 `bin/dispatch-task.zsh`、`bin/run-device-test.zsh`、`bin/accept-task.zsh`，以及任务内的 `VERIFY.sh`。找不到管线、缺少脚本，或没有已授权 ADB 设备时，结论必须是 `BLOCKED`，不得模拟执行或声称通过。

## 工作流

1. 检查目标工程、APK、包名/Activity、设备授权状态与已有证据。
2. 创建独立任务目录，填写 `TASK.md` 与 `scenario.json`；字段规范见 [scenario-schema.md](references/scenario-schema.md)。
3. 在实际截图分辨率下记录操作坐标，运行测试并收集每一步截图、OCR、UI XML、设备元数据、结果 JSON 与 Logcat。
4. 审阅证据后写入验收结论，并运行任务自己的独立 `VERIFY.sh`。
5. 报告测试种类（launch/smoke/regression/end-to-end）、覆盖范围、包名/Activity、设备型号、方向/分辨率、版本、崩溃或 ANR 信号，以及证据路径。

## 验收规则

- 无已连接且已授权的 ADB 设备时不得通过。
- 需要视觉基线却缺失时不得通过；基线只能从人工确认的已知良好构建建立，测试过程中不得静默覆盖。
- 平均绝对误差或像素不匹配比例超过配置阈值即失败。
- 缺少任一必需 OCR 文本即失败。
- Logcat 出现 `FATAL EXCEPTION`、`ANR in`、`Fatal signal`、`SIGSEGV` 或 `Abort message:` 即失败。
- Unity/Cocos 画布的 UI XML 可能为空；此时依赖截图和坐标元数据，并在报告中注明限制。
- 坐标必须来自设备实际截图分辨率，不能假定方向或像素密度。
- 不把密码或长期凭据写入场景、截图、提示或图像库；需要登录时仅使用用户提供的安全运行时输入。
- 采集遵守[采集负面清单](references/collection-boundaries.md)：凭据、Cookie、授权头、原始网络体与用户隐私数据不采集、不留存、不入报告；意外落入证据集时立即剔除并记录剔除动作。
- 不得把启动截图测试描述为完整流程通过。
- 视觉模型只用于语义识别或解释不确定状态，不能覆盖确定性失败，也不能在缺少证据时作通过判断。

## 状态

- `PASS`：所有请求的检查与证据均通过。
- `FAIL`：测试已执行，但至少一项检查失败。
- `BLOCKED`：缺少有效执行条件，例如设备未授权、管线缺失或必需基线缺失。
- `NEEDS_CONTEXT`：已收集证据不足以判断，例如账号或预期状态不明确。

输出必须包含任务目录、结果文件、实际 attempt 目录，以及具体通过或失败证据。
