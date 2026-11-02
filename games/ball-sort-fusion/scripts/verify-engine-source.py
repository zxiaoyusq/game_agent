"""比较已通过归档哈希校验的官方源码与实际构建目录；仅跳过明确替换的依赖锁。"""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

archive_path = Path(sys.argv[1])
engine_path = Path(sys.argv[2]).resolve()
checked = 0
mismatches = []
with tarfile.open(archive_path, "r:gz") as archive:
    for member in archive:
        if not member.isfile():
            continue
        relative = Path(*Path(member.name).parts[1:])
        if str(relative) == "package-lock.json":
            continue
        target = engine_path / relative
        expected = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        checked += 1
        if expected != actual:
            mismatches.append(str(relative))
print(json.dumps({"matched": not mismatches, "checkedFiles": checked, "mismatches": mismatches[:30], "excluded": ["package-lock.json"]}))
