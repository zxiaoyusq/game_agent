"""构建可直接交付的网页包与完整工程包；同时限制压缩前后均小于10MB。"""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 10_000_000
OUTPUT = ROOT / 'releases'
OUTPUT.mkdir(exist_ok=True)


def package(name: str, files: list[Path], prefix: str, base: Path) -> dict:
    """只打包显式选中的真实文件，不跟随外部符号链接或开发缓存。"""
    if any(path.is_symlink() for path in files):
        raise RuntimeError('交付包不能包含符号链接')
    unpacked = sum(path.stat().st_size for path in files)
    if unpacked > LIMIT:
        raise RuntimeError(f'{name} 展开后超出10MB：{unpacked}')
    target = OUTPUT / name
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            archive.write(path, f'{prefix}/{path.relative_to(base).as_posix()}')
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('压缩包校验失败')
    packed = target.stat().st_size
    if packed > LIMIT:
        raise RuntimeError(f'{name} ZIP超出10MB：{packed}')
    return {'file': name, 'files': len(files), 'uncompressed_bytes': unpacked,
            'zip_bytes': packed, 'limit_bytes': LIMIT,
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}


# 完整工程包含可运行构建、源代码、测试、文档与对照证据；依赖由锁文件重现。
files = [ROOT / name for name in ('README.md', 'index.html', 'package.json', 'package-lock.json', '.gitignore')]
for directory in ('src', 'public', 'scripts', 'tests', 'workflow', 'evidence', 'dist'):
    files.extend(path for path in (ROOT / directory).rglob('*') if path.is_file() and '__pycache__' not in path.parts)
if not (ROOT / 'dist/index.html').is_file():
    raise RuntimeError('请先运行 npm run build')
reports = [
    package('amber-caravan-project.zip', files, 'amber-caravan', ROOT),
    package('amber-caravan-web.zip', [path for path in (ROOT / 'dist').rglob('*') if path.is_file()], 'amber-caravan', ROOT / 'dist'),
]
report = {'packages': reports, 'excluded': ['node_modules（可由package-lock.json安装的开发依赖）', '原始游戏ZIP与旧引擎', '生图PNG母版', '临时缓存与重复发布ZIP']}
(OUTPUT / 'size-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
for result in reports:
    print(f"{result['file']}：ZIP {result['zip_bytes']} 字节，展开 {result['uncompressed_bytes']} 字节，校验通过")
