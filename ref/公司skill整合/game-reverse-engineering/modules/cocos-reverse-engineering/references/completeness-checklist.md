# 完整性验收清单
> **何时读我**：资产解密/提取/还原做完，要确认资产提取是否完整、要交付验收结论，或要逐项核对解密、重建、美术、报告是否都过关时。
> **读完能做到**：按「数量 + 全量验证结果」的证据标准逐项验收解密、重建、美术与报告，并用常见坑表定位图打不开、`Extra data`、黑块、贴图错位等问题的原因与修法。
> **范围**：`GENERAL_DEFAULT`

以下各项都应产出**证据**（数量 + 全量验证结果），不能只汇报文件数。

## 解密

资源解密：全部文件成功，0 错误；生成 `_manifest.json`（SHA1）。

JSC：全部解密为明文 JS（gzip 多成员处理正确）。

## 重建

bundle 数量与 `config.json` 一致；场景 `.fire`、预制体 `.prefab` 存在。

import 映射：每个 import 都能在工程中找到（语义路径或 `_packed` 镜像）。

无损坏 json：`json.loads` 全量通过；失败项用 `restore_skeleton_data.py` 从解密源修复。

## 美术

PNG 全量可解码（Pillow），0 损坏。

ETC1 `.pkm` 全部转出同名 `.png`。

Spine：每个 `.atlas` 有 `sp.SkeletonData`（或注明 SpriteFrame 图集）；`_skeletonJson` 提取为纯骨架 json；附件名在图集文本或全工程图集中可查；死引用单独列出。

DragonBones：`*_ske.json` 与 `*_tex.json` 成对，0 孤儿；内嵌骨架按 uuid 提取。

字体：native 与工程 SHA1 全量比对，缺失 `.ttf` 补齐。

## 报告

资源清单（分类统计 + 特殊处理说明）。

完整性报告（逐项结论 + 证据数量）。

工具/脚本留存（本 skill 的 scripts 即可复现全流程）。

## 常见坑

| 现象 | 原因 | 处理 |
|---|---|---|
| `.atlas` 有文件但打不开 | 同伴 json 是 `cc.SpriteFrame` 或损坏合并 | 分类/修复，按附件覆盖验证 |
| `Extra data` 解析失败 | 重建合并多个同路径资产 | restore_skeleton_data.py |
| 附件名找不到 | 多图集骨骼或死引用 | 全工程图集索引查，分类处理 |
| 图片显示黑块 | ETC1 PKM 未转换 | pkm_to_png.py |
| 骨骼能读但贴图错位 | 图集文本页名与实际 png 不一致 | 核对 textureNames/页名大小写 |
