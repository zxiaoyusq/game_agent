# 商店接口契约还原（挖端点 → 定方法 → 爆破参数）
> **何时读我**：已经确认宿主是小游戏商店、包体是"下载解压型"，需要把它的匿名目录/详情接口打通时。
> **读完能做到**：从 APK 静态字符串挖出全部候选端点，用 HTTP 状态码与业务错误码把"方法 / 参数名 / 参数结构"逐层收敛，最终拿到"搜索 → 详情 → 包体直链"的可用契约。
> **范围**：`GENERAL_DEFAULT`（方法与错误码判据） + `CASE_ONLY_AHA`（附录实测字面值）

---

## 1. 静态挖端点（先拿全候选，别急着猜）

宿主包体里有三处可挖，**优先级从高到低**：

1. **JS / 资源型资产**（`assets/**.js`、`**/*.json`）：H5 宿主或内嵌 web 常把接口路径写成明文，可读性最好。
2. **dex 字符串表**：5 个 dex 往往有 20 万+ 字符串，端点混在其中。
3. **so / 配置**：一般只留域名，端点少。

### dex 字符串提取（PowerShell 版，可移植到任意语言）

按可打印 ASCII 游程切串（长度 ≥6），落地成一个 txt 再反复 grep——**只扫一次，后续全靠 grep**：

```powershell
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[System.IO.Compression.ZipFile]::OpenRead($apk)
foreach($e in $zip.Entries){
  if($e.FullName -notmatch '^classes\d*\.dex$'){continue}
  $s=$e.Open(); $ms=New-Object System.IO.MemoryStream; $s.CopyTo($ms); $s.Close()
  $b=$ms.ToArray(); $ms.Dispose()
  # 逐字节切可打印串 -> 追加到 $all
}
```

> ⚠️ 用 `ZipArchiveEntry.Open()`，**不是** `ZipArchive.OpenRead()`（后者不存在，会被 try/catch 静默吞掉，结果是"扫了 0 条"却毫无报错）。见 `powershell-harvest-pitfalls.md` 坑 6。

### 端点筛法（按信息量排序）

| 筛法 | 正则 / 关键词 | 命中价值 |
|---|---|---|
| 以 `/` 开头的路径 | `^/(app\|api\|bff\|v\d\|search)[a-zA-Z0-9_/-]{2,60}$` | **最高**，直接是端点 |
| 无前导斜杠的路径 | `^[a-z][a-zA-Z0-9_-]*(/[a-zA-Z0-9_-]{2,30}){1,4}$` | 高（很多客户端拼 base 后再接） |
| 模块代号 | 在 dex 里 grep 一个**已知端点里的词**（如 `watertube`） | 高，能带出同模块兄弟端点 |
| 全域 URL | `https?://...` 汇总 host 频次 | 中，先分"业务域名 vs SDK 域名" |

**先分域名再挖端点**：把 host 按出现频次排名，业务域名（商店自己的）与 SDK 域名（广告/统计/崩溃）分开。业务域名通常有 `api.` / `tapi.`(test) / `ind-api.`(地区) 这类前缀族，**同一套端点会在多个前缀上都有**。

**模块代号是捷径**：客户端常给一个功能域起内部代号（案例：小游戏域叫 `watertube`）。用代号 grep 能一次性捞出该域的全部端点，比逐个猜路径快得多。

---

## 2. 错误码驱动的参数爆破（别盲猜参数名）

打通端点后，**不要靠猜**。先用空 body / 空参数打一发，让服务端把"缺什么"告诉你：

| 观测 | 含义 | 下一步 |
|---|---|---|
| `405 Method Not Allowed`（GET 打 POST 端点或反之） | **路径存在**，方法错 | 换方法重打 |
| `404` | 路径不存在 | 换候选端点 |
| `1004 media type error` | 方法对，**Content-Type 不对** | 换 JSON ↔ 表单 |
| `1006 message body can not be empty` | 参数名**已被识别**，但结构不对 | 该字段可能要嵌套对象 |
| `2001 Invalid params!` | 有必填项缺失 | 进入改名爆破 |
| `2000 system is busy` / `Illegal access` | 瞬时/限流，或需要签名 | 先重试 + 退避；仍失败记为未打通 |

### 参数名爆破的收敛技巧

1. **先定"哪个字段被识别了"**：把候选字段名逐个单独放进 body，**只要错误码发生变化**（例如从 `2001` 变成 `1006`），就说明这个字段名被服务端读到了。这一步能把 14 个候选收敛到 1 个。
2. **再定结构**：被识别的字段若是"查询对象"，试 `{"query":{...}}` 嵌套而不是平铺。案例中平铺 `{"keyword":...}` 恒为 `2001`，**嵌进 `query` 后立刻 `1000` 成功**。
3. **搜索类端点通常还需要分页字段**（`pageNo`/`pageSize`），但**分页不是第一阻塞项**——先把能通的打出来，再补分页。

### 方法探测

对每个候选端点，GET 与 POST 各打一发即可定性：
- GET `405` → 该端点只收 POST（或反之）
- 两者都 `404` → 路径不存在

> 批量探测时**必须节流**（≥1.2s），否则会因限流把"存在"误判成"不存在"。

---

## 3. 契约骨架（通用形状）

多数游戏商店 API 的形状高度一致：

```
base:  https://<api-host>/
封装:  {"code":1000,"message":"success","timestamp":...,"data":{...}}   # 1000=成功
```

四类端点足以覆盖拉取需求：

| 类别 | 作用 | 返回关键字段 |
|---|---|---|
| **发现** | 推荐流 / 分类 / 热词 | 游戏对象数组（含 id + 直链） |
| **搜索** | 关键字检索 | 同上 |
| **详情** | 按 id 取单个 | 元数据 + `bundles[]` + 全部素材字段 + 文案 |
| **批量** | 按 id 数组取多个 | icon + **hotgame** + 配色 |

**游戏对象的关键字段**（决定能不能拉）：

```
id, name, category, rate, type            # 身份
link                                       # 在线入口（H5 URL）
bundles[].url / .md5 / .size / .name       # ★ 包体直链（有它就能出库）
iconPictureLink / banner / themePictureLink / imageLink   # 素材
description / introduction / tags / source                # 文案
```

> **`bundles[]` 是核心**。任何"能批量拉"的路线，最终都要落到一个返回 `bundles[]` 的端点。

---

## 附录：AHA Games 实测契约（`CASE_ONLY_AHA`）

> ⚠️ 以下域名、路径、字段名为**该案例实测值**，换宿主必须重新取证（`DO_NOT_COPY_LITERAL_VALUES`）。方法照抄，字面值不许搬。

**宿主**：AHA Games，包名 `net.bat.store`，V6.6.50.0（2026-10-20 实测）
**小游戏形态**：A 型（下载解压），包体落 `files/h5GameCache/<md5>[/<ver>/ready]/<域名>/<游戏名>/`，每游戏有 `gameInfo`
**游玩账本**：`files/mmkv/game_statistics_kv`（`game.opened_<gameId>` / `game.loaded_<resourceId>`）
**功能域代号**：`watertube`

### 基址

`https://api.ahagamecenter.com`（另有 `tapi`(test) / `ind-api`(印度) / `sapi` / `pay-japi` 同套前缀）

### 核心四端点

```http
# ★ 搜索（发现 + 直链，一步到位）
POST /searcher/v2/search
Content-Type: application/json
{"query":{"keyword":"block","pageNo":1,"pageSize":20}}
→ data.list[]  每项含 bundles[]（url/md5/size）

# ★ 详情（按 id）
GET /ahaGames/detail/game?gameId=<id>
→ data.bundles[0].url/.md5/.size + iconPictureLink/banner/themePictureLink/imageLink
  + description/introduction/tags/source/category/rate/byteSize

# 轻量详情
GET /ahaGames/game/info?gameId=<id>

# ★ 批量（唯一给 hotgame 的端点；单次最多 20 个 id）
POST /app/game/offline-home     {"ids":[<id>,...]}
→ iconPictureLink / homeBannerImageLink / hotGameImageLink / colors
```

### 其他可用端点

| 端点 | 方法 | 说明 |
|---|---|---|
| `/bff/continue-playing` | POST `{}` | 推荐流，10 条/次，**每次随机**，含 `bundles[]` |
| `/bff/search.default` | POST `{}` | 搜索落地页：`data.tgp`（今日热门，含 bundles）+ `data.hotWord`（15 个热词） |
| `/bff/v2.category` | POST/GET | 分类表（Hot / New / Downloads / …） |
| `/app/operate/category` | GET | 分类（简版） |
| `/app/game/local-game-info` | POST `{"ids":[…]}` | 批量基础信息（**无 bundles**） |
| `/ahaGames/v3/aha-config/multi` | GET | 全局配置（含 `h5OfflineIntervalTime` 等） |

### 已知未打通（诚实登记）

`/bff/for-you`、`/bff/v3.store.home`、`/bff/game.list`、`/bff/category.game.v2`、`/bff/search.default_tgp_list`
→ 恒返回 `2000 system is busy / service error`，参数契约未解。
**影响**：目前只能靠"关键词搜索 + 推荐流 + 热词"抽样枚举，**无法按分类全量枚举**。补齐需抓真实请求（代理 / Frida hook HTTP 层）。

### CDN

`https://aha-zip-static.ahagamecenter.com/resources/<YYYYMMDD>/<名字>.zip|.zst`
- **无需鉴权**（`HEAD` 直接 200，`Content-Type: application/zip`）
- 两种容器：`.zip` 与 `.zst`（zstd，需额外解压步骤）
- **文件名常常就是 md5，但老资源不是**（如 `.../20240411/06363833886.zip`）→ **只信接口的 `md5` 字段**
- 素材域名 `https://static.ahagamecenter.com/resources/...`，**会无视 `.webp` 后缀返回 JPEG/PNG**
