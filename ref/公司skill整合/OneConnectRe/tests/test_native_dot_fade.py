import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_gameplay_layout_candidate import enable_native_dot_fade

data = json.loads((ROOT / 'game' / 'data.js').read_text(encoding='utf-8'))
before = copy.deepcopy(data)
enable_native_dot_fade(data)
instance = next(inst for layout in data['project'][5] for layer in layout[6]
                for inst in layer[14] if inst[1:3] == [7, 39])
assert instance[4][0] == [1, 0, 0, .25, 1]
instance[4][0][0] = 0
assert data == before, 'only the native fade activation may change'
instance[4][0][3] = .5
try:
    enable_native_dot_fade(data)
except ValueError:
    pass
else:
    raise AssertionError('changed native behavior must not be patched silently')
print('native removal dot patch is narrow and rejects unexpected defaults PASS')
