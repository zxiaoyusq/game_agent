# Scenario Schema

> **何时读我**：哥哥要写或改一次设备测试的 `scenario.json`，或问"基线截图怎么建才算数、阈值能不能放宽、多设备怎么指定"时。
> **读完能做到**：按字段约束写出可执行合同式的 `scenario.json`（device/apk/package/actions/expected_text/baseline_dir/阈值），并按五步基线建立流程产出只来自已知良好构建、经人工审阅的 `baselines/`，知道不得从失败或未审阅的运行自动生成基线。
> **范围**：`GENERAL_DEFAULT`

`scenario.json` 是一次设备测试的可执行合同：

```json
{
  "device": "optional ADB serial",
  "apk": "optional absolute APK path",
  "package": "com.example.app",
  "launch_activity": "com.example.app/.MainActivity",
  "actions": [
    {"type": "wait", "seconds": 2},
    {"type": "tap", "x": 1217, "y": 868},
    {"type": "swipe", "x1": 300, "y1": 700, "x2": 900, "y2": 700, "duration_ms": 300},
    {"type": "text", "value": "test"},
    {"type": "keyevent", "value": "KEYCODE_BACK"}
  ],
  "expected_text": ["开始游戏"],
  "baseline_dir": "baselines",
  "max_mean_abs_error": 18.0,
  "max_mismatch_ratio": 0.12
}
```

## 字段约束

- `device`：多设备时指定 ADB serial；省略时只能在“首个已授权设备”规则明确的管线中使用。
- `apk`：可选；设置后由执行器在启动前执行覆盖安装。
- `package` 与 `launch_activity`：由执行器启动应用时同时设置；测试已运行应用时可以留空 Activity。
- `actions`：所有坐标使用实际截图像素。每次动作后都应保存截图与 UI XML。
- `expected_text`：选择短且稳定的标签，避免时间戳、倒计时等动态文本。
- `baseline_dir`：基线命名与动作顺序一致，例如 `step-001-wait.png`、`step-002-tap.png`。
- 阈值：优先固定动画、裁切或遮罩动态区域；不能只为消除失败而放宽阈值。

## 基线建立

1. 在目标设备与分辨率上运行已知良好构建。
2. 完整执行同一场景并捕获每一步。
3. 人工审阅每张截图并记录构建/版本。
4. 只把已批准截图复制到 `baselines/`。
5. 再次运行同一场景，保留原基线不变以供后续比较。

不得从失败或未经审阅的运行自动生成基线。状态栏、时钟等动态区域应由稳定环境或显式遮罩处理。
