"""Compare two generated candidates and check only converted texture weights changed."""
import json
import sys
from pathlib import Path

old, new = map(Path, sys.argv[1:3])
a = json.loads((old / 'data.js').read_text(encoding='utf8'))
b = json.loads((new / 'data.js').read_text(encoding='utf8'))
converted = set(json.loads((new / 'asset-formats.json').read_text(encoding='utf8')).values())
counts = {'entries': 0, 'changes': 0}


def check(x, y):
    assert type(x) is type(y)
    if isinstance(x, list):
        assert len(x) == len(y)
        is_texture = len(y) >= 2 and isinstance(y[0], str) and y[0] in converted and type(y[1]) is int
        if is_texture:
            assert x[0] == y[0]
            assert y[1] == (new / y[0]).stat().st_size
            counts['entries'] += 1
            counts['changes'] += x[1] != y[1]
        for index, (left, right) in enumerate(zip(x, y)):
            if not (is_texture and index == 1):
                check(left, right)
    elif isinstance(x, dict):
        assert x.keys() == y.keys()
        for key in x:
            check(x[key], y[key])
    else:
        assert x == y


check(a, b)
assert counts['entries'] and counts['changes'], counts
print('converted texture metadata verified:', counts)
