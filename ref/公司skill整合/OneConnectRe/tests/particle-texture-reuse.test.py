import importlib.util
import json
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools'))
spec = importlib.util.spec_from_file_location('candidate_builder', root / 'tools/prepare_gameplay_layout_candidate.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

with tempfile.TemporaryDirectory() as tmp:
    game = Path(tmp)
    images = game / 'images'
    images.mkdir()
    canonical = images / 'shinetitle-sheet0.webp'
    duplicate = images / 'sparkparticle.webp'
    canonical.write_bytes(b'same-texture')
    duplicate.write_bytes(b'not-identical')
    data = game / 'data.js'
    data.write_text('["images/sparkparticle.webp",12]', encoding='utf8')
    formats = game / 'asset-formats.json'
    formats.write_text(json.dumps({'images/sparkparticle.png': 'images/sparkparticle.webp'}), encoding='utf8')
    try:
        builder.reuse_identical_particle_texture(game)
        raise AssertionError('different resources must be rejected')
    except ValueError:
        assert duplicate.exists()
    duplicate.write_bytes(canonical.read_bytes())
    extra = game / 'extra.js'
    extra.write_text('"images/sparkparticle.webp"', encoding='utf8')
    try:
        builder.reuse_identical_particle_texture(game)
        raise AssertionError('unhandled references must be rejected')
    except ValueError:
        assert duplicate.exists() and 'sparkparticle.webp' in data.read_text(encoding='utf8')
    extra.unlink()
    builder.reuse_identical_particle_texture(game)
    assert not duplicate.exists() and canonical.read_bytes() == b'same-texture'
    assert 'images/shinetitle-sheet0.webp' in data.read_text(encoding='utf8')
    assert json.loads(formats.read_text(encoding='utf8'))['images/sparkparticle.png'] == 'images/shinetitle-sheet0.webp'
print('particle texture reuse rejects mismatches and unhandled references PASS')
