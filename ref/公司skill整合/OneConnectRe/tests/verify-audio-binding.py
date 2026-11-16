"""Verify the exported C2 event table connects sound state to Audio.SetSilent."""
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
runtime = (root / 'c2runtime.js').read_text(encoding='utf8')
match = re.search(r'cr\.getObjectRefTable=function\(\)\{return\[(.*?)\]\}', runtime)
assert match, 'C2 object reference table missing'
refs = match.group(1).split(',')
project = json.loads((root / 'data.js').read_text(encoding='utf8'))['project']
assert refs[project[3][20][1]] == 'cr.plugins_.Audio'
assert refs[120] == 'cr.plugins_.Audio.prototype.acts.SetSilent'
assert refs[project[3][4][1]] == 'cr.plugins_.Function'
assert refs[28] == 'cr.plugins_.Function.prototype.cnds.OnFunction'
bindings = set()
volume_bindings = set()


def visit(value, in_volume=False):
    if isinstance(value, list):
        if len(value) >= 7 and value[0] == 0 and isinstance(value[5], list) and isinstance(value[6], list):
            in_volume = in_volume or any(isinstance(c, list) and len(c) >= 10 and c[:2] == [4, 28] and c[9] == [[1, [2, 'volumeChanged']]] for c in value[5])
            for condition in value[5]:
                if not isinstance(condition, list) or len(condition) < 10:
                    continue
                parameters = condition[9]
                for sound_value in (0, 1):
                    if parameters == [[11, 'sound'], [8, 0], [7, [0, sound_value]]]:
                        for action in value[6]:
                            if isinstance(action, list) and len(action) >= 6 and action[:2] == [20, 120]:
                                pair = (sound_value, action[5][0][1])
                                bindings.add(pair)
                                if in_volume:
                                    volume_bindings.add(pair)
        for item in value:
            visit(item, in_volume)
    elif isinstance(value, dict):
        for item in value.values():
            visit(item, in_volume)


visit(project[6])
assert {(1, 0), (0, 1)} <= bindings, bindings
assert {(1, 0), (0, 1)} <= volume_bindings, volume_bindings
print('C2 sound state binds to Audio.SetSilent:', sorted(bindings))
