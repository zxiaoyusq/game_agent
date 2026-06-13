"""知识库相关 Pydantic 模型。

知识库按「模块 / 分类」两级组织：
- module: planning / art / dev / ops，对应四个岗位
- category: 每个模块下的分类，例如 art 下有 docs / images / videos / motion / facial

每条记录对应一份原始物料文件（文档或多模态素材），
元信息以 JSON 维护在 data/knowledge/<module>/<category>/index.json。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class KbItem(BaseModel):
    """知识库条目元信息。"""

    id: str = Field(..., description="条目唯一 ID（uuid hex）")
    module: str = Field(..., description="所属模块：planning/art/dev/ops")
    category: str = Field(..., description="所属分类：docs/images/...")
    # 所属文件夹相对路径，"" 表示分类根目录；多级用 / 分隔，深度 ≤ 4
    folder: str = Field(default="", description="所属文件夹相对路径，'' 为根目录")

    # 业务展示字段
    title: str = Field(..., description="标题，默认取上传文件名（不含扩展名）")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    summary: str = Field(default="", description="摘要描述，可选")

    # 文件信息
    filename: str = Field(..., description="原始文件名")
    stored_name: str = Field(..., description="磁盘上实际落盘的文件名")
    size: int = Field(..., description="文件字节大小")
    content_type: str = Field(default="", description="MIME 类型，可空")

    # 时间戳，统一 ISO 8601 字符串
    created_at: str = Field(..., description="创建时间 ISO 字符串")
    updated_at: str = Field(..., description="更新时间 ISO 字符串")


class KbFolder(BaseModel):
    """知识库文件夹元信息（每个分类下独立维护）。"""

    path: str = Field(..., description="相对 category 的路径，例如 'design/character'")
    name: str = Field(..., description="文件夹叶子节点名（path 的最后一段）")
    desc: str = Field(default="", description="文件夹用途描述，可选；会带进提示词")
    created_at: str = Field(..., description="创建时间 ISO 字符串")
    updated_at: str = Field(..., description="更新时间 ISO 字符串")


class KbItemList(BaseModel):
    """列表查询响应。"""

    total: int
    items: List[KbItem]


class KbFolderList(BaseModel):
    """文件夹列表响应。"""

    total: int
    folders: List[KbFolder]


class KbDeleteResult(BaseModel):
    """删除操作响应。"""

    id: str
    deleted: bool = True
