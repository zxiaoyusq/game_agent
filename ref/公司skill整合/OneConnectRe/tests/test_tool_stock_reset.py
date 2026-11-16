"""Identify the native reset actions before designing persistent inventory migration."""
import json
import sys
from pathlib import Path

project = json.loads((Path(sys.argv[1]) / 'data.js').read_text(encoding='utf8'))
events = []
def walk(node):
    if isinstance(node, dict):
        for child in node.values(): walk(child)
    elif isinstance(node, list):
        if len(node) >= 7 and node[0] == 0 and node[4] == 914931905554985:
            events.append(node)
        for child in node: walk(child)
walk(project)
assert len(events) == 1
actions = {a[3]: a for a in events[0][6]}
assert actions[838575124468232][5] == [[11, 'tip'], [7, [0, 3]]]
assert actions[161379909006886][5] == [[11, 'shuffle'], [7, [0, 5]]]
print('candidate native layout-start includes tip=3 and shuffle=5 reset actions: PASS')
