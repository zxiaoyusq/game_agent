# AHAgames — AHA Games 小游戏原包体 + 美术素材

拉取日期：2026-10-20
来源：AHA Games (`net.bat.store` V6.6.50.0) 公开商店接口 + CDN 直链
状态：**仅拉取入库 + 建索引页，未做任何逆向分析**

## 快速入口

| 想做什么 | 打开 |
|---|---|
| **看全游戏介绍页（74 个）** | [`index.html`](index.html) ← 双击即可（含搜索 / 分类筛选） |
| 查原包体清单（含 md5 / 直链） | `manifest.csv` · `manifest.json` |
| 查美术素材 + 文案清单 | `art_manifest.csv` |
| 取原包体 | `<gameId>_<游戏名>\<游戏名>.zip` |
| 取美术素材 | `<gameId>_<游戏名>\art\` |

## 目录结构

```
AHAgames\
  index.html              ← 全游戏介绍页（引用式，本地相对图片；**入库的源文件**）
  README.md
  manifest.csv/json       ← 原包体清单
  art_manifest.csv        ← 美术素材 + 介绍文案清单
  <gameId>_<游戏名>\
     <游戏名>.zip          ← 原包体（H5 zip，未解压、未修改）
     gameInfo.json         ← 元数据（直链 / md5 / 分类 / 评分 / 开发商 / 在线入口）
     art\
        icon.*             图标
        hotgame.*          热门图（hot game）
        banner.*           横幅
        theme.*            主题图
        preview.gif        动态预览图
```

> 素材后缀随 CDN 实际格式变化（见下方"坑 5"）：本轮为 `.webp / .jpg / .png / .gif` 混用。

## 派生产物（不入库，可重生成）

以下目录/文件是**由已有产物二次生成**的，已写入仓库 `.gitignore`，不进 git 历史：

| 路径 | 大小 | 生成方式 |
|---|---|---|
| `_inlined_cache/` | 48.0 MB | `_tools_inline.py` 的中间件缓存 |
| `index.inlined_<日期>.html` | 64.4 MB | `_tools_inline.py` 产出的**自包含单文件版**（全部图片 base64 内联，可离线双击打开） |
| `index.backup.html`、`index.before_reskin_*.html` | 0.2 / 64.2 MB | 生成前的备份 |

> **为什么要区分**：入库存的是**引用式** `index.html`（~175 KB，图片相对引用 `art/`），diff 友好；
> 自包含版是**有损重编码**产物（素材 102.2 MB → 内联 48.0 MB，WebP q78/长边 1080），
> 且每次重新生成都会新增约 64 MB —— 放进 git 会持续膨胀历史。需要单文件分发时再本地生成。

## 汇报/分析产物（入库）

| 路径 | 内容 |
|---|---|
| `reskin_review/` | 74 个游戏的竞品选型审计：`verification.json`（双 SHA-256 锚点）、`reskin_ranking.csv/json`、`package_audit.json`、`筛选说明.md`、contact sheet |
| `art_direction/` | 美术方向产出：`界面效果图_20261022/`、`界面效果图_20261022_圆润简约版/`、`竞品美术分析_20261022/`（19 款竞品商店截图 + 分析 md + `screenshot_sources.json` 溯源） |
| `_tools_inline.py` | 自包含版生成脚本（可复算） |
| `_audit_reskin.py` | 选型审计脚本（可复算） |

> `art_direction/竞品美术分析_*/screens/` 下每个截图有 `.img` 与 `.jpg` 两份：
> **`.img` 为权威源**（`screenshot_sources.json` 记录 url/sha256/尺寸），**`.jpg` 供 `截图与风格对照.html` 渲染**，二者不可互相替代。
> 该目录截图源自 App Store / Google Play 商店页（第三方版权素材），仅作对标研究留存。

## 汇总

| 项 | 值 |
|---|---|
| 游戏数 | **74**（第 1 批 37 个按名称解析 + 第 2 批 37 个按 gameId 直取） |
| 原包体 | **74** 个 / **758.0 MB**（MD5 全部校验通过） |
| 美术素材 | **370** 张（74 × 5） / 102.2 MB |
| 介绍文案 | 74 组（`description` 一句话 + `introduction` 详情） |
| 素材缺失 | **0** |
| 分类数 | 18 |
| 包体可读性 | 74/74 可解压，共 50,477 条目，0 损坏，均含 html/js 入口 |
| 名称匹配 | 73 精确 + **1 模糊**（见下方待确认项） |

## 两批来源

| 批次 | 输入 | 解析方式 | 脚本 |
|---|---|---|---|
| 第 1 批 | 37 个游戏名（截图） | `POST /searcher/v2/search` 按名称匹配 | `pull_to_AHAgames.ps1` |
| 第 2 批 | 37 个 `gameId + 名称` | 直接用 ID 取详情，无需搜索 | `pull_by_id.ps1` |

第 2 批因为给了 ID，比第 1 批更可靠（没有同名歧义风险）。

## 接口字段来源

| 素材 | 接口 | 字段 |
|---|---|---|
| icon | `/ahaGames/detail/game`、`/app/game/offline-home` | `iconPictureLink` |
| **hotgame** | `/app/game/offline-home` | `hotGameImageLink` |
| banner | `/ahaGames/detail/game`、`/ahaGames/game/info` | `banner` |
| theme | `/ahaGames/detail/game` | `themePictureLink` |
| preview（gif） | `/ahaGames/detail/game` | `imageLink` |
| 包体直链 | `/ahaGames/detail/game` | `bundles[0].url` / `.md5` / `.size` |
| 文案 | `/ahaGames/detail/game` | `description` / `introduction` / `tags` / `source` |

## 复现

```powershell
cd E:\codex_apk_work\aha_minigame_pull

# 第 1 批（按名称）
.\pull_to_AHAgames.ps1
.\pull_art.ps1
.\fetch_hotgame.ps1
.\fix_meta.ps1

# 第 2 批（按 gameId）
.\pull_by_id.ps1 -TargetFile .\targets_batch2.txt

# 通用收尾
.\fix_ext.ps1        # 按 magic bytes 修正被 CDN 搞错的后缀
.\build_html.ps1     # 生成 index.html
.\check_html.ps1     # 校验：卡片数 / 图片引用 / 乱码 / 缺失
```

## 踩过的坑（复现时注意）

1. **PowerShell 5.1 读 UTF-8 无 BOM 的 .ps1 会按 ANSI 解**，脚本里的中文字面量会崩（`-f` 格式化报错）。
   → 含中文的 .ps1 必须存成 **UTF-8 with BOM**。
2. **函数名不能用单字母**：`function H` 会被 `h`(=`Get-History`) 别名抢占（别名优先级高于函数），
   报极具误导性的 `无法绑定参数"Id"`。改成 `Esc` 即可。
3. **`Invoke-WebRequest` 在 PS5.1 下把响应体按 Latin-1 解**，中文开发商名变 `ä¸æµ·...`。
   → 用 `[Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())` 显式解码。
4. **`/app/game/offline-home` 单次最多返回 20 个 id**，超出的**静默丢弃**（hotgame 图会缺）。
   → 按 6 个一批切分请求。
5. **CDN 会无视 URL 后缀返回真实格式**：`.../x.webp` 实际可能是 JPEG 或 PNG。
   本轮 370 张里有 7 张如此（4 JPEG + 3 PNG）。
   → `fix_ext.ps1` 按 magic bytes 改名；`build_html.ps1` 从 `artFiles` 取真实文件名，不硬编码 `.webp`。
6. `Export-Csv` / `Import-Csv` 会为含逗号的字段自动加引号（如 `tags` = `Match 3, Puzzle`），可安全往返。

## 边界说明（非分析结论）

- 本批是**接口返回的最新版原包**，与模拟器里该 App 已缓存的解压副本**版本可能不同**（设备缓存常为旧版）。
- 素材与包体为第三方游戏版权资源，此处仅作逆向 / 对标研究留存，未做分发合规评估。
- 全部 74 个均为 `gameType=1`（即点即玩 H5 zip），**不含**该商店的原生 APK 游戏。
- `art_manifest.csv` 的 `source` 字段是接口给的开发商/发行商，未做主体核验。
- `art_direction/竞品美术分析_*/screens/` 的 94 张截图取自 **App Store / Google Play 商店页**（第三方版权），仅作对标研究留存。

## 待确认项

**`95222` 名称模糊匹配**：清单原文 `Obby Escape from Barry Prison` 在 AHA 全站**无同名游戏**。

- 全站搜 `Barry` 仅 1 条 → `Noobs Escape Barrys Prison`（已入库，`match=FUZZY`）
- 另有名字更接近的 `95821 Obby Escape from Monster Tower`（**未**拉取）

如需改为 `95821` 或两者都留，请告知；其余 73 个均为精确匹配。

## 校验状态（harvest_validate.ps1）

最近一次全量校验：**G1–G5 全部 PASS**

```
G1/G2 package integrity : 0 failures (checked 74)   # magic + MD5
G3 art real format      : 0 failures (disk=370)     # 磁盘素材格式与后缀一致
G4/G5 catalog page      : file-refs=370 missing=0   # 引用全部可解析；0 乱码
cards=74  folder-divs=74  img-tags=370
```

> 校验脚本已支持**引用式与自包含式两种 index.html**（base64 `data:` URI 会按 magic 校验，不会被误判为缺失）。
