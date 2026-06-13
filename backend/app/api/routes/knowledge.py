"""知识库 HTTP 路由。

负责 4 个模块（策划/美术/程序/运营）下知识沉淀和多模态物料的：
上传 / 查阅 / 下载 / 删除 / 文件夹管理。当前阶段不含向量化与 RAG 检索。

URL 形态：
    POST   /api/knowledge/{module}/{category}/items                上传文件（可指定 folder）
    GET    /api/knowledge/items                                    全模块列表（可过滤）
    GET    /api/knowledge/{module}/{category}/items                单分类列表（可按 folder 过滤）
    GET    /api/knowledge/{module}/{category}/items/{item_id}      单条元信息
    GET    /api/knowledge/{module}/{category}/items/{item_id}/raw  下载原始文件
    DELETE /api/knowledge/{module}/{category}/items/{item_id}      删除文件
    GET    /api/knowledge/{module}/{category}/folders              列出该分类所有文件夹
    POST   /api/knowledge/{module}/{category}/folders              新建文件夹
    DELETE /api/knowledge/{module}/{category}/folders              删除空文件夹（path 走 query）
"""

from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import KB_MAX_UPLOAD_BYTES, KB_MODULE_CATEGORIES
from app.models.common import ApiResponse
from app.models.knowledge import (
    KbDeleteResult,
    KbFolder,
    KbFolderList,
    KbItem,
    KbItemList,
)
from app.services import knowledge as kb_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# ---- 工具：把 service 抛出的 ValueError 转 HTTP 400 -----------------------

def _bad_request(msg: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def _not_found(msg: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


# ---- 元数据：列出所有合法模块/分类 ---------------------------------------

@router.get("/modules", response_model=ApiResponse[dict])
def list_modules() -> ApiResponse[dict]:
    """返回模块及其支持的分类，前端可据此渲染分类下拉。"""
    return ApiResponse(data={"modules": KB_MODULE_CATEGORIES})


# ---- 列表：跨模块汇总查询 -------------------------------------------------

@router.get("/items", response_model=ApiResponse[KbItemList])
def list_all_items(
    module: Optional[str] = Query(None, description="按模块过滤"),
    category: Optional[str] = Query(None, description="按分类过滤；要求与 module 同时给出"),
) -> ApiResponse[KbItemList]:
    """跨模块汇总列表。
    - module 为空时 category 必须也为空，否则报 400
    """
    if category is not None and module is None:
        raise _bad_request("传 category 时必须同时指定 module")
    try:
        items = kb_service.list_items(module=module, category=category)
    except ValueError as e:
        raise _bad_request(str(e))
    return ApiResponse(data=KbItemList(total=len(items), items=items))


# ---- 单分类：列表 + 上传 --------------------------------------------------

@router.get(
    "/{module}/{category}/items",
    response_model=ApiResponse[KbItemList],
)
def list_category_items(
    module: str,
    category: str,
    folder: Optional[str] = Query(
        None,
        description="按文件夹过滤；不传 = 该分类所有文件，传 '' = 仅根目录，传具体路径 = 该 folder 直属",
    ),
) -> ApiResponse[KbItemList]:
    """列出单个分类下的条目，可按 folder 过滤。"""
    try:
        items = kb_service.list_items(module=module, category=category, folder=folder)
    except ValueError as e:
        raise _bad_request(str(e))
    return ApiResponse(data=KbItemList(total=len(items), items=items))


@router.post(
    "/{module}/{category}/items",
    response_model=ApiResponse[KbItem],
    status_code=status.HTTP_201_CREATED,
)
async def upload_item(
    module: str,
    category: str,
    file: UploadFile = File(..., description="待上传的物料文件"),
    title: Optional[str] = Form(None, description="标题；不填则取文件名"),
    summary: str = Form("", description="摘要描述"),
    tags: str = Form("", description="逗号分隔的标签字符串，例如 'UI,角色'"),
    folder: str = Form("", description="所属文件夹相对路径，留空 = 根目录"),
) -> ApiResponse[KbItem]:
    """上传一个知识库条目。

    使用 multipart/form-data：
        - file:    必填，原始文件
        - title:   选填
        - summary: 选填
        - tags:    选填，使用英文/中文逗号分隔
        - folder:  选填，目标文件夹相对路径（必须已创建）
    """
    # 读取文件全量到内存。当前 DEMO 阶段单文件 <50MB，可直接缓存；
    # 后续如需大文件分片，这一段应改为流式落盘。
    raw = await file.read()
    if not raw:
        raise _bad_request("文件内容为空")
    if len(raw) > KB_MAX_UPLOAD_BYTES:
        raise _bad_request(
            f"文件过大：{len(raw)} 字节，超过上限 {KB_MAX_UPLOAD_BYTES} 字节"
        )

    # 标签：同时支持中英文逗号
    parsed_tags: List[str] = []
    if tags:
        for piece in tags.replace("，", ",").split(","):
            t = piece.strip()
            if t:
                parsed_tags.append(t)

    try:
        item = kb_service.create_item(
            module=module,
            category=category,
            filename=file.filename or "untitled",
            file_bytes=raw,
            title=title,
            tags=parsed_tags,
            summary=summary,
            content_type=file.content_type or "",
            folder=folder,
        )
    except ValueError as e:
        raise _bad_request(str(e))

    return ApiResponse(data=item)


# ---- 单条：详情 / 下载 / 删除 ---------------------------------------------

@router.get(
    "/{module}/{category}/items/{item_id}",
    response_model=ApiResponse[KbItem],
)
def get_item_detail(module: str, category: str, item_id: str) -> ApiResponse[KbItem]:
    """获取单条元信息。"""
    try:
        item = kb_service.get_item(module, category, item_id)
    except ValueError as e:
        raise _bad_request(str(e))
    if item is None:
        raise _not_found(f"条目不存在：{item_id}")
    return ApiResponse(data=item)


@router.get("/{module}/{category}/items/{item_id}/raw")
def download_item_raw(
    module: str,
    category: str,
    item_id: str,
    download: int = Query(0, description="1=强制下载（attachment）；默认 0=内联（inline）"),
) -> FileResponse:
    """获取原始物料文件。
    - 默认 inline 返回，便于 <img>/<video>/<iframe> 直接渲染；
    - download=1 时附 attachment 头，触发浏览器下载到本地。
    """
    try:
        item = kb_service.get_item(module, category, item_id)
        path = kb_service.get_raw_path(module, category, item_id)
    except ValueError as e:
        raise _bad_request(str(e))
    if item is None or path is None:
        raise _not_found(f"文件不存在：{item_id}")
    return FileResponse(
        path=str(path),
        filename=item.filename,
        media_type=item.content_type or "application/octet-stream",
        content_disposition_type="attachment" if download else "inline",
    )


@router.delete(
    "/{module}/{category}/items/{item_id}",
    response_model=ApiResponse[KbDeleteResult],
)
def delete_item(
    module: str, category: str, item_id: str
) -> ApiResponse[KbDeleteResult]:
    """删除条目（同步删元信息和物理文件）。"""
    try:
        ok = kb_service.delete_item(module, category, item_id)
    except ValueError as e:
        raise _bad_request(str(e))
    if not ok:
        raise _not_found(f"条目不存在：{item_id}")
    return ApiResponse(data=KbDeleteResult(id=item_id, deleted=True))


# ---- 文件夹：列表 / 创建 / 删除 -------------------------------------------

class CreateFolderReq(BaseModel):
    """新建文件夹请求体。"""

    path: str = Field(..., min_length=1, description="文件夹相对路径，例如 'design/character'")
    desc: str = Field("", description="文件夹用途描述（会带进提示词）")


@router.get(
    "/{module}/{category}/folders",
    response_model=ApiResponse[KbFolderList],
)
def list_category_folders(module: str, category: str) -> ApiResponse[KbFolderList]:
    """列出某分类下所有已注册的文件夹。"""
    try:
        folders = kb_service.list_folders(module, category)
    except ValueError as e:
        raise _bad_request(str(e))
    return ApiResponse(data=KbFolderList(total=len(folders), folders=folders))


@router.post(
    "/{module}/{category}/folders",
    response_model=ApiResponse[KbFolder],
    status_code=status.HTTP_201_CREATED,
)
def create_category_folder(
    module: str,
    category: str,
    body: CreateFolderReq,
) -> ApiResponse[KbFolder]:
    """新建一个文件夹。父级必须已存在。"""
    try:
        folder = kb_service.create_folder(
            module, category, path=body.path, desc=body.desc
        )
    except ValueError as e:
        raise _bad_request(str(e))
    return ApiResponse(data=folder)


@router.delete(
    "/{module}/{category}/folders",
    response_model=ApiResponse[KbDeleteResult],
)
def delete_category_folder(
    module: str,
    category: str,
    path: str = Query(..., description="要删除的文件夹相对路径"),
) -> ApiResponse[KbDeleteResult]:
    """删除一个空文件夹。仍含文件或子文件夹时拒绝删除。"""
    try:
        ok = kb_service.delete_folder(module, category, path=path)
    except ValueError as e:
        raise _bad_request(str(e))
    if not ok:
        raise _not_found(f"文件夹不存在：{path}")
    # 复用 KbDeleteResult，把 path 借给 id 字段使用即可
    return ApiResponse(data=KbDeleteResult(id=path, deleted=True))


# ---- 保留：原有 ping，便于早期联调 ----------------------------------------

@router.get("/ping")
def ping() -> dict:
    """占位接口，确认路由挂载成功。"""
    return {"module": "knowledge", "status": "ok"}
