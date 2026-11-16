import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
runtime = (root / 'c2runtime.js').read_text(encoding='utf8')
refs = re.search(r'cr\.getObjectRefTable=function\(\)\{return\[(.*?)\]\}', runtime).group(1).split(',')
assert refs[86] == 'cr.plugins_.Touch.prototype.cnds.OnTouchObject'
project = json.loads((root / 'data.js').read_text(encoding='utf8'))['project']
assert project[3][21][0] == 't21' and 'images/pause-sheet0.webp' in str(project[3][21])
found = []
def visit(node):
    if isinstance(node, list):
        if len(node) >= 7 and node[0] == 0 and isinstance(node[5], list) and isinstance(node[6], list):
            if any(isinstance(c, list) and len(c) >= 10 and c[:2] == [6, 86] and c[9] == [[4, 21]] for c in node[5]):
                found.append(node[6])
        for item in node:
            visit(item)
    elif isinstance(node, dict):
        for item in node.values():
            visit(item)
visit(project[6])
assert found and any(action for actions in found for action in actions if isinstance(action, list) and action and action[0] == -1)
print('C2 t21 pause sprite has an OnTouchObject event PASS')
