import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from prepare_gameplay_layout_candidate import apply_verified_visual_images

project = Path(__file__).resolve().parents[1]
report = json.loads((project / 'analysis/_v228_visual_compression_report.json').read_text(encoding='utf8'))
record = next(x for x in report if Path(x['path']).name == 'ui-tool-slot.webp')
reference = Path(record['path']).parent
optimized = Path(record['out']).parent
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'images').mkdir()
    target = root / 'images/ui-tool-slot.webp'
    shutil.copyfile(record['path'], target)
    report_file = root / 'report.json'
    report_file.write_text(json.dumps([record]), encoding='utf8')
    assert apply_verified_visual_images(root, optimized, report_file, reference) == 1
    assert target.read_bytes() == Path(record['out']).read_bytes()
    shutil.copyfile(record['path'], target)
    changed = dict(record, after=record['after'] + 1)
    report_file.write_text(json.dumps([changed]), encoding='utf8')
    assert apply_verified_visual_images(root, optimized, report_file, reference) == 0
    assert target.read_bytes() == Path(record['path']).read_bytes()
    changed = dict(record, path=str(reference / 'unrelated.webp'))
    report_file.write_text(json.dumps([changed]), encoding='utf8')
    assert apply_verified_visual_images(root, optimized, report_file, reference) == 0
print('visual compression requires the reported original and output: PASS')
