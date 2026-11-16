"""Safely restore one art-integration backup; dry run unless --execute is set."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def checked(root, relative):
    value = Path(relative)
    if value.is_absolute() or '..' in value.parts or not value.parts:
        raise ValueError(f'unsafe relative path: {relative}')
    root = root.resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'path escapes root: {relative}')
    return path


def inspect(game, backup):
    data = json.loads((backup / 'integration_manifest.json').read_text(encoding='utf-8-sig'))
    entries = data['files']
    seen, actions, issues = set(), [], []
    for entry in entries:
        rel = entry['file']
        if rel in seen:
            raise ValueError(f'duplicate path: {rel}')
        seen.add(rel)
        dst, old = checked(game, rel), checked(backup, rel)
        if not dst.is_file() or digest(dst) != entry['candidate_sha256']:
            issues.append(f'current file changed or missing: {rel}')
        previous = entry['previous_sha256']
        if previous and (not old.is_file() or digest(old) != previous):
            issues.append(f'backup file changed or missing: {rel}')
        actions.append((rel, dst, old, previous))
    if not actions:
        raise ValueError('empty manifest')
    return actions, issues


def replace_atomically(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix='.oneconnect-restore-', dir=target.parent)
    os.close(handle)
    try:
        shutil.copyfile(source, name)
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path, required=True)
    parser.add_argument('--backup-dir', type=Path, required=True)
    parser.add_argument('--snapshot-dir', type=Path, help='new directory to preserve current files before execution')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    try:
        actions, issues = inspect(args.game_dir, args.backup_dir)
        for item in issues:
            print('REFUSE:', item)
        if issues:
            return 1
        print(f'Preflight OK: {len(actions)} files; new files to remove: {sum(not x[3] for x in actions)}')
        if not args.execute:
            print('DRY RUN: no files changed')
            return 0
        if not args.snapshot_dir:
            raise ValueError('--snapshot-dir is required with --execute')
        snap = args.snapshot_dir.resolve()
        if snap.exists() or snap.is_relative_to(args.game_dir.resolve()) or snap.is_relative_to(args.backup_dir.resolve()):
            raise ValueError('snapshot must be a new directory outside game and backup')
        snap.mkdir(parents=True)
        for rel, dst, _, _ in actions:
            target = checked(snap, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, target)
            if digest(target) != digest(dst):
                raise OSError(f'snapshot verification failed: {rel}')
        shutil.copy2(args.backup_dir / 'integration_manifest.json', snap / 'integration_manifest.json')
        for rel, dst, old, previous in actions:
            if previous:
                replace_atomically(old, dst)
                if digest(dst) != previous:
                    raise OSError(f'restored hash mismatch: {rel}')
            else:
                dst.unlink()
        print(f'RESTORED {len(actions)} files; prior state preserved: {snap}')
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print('ERROR:', exc)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
