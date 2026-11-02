# 测试数据记录 (test-fixtures)

> **何时读我**：哥哥要找换皮链路的验收数据在哪、真实导出与合成夹具分别放在哪个盘、想重生成夹具，或需要确认某个边界场景（中文/emoji 文件名、rotated/trimmed、尺寸不一致、部分回滚）有没有现成覆盖时。
> **读完能做到**：直接定位主目录 `E:\Gameprogram\game-skinning-pipeline-qa\` 下每一类数据的用途与只读/可改属性，用一条命令重新生成 18 文件合成夹具，并对照第 3 节七个 QA 边界点确认自己该测什么、哪些算 blocker。
> **范围**：`GENERAL_DEFAULT`

本文件记录 game-skinning-pipeline 的全部验收数据来源与合成夹具。

## 0. 测试数据主位置（2026-08-10 起）

- **主目录**：`E:\Gameprogram\game-skinning-pipeline-qa\`

`fixtures\` — 合成夹具（`skinpipe.py fixtures` 生成，18 文件）

- `skinpipe\` — 全链路 QA 夹具与证据：`new_art\`、`aliases.json`、`edge-test\`、`partial-rollback-test\`、`atlas-rebuild-test\`、`real-tree\`（真实树验证证据）、`spine\`（Spine 92 骨架全链路证据）

- `spine-qa-input\` — 92 骨架 Spine 输入（276 文件 / 13MB）

- `unity-qa\` — Unity 端到端证据（manifest / skin_map / apply / rollback / diff / verify 全套，681 文件 / 13.6MB）

- 旧路径 `E:\blast-res\skinpipe` / `E:\blast-res\qa-spine-input` / `E:\blast-res\unity-qa` 为 legacy 只读源，保留不动。

- 生成合成夹具：`python scripts\skinpipe.py fixtures --output "E:\Gameprogram\game-skinning-pipeline-qa\fixtures"`

## 1. 真实验收数据（只读，不修改）

| 数据 | 路径 | 用途 |
|---|---|---|
| Unity 真实导出 | `E:\download\sudoku-re\assets-export\` | Unity manifest / map / diff / verify（663 文件：319 Sprite PNG + 156 Texture2D + 17 AudioClip + 7 Font + 164 TextAsset） |
| Unity 分析报告 | `E:\download\sudoku-re\REVERSE_ANALYSIS_REPORT.md` | 资产数量对照基准 |
| Cocos meta 生成参考 | `E:\hermes\scripts\sudux_gen_metas.py` | Cocos uuid/sub_uuid 格式兼容 |
| Cocos 完整项目 | `E:\gameprogram\Blockudoku` | Cocos 端到端验证（Cocos 2.4.13） |
| Cocos 复刻项目 | `E:\Gameprogram\Sudux` | 黑屏/导入坑回归（assets/resources/UI 338 png + meta） |
| Cocos Creator 2.4.13 | `${COCOS_2X}\CocosCreator.exe` | P2 Cocos CLI 构建（可选） |
| Cocos Creator 3.8.7 | `${COCOS_3X}\CocosCreator.exe` | 3.x 备选 |
| Cocos Dashboard | `${COCOS_DASHBOARD}\CocosDashboard.exe` | 编辑器管理（brain 索引确认存在） |

## 2. 合成夹具（fixtures 子命令生成）

```powershell
python scripts\skinpipe.py fixtures --output ""
```

生成内容：

| 夹具 | 内容 |
|---|---|
| `cocos-mini-project/` | 微型 Cocos 2.4.13 工程：`project.json` + `Main.fire` + `assets/resources/UI/` 下 3 张 PNG（含中文、空格、括号、emoji 文件名）+ 对应 texture/sprite-frame meta |
| `cocos-atlas/` | 合成图集 `ui_atlas_1.png`（192x192，4 张 64x64 子图）+ Cocos 风格 meta（主 uuid + subMetas 子 uuid）+ `atlas_extract/index.json`（完整 rect/sprite_meta） |
| `cocos-atlas/atlas_extract/rotated_child.json` | rotated+trimmed 子图夹具（必须进入人工处理清单，禁止自动贴回） |
| `new_art/` | 替换素材：`sprite_a.png`（同尺寸）、`sprite_b.png`（同尺寸）、`sprite_b_big.png`（96x96 尺寸不一致）、`unused_icon.png`（未使用）、中文/空格/括号/emoji 文件名 |

## 3. QA 边界覆盖测试点

- 中文/空格/括号/emoji 文件名：cocos-mini-project + new_art 各一次（编码失败视为 blocker）

- 图集原位重建：cocos-atlas 换 2 张 → rect 不变、uuid/sub_uuid 不变、被替换 rect crop hash 变化、未替换 rect 不变

- rotated/trimmed：rotated_child.json → 拒绝自动重建，输出人工处理清单

- 尺寸不一致：sprite_b_big.png → 拒绝，`--allow-resize` 时缩放 + warning

- ambiguous：同名多文件需进入 ambiguous（除非 aliases 指定）

- 跨格式替换：PNG -> JPG 默认 format-mismatch 不执行

- 部分回滚：backup 单文件恢复失败不阻塞其它文件
