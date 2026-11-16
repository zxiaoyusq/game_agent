import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('status', root / 'tools/dsh_status_compact.py')
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)

with tempfile.TemporaryDirectory() as directory:
    status.HANDOFF = Path(directory)
    status.REVIEWED = status.HANDOFF / 'reviewed.json'

    def inspect(command, **kwargs):
        name = next(name for name, session in status.SESSIONS.items() if session in command)
        path = Path(command[command.index('--out') + 1])
        path.write_text(json.dumps({'sessionId': status.SESSIONS[name],
                                    'publicMessages': [{'seq': 42, 'text': 'new result'}]}), encoding='utf-8')
        return SimpleNamespace(returncode=0)

    def run(*args):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['status', *args]), contextlib.redirect_stdout(output):
            result = status.main()
        return result, [json.loads(line) for line in output.getvalue().splitlines()]

    with patch.object(status.subprocess, 'run', side_effect=inspect):
        for _ in range(2):
            result, lines = run()
            assert result == 0 and all(line['new_message'] for line in lines)
            assert all('message' not in line for line in lines)
        assert all(line['message'] == 'new result' for line in run('--full')[1])
        assert run('--ack', 'reverse', '--seq', '41')[0] == 1
        result, lines = run('--session', 'art', '--unread')
        assert result == 0 and len(lines) == 1 and lines[0]['session'] == 'art'
        assert lines[0]['unread'][0]['seq'] == 42
        assert not lines[0]['unread_may_be_truncated']
        assert (status.HANDOFF / 'art-unread.json').exists()
        assert run('--ack', 'reverse', '--seq', '42')[0] == 0
        result, lines = run()
        assert result == 0 and not lines[0]['new_message'] and lines[1]['new_message']
        assert run('--ack', 'reverse', '--seq', '41')[0] == 1

print('DSH unread messages persist until explicit matching review: PASS')
