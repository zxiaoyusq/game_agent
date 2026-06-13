"""美术 Agent 路由。

当前实现的接口：
- POST /api/art/image/generate
    multipart/form-data 入参：
      - prompt:    必填
      - size:      必填，例如 1024x1024 / 2048x1152
      - quality:   选填，默认 medium
      - references[]: 可选，多个，浏览器上传的参考图（image/png / image/jpeg）
      - kb_refs:   可选，已选知识库 file/folder 引用 key 列表（多次同名表单字段）
                   后端会从知识库解析出对应的图片合并进 references[]
    返回：
      - 默认 image/png 二进制流（StreamingResponse）
      - 加 ?json=1 时返回 {"image_base64":"..."} JSON，便于前端直接 dataURL 渲染
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.services import art_image as art_service
from app.services.art_image import ArtImageAPIError, ArtImageConfigError, ReferenceImage
from app.services.knowledge import (
    get_item,
    get_raw_path,
    list_items_under_folder,
)

router = APIRouter(prefix="/art", tags=["art"])

logger = logging.getLogger(__name__)


# 知识库引用 → 图片字节列表所允许的扩展名 / MIME
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _bad_request(msg: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def _is_image_item(item) -> bool:
    """看 KbItem 是不是 Azure 接受的参考图（PNG/JPEG）。"""
    ct = (item.content_type or "").lower()
    ext = Path(item.filename).suffix.lower()
    if ct.startswith("image/"):
        return ct in {"image/png", "image/jpeg", "image/jpg"}
    return ext in {".png", ".jpg", ".jpeg"}


def _kb_refs_to_references(kb_refs: List[str]) -> List[ReferenceImage]:
    """把前端传过来的 kb_refs 列表解析为 ReferenceImage[]（仅 PNG/JPEG 入选）。

    协议与 services/kb_context.py 保持一致：
      - 文件：file:<module>:<category>:<item_id>
              （兼容旧三段 <module>:<category>:<item_id>）
      - 文件夹：folder:<module>:<category>:<folder_path>
                folder ref 会递归展开下属所有图片
    """
    out: List[ReferenceImage] = []
    for raw_key in kb_refs or []:
        if not raw_key:
            continue
        parts = raw_key.split(":")
        kind = parts[0] if len(parts) >= 4 and parts[0] in {"file", "folder"} else "file"
        if kind == "file" and parts[0] == "file":
            module, category, item_id = parts[1], parts[2], ":".join(parts[3:])
        elif kind == "folder":
            module, category = parts[1], parts[2]
            folder_path = ":".join(parts[3:]) if len(parts) > 3 else ""
        elif len(parts) == 3:
            module, category, item_id = parts[0], parts[1], parts[2]
            kind = "file"
        else:
            continue

        try:
            if kind == "file":
                item = get_item(module, category, item_id)
                if item is None or not _is_image_item(item):
                    continue
                path = get_raw_path(module, category, item.id)
                if path is None:
                    continue
                out.append(_load_reference(path, item.filename, item.content_type))
            else:
                items = list_items_under_folder(module, category, folder_path)
                for it in items:
                    if not _is_image_item(it):
                        continue
                    path = get_raw_path(module, category, it.id)
                    if path is None:
                        continue
                    out.append(_load_reference(path, it.filename, it.content_type))
        except (ValueError, OSError) as e:
            logger.warning("kb_refs %s 解析失败：%s", raw_key, e)
            continue
    return out


def _load_reference(path: Path, filename: str, content_type: str) -> ReferenceImage:
    """读盘并构造 ReferenceImage；按扩展名兜底 content_type。"""
    data = path.read_bytes()
    ct = (content_type or "").lower()
    if not ct.startswith("image/"):
        ext = Path(filename).suffix.lower()
        ct = "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/png"
    return ReferenceImage(filename=filename, data=data, content_type=ct)


@router.post("/image/generate")
async def generate_image(
    prompt: str = Form(..., description="文生图提示词"),
    size: str = Form(..., description="输出尺寸，例如 1024x1024 / 2048x1152"),
    quality: str = Form("medium", description="质量等级：low / medium / high / auto"),
    references: List[UploadFile] = File(default=[], description="参考图（PNG / JPEG）"),
    kb_refs: List[str] = Form(default=[], description="已选知识库引用 key（可多个）"),
    as_json: int = Query(0, alias="json", description="1 则返回 base64 JSON，默认返回二进制 PNG"),
):
    """统一的图片生成入口：无参考图走 generations，有参考图走 edits。"""
    # 1) 解析浏览器直传的参考图
    direct_refs: List[ReferenceImage] = []
    for f in references or []:
        if not f or not f.filename:
            continue
        ct = (f.content_type or "").lower()
        if ct and not ct.startswith("image/"):
            raise _bad_request(f"参考图 {f.filename} 不是图片：{ct}")
        if ct not in {"", "image/png", "image/jpeg", "image/jpg"}:
            raise _bad_request(f"参考图 {f.filename} 暂不支持的格式：{ct}")
        data = await f.read()
        if not data:
            raise _bad_request(f"参考图 {f.filename} 内容为空")
        direct_refs.append(
            ReferenceImage(
                filename=f.filename,
                data=data,
                content_type=ct or "image/png",
            )
        )

    # 2) 解析 kb_refs（已选知识库里的图片）
    kb_image_refs = _kb_refs_to_references(kb_refs or [])

    all_refs = direct_refs + kb_image_refs

    # 3) 调底层服务
    try:
        if all_refs:
            png_bytes = await art_service.edit(
                prompt=prompt,
                size=size,
                quality=quality,
                references=all_refs,
            )
        else:
            png_bytes = await art_service.generate(
                prompt=prompt,
                size=size,
                quality=quality,
            )
    except ValueError as e:
        # 入参问题（size/quality 非法、prompt 空等）
        raise _bad_request(str(e))
    except ArtImageConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except ArtImageAPIError as e:
        # Azure 透传错误：用 502，让前端能区分本地校验失败 vs 上游失败
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.exception("art image generate failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(e).__name__}: {e}",
        )

    # 4) 返回
    if as_json:
        return JSONResponse(
            content={"image_base64": base64.b64encode(png_bytes).decode("ascii")}
        )
    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/ping")
def ping() -> dict:
    """占位接口，确认路由挂载成功。"""
    return {"module": "art", "status": "ok"}
