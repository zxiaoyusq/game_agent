# Cocos 逆向格式速查
> **何时读我**：遇到带 `HEK:` 头的加密资源、`.jsc` 脚本、ETC1 PKM 贴图，或要看懂 import 序列化数组、Spine 内嵌存储、DragonBones 资产对的真实结构与字段时。
> **读完能做到**：按头部特征识别并处理这几类资产（HEK 头 + 循环密钥 XOR、`.jsc` 的 XXTEA、PKM 转 PNG），把序列化数组或内嵌骨架还原成可直接打开的文件，并判断附件死引用与多图集情况。
> **范围**：`GENERAL_DEFAULT`

## v03 加密资源（HEK）

- 头部：`b"HEK:"` + 4 字节版本标记。

- 正文：明文与循环密钥做 XOR；密钥示例 `65485d8a-8161-4c`（16 字节循环）。

- 解密后的明文可能再套 gzip（`1F 8B`），需要解压。

- 并非所有文件都带 HEK 头，不带头的原样保留。

- 实测：Block Master `stage2_sdk/assets/assets/resources/import/**/*.json` 使用密钥 `65485d8a-8161-4c`，XOR 后直接是 JSON（无 gzip）。修改时必须保留 `HEK:` + 4 字节版本头，只对正文 XOR 回写，并解密复读校验。

## JSC 脚本

- `.jsc` 无 HEK 头，正文为 XXTEA（little-endian uint32，DELTA=0x9E3779B9）。

- 解密结果常为 gzip；**可能是多成员 gzip**（多个 gzip 流拼接），必须逐个成员解压再拼接。

- 若解密后不是 gzip 也不是可读 JS，可能是 SpiderMonkey 字节码，需 spidermonkey-dumper。

- XXTEA 密钥通常 16 字节，可从 main.js/application.js 或内存中提取；找不到时用 frida 运行时 dump 或静态分析 so。

## ETC1 PKM（Cocos Creator 2.x 贴图）

- 头 16 字节：`b"PKM 10"` + 4 未知字节 + `>HHH` 宽/高/origW（u16）。

- 数据：`ceil(w/4)*ceil(h/4)` 个 8 字节 ETC1 块；有 diff/non-diff、flip 两种模式和 8 张调制表。

- 转换脚本 `modules/cocos-reverse-engineering/scripts/pkm_to_png.py` 已实现完整 ETC1 解码。

## Cocos 序列化数组（import json）

解密目录里 import 资产是序列化数组，结构（示例）：

```json
[1, 0, 0,
[["sp.SkeletonData", ["_name", "_atlasText", "textureNames", "_skeletonJson", "textures"], -1, 3]],
[[0, 0, 1, 3]],
[[0, "name", "", ["a.png"], "", [0]]],
0, 0, [], [], []]
```

- `arr[3]` = 类定义列表（`[类型名, 字段名列表, ...]`）。

- `arr[5]` = 数据列表；`d[0]` 为索引，其余字段按类定义的字段顺序对应。

- 重建后的工程通常转为 dict 格式：`[{"__type__": "sp.SkeletonData", "_name": ..., "_atlasText": ..., "textureNames": [...], "_skeletonJson": {...}}]`。

- 同一语义路径可能对应多个 uuid（SkeletonData、图集 native `cc.Asset`、SpriteFrame 等），重建时若合并出错会得到损坏 json（`Extra data`），用 `restore_skeleton_data.py` 按 uuid 从解密源修复。

## Spine 内嵌存储

- `.atlas` 的同伴 `.json` 通常是 `sp.SkeletonData`：`_skeletonJson` 是纯 Spine 骨架，`_atlasText` 是图集文本，`textureNames` 是页面贴图文件名。

- 标准查看器（SpineViewer 等）需要“纯骨架 json + atlas + png”；从 `_skeletonJson` 提取出 `.skeleton.json` 即可直接打开。

- 部分 `.atlas` 同伴是 `cc.SpriteFrame`（普通纹理图集，不是 Spine）。

- 图集可能多页；附件（skin 里的 attachment 名）可能来自其他图集（多图集骨骼）或是不存在的死引用（未使用的皮肤附件）。

## DragonBones

- 资产对：`*_ske.json`（骨架）+ `*_tex.json`（纹理），同目录配对。

- 骨架数据可能内嵌在 import 序列化数组里（`dragonBones.DragonBonesAsset` 的 `_dragonBonesJson` 字段），需要按 uuid 找到 import 文件提取。

- 区分 lite/非 lite：同一名字可能有两份（如 `comb_ske-lite` 与 `comb_ske`），都要提取。
