"""Check the unmodified C2 tool instances, without opening the game."""
import json
import math
import sys
from pathlib import Path

game = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('analysis/ui_iteration_candidate_v190/game')
project = json.loads((game / 'data.js').read_text(encoding='utf8'))['project']
assert project[3][26][0] == 't26', 'tool type index changed'
layouts = [layout for layout in project[5] if isinstance(layout, list) and layout and layout[0] == 'game']
assert len(layouts) == 1, 'expected exactly one game layout'
layers = next(part for part in layouts[0] if isinstance(part, list) and part and isinstance(part[0], list) and isinstance(part[0][0], str))
matches = []
for layer in layers:
    if not isinstance(layer, list):
        continue
    for part in layer:
        if not isinstance(part, list) or len(part) != 13:
            continue
        matches.extend(entry for entry in part if isinstance(entry, list) and len(entry) >= 3 and isinstance(entry[0], list) and entry[1] == 26)
assert len(matches) == 2, f'expected two tool instances, got {len(matches)}'
boxes = []
for entry in matches:
    x, y, _, width, height, _, angle, _, hx, hy = entry[0][:10]
    assert math.isclose(angle, 0, abs_tol=1e-9) and width > 0 and height > 0
    boxes.append((x - width * hx, y - height * hy, x + width * (1 - hx), y + height * (1 - hy)))
a, b = boxes
assert a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1], 'native tool bounds overlap'
print('two native tool instances have separated unrotated bounds PASS')
