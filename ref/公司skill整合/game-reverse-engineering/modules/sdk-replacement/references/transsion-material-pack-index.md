# 传音素材包索引（Transsion material pack index）

Scope: `GENERALIZED_PATTERN`。素材本体**不随 skill 分发**（体积 + 供应商版权 + 含密钥/账号标识），
本文件只登记：素材在哪、哈希多少、类数多少、怎么一键重建。

## 1. 本机回收物登记（BlockMaster 传音版来源）

以下为历史登记，摘要只展示 SHA-256 前 16 位；完整性验收必须重新计算完整 64 位摘要，不能用前缀代替。

| 文件 | 大小 | SHA-256 前 16 位 |
| --- | --- | --- |
| `dex/SHIPPING_MAP.json` | 1743 | `e3864c48281e7a73` |
| `dex/firebase_part1.dex` | 8115304 | `b57a1f4078995884` |
| `dex/firebase_part2.dex` | 8073932 | `250e935114a8b9db` |
| `dex/hisavana_athena_sdk.dex` | 5116484 | `7bd3136490cddda0` |
| `dex/hisavana_common_app.dex` | 7936020 | `a1eda7a8c9fe41f8` |
| `manifest/AndroidManifest.fragment.xml` | 20496 | `a711aef66bf10530` |
| `manifest/AndroidManifest.stage2_sdk.reference.xml` | 66902 | `b2d617ac66642da0` |

类数（dex，按包前缀统计）：

| dex | 类总数 | com/transsion | com/cloud/hisavana | com/hisavana | net/bat |
| --- | --- | --- | --- | --- | --- |
| hisavana_common_app.dex | 9518 | 16* | 1062 |  |  |
| hisavana_athena_sdk.dex | 5592 | 312 | 269** | 269 | 285 |
| firebase_part1/2.dex | 8756 / 10781 |  |  |  |  |

\* 字符串命中数；\** 该 dex 内 `com/hisavana/` 与 `com/cloud/hisavana/` 分属 ADX 与聚合壳两层。

> 完整性与覆盖核对（官方包 vs 出货包 missing=0 的逐类明细）见项目侧
> `02_sdk_pack/transsion_sdk_pack/COMPLETENESS.md`。

## 2. 素材在哪

| 用途 | 路径 |
| --- | --- |
| 可注入素材（dex/so/Manifest 片段/参考源码） | `E:\codex_apk_work\Wallkickers\sdk_swap\02_sdk_pack\transsion_sdk_pack\` |
| 接口化宿主适配层示例 + 命令级实施手册 | `E:\codex_apk_work\Wallkickers\sdk_swap\03_adapter_draft\` |
| 接入知识与契约（本 skill） | `modules/sdk-replacement/references/android-transsion-sdk-suite.md` |
| 适配层示例代码（本 skill） | `modules/sdk-replacement/assets/transsion/` |

## 3. 一键重建（从任意已接入传音 SDK 的成品 APK）

```bash
# 1) 先看候选（不落盘）
python modules/sdk-replacement/scripts/extract_transsion_sdk_pack.py --apk shipped.apk --out my_pack --dry-run

# 2) 抽 dex + so（默认 arm64-v8a、常用 so 集；min-hits 控制『核心传音类』阈值）
python modules/sdk-replacement/scripts/extract_transsion_sdk_pack.py --apk shipped.apk --out my_pack --min-hits 5

# 3) 需要 Manifest 声明时：先用 apktool 解码，再 --decoded
java -jar apktool.jar d -f shipped.apk -o decoded
python modules/sdk-replacement/scripts/extract_transsion_sdk_pack.py --apk shipped.apk --out my_pack --decoded decoded

# 4) 需要配置样例时（自动抹密钥，仍建议人工复核 REDACTION-REPORT.md）
python modules/sdk-replacement/scripts/extract_transsion_sdk_pack.py --apk shipped.apk --out my_pack --include-config
```

重建后务必做完整性核对（不要只看文件是否存在）：

1. 用同一套解析逻辑对『官方成品包』与『目标包』做**逐类比对**（`com/transsion`、`com/cloud/hisavana`、
   `com/hisavana`、`net/bat` 等根分别计数，missing 必须为 0）；
2. native so 与 dex 的 ABI/版本要对齐目标包；
3. 广告网络 adapter（Vungle/Pangle/AdMob/SafeDK）按实际开启的广告源单独补齐，它们**不**属于传音自有 SDK。

## 4. 使用红线

- 素材里的 appId、APP_KEY、track_type、referrerId、google-services.json 一律
  `DO_NOT_COPY_LITERAL_VALUES`：只能作为**结构样例**，真实值必须由目标项目在传音后台申请。
- 不要把回收物提交到公共仓库或跨项目分发；供应商 SDK 的再分发权需要单独确认。
- 素材是【注入态】回收物，不是官方 SDK 发布物；有私有 Maven 通道时优先用官方 AAR。