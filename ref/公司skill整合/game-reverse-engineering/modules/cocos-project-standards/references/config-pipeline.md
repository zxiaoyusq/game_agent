# 配置规范（Luban 配置链路）

> **何时读我**：要新增/修改配置表、排查"配置没生效""界面一片空白""导表后别人跑不起来"时。
> **读完能做到**：独立完成一次配置改动并只更新必要产物，知道哪些文件是派生文件不能手改。
> **范围**：`[COCOS]` 工程链路（依赖 Luban，工具版本随项目）+ `[DADA]` 表清单不可复制。

本文件描述的是**配置表链路**这一层工程约定。它不依赖 Cocos 引擎本身，但依赖使用 **Luban** 作为导表工具（见 https://code-philosophy.com ）；若目标工程用别的导表方案，只借鉴"唯一真源 / 派生物禁手改 / 空数据兜底"三条原则。

## 1. 唯一真源准则（最重要）

- **`datas/Excels/*.xlsx` 是配置的唯一真源。** 生成器脚本（如 `gen_excels.py`）里的硬编码内容**只是历史初始化快照**，优先级低于当前 Excel。
- **收到配置修改需求后**：先读当前 Excel，再**只修改指定工作簿、工作表、记录和字段**；**禁止**先按"重建脚本"重建 Excel 再改。
- 修改前后校验变更范围，确保需求之外的工作簿/工作表/记录/字段**保持不变**；随后只跑导表链更新产物。
- **灾难重建脚本必须默认拒绝执行**，仅在 Excel 全部丢失且明确接受"用历史快照覆盖"时才允许显式强制模式。
  > 这是踩过的坑：重建脚本会用内置字面量重写 xlsx → 丢 key、中文变 `?`、主键重复。

## 2. 生成链与产物

```
datas/Excels/*.xlsx  ──Luban──▶  assets/scripts/config/schema/schema.ts   (表结构与类型)
                     ──merge──▶  assets/bundle/config/data.json           (运行时数据)
```

典型命令（`cwd = datas`；`.bat`/`.sh` 包装里常带 `pause`，命令行可拆解执行）：

```bash
dotnet <工具目录>/Luban.dll -t all -c typescript-json -d json --conf luban.conf \
  -x outputCodeDir=../assets/scripts/config/schema \
  -x outputDataDir=../assets/bundle/config
node merge-json.js ../assets/bundle/config ../assets/bundle/config/data.json
```

**两条派生物红线**（见 `ui-prefab-pipeline.md` 的同名原则，这里是配置侧）：

- `schema.ts` 与 `data.json` 是**派生文件，禁止手改**——下次导表即覆盖。
- 若导表因格式化（行尾空白等）产生噪声差异，用后处理脚本清理以保证 diff 稳定（例：`normalize-generated.js`）。
- 导表**可能改写** `schema.ts`（有时只是 CRLF/LF 差异）。判断"是否真改了"用 `git diff --numstat`：**LF/CRLF 差异时 numstat 为空 = 内容相同**。若确实生成了业务不该有的改动，立即还原。

### 运行时访问

```ts
// 全表（可按主键排序）
const list = CFW.tables.TbFood.getDataList().slice().sort((a, b) => a.id - b.id);
// 单条查表
const item = CFW.tables.TbLevel.get(pet.level);
// 单例常量表
const max = CFW.tables.TbGameConfig.maxLevel;
```

（`CFW.tables` 为 `[CFW]` 门面；原生工程自行加载 `data.json` 构表，见 `framework-boundary.md` 第 7 节。）

## 3. 表注册与三种表布局

表本身在 `__tables__.xlsx` 注册，每表一行：

| 列 | 含义 |
|---|---|
| `full_name` | 表全名（`Table.TbXxx`） |
| `value_type` | bean 类名（数据行结构） |
| `read_schema_from_file` | 固定 `1`：字段结构从数据文件第一行读 |
| `input` | 数据文件引用，格式 `sheet名@文件名` |
| `mode` | `one` = 单例表；留空 = map 表（首列为主键） |
| `comment` | 表注释 |

**改表前必须先 dump 表格确认布局**，不要假设。已知有三种：

1. **map 表**（首列为主键）
   ```
   第1行：##var   id   name   duration_seconds ...
   第2行：##type  int  string int              ...
   第3行：##      食物ID 食物名 喂食CD(秒)      ...
   第4行起：数据（首列唯一主键）
   ```
2. **one 表**（单例常量，列式）
   ```
   第1行：##column#var   ##type   ##
   第2行：（空）          描述     具体参数
   第3行起：变量名         类型     描述     值
   ```
3. **竖排表**（字段名在行、值在列）——存在此类表，**遇到再按实际 dump 处理**，不要套用上面两种。

## 4. 字段命名与主键陷阱

- **数据表字段用 `snake_case`**（`duration_seconds` / `unlock_type`），导表后自动转 **`camelCase`**（`durationSeconds` / `unlockType`）。业务代码只见到 camelCase。
- **多语言表的语言列用 `PascalCase`**（`English` / `Chinese` …），业务侧依赖"转大写后与语言枚举比对"；`id`（key）与 `Desc`（备注）列名固定不可改。
- **主键陷阱**：不同表的主键列**不一定是 `id`**。已实测有表以 `Desc` 为主键 → **新增行必须保证该列唯一，否则导表直接失败**。改表前先确认主键列。
- **字段名不得与 bean 类名相同**（例：`Level` bean 里不能有 `level` 字段，会导致生成代码编译错误）。撞名时改 bean 名。
- **空列占位**：表头行需写入空单元格，保证列对齐；**合并单元格信息必须保留**（导表工具依赖它判断复合字段范围，例：枚举表的 `*items` 跨列区必须是合并单元格）。
- **Excel 兼容性**：部分导表工具（NPOI 系）只识别 shared strings 与合并单元格 → 日常增量编辑必须保留现有工作簿格式与 shared strings，不要用"整表重写"的方式改表。

## 5. 多语言列约定（`*_key` 模式）

**含展示文案的业务表，统一加 `*_key` 列，值为多语言表的 `id`。**

- 中文原文列**保留**作运行时回退：`I18n.t(key, 中文原文)`，**不得删除**。
- 需参数化的说明列，回退文本中保留字面数字/占位，`{0}` 由词条承载（部分校验脚本依赖该约定）。
- 无展示消费的内部字段（内部定位名、未开发 UI 的展示名）**暂不加** `key` 列。
- **注意**：手工兼容写法（`_json_.xxx_key ?? ''`，缺列回落空串）在**重跑导表后会被生成器严格版本覆盖**——只要数据文件已含新列即一致；反之会编译或运行期缺字段。

详见 `i18n-and-text.md`。

## 6. 新增/删除表的流程

**新增**：
1. 在数据文件里加 sheet 与字段（保留格式与合并信息）
2. 在 `__tables__.xlsx` 注册一行
3. 需要枚举时改 `__enums__.xlsx`（注意 `*items` 的合并单元格）
4. 跑导表链
5. 检查 `git diff --numstat` 确认 `schema.ts` 无意外改动

**删除**：删除注册行后，其数据文件可一并移除。**先确认没有代码引用该表**（`CFW.tables.TbXxx` / `Tables.TbXxx`），再删。

## 7. 空数据兜底（必写）

配置缺失时界面会"一片空白"，无从排查。**凡是消费配置的界面，必须在列表为空时给出可见提示 + 带上下文的错误日志**：

```ts
if (list.length === 0) {
    CFW.log.error('[XxxUI] TbXxx 为空：配置未生成或未加载（检查 config/data.json）');
    this.setLabel('txtSubtitle', this.localize('XXX_EMPTY_TIP', '暂无数据'));
    return;
}
```

这条与 `data-modules.md`、`code-and-naming.md` 的空兜底要求是**同一条纪律在三个位置的落地**。

## 8. 存档与配置的版本对齐（高发事故）

**症状**：预览/启动黑屏，日志里只有一条无堆栈的 Promise 拒绝（例如 `[PreviewInEditor] PromiseRejectionEvent { isTrusted: [Getter] }`）。

**根因**：有人改了 Excel 但**没有提交重新导出的 `data.json`** → 谁重跑导表，数据里就会出现代码尚未对齐的字段 → 启动流程 Promise 拒绝 → 黑屏。

**安全流程**：

1. 只改需要的表；
2. **优先"就地同步"**：改 Excel 的同时用脚本改 `data.json` 的对应表，**不跑全量导表**；
3. 必须全量导表时，导出后立刻后处理：**以主干分支的 `data.json` 为底，只覆盖自己改过的表**，其余保持原样；
4. **验证**：打印 `data.json` 与主干的差异表清单，应当**只有自己改的表**。

```python
# 后处理核心片段：只覆盖自己改过的表
base = json.loads(subprocess.run(['git','show','origin/develop:assets/bundle/config/data.json'],
                                 cwd=R, capture_output=True).stdout.decode('utf-8'))
mine = json.load(open(DJ, encoding='utf-8'))
for k in MY_TABLES:
    base[k] = mine[k]
open(DJ,'w',encoding='utf-8').write(json.dumps(base, ensure_ascii=False, separators=(',',':')))
```

出问题想快速回到"已知能跑"：`data.json` 用主干版本。

**已经踩了、要按症状排查时**：走诊断入口 `modules/cocos-creator-repair/SKILL.md`（「数据与配置表不一致 → 点预览即黑屏」节）。本节只维护"规范怎么做"这一份。

## 9. 未取证项

- 来源项目的**具体表清单与 bean 名**属 `[DADA]`，本文件不复制；需要时读该项目的 `配置规范.md`。
- 竖排表布局的完整规则（合并单元格要求、字段列位置）在本次重建中**未逐项取证**，仅登记其存在。
