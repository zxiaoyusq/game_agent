# Seed 拷贝代码生成与验收

> `GENERAL_DEFAULT`：说明生成器契约，真实运行仍需 Android 设备验收。

## 入口与目标布局

从总集根目录运行：

```powershell
python modules/sdk-replacement/scripts/generate_seed_copier.py --package com.example.game --asset-dir assets/remote_seed --target-subdir seed --out SeedCopier.java --emit-usage seed-usage.md
```

默认整个 remote_seed → filesDir/seed，保留本地旧版参数/布局。原加载器若使用 filesDir/patch、filesDir/gamecaches，显式选 roots 和根布局：

```powershell
python modules/sdk-replacement/scripts/generate_seed_copier.py --package com.example.game --roots patch,gamecaches --target-subdir . --out SeedCopier.java
```

`--asset-dir` 剥掉 assets/ 前缀，拒绝绝对路径和 ..；保留 --class-name、--java-package、--log-tag、--marker、--emit-usage、不写文件的 --check。

Java 有静态 copyIfNeeded(context) 与实例 copySync()/copyAsync()。接入在 super.onCreate 之后；消费前确认完成，异步不能让引擎抢读半成品。文件经临时文件提交，全部成功才写完成标记；失败记录日志且不写标记。长度一致只作重试优化，最终仍验证清单/哈希。

## Smali 边界

--language smali 只输出显式 INCOMPLETE/TODO 接入骨架，未实现复制。真实 apktool 路线编译 Java 成 DEX，再对实际调用者接入。骨架存在不能关闭离线化义务。

## 工具级验证

`python -B modules/sdk-replacement/scripts/tests/test_seed_copier.py` 使用最小 Android API 桩编译/运行 Java，验证嵌套文件、字节、空文件、幂等/失败标记、roots/布局与参数。它不证明真机 AssetManager、壳/引擎启动或网络隔离通过；设备继续按 `modules/sdk-replacement/SKILL.md` 门禁验收。
