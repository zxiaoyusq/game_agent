# Carrom 开球候选策略与 shotPowerLimits 代码证据复核

## 1. 任务背景与复核目标
根据 `Carrom_native_evidence.zip` 提供的 ARM64 ELF 静态分析与反汇编证据（目标文件：`libgame-CARROM-GooglePlay-Gold-Release-Module-1491.so`，SHA256: `4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4`），核验 ARM64 开球候选策略和 `shotPowerLimits` 的联系，严格遵循静态证据边界，明确可证事实、缺口与下一步实证。

## 2. 可证事实（Verified Facts）
所有地址均为 ELF link virtual address（静态链接地址）：
- **虚表指针与类关联**：
  - Link VA `0x18b9d00` 作为对象的初始化/构造相关函数，其写入对象的虚表指针基址为 `0x27a2288 + 0x10`。
  - 虚表重定位（RELA）指向类型名 `24MatchOpeningShotStrategy`（Mangled C++ 类型名）。
  - 虚表项 `0x27a22a8` 确定指向函数地址 `0x18b9d34`。
- **调用点与参数访问**：
  - Link VA `0x18c6b74` 处存在 `BL 0x18b9d00` 直接调用指令，验证了该开球策略对象的创建/调用链入口。
  - 在 `0x18b9ff8` 至 `0x18ba00c` 指令片段中，代码从候选全局/上下文对象的 `+0x20` 偏移处连续加载两个 `double` 浮点数，随后调用 `0x18b2e38`。
- **shotPowerLimits 静态存在与调用**：
  - 字符串 `shotPowerLimits` 在 `0x18b0a64` 被引用，位于 FDE `0x18b09d4–0x18b15a4` 内。
  - 存在静态直接调用边：`0x18b3374` 和 `0x18b339c`（位于 `0x18b31fc` 范围）通过 `BL 0x18b09d4` 调用该包含 `shotPowerLimits` 的 FDE。

## 3. 关键缺口与不确定性（Gaps & Uncertainties）
- **开球策略与 shotPowerLimits 之间缺乏直接因果边**：
  - `MatchOpeningShotStrategy`（`0x18b9d00` / `0x18b9d34` / `0x18b9ff8`）虽然在语义命名上与“开球策略”相关，但静态调用图上未发现其与 `shotPowerLimits`（`0x18b09d4`）存在直接的直接调用、跳转或确定的数据流传递。
- **结构体字段与力学含义未定**：
  - `+0x20` 处访问的两个 `double` 仅证明其数据宽度为 64-bit 浮点数，可能是最小/最大力度、坐标范围、时间窗口或角速度，不可主观断定为具体力度阈值或物理参数。
- **函数 0x18b2e38 语义未封闭**：
  - 被调用的 `0x18b2e38` 位于 `0x18b09d4`（`shotPowerLimits`）与 `0x18b31fc`（调用方）附近，虽在同个逻辑模块区间，但是否执行求解限制裁决依然未经验证。
- **无动态运行时数据**：
  - 缺少真实进程 maps 与 load bias，无运行时内存快照；不可将静态 link VA 等同于运行态逻辑，不可断言实机执行已跑通或参数数值已证实。

## 4. 下一步实证建议（Next Verifications）
1. **控制流图交叉分析**：跟踪 `0x18b2e38` 的控制流与内部引用，核验其是否引用或间接跳转到 `0x18b09d4`，查明两者是否共享全局上下文或配置缓存。
2. **动态断点取证**：在真实或模拟环境中结合计算出的 load bias 对 `0x18b9d00`、`0x18b9ff8`、`0x18b2e38` 和 `0x18b09d4` 下断点，打印 `x0`/`v0`/`v1` 寄存器值与调用栈。
3. **数据流追踪**：验证从 `+0x20` 取出的两个 double 在传入 `0x18b2e38` 后是否被用于截断（clamp）或映射（map）开球击球向量。

## 5. 复核结论
静态汇编与重定位证据证实了 `MatchOpeningShotStrategy` 虚表、构造流程、调用点（`0x18c6b74`）及 `+0x20` 处访问双精度浮点数并传入 `0x18b2e38` 的指令链；但目前**无法证明**该策略直接绑定或消费了 `shotPowerLimits`。两者同属一个求解/配置大模块，但中间仍缺失直接控制流与数据流连接证据，严禁推测为已验证玩法或直接下结论。
