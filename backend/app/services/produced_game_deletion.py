"""按工程归属删除游戏及其产出，路径校验与游戏目录共用同一边界。"""

import json
import re
import shutil
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from app.services import produced_games


class GameDeletionConflict(ValueError):
    """工程正在执行或归属冲突时，保留所有文件供用户处理。"""


def _records(store: Path, kind: str) -> dict[str, dict]:
    """文件名作为记录标识，损坏和链接记录不参与跨工程归属推断。"""
    directory = produced_games._child(store, kind)
    records = {}
    for path in directory.glob("*.json"):
        if path.is_symlink() or not produced_games.IDENTIFIER.fullmatch(path.stem):
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                records[path.stem] = value
        except (OSError, ValueError):
            continue
    return records


def _workspace(root: Path, relative: str) -> Path:
    """归属记录只能指向 games 内的独立工作区，不能授权删除其他目录。"""
    if not isinstance(relative, str) or not relative.startswith("games/"):
        raise ValueError("游戏工程归属路径无效")
    return produced_games._child(root, relative)


def ensure_workspace_not_deleting(root: Path, store: Path, workspace: Path) -> None:
    """清理中断后继续保留工作区门禁，防止新任务写入尚未清理完的目录。"""
    for record in _records(store, "deletions").values():
        pending = _workspace(root, record.get("workspace"))
        if workspace.is_relative_to(pending) or pending.is_relative_to(workspace):
            raise GameDeletionConflict("该工程的删除尚未完成，请先在产出游戏中重试删除。")


def _delete(identifier: str, root: Path, store: Path, *, project_id: str | None = None) -> dict:
    """删除可重试；关联记录最后移除，清理失败后仍能按同一标识继续。"""
    from app.services.workflow import engine, pipeline

    if not produced_games.IDENTIFIER.fullmatch(identifier):
        raise ValueError("游戏标识无效")
    # 与创建、恢复及发布共用锁，阻止清理期间启动同一工程的新任务。
    with engine.LOCK:
        projects = _records(store, "projects")
        publications = _records(store, "publications")
        deletions = _records(store, "deletions")
        if project_id:
            pending_id = next((key for key, value in deletions.items()
                               if project_id in value.get("project_ids", [])), f"project-{project_id}")
        else:
            pending_id = next((key for key, value in deletions.items()
                               if key == identifier or isinstance(value.get("aliases"), list)
                               and identifier in value["aliases"]), identifier)
        pending_file = produced_games._child(store, f"deletions/{pending_id}.json")
        pending = deletions.get(pending_id, {})
        if pending_file.exists() and not pending:
            raise GameDeletionConflict("删除记录损坏，暂时无法继续清理。")
        for field in ("project_ids", "run_ids", "aliases", "publication_ids"):
            values = pending.get(field, [])
            if not isinstance(values, list) or any(not isinstance(value, str) or not produced_games.IDENTIFIER.fullmatch(value) for value in values):
                raise ValueError("删除记录中的标识无效")
        owner_file = produced_games._child(store, f"publications/{identifier}.json")
        if not project_id and owner_file.exists() and identifier not in publications:
            raise GameDeletionConflict("发布归属记录损坏，暂时无法确认删除范围。")

        owner = projects.get(project_id) if project_id else None
        if project_id and not owner and not pending:
            # 重复删除不再按同名游戏目录推断归属，避免清理随后创建的其他内容。
            return {"id": identifier, "deleted": True, "deleted_ids": [], "deleted_project_ids": []}
        workspace = _workspace(root, pending.get("workspace") or (owner.get("workspace") if owner else f"games/{identifier}"))
        if not project_id and identifier in publications and not pending:
            owner = projects.get(publications[identifier].get("project_id"))
            if owner is None:
                raise GameDeletionConflict("发布版本缺少对应项目记录，暂时无法确认工程归属。")
            source = _workspace(root, owner.get("workspace"))
            if source != workspace and workspace.exists():
                raise GameDeletionConflict("发布路径与另一个游戏工程重名，暂时无法安全删除。")
            workspace = source

        relative = workspace.relative_to(root).as_posix()
        owners = {project_id} if project_id else {key for key, project in projects.items() if project.get("workspace") == relative}
        if pending and not owners.issubset(pending.get("project_ids", [])):
            raise GameDeletionConflict("该目录已出现新的项目归属，暂时无法继续删除。")
        owners.update(pending.get("project_ids", []))
        preserve_workspace = bool(pending.get("preserve_workspace"))
        # 项目删除只移除本项目归属；共享或嵌套的工程目录继续由其他项目使用。
        for key, project in projects.items():
            if key in owners:
                continue
            try:
                other = _workspace(root, project.get("workspace"))
            except ValueError:
                continue
            if workspace.is_relative_to(other) or other.is_relative_to(workspace):
                if project_id:
                    preserve_workspace = True
                else:
                    raise GameDeletionConflict("该工程与其他项目共用父子目录，请先拆分工程目录。")

        runs = {key: run for key, run in _records(store, "runs").items() if run.get("project_id") in owners}
        for key, run in runs.items():
            worker = engine.WORKERS.get(key)
            if run.get("status") in engine.ACTIVE or worker is not None and not worker.done():
                raise GameDeletionConflict("该游戏还有生成任务在执行，请先取消任务或等待完成。")
        for key in owners:
            worker = pipeline.PIPELINES.get(key)
            if projects.get(key, {}).get("pipeline", {}).get("status") == "running" or worker is not None and not worker.done():
                raise GameDeletionConflict("该游戏的全流程任务仍在执行，请先取消任务或等待完成。")

        # 同一工程的工作区入口和全部发布别名一起移除，避免删除后出现残留条目。
        aliases = set() if project_id else {identifier}
        aliases.update(pending.get("aliases", []))
        parts = Path(relative).parts
        if len(parts) == 2 and not preserve_workspace:
            aliases.add(parts[1])
        publication_ids = {key for key, value in publications.items() if value.get("project_id") in owners}
        publication_ids.update(pending.get("publication_ids", []))
        aliases.update(publication_ids)
        if project_id:
            # 同名公开入口若明确属于另一个项目，只清理当前项目自己的发布版本。
            aliases = {alias for alias in aliases if alias not in publications or publications[alias].get("project_id") in owners}
        directories = [] if preserve_workspace else [workspace]
        for alias in sorted(aliases):
            other_workspace = _workspace(root, f"games/{alias}")
            if other_workspace != workspace and other_workspace.exists():
                raise GameDeletionConflict("关联发布名称与其他工程重名，暂时无法安全删除。")
            directories.append(produced_games._child(root, f"frontend/public/games/{alias}"))
        for alias in publication_ids:
            backups = produced_games._child(store, "publications/backups")
            for path in backups.glob(f"{alias}-*"):
                if re.fullmatch(r"[0-9a-f]{32}", path.name[len(alias) + 1:]):
                    directories.append(produced_games._child(store, f"publications/backups/{path.name}"))
        run_ids = set(runs) | set(pending.get("run_ids", []))
        for key in run_ids:
            directories.extend(produced_games._child(store, f"{kind}/{key}") for kind in ("artifacts", "inputs"))
        run_files = [produced_games._child(store, f"runs/{key}.json") for key in run_ids]
        publication_files = [produced_games._child(store, f"publications/{key}.json") for key in publication_ids]
        project_files = [produced_games._child(store, f"projects/{key}.json") for key in owners]
        checkpoints = produced_games._child(store, "checkpoints.sqlite")
        # 先校验完整删除计划，任一路径异常都不能导致其他目录先被清理。
        for path in directories:
            if path.exists() and not path.is_dir():
                raise ValueError("游戏产出目录类型异常，无法删除")
        for path in [*run_files, *publication_files, *project_files, checkpoints]:
            if path.exists() and not path.is_file():
                raise ValueError("游戏生成记录类型异常，无法删除")

        # 在任何物理删除前原子保存归属，发布记录或项目记录清理失败后仍可重试。
        record = {"id": pending_id, "workspace": relative,
                  "name": pending.get("name")
                  or next((projects[key]["name"] for key in sorted(owners) if projects.get(key, {}).get("name")), None)
                  or produced_games._import_metadata(identifier).get("name") or identifier,
                  "project_ids": sorted(owners), "run_ids": sorted(run_ids),
                  "aliases": sorted(aliases), "publication_ids": sorted(publication_ids)}
        if project_id or pending.get("kind") == "project":
            record.update(kind="project", preserve_workspace=preserve_workspace,
                          projects={key: projects.get(key) or pending.get("projects", {}).get(key)
                                    for key in owners if projects.get(key) or pending.get("projects", {}).get(key)})
        pending_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = produced_games._child(store, f"deletions/{pending_id}.tmp")
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(pending_file)

        # 先清理文件与检查点，再清理归属记录；中断或磁盘错误后重试不会丢失清理依据。
        for path in dict.fromkeys(directories):
            if path.exists():
                shutil.rmtree(path)
        if run_ids and checkpoints.exists():
            with SqliteSaver.from_conn_string(str(checkpoints)) as saver:
                for key in run_ids:
                    saver.delete_thread(key)
        for path in [*run_files, *publication_files, *project_files]:
            path.unlink(missing_ok=True)
        pending_file.unlink()
        return {"id": identifier, "deleted": True, "deleted_ids": sorted(aliases),
                "deleted_project_ids": sorted(owners), "workspace_preserved": preserve_workspace}


def delete_game(identifier: str) -> dict:
    """删除游戏入口及其工程、发布版本和全部关联项目。"""
    return _delete(identifier, produced_games.ROOT, produced_games.PROJECTS_DIR.parent)


def delete_project(identifier: str) -> dict:
    """按项目 ID 定位工程，兼容自定义工作区及还没有构建的项目。"""
    from app.services.workflow import engine
    return _delete(identifier, engine.ROOT, engine.STORE, project_id=identifier)


def pending_projects(store: Path) -> dict[str, dict]:
    """清理失败时保留项目卡片，记录已被移除的项目也能再次点击删除。"""
    result = {}
    for record in _records(store, "deletions").values():
        if record.get("kind") != "project":
            continue
        for key, project in record.get("projects", {}).items():
            result[key] = {**project, "deletion_pending": True}
    return result
