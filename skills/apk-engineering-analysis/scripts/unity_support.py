"""Unity 输入发现与固定头校正，集中处理格式相关的非显然细节。"""
from pathlib import Path
from common import local_path, read_json


def load_environment(workspace, extra_paths=None):
    """扫描所有分包的 Unity 数据目录及任意层级的 UnityFS/Raw/Web 资源包。"""
    import UnityPy
    summary = read_json(workspace / 'package_summary.json')
    roots = [local_path(workspace, archive['raw_root']) for archive in summary['archives']]
    roots.extend(path for path in (workspace / 'containers').glob('*') if path.is_dir())
    data_dirs = sorted({path for root in roots for path in root.rglob('Data')
                        if path.is_dir() and path.parent.name == 'bin' and path.parent.parent.name == 'assets'})
    environment = UnityPy.load(*map(str, data_dirs))
    loaded = [str(path) for path in data_dirs]
    for root in roots:
        for path in sorted(root.rglob('*')):
            if not path.is_file() or any(path.is_relative_to(folder) for folder in data_dirs):
                continue
            with path.open('rb') as stream:
                header = stream.read(8)
            if header.startswith((b'UnityFS', b'UnityRaw', b'UnityWeb')):
                environment.load_file(str(path))
                loaded.append(str(path))
    for path in extra_paths or []:
        path = Path(path).expanduser().resolve()
        if str(path) not in loaded:
            environment.load_folder(str(path)) if path.is_dir() else environment.load_file(str(path))
            loaded.append(str(path))
    objects = list(environment.objects)
    files = {}
    for obj in objects:
        source = obj.assets_file.name
        if source in files and files[source] is not obj.assets_file:
            raise ValueError(f'多个序列化文件同名，无法安全解析外部引用：{source}；请按资源上下文分别分析')
        files[source] = obj.assets_file
    if not objects:
        raise ValueError('没有读取到 Unity 对象，请检查资产格式、分包或显式提供 --asset-path')
    return environment, objects, files, loaded


def fixed_header(head):
    """固定头按 Unity 内置读取器校正，避免动态类型树导致 m_Script 指针字节错位。"""
    return {'m_Script': {'m_FileID': head.m_Script.m_FileID, 'm_PathID': head.m_Script.m_PathID},
            'm_GameObject': {'m_FileID': head.m_GameObject.m_FileID, 'm_PathID': head.m_GameObject.m_PathID},
            'm_Name': head.m_Name, 'm_Enabled': head.m_Enabled}
