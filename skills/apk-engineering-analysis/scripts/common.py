"""分析脚本共享的小型文件工具，避免依赖项目后端或固定工作目录。"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

# 可使用隔离的 pip --target 目录；未指定时沿用当前 Python 环境。
package_path = os.environ.get('APK_ANALYSIS_PYTHONPATH')
if package_path:
    sys.path.insert(0, str(Path(package_path).expanduser().resolve()))


def write_json(path, value):
    """保存可阅读的 UTF-8 JSON，并自动建立父目录。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha256(path):
    """流式计算大文件哈希，避免把 APK 或资源包整体载入内存。"""
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(value):
    """名称只用于输出文件，不作为原始对象唯一身份。"""
    return re.sub(r'[^\w.\-]+', '_', str(value))[:90].strip('.') or 'unnamed'


def local_path(root, relative):
    """只允许工作区内相对路径，用于校验清单、引用和打包输入。"""
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError(f'引用越出工作区：{relative}')
    return path
