"""公司游戏参考目录与商店图接口；原始包体保留在参考目录，不在此执行。"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services import reference_games

router = APIRouter(prefix="/workflow/reference-games", tags=["公司游戏参考"])


def _read(function, *args):
    """将路径或资料问题返回为可读错误，避免目录异常泄漏为服务器错误。"""
    try:
        return function(*args)
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error


@router.get("")
def list_games():
    """按当前磁盘生成目录、原包状态与历史清单差异。"""
    return _read(reference_games.list_reference_games)


@router.get("/research-document")
def research_document(path: str):
    """按参考路径读取已编目的研究文档，供页面查看及按需选择。"""
    return _read(reference_games.read_research_document, path)


@router.get("/{identifier}")
def game(identifier: str):
    """提供说明、来源路径和实际图片，供知识库及新建项目共用。"""
    return _read(reference_games.get_reference_game, identifier)


@router.get("/{identifier}/assets/{asset_name}")
def asset(identifier: str, asset_name: str):
    """只服务目录中已验证的商店图片，不将参考目录变为任意文件服务。"""
    path = _read(reference_games.reference_game_asset, identifier, asset_name)
    return FileResponse(path, headers={"X-Content-Type-Options": "nosniff"})
