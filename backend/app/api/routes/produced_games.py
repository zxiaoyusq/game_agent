"""产出游戏目录与运行资源接口。"""

import logging
import sqlite3

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services import produced_game_deletion, produced_games

router = APIRouter(prefix="/produced-games", tags=["产出游戏"])
logger = logging.getLogger(__name__)


def _read(function, *args):
    """目录和资源错误保持明确状态，前端可以提示并重新选择。"""
    try:
        return function(*args)
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error


@router.get("")
def games():
    return _read(produced_games.list_games)


@router.delete("/{identifier}")
def delete_game(identifier: str):
    """永久删除对应工程、发布版本和关联生成内容。"""
    try:
        return produced_game_deletion.delete_game(identifier)
    except produced_game_deletion.GameDeletionConflict as error:
        raise HTTPException(409, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except (OSError, sqlite3.Error) as error:
        logger.exception("游戏及产出清理失败，游戏标识为 %s", identifier)
        raise HTTPException(503, "删除未完成，请重试。") from error


@router.get("/{identifier}/cover")
def cover(identifier: str):
    return FileResponse(_read(produced_games.cover_file, identifier), headers={"X-Content-Type-Options": "nosniff"})


@router.api_route("/{identifier}/play/{file_path:path}", methods=["GET", "HEAD"])
def play(identifier: str, file_path: str):
    # HEAD 让播放器先确认入口存在，避免把 404 错误页当成已运行的游戏。
    return FileResponse(_read(produced_games.game_file, identifier, file_path),
                        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "no-cache"})
