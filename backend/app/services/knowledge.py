"""知识库服务：基于本地文件系统的物料管理。

存储约定：
    data/knowledge/<module>/<category>/
        index.json                       # 该分类下所有条目元信息 + 文件夹元信息
        <item_id>__<原文件名>            # 根目录下落盘的文件
        <folder_path>/<item_id>__<原>    # 子文件夹下落盘的文件，folder_path 用 / 分隔

index.json 格式（自 v1.1 起）：
    {
        "items":   [KbItem, ...],
        "folders": [KbFolder, ...]
    }
v1.0 老格式（直接是 KbItem 数组）会被自动识别并兼容读出，
首次写回时自动升级到 v1.1，folder 字段缺失时默认为根目录 ""。

当前阶段仍只做本地文件 + JSON 管理，不涉及向量化与检索。
"""

from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from app.config import KB_MODULE_CATEGORIES, KNOWLEDGE_DIR
from app.models.knowledge import KbFolder, KbItem

logger = logging.getLogger(__name__)


# ---- 常量 -----------------------------------------------------------------

# 文件夹相对路径深度上限，超出会拒绝创建（磁盘扫描时同样按此截断）
MAX_FOLDER_DEPTH = 4

# 文件夹每段名字允许的字符：中英文 / 数字 / 下划线 / 连字符 / 点 / 空格
_FOLDER_SEG_RE = re.compile(r"^[0-9A-Za-z_.\-一-龥 ]{1,64}$")

# 同步时直接忽略的文件名（与隐藏文件一并跳过）
_SYNC_IGNORE_NAMES = {"index.json", ".DS_Store", "Thumbs.db"}

# 同步时直接忽略的目录名
_SYNC_IGNORE_DIRS = {"__pycache__", ".git"}

# 用于识别"由本服务上传"的文件名前缀：<32 hex>__<rest>
_STORED_NAME_RE = re.compile(r"^([0-9a-fA-F]{32})__(.+)$")


# ---- 通用工具 -------------------------------------------------------------

def _now_iso() -> str:
    """返回带时区的 ISO 时间字符串，便于前端直接展示。"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _validate_module_category(module: str, category: str) -> None:
    """校验模块与分类是否合法，避免目录越权。"""
    allowed = KB_MODULE_CATEGORIES.get(module)
    if allowed is None:
        raise ValueError(f"未知模块：{module}")
    if category not in allowed:
        raise ValueError(f"模块 {module} 下无分类：{category}")


def _category_dir(module: str, category: str) -> Path:
    """返回某模块某分类的物理目录，并确保存在。"""
    _validate_module_category(module, category)
    target = KNOWLEDGE_DIR / module / category
    target.mkdir(parents=True, exist_ok=True)
    return target


def _index_path(module: str, category: str) -> Path:
    """返回该分类的 index.json 路径。"""
    return _category_dir(module, category) / "index.json"


def _safe_folder_path(path: str) -> str:
    """把外部传入的 folder 路径标准化为安全的相对路径。

    规则：
    - 允许空串 ""，表示根目录
    - 用 / 分隔，禁止 \\、绝对路径前缀、.. 段
    - 每段必须匹配 _FOLDER_SEG_RE
    - 总深度不得超过 MAX_FOLDER_DEPTH
    返回值是规整后的字符串（无前后斜杠），不会包含连续斜杠。
    """
    if path is None:
        return ""
    raw = str(path).strip()
    if not raw:
        return ""
    raw = raw.replace("\\", "/").strip("/")
    segs = [s for s in raw.split("/") if s]
    if not segs:
        return ""
    if len(segs) > MAX_FOLDER_DEPTH:
        raise ValueError(
            f"文件夹层级过深（最多 {MAX_FOLDER_DEPTH} 级，收到 {len(segs)} 级）"
        )
    for s in segs:
        if s in {".", ".."}:
            raise ValueError(f"文件夹名包含非法段：{s}")
        if not _FOLDER_SEG_RE.match(s):
            raise ValueError(f"文件夹名含非法字符：{s}")
    return "/".join(segs)


def _read_raw_index(module: str, category: str) -> dict:
    """读取 index.json 原始 dict；不存在或损坏时返回空骨架。

    兼容 v1.0 老格式（数组）：自动升级为 {"items": [...], "folders": []}。
    """
    path = _index_path(module, category)
    if not path.exists():
        return {"items": [], "folders": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # 索引损坏：回退为空骨架，避免阻塞整个模块查询
        return {"items": [], "folders": []}
    if isinstance(raw, list):
        # v1.0：纯 item 数组 → 升级骨架（不写盘，等下次写入再持久化）
        return {"items": raw, "folders": []}
    if not isinstance(raw, dict):
        return {"items": [], "folders": []}
    raw.setdefault("items", [])
    raw.setdefault("folders", [])
    return raw


# ---- 磁盘 → index 同步 ----------------------------------------------------

# 缓存：避免每次列表请求都全量扫盘。键是 (module, category)，
# 值是上次同步时分类根目录递归扫描得到的"指纹"——只要任意子文件 mtime 改了就会失效
_sync_cache: dict[Tuple[str, str], int] = {}


def _disk_signature(category_dir: Path) -> int:
    """对分类目录做一次轻量"指纹"：递归累加所有文件夹/文件的 mtime。

    这是为了让 _sync_with_disk 自己缓存，避免每次列表都重新扫描；
    用户手动拖入新目录或新文件后，dir 的 mtime 会变，指纹随即失效。
    """
    sig = 0
    if not category_dir.exists():
        return sig
    # 用 walk 比逐 stat 快很多；name 集合先过一遍忽略列表减少访问开销
    for root, dirs, files in os.walk(category_dir):
        # in-place 修剪 dirs 让 walk 跳过隐藏 / 缓存目录
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in _SYNC_IGNORE_DIRS]
        try:
            sig ^= int(Path(root).stat().st_mtime_ns)
        except OSError:
            pass
        for f in files:
            if f.startswith(".") or f in _SYNC_IGNORE_NAMES:
                continue
            try:
                sig ^= int((Path(root) / f).stat().st_mtime_ns)
            except OSError:
                pass
    return sig


def _scan_disk(module: str, category: str) -> Tuple[List[KbFolder], List[KbItem]]:
    """递归扫描分类目录，得到 (folders, items)。

    - folders：按 path 排序；超过 MAX_FOLDER_DEPTH 的子目录跳过并 log 警告
    - items  ：每份非忽略文件一条；id 提取规则：
        * <32 hex>__<rest> → 取 hex 作为 id（service 自己上传的文件）
        * 否则 → md5(folder + '/' + filename) 作为稳定 id（用户手动拖入）
    时间戳一律取自 stat（mtime / ctime）。
    """
    base = _category_dir(module, category)
    folders: List[KbFolder] = []
    items: List[KbItem] = []

    for root, dirs, files in os.walk(base):
        # 修剪掉隐藏 / 缓存子目录
        dirs[:] = [
            d for d in sorted(dirs)
            if not d.startswith(".") and d not in _SYNC_IGNORE_DIRS
        ]

        rel_root = Path(root).relative_to(base)
        rel_str = "" if str(rel_root) == "." else rel_root.as_posix()

        # 1) folder 元信息：rel_str 非空时即为一个 folder
        if rel_str:
            depth = rel_str.count("/") + 1
            if depth > MAX_FOLDER_DEPTH:
                # 超深目录：从 walk 里跳过，避免继续往下递归
                logger.warning(
                    "kb sync: skip deep folder (>%d levels): %s/%s/%s",
                    MAX_FOLDER_DEPTH, module, category, rel_str,
                )
                dirs[:] = []
                continue

            # 段名校验：不合法不影响展示，仅记录到 log，folder 仍纳入
            for seg in rel_str.split("/"):
                if not _FOLDER_SEG_RE.match(seg):
                    logger.warning(
                        "kb sync: folder segment with non-allowed chars: %s/%s/%s",
                        module, category, rel_str,
                    )
                    break

            try:
                stat = Path(root).stat()
                mtime = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
                ctime = datetime.fromtimestamp(stat.st_ctime).astimezone().isoformat(timespec="seconds")
            except OSError:
                mtime = ctime = _now_iso()

            folders.append(
                KbFolder(
                    path=rel_str,
                    name=rel_str.split("/")[-1],
                    desc="",
                    created_at=ctime,
                    updated_at=mtime,
                )
            )

        # 2) file → KbItem
        for fn in sorted(files):
            if fn.startswith(".") or fn in _SYNC_IGNORE_NAMES:
                continue

            full = Path(root) / fn
            m = _STORED_NAME_RE.match(fn)
            if m:
                item_id = m.group(1).lower()
                stored_name = fn
                origin_filename = m.group(2)
            else:
                # 手动拖进来的文件：用 (folder, filename) 做稳定 hash
                key = f"{rel_str}/{fn}" if rel_str else fn
                item_id = hashlib.md5(key.encode("utf-8")).hexdigest()
                stored_name = fn
                origin_filename = fn

            try:
                stat = full.stat()
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
                ctime = datetime.fromtimestamp(stat.st_ctime).astimezone().isoformat(timespec="seconds")
            except OSError:
                size = 0
                mtime = ctime = _now_iso()

            ct = mimetypes.guess_type(origin_filename)[0] or ""

            items.append(
                KbItem(
                    id=item_id,
                    module=module,
                    category=category,
                    folder=rel_str,
                    title=_stem(origin_filename),
                    tags=[],
                    summary="",
                    filename=origin_filename,
                    stored_name=stored_name,
                    size=size,
                    content_type=ct,
                    created_at=ctime,
                    updated_at=mtime,
                )
            )

    folders.sort(key=lambda f: f.path)
    return folders, items


def _sync_with_disk(module: str, category: str) -> None:
    """把磁盘真实情况合并进 index.json。

    合并规则：以磁盘为准（folder/file 是否存在），元数据以 index 为准（title/desc/tags/summary）。
    扫盘有缓存，只在指纹变化时才重新扫。
    """
    _validate_module_category(module, category)
    cat_dir = _category_dir(module, category)

    sig = _disk_signature(cat_dir)
    cache_key = (module, category)
    if _sync_cache.get(cache_key) == sig:
        return

    disk_folders, disk_items = _scan_disk(module, category)

    raw = _read_raw_index(module, category)
    indexed_items: List[dict] = list(raw.get("items") or [])
    indexed_folders: List[dict] = list(raw.get("folders") or [])

    # 1) 合并 folders：以磁盘 set 为准；保留 index 里已有的 desc 等元数据
    indexed_by_path = {f["path"]: f for f in indexed_folders if isinstance(f, dict)}
    merged_folders: List[KbFolder] = []
    for f in disk_folders:
        prev = indexed_by_path.get(f.path)
        if prev:
            merged_folders.append(
                KbFolder(
                    path=f.path,
                    name=f.name,
                    desc=str(prev.get("desc", "") or ""),
                    created_at=str(prev.get("created_at", f.created_at)),
                    updated_at=f.updated_at,
                )
            )
        else:
            merged_folders.append(f)

    # 2) 合并 items：磁盘上现存的文件，能在 index 里按 (folder, stored_name) 命中
    #    就保留原有 title/tags/summary；否则用扫盘出来的默认值。
    indexed_by_key = {}
    for it in indexed_items:
        if not isinstance(it, dict):
            continue
        key = (it.get("folder", ""), it.get("stored_name", ""))
        indexed_by_key[key] = it

    merged_items: List[KbItem] = []
    for it in disk_items:
        prev = indexed_by_key.get((it.folder, it.stored_name))
        if prev:
            # 业务字段保留 index；物理字段（size/mtime/path）以磁盘为准
            merged_items.append(
                KbItem(
                    id=str(prev.get("id", it.id)),
                    module=module,
                    category=category,
                    folder=it.folder,
                    title=str(prev.get("title", it.title) or it.title),
                    tags=list(prev.get("tags") or []),
                    summary=str(prev.get("summary", "") or ""),
                    filename=it.filename,
                    stored_name=it.stored_name,
                    size=it.size,
                    content_type=str(prev.get("content_type") or it.content_type),
                    created_at=str(prev.get("created_at", it.created_at)),
                    updated_at=it.updated_at,
                )
            )
        else:
            merged_items.append(it)

    _write_index(module, category, merged_items, merged_folders)
    _sync_cache[cache_key] = sig


def _read_index(module: str, category: str) -> List[KbItem]:
    """读取 KbItem 列表（缺 folder 字段时默认根目录）。

    读之前先做一次磁盘同步，确保用户手动拖入的文件 / 文件夹也能被识别。
    """
    _sync_with_disk(module, category)
    raw = _read_raw_index(module, category)
    items: List[KbItem] = []
    for it in raw["items"] or []:
        if isinstance(it, dict) and "folder" not in it:
            it["folder"] = ""
        items.append(KbItem.model_validate(it))
    return items


def _read_folders(module: str, category: str) -> List[KbFolder]:
    """读取该分类下的 KbFolder 列表。同样会先做磁盘同步。"""
    _sync_with_disk(module, category)
    raw = _read_raw_index(module, category)
    return [KbFolder.model_validate(f) for f in (raw["folders"] or [])]


def _write_index(
    module: str,
    category: str,
    items: List[KbItem],
    folders: List[KbFolder],
) -> None:
    """把内存中的条目 + 文件夹一并写回 index.json。"""
    path = _index_path(module, category)
    payload = {
        "items": [it.model_dump() for it in items],
        "folders": [f.model_dump() for f in folders],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _safe_filename(name: str) -> str:
    """把上传文件名清洗成相对安全的形式，去掉路径分隔符等危险字符。

    只保留：中英文、数字、下划线、点、连字符、空格。其余替换为下划线。
    """
    # 取 basename 防止用户传 ../foo
    name = os.path.basename(name or "").strip()
    if not name:
        return "untitled"
    return re.sub(r"[^0-9A-Za-z_.\-一-龥 ]+", "_", name)


def _stem(filename: str) -> str:
    """取文件名（不含扩展名）作为默认标题。"""
    base = os.path.basename(filename)
    stem, _ext = os.path.splitext(base)
    return stem or base


def _resolved_file_path(module: str, category: str, item: KbItem) -> Path:
    """根据 item 的 folder + stored_name 算出实际物理路径。"""
    base = _category_dir(module, category)
    if item.folder:
        return base / item.folder / item.stored_name
    return base / item.stored_name


# ---- 对外接口：条目 -------------------------------------------------------

def list_items(
    module: Optional[str] = None,
    category: Optional[str] = None,
    folder: Optional[str] = None,
) -> List[KbItem]:
    """列出条目。
    - 不传参：返回所有模块所有分类的全部条目
    - 仅传 module：返回该模块下全部分类的条目
    - 同时传 module + category：返回单个分类
    - folder：可选过滤；不传等同 None（所有文件夹），传 "" 表示仅根目录，
      传 "design/character" 表示仅该 folder 直属（不递归子文件夹）
    """
    results: List[KbItem] = []
    if module is None:
        modules_to_scan = list(KB_MODULE_CATEGORIES.keys())
    else:
        if module not in KB_MODULE_CATEGORIES:
            raise ValueError(f"未知模块：{module}")
        modules_to_scan = [module]

    # folder 过滤前先做合法性校验
    folder_filter: Optional[str]
    if folder is None:
        folder_filter = None
    else:
        folder_filter = _safe_folder_path(folder)

    for m in modules_to_scan:
        cats = KB_MODULE_CATEGORIES[m]
        if category is not None:
            if category not in cats:
                raise ValueError(f"模块 {m} 下无分类：{category}")
            cats = [category]
        for c in cats:
            for it in _read_index(m, c):
                if folder_filter is not None and it.folder != folder_filter:
                    continue
                results.append(it)

    # 按更新时间倒序，最近上传的排前面
    results.sort(key=lambda it: it.updated_at, reverse=True)
    return results


def get_item(module: str, category: str, item_id: str) -> Optional[KbItem]:
    """获取单条元信息，找不到返回 None。"""
    for it in _read_index(module, category):
        if it.id == item_id:
            return it
    return None


def get_raw_path(module: str, category: str, item_id: str) -> Optional[Path]:
    """返回原始物料文件的物理路径，找不到则 None。"""
    item = get_item(module, category, item_id)
    if item is None:
        return None
    path = _resolved_file_path(module, category, item)
    return path if path.exists() else None


def create_item(
    module: str,
    category: str,
    *,
    filename: str,
    file_bytes: bytes,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    summary: str = "",
    content_type: str = "",
    folder: str = "",
) -> KbItem:
    """新增条目：落盘原始文件 + 写入 index.json。

    folder 可选（默认根目录）；若指定则必须先用 create_folder 注册过，
    避免出现"实际有文件但 folders 列表里没记录"的悬挂状态。
    """
    _validate_module_category(module, category)

    folder_path = _safe_folder_path(folder)
    if folder_path:
        # folder 不强制要求预登记：缺哪级就建哪级，并把元信息补进 index。
        # 这样上传表单选择 folder 的流程不会因为索引上没有它而失败。
        existing_folders = _read_folders(module, category)
        existing_paths = {f.path for f in existing_folders}
        new_segments: List[KbFolder] = []
        now = _now_iso()
        accum = ""
        for seg in folder_path.split("/"):
            accum = f"{accum}/{seg}" if accum else seg
            if accum in existing_paths:
                continue
            (_category_dir(module, category) / accum).mkdir(parents=True, exist_ok=True)
            new_segments.append(
                KbFolder(
                    path=accum,
                    name=seg,
                    desc="",
                    created_at=now,
                    updated_at=now,
                )
            )
            existing_paths.add(accum)
        if new_segments:
            _write_index(
                module,
                category,
                _read_index(module, category),
                existing_folders + new_segments,
            )

    safe_name = _safe_filename(filename)
    item_id = uuid.uuid4().hex
    stored_name = f"{item_id}__{safe_name}"

    target_dir = _category_dir(module, category)
    if folder_path:
        target_dir = target_dir / folder_path
        target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / stored_name
    # 写文件：用二进制模式直接落盘
    target_path.write_bytes(file_bytes)

    # 上传方未带 content_type 时，按扩展名兜底；
    # 这一步对 PNG/JPG/MP4 等很关键，否则浏览器拿到 octet-stream 不会内联渲染
    final_ct = content_type or mimetypes.guess_type(safe_name)[0] or ""

    now = _now_iso()
    item = KbItem(
        id=item_id,
        module=module,
        category=category,
        folder=folder_path,
        title=(title or _stem(safe_name)).strip() or _stem(safe_name),
        tags=tags or [],
        summary=summary or "",
        filename=safe_name,
        stored_name=stored_name,
        size=len(file_bytes),
        content_type=final_ct,
        created_at=now,
        updated_at=now,
    )

    items = _read_index(module, category)
    folders = _read_folders(module, category)
    items.append(item)
    _write_index(module, category, items, folders)
    return item


def delete_item(module: str, category: str, item_id: str) -> bool:
    """删除条目：先删物理文件再更新索引；找不到返回 False。"""
    items = _read_index(module, category)
    folders = _read_folders(module, category)
    target = next((it for it in items if it.id == item_id), None)
    if target is None:
        return False

    # 先尝试删物理文件，删不掉时不阻塞索引清理（可能文件已被外部清理）
    file_path = _resolved_file_path(module, category, target)
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            # 删除失败仅记录到日志层（此处暂不引入 logger，保持简单）
            pass

    new_items = [it for it in items if it.id != item_id]
    _write_index(module, category, new_items, folders)
    return True


# ---- 对外接口：文件夹 -----------------------------------------------------

def list_folders(module: str, category: str) -> List[KbFolder]:
    """列出某分类下所有已登记的文件夹（按 path 字典序）。"""
    _validate_module_category(module, category)
    folders = _read_folders(module, category)
    folders.sort(key=lambda f: f.path)
    return folders


def create_folder(
    module: str,
    category: str,
    *,
    path: str,
    desc: str = "",
) -> KbFolder:
    """登记一个文件夹。父级必须已存在（除非本次创建的是顶层目录）。

    路径规则见 _safe_folder_path：仅允许 [A-Za-z0-9_.\\- 中文]，每段 ≤64 字符，
    最多 4 级深度。重名直接 400。
    """
    _validate_module_category(module, category)
    folder_path = _safe_folder_path(path)
    if not folder_path:
        raise ValueError("文件夹路径不能为空")

    folders = _read_folders(module, category)
    existing_paths = {f.path for f in folders}
    if folder_path in existing_paths:
        raise ValueError(f"文件夹已存在：{folder_path}")

    # 父级若非根，必须已注册
    parent_segs = folder_path.split("/")[:-1]
    if parent_segs:
        parent_path = "/".join(parent_segs)
        if parent_path not in existing_paths:
            raise ValueError(f"上级文件夹不存在：{parent_path}")

    # 物理目录提前建好，便于上传时直接落盘
    (_category_dir(module, category) / folder_path).mkdir(parents=True, exist_ok=True)

    now = _now_iso()
    leaf = folder_path.split("/")[-1]
    folder = KbFolder(path=folder_path, name=leaf, desc=desc or "", created_at=now, updated_at=now)
    folders.append(folder)
    _write_index(module, category, _read_index(module, category), folders)
    return folder


def delete_folder(module: str, category: str, *, path: str) -> bool:
    """删除文件夹（递归）。

    会同时删除该文件夹下所有后代子文件夹与文件——前端在调用前已做二次确认，
    这里不再因为"非空"而拒绝，避免用户为了删一个嵌套目录要先一层层手动清空。
    """
    _validate_module_category(module, category)
    folder_path = _safe_folder_path(path)
    if not folder_path:
        raise ValueError("文件夹路径不能为空")

    folders = _read_folders(module, category)
    target = next((f for f in folders if f.path == folder_path), None)
    if target is None:
        return False

    # 计算"待清理"前缀：folder_path 本身 + 任何以 "folder_path/" 开头的后代
    prefix = folder_path + "/"

    def _under_target(p: str) -> bool:
        return p == folder_path or p.startswith(prefix)

    # 1) 物理目录：rmtree 一并清掉文件夹下所有文件 + 子目录（不存在则跳过）
    fs_dir = _category_dir(module, category) / folder_path
    if fs_dir.exists():
        # ignore_errors=True：Windows 下偶发的"文件被占用"也不阻断索引清理
        shutil.rmtree(fs_dir, ignore_errors=True)

    # 2) 索引：剔除该文件夹及其后代登记的 folders 和 items
    items = _read_index(module, category)
    new_folders = [f for f in folders if not _under_target(f.path)]
    new_items = [it for it in items if not _under_target(it.folder)]

    _write_index(module, category, new_items, new_folders)
    return True


# ---- 对外接口：批量读取（供 kb_context.resolve_kb 用）---------------------

def list_items_under_folder(
    module: str,
    category: str,
    folder: str,
) -> List[KbItem]:
    """递归列出某 folder 下所有文件（含子文件夹中的文件）。

    folder == "" 视为分类根目录（递归整个分类），与"选根目录"语义一致。
    返回按 (folder, updated_at) 排序，便于提示词阅读。
    """
    _validate_module_category(module, category)
    folder_path = _safe_folder_path(folder)
    items = _read_index(module, category)
    out: List[KbItem] = []
    prefix = folder_path + "/" if folder_path else ""
    for it in items:
        if folder_path == "":
            out.append(it)
        elif it.folder == folder_path or it.folder.startswith(prefix):
            out.append(it)
    out.sort(key=lambda it: (it.folder, it.updated_at))
    return out


def get_folder(module: str, category: str, path: str) -> Optional[KbFolder]:
    """按 path 取单个 folder 元信息，找不到返回 None。"""
    folder_path = _safe_folder_path(path)
    if not folder_path:
        return None
    for f in _read_folders(module, category):
        if f.path == folder_path:
            return f
    return None
