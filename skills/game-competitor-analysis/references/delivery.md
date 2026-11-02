# 交付与验收

## 来源清单

`sources.json` 使用以下结构，字段填写实际证据，没有数据用 null 或空列表；不要为了通过清单检查编造值：

```json
{
  "topic": "本次游戏名或类型",
  "research_date": "YYYY-MM-DD",
  "scope": "平台、地区、语言、目标和限制",
  "products": [
    {"id": "product-a", "name": "实际展示名", "publisher": "实际开发商", "platform": "Android", "package_or_app_id": "实际包名", "store_url": "https://实际商店地址"}
  ],
  "sources": [
    {"id": "S01", "product_id": "product-a", "title": "实际页面名", "url": "https://实际来源地址", "accessed_at": "YYYY-MM-DD", "published_at": null, "kind": "官方商店", "access_status": "已读取", "supports": ["具体支持的事实"], "limitations": ["具体不能证明的事"], "local_path": null}
  ]
}
```

数值在正文表格中保留日期、单位、档位/估计等口径；需要机器复用时可在条目添加 `metrics`，其中每项含 value、unit、period、region、method、source_id。不可用缺省 0 表示未知。

`screenshots.json` 是数组，每项示例：

```json
{
  "id": "IMG01",
  "product_id": "product-a",
  "source_id": "S01",
  "kind": "商店展示图",
  "image_url": "https://实际图像地址",
  "local_path": null,
  "inspected": true,
  "observations": ["实际看到的构图或界面状态"],
  "limitations": ["不能据此确认解锁关卡"]
}
```

正文关键结论就近使用有意义的 Markdown 来源链接；末尾可再提供索引。截图附产品、编号、来源和类型，不单独放 24 张图片而没有分析。报告图数由 inspected=true 的原始图像计算，不能按网页下载成功数或缩略图数量计算。

## 报告渲染

脚本依赖 Python-Markdown，项目约定使用 conda base 时先激活。`requirements.txt` 为本次验证版本。支持 Markdown 表格、代码块、自动目录，使用响应式网页与打印样式。

```bash
python "$SKILL_DIR/scripts/render_report.py" --source "$OUTPUT/report.md" --output "$OUTPUT/index.html" --title '实际报告标题'
```

- 输出应和 Markdown 在同一目录，以保持来源/证据相对链接一致。
- 本地 PNG、JPEG、WebP、GIF 内嵌到 HTML，报告可以独立显示这些插图；不改变原图与引用文件。
- 远程 HTTP(S) 图片不下载，保留在线依赖并在 `render_manifest.json` 记录。不能因此称报告完全离线可读。
- 缺失图片、越出研究目录的图像路径、空源稿、含未替换初始化占位符时失败，避免悄悄交付坏页面。
- 普通证据链接不会自动打包或内嵌。脚本列出缺失本地链接；上层报告确实引用目录外已有研究材料时确认其用途和可访问性，若交付可迁移包需一并整理相关材料。
- 不将抓取的原始 HTML 注入 Markdown。源稿是 Agent 写出的可信研究内容，脚本不是通用 HTML 安全净化器。

渲染清单记录章节数、插图数量和链接缺口，**不检验事实或替 Agent 执行研究**。完整交付还要逐项复核以下内容。

## 完成标准

1. 游戏身份准确，实际研究对象与用户一致，“头部”有明确口径。
2. 关键数值有本次核实来源和时间；不能核实的内容明确未知。
3. 每个核心观察有已读文字、已查看图像、已观看视频或实测支撑；建议和推断明确标注。
4. 逐款分析、横向比较、美术建议和融合取舍有足够具体的依据，用户能据此写原型任务。
5. 资料缺口、评论样本限制和运行验证状态如实列出。
6. 报告正文、目录、表格、图片及来源链接可读；有浏览器工具则实际打开验证桌面/窄屏及控制台错误。
7. 用户指定知识库或外部页面时，在已有授权范围内保存并核对内容；没有指定时交付本地报告即可。

仅生成目录、模板、资料链接或自动摘要，不等于完成详细拆解报告。资料有限时缩小可证明的范围，仍写出有证据的结论与明确缺口，不能填充虚构的完整度。
