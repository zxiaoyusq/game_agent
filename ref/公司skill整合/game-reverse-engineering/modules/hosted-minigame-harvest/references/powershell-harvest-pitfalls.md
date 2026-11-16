# PowerShell 拉取脚本实测六坑
> **何时读我**：脚本跑不通 —— 中文字面量报错、出现莫名其妙的参数绑定错误、中文变乱码、批量接口少返、图片打不开、CSV 读回来串列时。
> **读完能做到**：直接认出这六类症状的根因并改掉；每条都给了症状 → 根因 → 修法。
> **范围**：`GENERAL_DEFAULT`。Windows PowerShell 5.1 实测；PowerShell 7 / 其它语言按同思路规避。

---

## 坑 1 · UTF-8 无 BOM 的 .ps1 里的中文字面量会崩

**症状**：`在设置字符串格式时出错: 输入字符串的格式不正确` / `字符串缺少终止符`，报错行指向某个含中文的 `-f` 或字符串。
**根因**：PowerShell 5.1 读**无 BOM** 的 `.ps1` 时按**系统 ANSI**（中文 Windows 为 GBK）解码。UTF-8 的中文字节被按 GBK 重解，可能产出 `{`、`'` 等**元字符**，格式化字符串与引号配对因此被破坏。

**修法**：含中文的 `.ps1` **必须存成 UTF-8 with BOM**。

```powershell
$txt = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)   # 先按 UTF-8 正确读
[System.IO.File]::WriteAllText($p, $txt, (New-Object System.Text.UTF8Encoding($true)))  # $true = 写 BOM
```

**自检**：
```powershell
$b = [System.IO.File]::ReadAllBytes($p)[0..2]
# EF BB BF = 有 BOM
```

> 更稳的做法：**脚本正文只用 ASCII**（注释也用英文），把中文留给数据文件与生成的 HTML。本模块的两个脚本就是这么写的。

---

## 坑 2 · 单字母函数名被内置别名抢占 → 报一个完全不相干的错

**症状**：`无法绑定参数"Id"。无法将值"..."转换为类型"System.Int64"`，或 `无法绑定参数"Id"。无法将值"Action"转换为类型...` —— 报错里的值根本不是你传的参数名。

**根因**：PowerShell 命令解析优先级是 **别名 > 函数 > cmdlet**。`function H` 会被内置别名 `h`（= `Get-History`，有 `Int64 -Id` 参数）抢走，实际执行的是 `Get-History -Id <你的字符串>`。

**修法**：**别用会和内置别名撞名的短名**（尤其单字母）。改成长名，如 `H` → `Esc`。

**定位手法**（脚本里还有别的隐藏撞名时，一次抓全）：

```powershell
$ast = [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e)
$ast.FindAll({param($n) $n -is [System.Management.Automation.Language.CommandAst]}, $true) |
  ForEach-Object { $_.GetCommandName() } | Sort-Object -Unique |
  ForEach-Object { $a = Get-Alias -Name $_ -ErrorAction SilentlyContinue
                   if($a){ "ALIAS! {0} -> {1}" -f $_,$a.Definition } }
```

> 同理注意：只替换 `(H $` 会漏掉 `(H (` 这种**参数以括号开头**的写法。改完用 AST 复扫一遍，别靠肉眼。

---

## 坑 3 · `Invoke-WebRequest` 把响应体按 Latin-1 解 → 中文变 `ä¸æµ·...`

**症状**：接口返回的中文（开发商名、游戏名）落盘后是 `ä¸æµ·å°å¯çºªç§æ` 这类乱码；英文正常。
**根因**：PS 5.1 的 `$r.Content` 在响应头缺 charset 或不合口味时按 Latin-1 解码。

**修法**：不要用 `$r.Content`，**取原始字节自己按 UTF-8 解**：

```powershell
$r = Invoke-WebRequest -Uri $u -UseBasicParsing -Headers $hdr
$txt = [System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
$json = $txt | ConvertFrom-Json
```

**已有乱码的补救**（把 Latin-1 字节还原回 UTF-8）：
```powershell
$fixed = [System.Text.Encoding]::UTF8.GetString(
           [System.Text.Encoding]::GetEncoding(28591).GetBytes($broken))
# 28591 = ISO-8859-1；仅当还原结果出现 CJK 时才采用，避免二次破坏
```

> 控制台显示乱码 ≠ 文件乱码。判断以**落盘文件 + 校验器**为准（G5 门禁）。

---

## 坑 4 · 批量接口有静默上限，超出的**不报错**直接丢

**症状**：传 37 个 id，只回来 20 个；不报错、不提示，hotgame 素材缺 17 张。
**根因**：服务端对 id 数组长度设了上限（案例 = 20），超出部分**静默截断**。

**修法**：**切批**，且**每批核对返回条数**：

```powershell
for($i=0; $i -lt $ids.Count; $i+=6){
  $slice = $ids[$i..([Math]::Min($i+5,$ids.Count-1))]
  # 请求 -> 断言 returned == $slice.Count，不等就报警
}
```

**通用做法**：任何批量端点都当"可能静默截断"处理 —— **永远断言 `返回条数 == 请求条数`**，不要只看 HTTP 200。

---

## 坑 5 · CDN 无视 URL 后缀返回真实格式 → 图片打不开

**症状**：文件名 `hotgame.webp`，浏览器/解码器打不开；文件大小正常。
**根因**：CDN 按**存储的原始格式**返回内容，不管 URL 里写的 `.webp`。案例 370 张里 7 张如此（4 张 JPEG + 3 张 PNG）。

**修法**：下载后**按 magic bytes 判真实格式**，改名到正确后缀；**列表页从清单读真实文件名**，不硬编码后缀。

| 格式 | magic（前几字节） |
|---|---|
| WebP | `52 49 46 46 .. .. .. .. 57 45 42 50`（`RIFF`+4B+`WEBP`） |
| JPEG | `FF D8 FF`（JFIF `FFD8FFE0` / Exif `FFD8FFE1`） |
| PNG | `89 50 4E 47 0D 0A 1A 0A` |
| GIF | `47 49 46 38`（`GIF8`） |

> 只按"文件非空"判断是不够的 —— HTML 错误页也有内容。G3 门禁就是查这个。

---

## 坑 6 · 静默吞掉的读取错误 → "扫了 0 条"却毫无报错

**症状**：字符串提取脚本跑完输出 `0 strings`，没有任何报错。
**根因**：`ZipArchive` **没有 `OpenRead(name)` 方法**（那是 `ZipFile` 的静态方法）。调用抛异常，被 `try/catch { continue }` 吞掉，于是每个 entry 都被"跳过"。

**修法**：用 `$entry.Open()`。

```powershell
$s = $e.Open()          # ✅ ZipArchiveEntry.Open()
# $zip.OpenRead($e.FullName)   ❌ 方法不存在
```

**通用教训**：批量循环里的 `catch { continue }` 会**把系统性错误伪装成空结果**。至少统计并打印**跳过计数**；为 0 结果时先怀疑"根本没进循环"，而不是"数据里没有"。

---

## 附：CSV 往返（不是坑，但要知道）

`Export-Csv` / `Import-Csv` 会为含分隔符的字段**自动加引号**，因此 `tags` 字段含逗号（如 `Match 3, Puzzle`）可安全往返，不必手工转义。
但**读取时务必指定 `-Encoding UTF8`**，否则会踩坑 1 的同款解码问题。
