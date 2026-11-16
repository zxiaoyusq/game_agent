"""Verify the native event ancestry used to reason about gravity timing."""
import json
import re
import sys
from pathlib import Path

game = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('game')
project = json.loads((game / 'data.js').read_text(encoding='utf-8'))
runtime = (game / 'c2runtime.js').read_text(encoding='utf-8')
table = re.search(r'getObjectRefTable\s*=\s*function\s*\(\s*\)\s*\{\s*return\s*\[([^\]]+)\]', runtime)
assert table, 'Construct object reference table missing'
refs = [item.strip() for item in table.group(1).split(',')]
assert refs[31] == 'cr.plugins_.Sprite.prototype.acts.Destroy'
assert refs[99] == 'cr.behaviors.lunarray_LiteTween.prototype.cnds.OnEnd'

found = []
def walk(node, parents):
    if isinstance(node, dict):
        for child in node.values(): walk(child, parents)
    elif isinstance(node, list):
        if len(node) >= 7 and node[0] == 0 and isinstance(node[5], list) and isinstance(node[6], list):
            parents = parents + [node]
            if node[4] == 418432007757224: found.append(parents)
        for child in node: walk(child, parents)
walk(project, [])
assert len(found) == 1
parent, score = found[0][-2:]
assert parent[4] == 153030474989047
assert any(c[0] == 5 and c[1] == 99 for c in parent[5]), 'parent must be tile tween end'
assert any(a[0] == 5 and a[1] == 31 and a[3] == 757250555646969 for a in parent[6]), 'tile destroy must be a parent action'
assert any(a[3] == 196425296963217 for a in score[6]), 'match hook must be in the child event'
print('native tile destroy is a parent action before the score child event: PASS')
