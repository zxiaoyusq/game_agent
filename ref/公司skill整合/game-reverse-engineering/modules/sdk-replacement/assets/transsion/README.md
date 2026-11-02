# 传音体系适配层示例（assets/transsion）

这些文件来自 Wall Kickers 案例（原包 sidecar 注入 + 结局 A），作为**接口化宿主替换范式**的示例：

| 文件 | 作用 |
| --- | --- |
| `HisavanaAdsFeature.java` | 把宿主的广告抽象接口（示例 19 方法：init/lifecycle/奖励/插屏/开关）实现为 Hisavana |
| `HisavanaAnalyticsFeature.java` | 把宿主埋点接口（示例 7 方法）实现为 Athena |
| `WjHisavanaFeatureFactory.java` | 宿主工厂的实现替换 |
| `WjSdkInstaller.java` | 装配入口（必须在宿主默认工厂之后执行） |
| `INTEGRATION_PLAN.md` | 命令级实施手册（编译/注入 dex/合并 Manifest/插桩/签名/验收） |
| `AndroidManifest.fragment.redacted.xml` | 从成品包回收的 Manifest 声明（**密钥已抹除**） |

使用前必须重新取证：
1. 宿主接口的方法集/语义（奖励 vs 插屏的映射按宿主原实现确认）；
2. 传音 SDK 的版本差异（类名、`TAdRequestBody` 等 API 在版本间会变，以本项目回收物为准）；
3. appId / 广告位 ID / track_type / referrerId / google-services.json **全部重新申请**；
4. 先跑离线（无广告）冒烟，再接通广告源，最后做真机三层抓包验收。
