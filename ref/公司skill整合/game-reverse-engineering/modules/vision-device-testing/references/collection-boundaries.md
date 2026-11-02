# 采集负面清单（不采集什么）

> **何时读我**：哥哥要开设备测试或抓包取证、写采集脚本、准备把证据集交付出去时；也用于事后发现 logcat 混进了 token、抓包带出了 body、截图里出现了真实账号，需要判断该不该留时。
> **读完能做到**：按凭据、Cookie/授权头、原始网络体、用户隐私、玩家真实存档、未审阅截图、无授权资产七类负面清单设计字段白名单式采集脚本，意外采到时按处置规则剔除并留剔除记录，交付时能声明"采集已按负面清单执行"。
> **范围**：`GENERAL_DEFAULT`

范围：`GENERAL_DEFAULT`。本清单约定设备测试与证据采集中**一律不采集、不留存、不入报告、不入截图库**的数据。采集证据最小化：只采集证明验收结论所需的数据。

## 负面清单

以下数据不采集；意外落入证据集的，立即剔除：

1. **凭据类**：密码、token、apiKey、session、任何长期凭据。
2. **Cookie 与授权头**：`Cookie`、`Set-Cookie`、`Authorization`、任何 Bearer 或签名字段。
3. **原始网络体**：请求/响应 body 全文、上传文件内容。抓包只留 DNS query、TLS SNI、HTTP Host、域名、IP、路径、状态码与时间戳。
4. **用户隐私数据**：真实账号、通讯录、位置、相册、剪贴板内容、广告标识与设备唯一标识。测试账号仅限用户提供的。
5. **玩家真实存档**：测试前推入基线存档，测试后立即逐字节恢复；不留脏测试存档（门禁见 `modules/godot-migration-port/references/native-restoration-gates.md`）。
6. **未审阅截图**：基线只能来自人工确认的已知良好构建；失败或未审阅的运行不得自动生成基线（约束见 `modules/vision-device-testing/references/scenario-schema.md`）。
7. **无授权资产与密钥**：不重新分发无授权的原始游戏资产、密钥或用户数据（全局规则见 `references/global-rules.md`）。

## 处置规则

- **意外采集**：logcat 混入凭据、抓包带出 body、截图中出现测试账号隐私时，立即从证据集剔除，并在记录中写明剔除动作与时间。剔除记录本身入交付，原始污染数据不入。
- **脚本白名单**：采集脚本按字段白名单设计。网络证据只落 `ts,direction,type,domain,ip,path,status` 这类元数据字段；新增采集字段前先对照本清单。
- **交付边界**：交付以脚本、映射、差异、验证报告和可复现步骤为主，不以原始采集数据为主。

## 适用范围

- `vision-device-testing`：截图、OCR、UI dump、Logcat 全部流程。
- `sdk-replacement`：Phase 1 表面盘点与 Phase 8 真机抓包。
- `gameplay-logic-reverse`：运行时捕获（heap、eval、Frida hook 输出）。
- `cocos-qa`：截图证据包与设备日志。

引用方式：任务报告声明「采集已按负面清单执行」，并在发现污染时附剔除记录。本清单不改变各模块自身的验收门禁，只是其采集前提。
