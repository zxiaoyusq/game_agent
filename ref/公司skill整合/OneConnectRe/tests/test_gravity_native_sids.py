"""Verify the only native calls suppressed by the candidate gravity adapter."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from prepare_gameplay_layout_candidate import verify_gravity_native_actions

game = Path(sys.argv[1])
project = json.loads((game / 'data.js').read_text(encoding='utf8'))
expected = {
    430431574539661: [(155796769104064, 'fall'), (491047488641600, 'fall')],
    618231579992059: [(657297107410907, 'move'), (422821596409828, 'move')],
}
found = {}
def walk(node, ancestors):
    if isinstance(node, dict):
        for item in node.values(): walk(item, ancestors)
    elif isinstance(node, list):
        if len(node) >= 7 and node[0] == 0 and isinstance(node[5], list) and isinstance(node[6], list):
            ancestors = ancestors + [node[4]]
            if node[4] in expected:
                assert node[4] not in found, 'duplicate event ID'
                assert 418432007757224 in ancestors, 'movement must be a descendant of the match event'
                found[node[4]] = [(a[3], a[5][0][1][1]) for a in node[6]]
        for item in node: walk(item, ancestors)
walk(project, [])
assert found == expected, (found, expected)
verify_gravity_native_actions(project)
def find_action(node):
    if isinstance(node, list):
        if len(node) >= 7 and node[0] == 0 and node[4] == 430431574539661: return node[6][0]
        for child in node:
            result = find_action(child)
            if result is not None: return result
    elif isinstance(node, dict):
        for child in node.values():
            result = find_action(child)
            if result is not None: return result
    return None
action = find_action(project)
assert action is not None
original_type = action[0]
action[0] = 99
try: verify_gravity_native_actions(project)
except ValueError: pass
else: raise AssertionError('builder must reject a changed native action type')
action[0] = original_type
def alter(node):
    if isinstance(node, list):
        if len(node) >= 7 and node[0] == 0 and node[4] == 430431574539661:
            node[6][0][5][0][1][1] = 'different_function'
            return True
        return any(alter(child) for child in node)
    if isinstance(node, dict): return any(alter(child) for child in node.values())
    return False
assert alter(project)
try: verify_gravity_native_actions(project)
except ValueError: pass
else: raise AssertionError('builder must reject a changed native movement action')
print('native movement action IDs, function names and match ancestry verified: PASS')
