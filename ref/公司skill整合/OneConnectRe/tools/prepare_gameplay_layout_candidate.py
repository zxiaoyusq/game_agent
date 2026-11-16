"""Create a new isolated, unverified layout candidate from the current game.

The destination must not exist. This script never opens a browser or touches
localStorage; the user handles gameplay QA separately.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import re
import shutil
from PIL import Image, ImageChops, ImageStat

from build_offline_worker import build
from clean_tile_atlas_gutters import clean as clean_tile_gutters
from build_ramadan_atlas import build as build_ramadan_atlas
from ramadan_animation_candidate import add_ramadan_animation

PROJECT = Path(__file__).resolve().parent.parent

def enable_native_dot_fade(data):
    """Make the original white removal sprite fade and self-destruct on spawn."""
    project = data['project']
    if project[3][7][0] != 't7' or project[3][7][8][0][0] != 'Fade':
        raise ValueError('unexpected native removal effect type')
    matches = [inst for layout in project[5] for layer in layout[6]
               for inst in layer[14] if inst[1] == 7 and inst[2] == 39]
    if len(matches) != 1 or matches[0][4][0] != [0, 0, 0, 0.25, 1]:
        raise ValueError('unexpected native removal fade defaults')
    matches[0][4][0][0] = 1
    return data
ANALYSIS = (PROJECT / 'analysis').resolve()


def verify_gravity_native_actions(project):
    expected = {430431574539661: [(155796769104064, 'fall'), (491047488641600, 'fall')],
                618231579992059: [(657297107410907, 'move'), (422821596409828, 'move')]}
    found = {}
    def walk(node, ancestors):
        if isinstance(node, dict):
            for child in node.values(): walk(child, ancestors)
        elif isinstance(node, list):
            if len(node) >= 7 and node[0] == 0 and isinstance(node[5], list) and isinstance(node[6], list):
                ancestors = ancestors + [node[4]]
                if node[4] in expected:
                    if node[4] in found or 418432007757224 not in ancestors:
                        raise ValueError('unexpected native gravity action ancestry')
                    try:
                        found[node[4]] = [(a[3], a[5][0][1][1]) for a in node[6]]
                        if any(a[0] != 4 or a[1] != 34 for a in node[6]):
                            raise ValueError('native gravity action is not a Function call')
                    except (IndexError, TypeError) as error: raise ValueError('invalid native gravity action') from error
            for child in node: walk(child, ancestors)
    walk(project, [])
    if found != expected: raise ValueError('native gravity action IDs or function names changed')


def replace_once(text, before, after, label):
    if text.count(before) != 1:
        raise ValueError(f'unexpected {label} structure')
    return text.replace(before, after, 1)


def validate_candidate_pool(pool, entry, frames):
    if len(frames) not in (3, 4) or any(not isinstance(x, int) or x < 1 for x in frames):
        raise ValueError('unexpected tile animations')
    generator = entry.get('generator')
    if not generator:
        raise ValueError('pool requires a generated board')
    capacity = min(frames[:3])
    if entry.get('theme') == 3:
        capacity = min(capacity, 20, frames[3] if len(frames) == 4 else 20)
    if (not isinstance(pool, list) or len(pool) < generator['typeCount'] or len(pool) > 30 or
        any(type(value) is not int or value < 1 or value > capacity for value in pool) or len(set(pool)) != len(pool)):
        raise ValueError('invalid or unavailable pool')


def verify_original_fx(root, baseline):
    for name in ('line-sheet0.png', 'popfx-sheet0.png', 'popfx-sheet1.png'):
        original = baseline / 'images' / name
        candidate = root / 'images' / name
        if not original.is_file() or not candidate.is_file():
            raise ValueError(f'original effect asset missing: {name}')
        if hashlib.sha256(original.read_bytes()).digest() != hashlib.sha256(candidate.read_bytes()).digest():
            raise ValueError(f'original effect asset changed: {name}')


def compress_ui_images(root):
    # Existing game already uses WebP; retain the artist's PNGs untouched.
    # Verify every RGBA byte, including RGB under fully transparent pixels.
    for stem in ('ui-dialog-panel', 'ui-victory-rays', 'ui-encouragement-banner',
                 'ui-tutorial-card', 'ui-victory-title', 'ui-victory-next', 'timeup-title', 'timeout-clock',
                 'ui-progress-fill', 'ui-progress-track', 'ui-blue-button',
                 'ui-tool-slot', 'ui-settings-button', 'ui-tutorial-hand',
                 'ui-lock', 'ui-victory-home', 'ui-star-filled',
                 'replace-theme-icon', 'ui-tutorial-tile', 'hammer-icon', 'ui-tutorial-clock',
                 'menu-score-plate',
                 'settings-title_word_settings_en', 'settings-icon_sound', 'settings-icon_help',
                 'settings-icon_vibration', 'settings-chevron_right', 'settings-toggle_on', 'settings-toggle_off'):
        source = root / 'images' / (stem + '.png')
        target = source.with_suffix('.webp')
        with Image.open(source) as image:
            original = image.convert('RGBA')
            export = original
            if stem == 'timeout-clock':
                # The clock occupies under one third of the portrait dialog;
                # retain the original source and ship a display-sized copy.
                export = original.copy()
                export.thumbnail((320, 320), Image.Resampling.LANCZOS)
            if stem == 'ui-victory-rays':
                if original.size != (720, 360): raise ValueError('unexpected victory rays size')
                export = original.resize((512, 256), Image.Resampling.LANCZOS)
                # The largest current use is below 420 CSS pixels. Check both
                # light and dark composites at representative display sizes.
                for width in (320, 380, 420):
                    size = (width, width // 2)
                    a = original.resize(size, Image.Resampling.LANCZOS)
                    b = export.resize(size, Image.Resampling.LANCZOS)
                    for color in ((4,15,51,255), (255,255,255,255)):
                        bg = Image.new('RGBA', size, color)
                        diff = ImageChops.difference(Image.alpha_composite(bg,a).convert('RGB'), Image.alpha_composite(bg,b).convert('RGB'))
                        if max(ImageStat.Stat(diff).rms) >= 1 or max(extent[1] for extent in diff.getextrema()) > 8:
                            raise ValueError('victory rays reduction exceeds display-size tolerance')
            if stem == 'settings-title_word_settings_en':
                if original.size != (1024, 320): raise ValueError('unexpected settings title size')
                export = original.resize((512, 160), Image.Resampling.LANCZOS)
                # The settings panel is at most 380 CSS pixels wide. Compare
                # the composited result at two display sizes on both dark and
                # light backgrounds before accepting a smaller source image.
                for width in (320, 380):
                    size=(width,round(width*320/1024))
                    a=original.resize(size,Image.Resampling.LANCZOS)
                    b=export.resize(size,Image.Resampling.LANCZOS)
                    for color in ((4,15,51,255),(255,255,255,255)):
                        bg=Image.new('RGBA',size,color)
                        diff=ImageChops.difference(Image.alpha_composite(bg,a).convert('RGB'),Image.alpha_composite(bg,b).convert('RGB'))
                        if max(ImageStat.Stat(diff).rms)>=1 or max(extent[1] for extent in diff.getextrema())>16:
                            raise ValueError('settings title reduction exceeds display-size tolerance')
            # The default lossless encoder is occasionally smaller than method
            # 6 for icon art. Pick the smaller byte stream, then verify pixels.
            variants = []
            encoders = [{'method': 6}, {}]
            # This panel is shared across several dialogs. A higher-effort
            # lossless encode is smaller without changing its stretch pixels.
            if stem == 'ui-dialog-panel':
                encoders.append({'method': 6, 'quality': 100})
            for options in encoders:
                encoded = io.BytesIO()
                export.save(encoded, format='WEBP', lossless=True, exact=True, **options)
                variants.append(encoded.getvalue())
            target.write_bytes(min(variants, key=len))
            with Image.open(target) as encoded:
                decoded = encoded.convert('RGBA')
                if decoded.size != export.size or decoded.tobytes() != export.tobytes():
                    raise ValueError(f'lossless UI conversion changed pixels: {stem}')
        if target.stat().st_size >= source.stat().st_size:
            raise ValueError(f'lossless UI conversion did not reduce size: {stem}')
        old = 'images/' + stem + '.png'
        new = 'images/' + stem + '.webp'
        found = 0
        for file in root.rglob('*'):
            if not file.is_file() or file.suffix not in ('.js', '.html', '.css'):
                continue
            text = file.read_text(encoding='utf8')
            if old in text:
                found += text.count(old)
                file.write_text(text.replace(old, new), encoding='utf8', newline='\n')
        if not found:
            raise ValueError(f'UI asset has no expected references: {stem}')
        source.unlink()


def compress_reserve_atlas(root):
    source = root / 'images' / 'tiles-reserve-test.png'
    target = source.with_suffix('.webp')
    with Image.open(source) as image:
        original = image.convert('RGBA')
        original.save(target, format='WEBP', lossless=True, method=6, exact=True)
        with Image.open(target) as encoded:
            decoded = encoded.convert('RGBA')
            if decoded.size != original.size or decoded.tobytes() != original.tobytes():
                raise ValueError('reserve atlas conversion changed pixels')
    if target.stat().st_size >= source.stat().st_size:
        raise ValueError('reserve atlas conversion did not reduce size')
    data_file = root / 'data.js'
    data = data_file.read_text(encoding='utf8')
    old = '"images/tiles-reserve-test.png",' + str(source.stat().st_size)
    new = '"images/tiles-reserve-test.webp",' + str(target.stat().st_size)
    if not data.count(old):
        raise ValueError('reserve atlas metadata not found or size changed')
    data = data.replace(old, new)
    if 'images/tiles-reserve-test.png' in data:
        raise ValueError('unexpected reserve atlas reference')
    data_file.write_text(data, encoding='utf8', newline='\n')
    source.unlink()


def reuse_identical_particle_texture(root):
    """Share a byte-identical texture without altering the source assets."""
    images = root / 'images'
    canonical = images / 'shinetitle-sheet0.webp'
    duplicate = images / 'sparkparticle.webp'
    if not canonical.is_file() or not duplicate.is_file() or canonical.read_bytes() != duplicate.read_bytes():
        raise ValueError('particle textures are missing or no longer identical')
    formats_path = root / 'asset-formats.json'
    formats = json.loads(formats_path.read_text(encoding='utf8'))
    old, new = 'images/sparkparticle.webp', 'images/shinetitle-sheet0.webp'
    if formats.get('images/sparkparticle.png') != old:
        raise ValueError('unexpected particle format mapping')
    data_path = root / 'data.js'
    data = data_path.read_text(encoding='utf8')
    if data.count('"' + old + '"') != 1:
        raise ValueError('unexpected particle texture references')
    # Refuse removal if a non-metadata consumer directly names the duplicate.
    for file in root.rglob('*'):
        if not file.is_file() or file in (data_path, formats_path) or file.name == 'offline-worker.js' or file.suffix not in ('.js', '.html', '.css'):
            continue
        if old in file.read_text(encoding='utf8'):
            raise ValueError('particle texture is referenced by ' + str(file.relative_to(root)))
    data_path.write_text(data.replace('"' + old + '"', '"' + new + '"'), encoding='utf8', newline='\n')
    formats['images/sparkparticle.png'] = new
    formats_path.write_text(json.dumps(formats, ensure_ascii=False, separators=(',', ':')), encoding='utf8', newline='\n')
    duplicate.unlink()


def verify_literal_image_references(root):
    # Only root-level documents/scripts resolve these literal paths against
    # game/. Nested host CSS/API use different relative URL bases.
    pattern = re.compile(r'images/[A-Za-z0-9_.-]+\.(?:png|webp|svg|jpg)')
    missing = set()
    for file in root.iterdir():
        if not file.is_file() or file.suffix not in ('.js', '.html', '.css') or file.name == 'offline-worker.js':
            continue
        for reference in pattern.findall(file.read_text(encoding='utf8')):
            if not (root / reference).is_file():
                missing.add(reference)
    if missing:
        raise ValueError('missing literal image references: ' + ', '.join(sorted(missing)))


def synchronize_converted_texture_sizes(root):
    """Keep C2 preload weights aligned with changed candidate textures."""
    formats = json.loads((root / 'asset-formats.json').read_text(encoding='utf8'))
    # These two retain their PNG names but were replaced in the development
    # game, so their baseline byte weights no longer match their contents.
    converted = set(formats.values()) | {'images/credits-sheet0.png', 'images/gametilebg.png'}
    data_path = root / 'data.js'
    data = json.loads(data_path.read_text(encoding='utf8'))
    changed = 0

    def visit(value):
        nonlocal changed
        if isinstance(value, list):
            if len(value) >= 2 and isinstance(value[0], str) and value[0] in converted and type(value[1]) is int:
                path = root / value[0]
                if not path.is_file():
                    raise ValueError('converted texture missing: ' + value[0])
                size = path.stat().st_size
                if value[1] != size:
                    value[1] = size
                    changed += 1
            for child in value:
                visit(child)
        elif isinstance(value, dict):
            for child in value.values():
                visit(child)

    visit(data)
    data_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    return changed


def apply_verified_lossless_images(root, optimized):
    optimized = Path(optimized)
    for candidate in optimized.iterdir():
        target = root / 'images' / candidate.name
        if not candidate.is_file() or not target.is_file() or candidate.stat().st_size >= target.stat().st_size:
            continue
        with Image.open(target) as before, Image.open(candidate) as after:
            a, b = before.convert('RGBA'), after.convert('RGBA')
            if a.size != b.size or a.tobytes() != b.tobytes():
                raise ValueError('optimized image pixels differ: ' + candidate.name)
        shutil.copyfile(candidate, target)
    synchronize_all_texture_sizes(root)


def synchronize_all_texture_sizes(root):
    data_path = root / 'data.js'
    data = json.loads(data_path.read_text(encoding='utf8'))
    def sync(value):
        if isinstance(value, list):
            if len(value) >= 2 and isinstance(value[0], str) and value[0].startswith('images/') and type(value[1]) is int:
                path = root / value[0]
                if path.is_file(): value[1] = path.stat().st_size
            for item in value: sync(item)
        elif isinstance(value, dict):
            for item in value.values(): sync(item)
    sync(data)
    data_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf8')


def apply_verified_visual_images(root, optimized, report_path, reference):
    optimized, reference = Path(optimized), Path(reference)
    report = json.loads(Path(report_path).read_text(encoding='utf8'))
    accepted = 0
    for record in report:
        if record.get('status') != 'compressed': continue
        name = Path(record.get('path', '')).name
        target, source, candidate = root / 'images' / name, reference / name, optimized / name
        detail = record.get('detail') or {}
        # Original link and elimination effects retain exact decoded pixels.
        if name in {'line-sheet0.png', 'dots-sheet0.png', 'popfx-sheet0.png', 'popfx-sheet1.png'}: continue
        if not name or not target.is_file() or not source.is_file() or not candidate.is_file(): continue
        # A quality score applies only to the exact pair named by the report.
        # Reject stale or relocated files rather than silently applying that
        # score to unrelated images that happen to have the same filename.
        if source.resolve() != Path(record.get('path', '')).resolve(): continue
        if candidate.resolve() != Path(record.get('out', '')).resolve(): continue
        if source.stat().st_size != record.get('before') or candidate.stat().st_size != record.get('after'): continue
        if record.get('ssim', 0) < .995 or detail.get('ssim_p1', 1) < .95 or detail.get('residual', 0) > 6: continue
        if candidate.stat().st_size >= target.stat().st_size: continue
        with Image.open(target) as original, Image.open(source) as baseline, Image.open(candidate) as result:
            a,b,c = original.convert('RGBA'),baseline.convert('RGBA'),result.convert('RGBA')
            if a.size != b.size or a.tobytes() != b.tobytes(): continue
            if a.size != c.size or a.getchannel('A').tobytes() != c.getchannel('A').tobytes(): continue
        shutil.copyfile(candidate, target)
        accepted += 1
    return accepted


def add_pause_close_wait(data, runtime_source):
    marker = 'cr.getObjectRefTable=function(){return['
    if marker not in runtime_source:
        raise ValueError('Construct reference table missing')
    table = runtime_source.split(marker, 1)[1].split(']', 1)[0].split(',')
    if len(table) <= 85 or table[85] != 'cr.system_object.prototype.acts.Wait':
        raise ValueError('Construct Wait reference changed')
    matches = []
    tutorial_matches = []
    wait_sids = []
    def visit(value):
        if isinstance(value, list):
            if len(value) > 6 and value[4] == 854484185937641 and isinstance(value[6], list): matches.append(value)
            if len(value) > 6 and value[4] == 462235957291603 and isinstance(value[6], list): tutorial_matches.append(value)
            if len(value) > 3 and value[3] in (874223100987651, 874223100987652): wait_sids.append(value)
            for child in value: visit(child)
        elif isinstance(value, dict):
            for child in value.values(): visit(child)
    visit(data)
    if len(matches) != 1 or len(tutorial_matches) != 1 or wait_sids: raise ValueError('native pause close event or wait SID changed')
    actions = matches[0][6]
    indexes = [i for i, action in enumerate(actions) if isinstance(action, list) and len(action) > 3 and action[3] == 918927348401778]
    if len(indexes) != 1: raise ValueError('native pause hide action changed')
    actions.insert(indexes[0], [-1, 85, None, 874223100987651, False, [[0, [1, .18]]]])
    actions = tutorial_matches[0][6]
    indexes = [i for i, action in enumerate(actions) if isinstance(action, list) and len(action) > 3 and action[3] == 268127763738893]
    if len(indexes) != 1: raise ValueError('native tutorial close action changed')
    actions.insert(indexes[0], [-1, 85, None, 874223100987652, False, [[0, [1, .18]]]])
    return data


def native_path_event_sids(data):
    names = {'_match', '_is_row_clear', '_is_col_clear', '_look_aside', '_match_perimeter_pattern',
             '_look_left_right', '_look_up_down', '_match_from_position', '_index_at', '_build_path', '_add_to_sub_path'}
    functions = data['project'][6][0][1][0][7][9][7]
    events, found = set(), set()
    def visit(value):
        if isinstance(value, list):
            if len(value) > 6 and value[0] == 0 and type(value[4]) is int and isinstance(value[5], list) and isinstance(value[6], list): events.add(value[4])
            for child in value: visit(child)
        elif isinstance(value, dict):
            for child in value.values(): visit(child)
    for item in functions:
        try: name = item[5][0][9][0][1][1]
        except (IndexError, KeyError, TypeError): continue
        if name in names: found.add(name); visit(item)
    if found != names or not events: raise ValueError('native path function structure changed')
    return sorted(events)


def shorten_no_match_transition(data):
    """Keep the native shuffle chain while removing its long hidden waits."""
    found_wait, found_instances = [], {}
    def visit(value):
        if isinstance(value, list):
            if len(value) > 5 and value[3] == 730435901061908:
                if value[5] != [[0, [0, 1]]]: raise ValueError('unexpected no-match wait')
                value[5] = [[0, [1, 0.05]]]
                found_wait.append(True)
            if len(value) == 6 and isinstance(value[0], list) and len(value[0]) > 4 and value[1] in (49, 50) and isinstance(value[2], int):
                found_instances[value[1]] = value
            for item in value: visit(item)
        elif isinstance(value, dict):
            for item in value.values(): visit(item)
    visit(data['project'][6])
    visit(data['project'][5])
    if len(found_wait) != 1 or set(found_instances) != {49, 50}: raise ValueError('native no-match structure changed')
    a, b = found_instances[49][4][0], found_instances[50][4][0]
    if a[5] != 0.5 or b[1:4] != [0.3, 2, 0.2]: raise ValueError('native no-match tween timing changed')
    a[5] = 0.05
    # t50 continues the chain only on Sprite.OnDestroyed: its Fade wait,
    # not just fade-out duration, used to add two hidden seconds.
    b[1:4] = [0.05, 0.05, 0.05]
    return data


def reuse_timeout_clock(root):
    """Use the existing red timeout artwork for the native shaking clock."""
    root = Path(root)
    data_path = root / 'data.js'
    data = json.loads(data_path.read_text(encoding='utf8'))
    clock = root / 'images/timeout-clock.webp'
    with Image.open(clock) as image:
        width, height = image.size
    sprite = data['project'][3][51]
    if sprite[0] != 't51' or not any('lg_Shake' in str(x) for x in sprite[8]):
        raise ValueError('native timeout clock or shake behavior changed')
    frame = sprite[7][0][7][0]
    if frame[0] != 'images/timesup-sheet0.webp':
        raise ValueError('unexpected native timeout clock texture')
    frame[0:6] = ['images/timeout-clock.webp', clock.stat().st_size, 0, 0, width, height]
    changed = []
    def visit(value):
        if isinstance(value, list):
            if len(value) == 6 and isinstance(value[0], list) and len(value[0]) > 4 and value[1] == 51 and isinstance(value[2], int):
                value[0][3], value[0][4] = width, height
                changed.append(value[2])
            for item in value: visit(item)
        elif isinstance(value, dict):
            for item in value.values(): visit(item)
    visit(data['project'][5])
    if len(changed) != 1: raise ValueError('unexpected native timeout clock instances')
    data_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    formats_path = root / 'asset-formats.json'
    formats = json.loads(formats_path.read_text(encoding='utf8'))
    old, new = 'images/timesup-sheet0.webp', 'images/timeout-clock.webp'
    if formats.get('images/timesup-sheet0.png') != old: raise ValueError('unexpected timeout texture mapping')
    for file in root.rglob('*'):
        if not file.is_file() or file in (data_path, formats_path) or file.name == 'offline-worker.js' or file.suffix not in ('.js', '.html', '.css'):
            continue
        if old in file.read_text(encoding='utf8'): raise ValueError('old timeout texture still referenced by ' + str(file))
    formats['images/timesup-sheet0.png'] = new
    formats_path.write_text(json.dumps(formats, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    (root / old).unlink()


def prepare(destination, pool_config=None, combi_sdk_zip=None, optimized_images=None, visual_images=None, visual_report=None, visual_reference=None, experimental_starfield=False):
    destination = Path(destination).resolve()
    if destination == ANALYSIS or ANALYSIS not in destination.parents:
        raise ValueError('destination must be a new directory inside analysis')
    # Pool candidates are independent experiments, even on the same origin.
    # Keep legacy candidates unchanged so their existing data is not migrated.
    namespace = hashlib.sha256(str(destination).encode('utf8')).hexdigest()[:12] if pool_config is not None else None
    destination.mkdir(parents=True, exist_ok=False)
    root = destination / 'game'
    shutil.copytree(PROJECT / 'game', root)
    # Local art direction only: these theme selections are not competitor data.
    configured_themes = json.loads((PROJECT / 'config/theme_overrides_candidate.json').read_text(encoding='utf8'))
    editor_themes = (PROJECT / 'config/theme_overrides_candidate.js').read_text(encoding='utf8').strip()
    if editor_themes != 'window.oneConnectProjectThemeOverrides=' + json.dumps(configured_themes, separators=(',', ':')) + ';':
        raise ValueError('editor theme overrides do not match candidate configuration')
    theme_overrides = configured_themes if pool_config is None else {}
    config_path = root / 'level-config.js'
    config_text = config_path.read_text(encoding='utf8').strip()
    config_prefix = 'window.oneConnectLevels='
    if not config_text.startswith(config_prefix) or not config_text.endswith(';'):
        raise ValueError('unexpected level configuration')
    candidate_config = json.loads(config_text[len(config_prefix):-1])
    entries_by_level = {str(row['level']): row for row in candidate_config['levels']}
    for level, theme in theme_overrides.items():
        row = entries_by_level.get(level)
        if row is None or theme != 3:
            raise ValueError('invalid candidate theme override: ' + str(level))
        generator = row.get('generator') or {}
        board = row.get('board') or []
        if (not generator and not board) or generator.get('typeCount', 0) > 20 or any(cell > 20 for line in board for cell in line):
            raise ValueError('Ramadan theme cannot cover level: ' + str(level))
    if pool_config is not None:
        pools = json.loads(Path(pool_config).read_text(encoding='utf-8-sig'))
        if not isinstance(pools, dict) or not pools:
            raise ValueError('pool configuration must be a nonempty object keyed by level')
        config_path = root / 'level-config.js'
        text = config_path.read_text(encoding='utf8').strip()
        prefix = 'window.oneConnectLevels='
        if not text.startswith(prefix) or not text.endswith(';'):
            raise ValueError('unexpected level configuration')
        config = json.loads(text[len(prefix):-1])
        entries = {str(row['level']): row for row in config['levels']}
        data_text = (root / 'data.js').read_text(encoding='utf8').strip()
        data = json.loads(data_text[data_text.index('{'):].rstrip(';'))
        frames = [len(anim[7]) for anim in data['project'][3][5][7]]
        for level, pool in pools.items():
            if level not in entries or str(int(level)) != level:
                raise ValueError('pool references an unconfigured level: ' + str(level))
            generator = entries[level].get('generator')
            if not generator:
                raise ValueError('pool requires a generated board: ' + level)
            validate_candidate_pool(pool, entries[level], frames)
            generator['pool'] = pool
        config_path.write_text(prefix + json.dumps(config, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf8')
    # Keep the added project-owned progress, tool and tutorial keys separate
    # even when a browser happens to reuse an origin for multiple copies.
    for filename, key in [
        ('level-progress.js', 'oneconnect.currentLevel.v1'),
        ('hammer-runtime.js', 'oneconnect.hammer.v1'),
        ('tutorial-first.js', 'oneconnect.tutorial1.v1'),
        ('tutorial-second.js', 'oneconnect.tutorial2.v1'),
        ('tutorial-third.js', 'oneconnect.tutorial3.v1'),
        ('tutorial-fifth.js', 'oneconnect.tutorial5.v1'),
        ('tutorial-seventh.js', 'oneconnect.tutorial7.v1'),
        ('tutorial-tenth.js', 'oneconnect.tutorial10.v1'),
    ]:
        path = root / filename
        replacement = key.replace('.v1', '.candidate.' + namespace + '.v1' if namespace else '.candidate.v1')
        content = replace_once(path.read_text(encoding='utf8'), key, replacement, filename + ' save key')
        path.write_text(content, encoding='utf8', newline='\n')
    # These literals are the original LocalStorage key arguments and matching
    # callbacks in the current exported event sheet; fail closed if it changes.
    data_file = root / 'data.js'
    data = data_file.read_text(encoding='utf8')
    for key, count in [('connectBest', 5), ('muted', 9)]:
        literal = '"' + key + '"'
        if data.count(literal) != count:
            raise ValueError('unexpected original storage references: ' + key)
        data = data.replace(literal, '"candidate.' + (namespace + '.' if namespace else '') + key + '"')
    data_file.write_text(data, encoding='utf8', newline='\n')
    api_file = root / 'html5games/gameapi/v1.js'
    api = api_file.read_text(encoding='utf8')
    prefix = 'window.famobi_gameID+":"'
    if api.count(prefix) != 4:
        raise ValueError('unexpected Famobi storage prefix')
    api_file.write_text(api.replace(prefix, 'window.famobi_gameID+":candidate:' + (namespace + ':' if namespace else '') + '"'), encoding='utf8', newline='\n')
    # A failure result bridge requests the ad from its Home/Retry action. If it
    # failed to install, retain the original analytics-event fallback.
    custom_file = root / 'custom.js'
    custom = custom_file.read_text(encoding='utf8')
    custom = replace_once(custom, 'window.oneConnectHost.showInterstitialFor("fail"),n.reason',
        '(!window.oneConnectResultBridgeCandidate||!window.oneConnectResultBridgeCandidate.handlesFailure())&&window.oneConnectHost.showInterstitialFor("fail"),n.reason', 'failure interstitial timing')
    custom_file.write_text(custom, encoding='utf8', newline='\n')
    for source, target in [
        ('tools/in_game_layout.js', 'layout-geometry.js'),
        ('tools/in_game_layout_adapter.js', 'layout-adapter.js'),
        ('tools/layout_candidate.js', 'layout-candidate.js'),
        ('tools/tool_press_candidate.js', 'tool-press-candidate.js'),
        ('tools/theme_switch_candidate.js', 'theme-switch-candidate.js'),
        ('tools/shuffle_motion_map.js', 'shuffle-motion-map.js'),
        ('tools/shuffle_motion_candidate.js', 'shuffle-motion-candidate.js'),
        ('tools/tile_pool_candidate.js', 'tile-pool-candidate.js'),
        ('tools/haptics_candidate.js', 'haptics-candidate.js'),
        ('tools/how_to_play_candidate.js', 'how-to-play-candidate.js'),
        ('tools/home_settings_candidate.js', 'home-settings-candidate.js'),
        ('tools/ui_motion_candidate.js', 'ui-motion-candidate.js'),
        ('tools/native_pause_motion_candidate.js', 'native-pause-motion.js'),
        ('tools/tutorial_motion_adapter.js', 'tutorial-motion-adapter.js'),
        ('tools/tutorial_motion_integration.js', 'tutorial-motion-integration.js'),
        ('tools/visible_gravity_bounds.js', 'visible-gravity-bounds.js'),
        ('tools/native_move_bounds_candidate.js', 'native-move-bounds.js'),
        ('tools/native_board_mask_candidate.js', 'native-board-mask.js'),
        ('tools/result_panel_candidate.js', 'result-panel-candidate.js'),
        ('tools/result_bridge_candidate.js', 'result-bridge-candidate.js'),
        ('tools/level_score_candidate.js', 'level-score-candidate.js'),
        ('tools/home_star_candidate.js', 'home-star-candidate.js'),
        ('tools/link_points_capture_candidate.js', 'link-points-candidate.js'),
        ('tools/link_star_candidate.js', 'link-star-candidate.js'),
        ('tools/invalid_link_capture_candidate.js', 'invalid-link-capture-candidate.js'),
        ('tools/invalid_link_feedback_candidate.js', 'invalid-link-feedback-candidate.js'),
        ('tools/selection_frame_candidate.js', 'selection-frame-candidate.js'),
        ('tools/tutorial_visual_candidate.js', 'tutorial-visual-candidate.js'),
        ('tools/board_progress_candidate.js', 'board-progress-candidate.js'),
        ('tools/tool_reward_candidate.js', 'tool-reward-candidate.js'),
        ('tools/reward_lifecycle_candidate.js', 'reward-lifecycle.js'),
        ('tools/combi_sdk_adapter.js', 'combi-sdk-adapter.js'),
        ('tools/auto_shuffle_candidate.js', 'auto-shuffle.js'),
        ('tools/flystar_candidate.js', 'flystar-candidate.js'),
        ('美术换皮准备/局内道具布局/原始候选/hammer_icon_128.png', 'images/hammer-icon.png'),
        ('美术换皮准备/局内道具布局/原始候选/replace_theme_icon_128.png', 'images/replace-theme-icon.png'),
        ('美术换皮准备/局内新增UI重绘/dialog_panel.png', 'images/ui-dialog-panel.png'),
        ('美术换皮准备/局内新增UI重绘/warning-icon.webp', 'images/warning-icon.webp'),
        ('美术换皮准备/局内新增UI重绘/blue_button.png', 'images/ui-blue-button.png'),
        ('美术换皮准备/局内新增UI重绘/star_filled.png', 'images/ui-star-filled.png'),
        ('美术换皮准备/局内新增UI重绘/settings_button.png', 'images/ui-settings-button.png'),
        ('美术换皮准备/局内新增UI重绘/tool_slot.png', 'images/ui-tool-slot.png'),
        ('美术换皮准备/局内新增UI重绘/lock.png', 'images/ui-lock.png'),
        ('美术换皮准备/局内新增UI重绘/tutorial_hand.png', 'images/ui-tutorial-hand.png'),
        ('美术换皮准备/局内新增UI重绘/tutorial_card.png', 'images/ui-tutorial-card.png'),
        ('美术换皮准备/局内新增UI重绘/tutorial_tile.png', 'images/ui-tutorial-tile.png'),
        ('美术换皮准备/局内新增UI重绘/tutorial_clock.png', 'images/ui-tutorial-clock.png'),
        ('美术换皮准备/局内新增UI重绘/progress_track.png', 'images/ui-progress-track.png'),
        ('美术换皮准备/局内新增UI重绘/progress_fill.png', 'images/ui-progress-fill.png'),
        ('美术换皮准备/结算界面组件/victory_title.png', 'images/ui-victory-title.png'),
        ('美术换皮准备/结算界面组件/timeup_title_v1.png', 'images/timeup-title.png'),
        ('美术换皮准备/结算界面组件/timeout_clock_v1.png', 'images/timeout-clock.png'),
        ('美术换皮准备/结算界面组件/victory_next_button.png', 'images/ui-victory-next.png'),
        ('美术换皮准备/结算界面组件/victory_rays.png', 'images/ui-victory-rays.png'),
        ('美术换皮准备/结算界面组件/home_button_trimmed.png', 'images/ui-victory-home.png'),
        ('美术换皮准备/结算界面组件/encouragement_banner.png', 'images/ui-encouragement-banner.png'),
        ('美术换皮准备/结算界面组件/victory_confetti_strip.png', 'images/victory-confetti-strip.png'),
        ('美术换皮准备/结算界面组件/victory_confetti_square.png', 'images/victory-confetti-square.png'),
        *[(f'美术换皮准备/设置界面组件/{name}.png', f'images/settings-{name}.png') for name in
          ('title_word_settings_en', 'icon_sound', 'icon_help', 'icon_vibration', 'chevron_right', 'toggle_on', 'toggle_off')],
    ]:
        shutil.copyfile(PROJECT / source, root / target)
    if namespace:
        haptics_file = root / 'haptics-candidate.js'
        haptics = replace_once(haptics_file.read_text(encoding='utf8'), 'oneconnect.haptics.candidate.v1',
            'oneconnect.haptics.candidate.' + namespace + '.v1', 'candidate haptics save key')
        haptics_file.write_text(haptics, encoding='utf8', newline='\n')
        progress_file = root / 'board-progress-candidate.js'
        progress = replace_once(progress_file.read_text(encoding='utf8'), 'oneconnect.user-level.candidate.v1',
            'oneconnect.user-level.candidate.' + namespace + '.v1', 'candidate player level save key')
        progress_file.write_text(progress, encoding='utf8', newline='\n')
        layout_file = root / 'layout-candidate.js'
        layout = replace_once(layout_file.read_text(encoding='utf8'), 'oneconnect.theme-tool.candidate.v1',
            'oneconnect.theme-tool.candidate.' + namespace + '.v1', 'candidate theme tool save key')
        layout_file.write_text(layout, encoding='utf8', newline='\n')

    page = root / 'game.html'
    s = page.read_text(encoding='utf8')
    s = replace_once(s, '<link rel="preload" href="data.js" as="fetch" crossorigin="anonymous">',
        '<link rel="preload" href="data.js" as="fetch" crossorigin="anonymous">\n'
        '<link rel="preload" href="host-adapter.js" as="script">\n'
        '<link rel="preload" href="level-config.js" as="script">\n'
        '<link rel="preload" href="board-generator.js" as="script">\n'
        '<link rel="preload" href="layout-candidate.js" as="script">', 'early startup script preloads')
    s = replace_once(s, '<script src="round-save.js"></script>',
        '<script src="level-score-candidate.js"></script>\n    <script src="round-save.js"></script>', 'round-score script')
    s = replace_once(s, '<script src="gravity-runtime.js"></script>', '<script src="visible-gravity-bounds.js"></script>\n    <script src="native-path-sids.js"></script>\n    <script src="native-board-mask.js"></script>\n    <script src="native-move-bounds.js"></script>\n    <script src="gravity-runtime.js"></script>', 'visible gravity limits')
    s = replace_once(s, '<script src="hammer-runtime.js"></script>',
        '<script src="layout-geometry.js"></script>\n'
        '    <script src="layout-adapter.js"></script>\n'
        '    <script src="theme-switch-candidate.js"></script>\n'
        '    <script src="shuffle-motion-map.js"></script>\n'
        '    <script src="shuffle-motion-candidate.js"></script>\n'
        '    <script src="tile-pool-candidate.js"></script>\n'
        '    <script src="layout-candidate.js"></script>\n'
        '    <script src="tool-press-candidate.js"></script>\n'
        '    <script src="haptics-candidate.js"></script>\n'
        '    <script src="how-to-play-candidate.js"></script>\n'
        '    <script src="home-settings-candidate.js"></script>\n'
        '    <script src="ui-motion-candidate.js"></script>\n'
        '    <script src="native-pause-motion.js"></script>\n'
        '    <script src="tutorial-motion-adapter.js"></script>\n'
        '    <script src="tutorial-motion-integration.js"></script>\n'
        '    <script src="home-star-candidate.js"></script>\n'
        '    <script src="link-star-candidate.js"></script>\n'
        '    <script src="link-points-candidate.js"></script>\n'
        '    <script src="invalid-link-capture-candidate.js"></script>\n'
        '    <script src="invalid-link-feedback-candidate.js"></script>\n'
        '    <script src="selection-frame-candidate.js"></script>\n'
        '    <script src="tutorial-visual-candidate.js"></script>\n'
        '    <script src="board-progress-candidate.js"></script>\n'
        '    <script src="tool-reward-candidate.js"></script>\n'
        '    <script src="combi-sdk-adapter.js"></script>\n'
        '    <script src="flystar-candidate.js"></script>\n'
        '    <script src="result-panel-candidate.js"></script>\n'
        '    <script src="result-bridge-candidate.js"></script>\n'
        '    <script src="hammer-runtime.js"></script>', 'game scripts')
    s = replace_once(s, 'oneConnectHammer.install();',
        'oneConnectHammer.install();\n            oneConnectLayoutCandidate.install();\n'
        '            oneConnectHomeSettingsCandidate.install();\n'
        '            oneConnectHomeStarCandidate.install();\n'
        '            oneConnectLinkPointsCandidate.install();\n'
        '            oneConnectInvalidLinkCaptureCandidate.install();\n'
        '            oneConnectInvalidLinkFeedbackCandidate.install();\n'
        '            oneConnectSelectionFrameCandidate.install();\n'
        '            oneConnectFlyStarCandidate.install();\n'
        '            oneConnectResultBridgeCandidate.install();', 'game startup')
    s = replace_once(s, 'oneConnectTenthGuide.install();',
        'oneConnectTenthGuide.install();\n            oneConnectTutorialVisualCandidate.install();\n            oneConnectTutorialMotionIntegration.install();\n            oneConnectToolRewardCandidate.install();\n            oneConnectCombiSdkAdapter.install();', 'tutorial art startup')
    s = replace_once(s, 'oneConnectAutoShuffle.install();',
        'oneConnectAutoShuffle.install();\n            oneConnectNativeBoardMask.install();\n            oneConnectNativeMoveBounds.install();\n            oneConnectNativePauseMotion.install();\n            oneConnectShuffleMotionCandidate.install();', 'shuffle motion startup')
    page.write_text(s, encoding='utf8', newline='\n')

    # Keep experimental round data separate from the player's production save.
    round_save = root / 'round-save.js'
    s = round_save.read_text(encoding='utf8')
    s = replace_once(s, "if(d.type==='game.auto_shuffle_complete')shuffling=false;",
        "if(d.type==='game.auto_shuffle_complete'||d.type==='game.auto_shuffle_exhausted'||d.type==='game.auto_shuffle_expired')shuffling=false;", 'shuffle save cleanup')
    round_key = "'oneconnect.round.score-candidate." + (namespace + '.' if namespace else '') + "v1'"
    s = replace_once(s, "'oneconnect.round.v1'", round_key, 'candidate save key')
    s = replace_once(s, 'if(!window.oneConnectRoundSaveModel.validate(s,entry))return false;',
        "var theme=variable(r,'theme');if(theme&&Number.isInteger(theme.data)&&theme.data>=0&&theme.data<=3){if(theme.data===3&&s.board.some(function(row){return row.some(function(v){return v>20;});}))return false;s.theme=theme.data;}"
        'if(!window.oneConnectRoundSaveModel.validate(s,entry))return false;', 'candidate theme snapshot')
    s = replace_once(s, 'pendingDisplay=s;return s;',
        'window.oneConnectLevelScoreCandidate.restore(s);pendingDisplay=s;return s;', 'score restore')
    s = replace_once(s, 'if(!window.oneConnectRoundSaveModel.validate(s,entry))return false;',
        'var base=window.oneConnectLevelScoreCandidate.baseline(lev.data,score.data), matchScore=window.oneConnectLevelScoreCandidate.matchScore(lev.data,score.data);if(base!==null)s.scoreBase=base;if(matchScore!==null)s.matchScore=matchScore;\n  '
        'if(!window.oneConnectRoundSaveModel.validate(s,entry))return false;', 'score snapshot')
    s = replace_once(s, "if(d.type==='game.auto_shuffle_start')shuffling=true;",
        "if(d.type==='game.round_source'&&d.detail&&!d.detail.resumed){var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),v=r&&variable(r,'score');window.oneConnectLevelScoreCandidate.begin(d.detail.level,v&&v.data);}\n   "
        "if(d.type==='game.match'&&d.detail)window.oneConnectLevelScoreCandidate.match(d.detail.level);\n   "
        "if(d.type==='game.auto_shuffle_start')shuffling=true;", 'score start')
    s = replace_once(s, 'tutorial=false,shuffling=false', 'tutorial=false,tutorialOwner=null,shuffling=false', 'tutorial save owner')
    s = replace_once(s, "if(d.type==='tutorial.start')tutorial=true;", "if(d.type==='tutorial.start'){tutorial=true;tutorialOwner=d.detail&&d.detail.level;}", 'tutorial save start owner')
    s = replace_once(s, "if(d.type==='tutorial.complete')tutorial=false;", "if((d.type==='tutorial.complete'||d.type==='tutorial.cancelled')&&(!d.detail||d.detail.level===tutorialOwner)){tutorial=false;tutorialOwner=null;}", 'cancelled tutorial save unlock')
    round_save.write_text(s, encoding='utf8', newline='\n')

    # Board restoration runs before the saved tiles are created. Older saves
    # without a theme retain the configured/default theme.
    board_hooks = root / 'board-hooks.js'
    s = board_hooks.read_text(encoding='utf8')
    s = replace_once(s, "      var variables = runtime.all_global_vars, rows = variables.find(function(v){return v.name === 'ROWS_COUNT';}), cols = variables.find(function(v){return v.name === 'COLUMNS_COUNT';});",
        "      if (entry.generator && !saved && entry.generator.pool !== undefined) {\n"
        "        if (!window.oneConnectTilePoolCandidate) throw Error('candidate tile pool unavailable');\n"
        "        var mapped = window.oneConnectTilePoolCandidate.apply({board:board}, entry.generator.pool, seed);\n"
        "        board = mapped.board; generated.selectedTileIds = mapped.selectedTileIds;\n"
        "      }\n"
        "      var variables = runtime.all_global_vars, rows = variables.find(function(v){return v.name === 'ROWS_COUNT';}), cols = variables.find(function(v){return v.name === 'COLUMNS_COUNT';});", 'candidate pool mapping')
    s = replace_once(s, "        var generatedEvent={level:current,seed:generated.seed,strategy:generated.strategy};",
        "        var generatedEvent={level:current,seed:generated.seed,strategy:generated.strategy};\n"
        "        if (generated.selectedTileIds) { generatedEvent.candidatePool = entry.generator.pool.slice(); generatedEvent.selectedTileIds = generated.selectedTileIds.slice(); }",
        'candidate pool event')
    s = replace_once(s, '  var installed = false, pendingLevel = null;',
        '  var installed = false, pendingLevel = null, candidateSavedThemeActive = false, candidateThemeLevel = null;\n  var projectThemeOverrides=' + json.dumps(theme_overrides, separators=(',', ':')) + ';', 'candidate theme owner')
    s = replace_once(s, '    if (installed) return;\n    if (cr.action.prototype.run_system)',
        "    if (installed) return;\n    window.addEventListener('oneconnect:event',function(e){var t=e.detail&&e.detail.type;if(t==='game.level_fail'||t==='game.level_win'||t==='screen.SCREEN_BONUS'){candidateSavedThemeActive=false;candidateThemeLevel=null;}});\n    if (cr.action.prototype.run_system)", 'candidate theme round end reset')
    s = replace_once(s, '    var current = pendingLevel === null ? level(runtime) : pendingLevel;\n    var entries',
        '    var current = pendingLevel === null ? level(runtime) : pendingLevel;\n    candidateSavedThemeActive = false; candidateThemeLevel = current;\n    var entries', 'candidate theme reset')
    s = replace_once(s, '    if (!hasBoard && !saved) {',
        "    if (saved && Number.isInteger(saved.theme) && saved.theme >= 0 && saved.theme <= 3 && (saved.theme !== 3 || !saved.board.some(function(row){return row.some(function(v){return v>20;});}))) {\n"
        "      var savedTheme = runtime.all_global_vars.find(function(v){ return v.name === 'theme'; });\n"
        "      if (savedTheme) { savedTheme.data = saved.theme; candidateSavedThemeActive = true; }\n"
        "    }\n"
        '    if (!hasBoard && !saved) {', 'candidate theme restoration')
    s = replace_once(s,
        "          if (theme) theme.data = entry && Number.isInteger(entry.theme) && entry.theme >= 0 && entry.theme <= 2 ? entry.theme : 0;",
        "          if (candidateThemeLevel !== current) { candidateSavedThemeActive = false; candidateThemeLevel = current; }\n          if (theme && !candidateSavedThemeActive) theme.data = Object.prototype.hasOwnProperty.call(projectThemeOverrides,String(current)) ? projectThemeOverrides[String(current)] : (entry && Number.isInteger(entry.theme) && entry.theme >= 0 && entry.theme <= 3 ? entry.theme : 0);",
        'preserve restored theme during tile creation')
    s = replace_once(s, '  window.oneConnectBoard = { install: install };',
        '  window.oneConnectBoard = { install: install, markCandidateTheme: function(){ var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(); candidateSavedThemeActive = true; candidateThemeLevel = r ? level(r) : null; } };',
        'candidate active theme owner')
    s = replace_once(s, 'var boardEvent={level:current};',
        'var boardEvent={level:current,tileCount:present};', 'board ready tile count')
    board_hooks.write_text(s, encoding='utf8', newline='\n')

    hammer = root / 'hammer-runtime.js'
    s = hammer.read_text(encoding='utf8')
    s = replace_once(s, 'tutorialLocked=false,button,label', 'tutorialLocked=false,tutorialOwner=null,button,label', 'tutorial hammer owner')
    s = replace_once(s, "else if(x.type==='tutorial.start')tutorialLocked=true;", "else if(x.type==='tutorial.start'){tutorialLocked=true;tutorialOwner=x.detail&&x.detail.level;}", 'tutorial hammer start owner')
    s = replace_once(s, "else if(x.type==='tutorial.complete')tutorialLocked=false;", "else if((x.type==='tutorial.complete'||x.type==='tutorial.cancelled')&&(!x.detail||x.detail.level===tutorialOwner)){tutorialLocked=false;tutorialOwner=null;}", 'cancelled tutorial hammer unlock')
    s = replace_once(s, 'function ready(r){if(!r',
        'function ready(r){if(window.oneConnectShuffleMotionCandidate&&window.oneConnectShuffleMotionCandidate.state().moving)return false;if(!r', 'hammer shuffle lock')
    s = replace_once(s, "var key='oneconnect.hammer.candidate.v1',memory=2,installed=false",
        "var key='oneconnect.hammer.candidate.v1',memory=2,stockLoaded=false,installed=false", 'hammer stock cache') if namespace is None else s
    if namespace is not None:
        s = replace_once(s, "var key='oneconnect.hammer.candidate." + namespace + ".v1',memory=2,installed=false",
            "var key='oneconnect.hammer.candidate." + namespace + ".v1',memory=2,stockLoaded=false,installed=false", 'hammer stock cache')
    s = replace_once(s, 'function stock(){try{var raw=localStorage.getItem(key);',
        'function stock(){if(stockLoaded)return memory;stockLoaded=true;try{var raw=localStorage.getItem(key);', 'hammer stock cached read')
    s = replace_once(s, 'function save(n){memory=n;try{localStorage.setItem(key,String(n));}catch(_){}}',
        'var rewardSaved=true,rewardExternalRevision=0;function save(n){memory=n;try{localStorage.setItem(key,String(n));return true;}catch(_){return false;}}', 'hammer reward persistence result')
    s = replace_once(s, "window.addEventListener('oneconnect:event',function(e){var x=e.detail;",
        "window.addEventListener('storage',function(e){if(e.key===key||e.key===null){rewardExternalRevision++;stockLoaded=false;}});\n    window.addEventListener('oneconnect:event',function(e){var x=e.detail;", 'hammer stock external update')
    s = replace_once(s, "if(!options.free&&count<=0){notice('No hammers');return {status:'empty'};}",
        "if(!options.free&&count<=0){if(window.oneConnectToolRewardCandidate)window.oneConnectToolRewardCandidate.open('hammer');return {status:'empty'};}", 'hammer reward prompt')
    s = replace_once(s, 'window.oneConnectHammer={install:install,use:use,state:function()',
        "window.oneConnectHammer={install:install,use:use,credit:function(n){var old=stock();if(!Number.isInteger(n)||n<1||old+n>999)return false;rewardSaved=save(old+n);return true;},rewardPersisted:function(){return rewardSaved;},rewardRevision:function(){return rewardExternalRevision;},retryRewardSave:function(before,revision){if(revision!==rewardExternalRevision)return 'conflict';var current=stock();try{var raw=localStorage.getItem(key);if(!(raw===String(before)||(raw===null&&before===2)))return 'conflict';localStorage.setItem(key,String(current));rewardSaved=true;return 'saved';}catch(_){return 'retry';}},state:function()", 'hammer reward credit')
    pattern = r"button\.style\.cssText='display:none;position:fixed;left:50%;bottom:3%;.*?';button\.innerHTML='<svg.*?</svg>';"
    replacement = ("button.style.cssText='display:none;position:fixed;z-index:22;align-items:center;"
        "justify-content:center;gap:2px;border:0;background:transparent;color:white;font:bold 19px sans-serif;"
        "cursor:pointer;touch-action:manipulation';button.innerHTML='<img src=\"images/hammer-icon.png\" "
        "alt=\"\" style=\"position:absolute;left:12%;top:14%;width:47%;height:72%;object-fit:contain\">';")
    s, count = re.subn(pattern, replacement, s)
    if count != 1:
        raise ValueError('unexpected hammer button structure')
    s = replace_once(s, "label=document.createElement('span');button.appendChild(label);",
        "label=document.createElement('span');label.style.cssText='position:absolute;left:65%;top:25%;color:white;font:bold clamp(12px,3.5vw,20px) sans-serif';button.appendChild(label);", 'hammer counter placement')
    s, count = re.subn(r"    var responsive=document\.createElement\('style'\);responsive\.textContent=.*?;document\.head\.appendChild\(responsive\);\n", '', s)
    if count != 1:
        raise ValueError('unexpected hammer responsive style')
    s = replace_once(s, 'level.data>=7&&!ended;button.style.display',
        "level.data>=7&&!ended&&!(r.all_global_vars.find(function(v){return v.name==='pause';})||{}).data;button.style.display",
        'hammer pause visibility')
    s = replace_once(s,
        "button.style.display=show?'flex':'none';label.textContent=String(stock());button.disabled=!!(show&&!ready(r));if(message&&Date.now()-lastMessage>1800)message.style.opacity='0';",
        "var display=show?'flex':'none',count=String(stock()),disabled=!!(show&&!ready(r));if(button.style.display!==display)button.style.display=display;if(label.textContent!==count)label.textContent=count;if(button.disabled!==disabled)button.disabled=disabled;if(message&&Date.now()-lastMessage>1800&&message.style.opacity!=='0')message.style.opacity='0';",
        'avoid unchanged hammer DOM writes')
    hammer.write_text(s, encoding='utf8', newline='\n')

    guide = root / 'tutorial-seventh.js'
    s = replace_once(guide.read_text(encoding='utf8'),
        "document.querySelector('#oc-hammer svg')", "document.querySelector('#oc-hammer img')", 'hammer tutorial')
    guide.write_text(s, encoding='utf8', newline='\n')
    for name in ('tutorial-fifth.js', 'tutorial-tenth.js'):
        guide = root / name
        s = guide.read_text(encoding='utf8')
        before = 'rect.left+l.layerToCanvas(t.x+t.width*v[0],t.y+t.height*v[1],true),rect.top+l.layerToCanvas(t.x+t.width*v[0],t.y+t.height*v[1],false)'
        after = ('rect.left+l.layerToCanvas(t.x+t.width*v[0],t.y+t.height*v[1],true)*(r.isRetina?r.devicePixelRatio:1)*rect.width/r.canvas.width,'
                 'rect.top+l.layerToCanvas(t.x+t.width*v[0],t.y+t.height*v[1],false)*(r.isRetina?r.devicePixelRatio:1)*rect.height/r.canvas.height')
        guide.write_text(replace_once(s, before, after, name + ' canvas coordinates'), encoding='utf8', newline='\n')
    for name, before, after in (
        ('tutorial-second.js',
         'rect.left+layer.layerToCanvas(x,y,true),rect.top+layer.layerToCanvas(x,y,false)',
         'rect.left+layer.layerToCanvas(x,y,true)*(r.isRetina?r.devicePixelRatio:1)*rect.width/r.canvas.width,rect.top+layer.layerToCanvas(x,y,false)*(r.isRetina?r.devicePixelRatio:1)*rect.height/r.canvas.height'),
        ('tutorial-third.js',
         'rect.left+layer.layerToCanvas(p[0],p[1],true),rect.top+layer.layerToCanvas(p[0],p[1],false)',
         'rect.left+layer.layerToCanvas(p[0],p[1],true)*(r.isRetina?r.devicePixelRatio:1)*rect.width/r.canvas.width,rect.top+layer.layerToCanvas(p[0],p[1],false)*(r.isRetina?r.devicePixelRatio:1)*rect.height/r.canvas.height'),
    ):
        guide = root / name
        guide.write_text(replace_once(guide.read_text(encoding='utf8'), before, after, name + ' canvas coordinates'), encoding='utf8', newline='\n')
    guide = root / 'tutorial-second.js'
    s = guide.read_text(encoding='utf8')
    s = replace_once(s, 'function findPair(tiles) {', 'function findPair(tiles,step) {\n    step=Number.isFinite(step)&&step>0?step:101;', 'second guide configurable spacing')
    s = replace_once(s,
        "var grid = new Map(), points = tiles.map(function(t){var x=xs.indexOf(Math.round(t.x))+1,y=ys.indexOf(Math.round(t.y))+1;grid.set(x+','+y,t);return {x:x,y:y,t:t};});",
        "var width=Math.round((xs[xs.length-1]-xs[0])/step)+1,height=Math.round((ys[ys.length-1]-ys[0])/step)+1;var grid = new Map(), points = tiles.map(function(t){var x=Math.round((t.x-xs[0])/step)+1,y=Math.round((t.y-ys[0])/step)+1;grid.set(x+','+y,t);return {x:x,y:y,t:t};});",
        'second guide preserve empty rows and columns')
    s = replace_once(s, 'x>xs.length+1||y>ys.length+1', 'x>width+1||y>height+1', 'second guide sparse grid bounds')
    s = replace_once(s, 'xs[0]+(p[0]-1)*101,ys[0]+(p[1]-1)*101', 'xs[0]+(p[0]-1)*step,ys[0]+(p[1]-1)*step', 'second guide path spacing')
    s = replace_once(s, "var game=r&&r.running_layout&&r.running_layout.name==='game'&&level&&level.data===2;",
        "var game=r&&r.running_layout&&r.running_layout.name==='game'&&level&&level.data===2;var size=r&&r.all_global_vars.find(function(v){return v.name==='ITEM_SIZE';}),gap=r&&r.all_global_vars.find(function(v){return v.name==='ITEM_SPACING';});var step=size&&gap&&Number.isFinite(size.data)&&Number.isFinite(gap.data)&&size.data+gap.data>0?size.data+gap.data:101;", 'second guide runtime spacing')
    s = replace_once(s, 'findPair(r.types.t5.instances)', 'findPair(r.types.t5.instances,step)', 'second guide use runtime spacing')
    s = replace_once(s, 'screen(t.x+101,t.y)', 'screen(t.x+step,t.y)', 'second guide highlight spacing')
    s = replace_once(s,
        "circles[i].setAttribute('cx',p[0]);circles[i].setAttribute('cy',p[1]);circles[i].setAttribute('r',Math.hypot(edge[0]-p[0],edge[1]-p[1])*.46);",
        "var size=Math.hypot(edge[0]-p[0],edge[1]-p[1])*1.08;circles[i].setAttribute('x',p[0]-size/2);circles[i].setAttribute('y',p[1]-size/2);circles[i].setAttribute('width',size);circles[i].setAttribute('height',size);",
        'second guide frame placement')
    s = replace_once(s,
        "var c=document.createElementNS(ns,'circle');c.setAttribute('fill','none');c.setAttribute('stroke','#ffe35f');c.setAttribute('stroke-width','4');",
        "var c=document.createElementNS(ns,'image');c.setAttribute('href','images/mark-sheet0.webp');c.style.cssText='filter:sepia(1) saturate(4) hue-rotate(355deg) brightness(1.15);animation:oc-guide-frame-pulse .3s linear infinite;transform-box:fill-box;transform-origin:center';",
        'second guide frame artwork')
    s = replace_once(s, '  function frame() {',
        '  var frameQueued=false;function schedule(){if(!frameQueued){frameQueued=true;requestAnimationFrame(frame)}}\n  function frame() {\n    frameQueued=false;', 'second guide scheduler')
    if s.count('    requestAnimationFrame(frame);') != 2:
        raise ValueError('unexpected second guide frame requests')
    s = s.replace('    requestAnimationFrame(frame);', '    if(pending||active)schedule();', 1)
    s = s.replace('    requestAnimationFrame(frame);', '', 1)
    s = replace_once(s, 'dismiss();pending=!completed();', 'dismiss();pending=!completed();if(pending)schedule();', 'second guide activation')
    s = replace_once(s, "var completionKey = 'oneconnect.tutorial2.candidate.v1';",
        "var expectedTiles=0, waitingFrames=0, shuffling=false;\n  var completionKey = 'oneconnect.tutorial2.candidate.v1';", 'second guide expected count')
    s = replace_once(s,
        'if(pending && game && r.types.t5.instances.length===30){var pair=findPair(r.types.t5.instances,step);pending=false;if(pair){target=pair.tiles;route=pair.path;active=true;}}',
        "if(pending && game && !shuffling && !(window.oneConnectShuffleMotionCandidate&&window.oneConnectShuffleMotionCandidate.state().moving)){if(r.types.t5.instances.length===expectedTiles){var pair=findPair(r.types.t5.instances,step);pending=false;if(pair){target=pair.tiles;route=pair.path;active=true;}else if(window.oneConnectHost)window.oneConnectHost.emit('candidate.tutorial2_no_pair',{level:2,tiles:expectedTiles});}else if(++waitingFrames>300){pending=false;if(window.oneConnectHost)window.oneConnectHost.emit('candidate.tutorial2_wait_timeout',{expected:expectedTiles,actual:r.types.t5.instances.length});}}",
        'second guide restored count and bounded wait')
    s = replace_once(s, "if(x.type==='game.board_configured'&&x.detail.level===2){dismiss();pending=!completed();if(pending)schedule();}",
        "if(x.type==='game.board_configured'&&x.detail.level===2){dismiss();expectedTiles=x.detail.tileCount;waitingFrames=0;shuffling=false;pending=!completed()&&Number.isInteger(expectedTiles)&&expectedTiles>=2;if(pending)schedule();}else if(x.type==='game.auto_shuffle_start'){dismiss();shuffling=true;}else if(x.type==='game.auto_shuffle_exhausted'||x.type==='game.auto_shuffle_expired'){shuffling=false;dismiss();}else if(x.type==='game.hammer'&&x.detail&&x.detail.level===2){dismiss();expectedTiles=Math.max(0,expectedTiles-2);waitingFrames=0;pending=!completed()&&expectedTiles>=2;if(pending)schedule();}else if(x.type==='game.auto_shuffle_complete'){shuffling=false;var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),v=r&&r.all_global_vars.find(function(v){return v.name==='level';});if(x.detail&&x.detail.level===2&&v&&v.data===2&&!completed()){waitingFrames=0;pending=expectedTiles>=2;if(pending)schedule();}}",
        'second guide shuffle lifecycle')
    guide.write_text(s, encoding='utf8', newline='\n')
    guide = root / 'tutorial-first.js'
    s = guide.read_text(encoding='utf8')
    s = replace_once(s, 'var row = Math.round((tile.y-133)/101), col = Math.round((tile.x-89)/101);',
        "var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),vars=r&&r.all_global_vars;function value(name){var v=Array.isArray(vars)&&vars.find(function(x){return x.name===name;});return v&&v.data;}var size=value('ITEM_SIZE'),gap=value('ITEM_SPACING'),ox=value('BOARD_OFFSET_X'),oy=value('BOARD_OFFSET_Y');var valid=[size,gap,ox,oy].every(Number.isFinite)&&size>0&&gap>=0;var pitch=valid?size+gap:101,originX=valid?ox+gap+size/2:89,originY=valid?oy+gap+size/2:133;var row=Math.round((tile.y-originY)/pitch),col=Math.round((tile.x-originX)/pitch);",
        'first guide runtime grid geometry')
    s = replace_once(s, 'window.oneConnectTutorial={install:install,', 'window.oneConnectTutorial={slot:slot,install:install,', 'first guide testable slot mapping')
    s = replace_once(s, "cursor=document.createElement('div');cursor.textContent='☝';",
        "cursor=document.createElement('div');cursor.setAttribute('data-ui-tutorial-cursor','');", 'tutorial hand')
    s = replace_once(s, "if(skipButton)skipButton.style.display=step>=4?'block':'none';",
        "if(skipButton)skipButton.style.display='block';", 'tutorial skip availability')
    # Explain that the highlighted pair is an illustration, then guide the
    # next connectable pair. The demonstration blocks input only briefly.
    s = replace_once(s, 'demoRemaining=step===3?1800:0;', 'demoRemaining=step===3?3000:0;', 'tutorial resume blocked-pair demo')
    s = replace_once(s, 'if(step===3)demoRemaining=1800;', 'if(step===3)demoRemaining=3000;', 'tutorial blocked-pair demo duration')
    s = replace_once(s, "'These tiles cannot connect yet'", "'Blocked! Clear other pairs first.'", 'tutorial blocked-pair explanation')
    s = replace_once(s,
        'border:4px solid #ffde58;border-radius:16px;box-shadow:0 0 14px #fff391;transform:translate(-50%,-50%);pointer-events:none',
        'background:url("images/mark-sheet0.webp") center/100% 100% no-repeat;filter:sepia(1) saturate(4) hue-rotate(355deg) brightness(1.15);animation:oc-guide-frame-centered .3s linear infinite;transform:translate(-50%,-50%);pointer-events:none',
        'first guide frame artwork')
    for before, after in (
        ('var rect=r.canvas.getBoundingClientRect(),targets=current()', 'var rect=r.canvas.getBoundingClientRect(),sx=(r.isRetina?r.devicePixelRatio:1)*rect.width/r.canvas.width,sy=(r.isRetina?r.devicePixelRatio:1)*rect.height/r.canvas.height,targets=current()'),
        ('dtile.layer.layerToCanvas(dtile.x+101,dtile.y,true)-dx,dtile.layer.layerToCanvas(dtile.x+101,dtile.y,false)-dy', '(dtile.layer.layerToCanvas(dtile.x+Math.abs(dtile.width),dtile.y,true)-dx)*sx,(dtile.layer.layerToCanvas(dtile.x+Math.abs(dtile.width),dtile.y,false)-dy)*sy'),
        ('tile.layer.layerToCanvas(tile.x+101,tile.y,true)-x,tile.layer.layerToCanvas(tile.x+101,tile.y,false)-y', '(tile.layer.layerToCanvas(tile.x+Math.abs(tile.width),tile.y,true)-x)*sx,(tile.layer.layerToCanvas(tile.x+Math.abs(tile.width),tile.y,false)-y)*sy'),
        ('rect.left+dx', 'rect.left+dx*sx'), ('rect.top+dy', 'rect.top+dy*sy'),
        ('rect.left+x', 'rect.left+x*sx'), ('rect.top+y', 'rect.top+y*sy'),
        ('rect.left+target.layer.layerToCanvas(target.x,target.y,true)', 'rect.left+target.layer.layerToCanvas(target.x,target.y,true)*sx'),
        ('rect.top+target.layer.layerToCanvas(target.x,target.y,false)', 'rect.top+target.layer.layerToCanvas(target.x,target.y,false)*sy'),
    ):
        s = replace_once(s, before, after, 'first tutorial canvas coordinates')
    # Inactive tutorials previously requested a frame throughout every level.
    # A pending final frame still hides the overlay on completion or failure.
    s = replace_once(s, '  function draw() {',
        '  var frameQueued=false; function schedule(){if(!frameQueued){frameQueued=true;requestAnimationFrame(draw)}}\n  function draw() {\n    frameQueued=false;', 'first tutorial frame scheduler')
    s = replace_once(s, '    requestAnimationFrame(draw);\n  }',
        '    if(active)schedule();\n  }', 'first tutorial idle scheduling')
    s = replace_once(s, 'if(installed)return;installed=true;setupUI();requestAnimationFrame(draw);',
        'if(installed)return;installed=true;setupUI();', 'first tutorial install scheduling')
    s = replace_once(s, "window.oneConnectHost.emit('tutorial.start',{level:1})}",
        "window.oneConnectHost.emit('tutorial.start',{level:1});schedule()}", 'first tutorial activation scheduling')
    s = replace_once(s, "else if(event.type==='game.match' && active){", "else if(event.type==='game.match' && active && event.detail && event.detail.level===1){", 'first tutorial match level guard')
    s = replace_once(s, "else if(event.type==='game.level_fail')active=false;",
        "else if(event.type==='game.level_fail'||event.type==='game.level_win'||event.type==='game.round_ready'||event.type==='game.board_configured'){if(active){active=false;if(panel)panel.style.display='none';if(window.oneConnectHost)window.oneConnectHost.emit('tutorial.cancelled',{level:1});}}",
        'first tutorial round transition cleanup')
    s = replace_once(s, "    var visible=active && r && r.running_layout",
        "    if(active&&r&&r.running_layout&&r.running_layout.name!=='game'){active=false;if(panel)panel.style.display='none';if(window.oneConnectHost)window.oneConnectHost.emit('tutorial.cancelled',{level:1});return;}\n    var visible=active && r && r.running_layout", 'first tutorial cancel after leaving gameplay')
    s = replace_once(s, "if(!ok || !active || !type)return ok;if(type.name==='t26')return false;",
        "if(!ok || !active || !type)return ok;var rt=window.cr_getC2Runtime&&window.cr_getC2Runtime();if(rt&&rt.running_layout&&rt.running_layout.name!=='game')return ok;if(type.name==='t26')return false;", 'first tutorial release input outside gameplay')
    s = replace_once(s, "  function done() {", "  var missingTargetMs=0,missingTargetLast=null;\n  function done() {", 'first tutorial missing target state')
    s = replace_once(s, 'targets=current(),tiles=r.types.t5.instances,nonTargets=tiles.filter',
        'targets=current(),tileList=r.types&&r.types.t5&&r.types.t5.instances,tiles=Array.isArray(tileList)?tileList:[],nonTargets=tiles.filter', 'first tutorial tolerate missing tile type')
    s = replace_once(s, 'var target=tiles.find(function(t){return slot(t)===targets[Math.floor(Date.now()/900)%2]});',
        "var missing=targets.length!==2||targets.some(function(n){return !tiles.some(function(t){return slot(t)===n;});});if(missing){if(!document.hidden){if(missingTargetLast!==null)missingTargetMs+=Math.max(0,now-missingTargetLast);missingTargetLast=now;if(missingTargetMs>=5000){active=false;if(panel)panel.style.display='none';if(window.oneConnectHost){window.oneConnectHost.emit('tutorial.cancelled',{level:1});window.oneConnectHost.emit('candidate.tutorial1_target_missing',{level:1});}return;}}else missingTargetLast=null;}else{missingTargetMs=0;missingTargetLast=null;}var target=tiles.find(function(t){return slot(t)===targets[Math.floor(Date.now()/900)%2]});", 'first tutorial missing target escape')
    s = replace_once(s, '    if(active)schedule();\n  }', '    if(!visible||document.hidden)missingTargetLast=null;\n    if(active)schedule();\n  }', 'first tutorial pause missing target budget')
    s = replace_once(s, 'if(installed)return;installed=true;setupUI();', "if(installed)return;installed=true;setupUI();if(document.addEventListener)document.addEventListener('visibilitychange',function(){if(document.hidden)missingTargetLast=null;});", 'first tutorial reset on background')
    s = replace_once(s, "active=true;step=Number.isInteger(event.detail.tutorialStep)", "missingTargetMs=0;missingTargetLast=null;active=true;step=Number.isInteger(event.detail.tutorialStep)", 'first tutorial reset target budget')
    s = replace_once(s, "event.type==='game.level_fail'||event.type==='game.level_win'", "event.type==='screen.SCREEN_BONUS'||event.type==='game.level_fail'||event.type==='game.level_win'", 'first tutorial cancel on bonus screen')
    guide.write_text(s, encoding='utf8', newline='\n')
    # Other one-shot guides need frames only between activation and dismissal.
    for name, level, raf in (
        ('tutorial-third.js', 3, 'requestAnimationFrame'),
        ('tutorial-fifth.js', 5, 'requestAnimationFrame'),
        ('tutorial-seventh.js', 7, 'window.requestAnimationFrame'),
        ('tutorial-tenth.js', 10, 'requestAnimationFrame'),
    ):
        guide = root / name
        s = guide.read_text(encoding='utf8')
        s = replace_once(s, 'function frame(){',
            'var frameQueued=false;function schedule(){if(!frameQueued){frameQueued=true;'+raf+'(frame)}}\n  function frame(){frameQueued=false;', name + ' scheduler')
        call = raf + '(frame);'
        if s.count(call) != 2:
            raise ValueError('unexpected ' + name + ' frame requests')
        s = s.replace(call, 'if(active)schedule();', 1)
        s = s.replace(call, '', 1)
        s = replace_once(s, "active=true;window.oneConnectHost.emit('tutorial.start',{level:"+str(level)+"});",
            "active=true;schedule();window.oneConnectHost.emit('tutorial.start',{level:"+str(level)+"});", name + ' activation')
        if level in (3, 5, 7, 10):
            old_exit = "else if(x.type==='game.level_fail'){active=false;}" if level == 3 else "else if(x.type==='game.level_fail')active=false;"
            s = replace_once(s, old_exit,
                "else if(x.type==='game.level_fail'||x.type==='game.level_win'||x.type==='game.round_ready'||x.type==='game.board_configured'){if(active){active=false;if(overlay)overlay.style.display='none';if(window.oneConnectHost)window.oneConnectHost.emit('tutorial.cancelled',{level:"+str(level)+"});}}",
                name + ' end or replace guide on round change')
        if level in (3, 7):
            s = replace_once(s, 'function frame(){frameQueued=false;',
                "function frame(){frameQueued=false;var current=window.cr_getC2Runtime&&window.cr_getC2Runtime();if(active&&current&&current.running_layout&&current.running_layout.name!=='game'){active=false;if(overlay)overlay.style.display='none';if(window.oneConnectHost)window.oneConnectHost.emit('tutorial.cancelled',{level:"+str(level)+"});return;}",
                name + ' cancel after leaving gameplay')
        if level == 3:
            s = replace_once(s,
                "var text=r.types.t25.instances.find(function(t){return t.instance_vars&&t.instance_vars[0]===1;}),clock=r.types.t24.instances.find(function(t){return t.cur_frame===1;});",
                "var types=r.types||{},texts=types.t25&&types.t25.instances||[],clocks=types.t24&&types.t24.instances||[],text=texts.find(function(t){return t.instance_vars&&t.instance_vars[0]===1;}),clock=clocks.find(function(t){return t.cur_frame===1;});", 'third guide tolerate missing targets')
            s = replace_once(s, 'if(text&&clock){var rect=', "if(text&&clock){highlight.style.display='block';overlay.style.background='';var rect=", 'third guide restore highlight')
            s = replace_once(s, "      overlay.style.display='block';", "      else{highlight.style.display='none';overlay.style.background='rgba(4,10,30,.72)';}\n      overlay.style.display='block';", 'third guide preserve dim when highlight missing')
        if level in (5, 10):
            s = replace_once(s,
                "pause=r&&variable(r,'pause');if(active&&r&&r.running_layout&&r.running_layout.name==='game'",
                "pause=r&&variable(r,'pause');if(active&&r&&r.running_layout&&r.running_layout.name!=='game'){active=false;if(overlay)overlay.style.display='none';if(window.oneConnectHost)window.oneConnectHost.emit('tutorial.cancelled',{level:"+str(level)+"});return;}if(active&&r&&r.running_layout&&r.running_layout.name==='game'",
                name + ' cancel after leaving gameplay')
            s = replace_once(s,
                "if(!ok||!active||!type||(pause&&pause.data))return ok;",
                "if(!ok||!active||!type||(r&&r.running_layout&&r.running_layout.name!=='game')||(pause&&pause.data))return ok;",
                name + ' release input outside gameplay')
            s = replace_once(s, "if(type.name!=='t26')return false;",
                "if(type.name==='t21')return ok;if(type.name!=='t26')return false;", name + ' allow native pause button')
        if level == 5:
            s = replace_once(s, "var key='oneconnect.tutorial5", "var missingTargetFrames=0;\n  var key='oneconnect.tutorial5", 'fifth guide missing target counter')
            s = replace_once(s, 'active=false,installed=false,overlay,highlight;', 'active=false,installed=false,overlay,highlight,label,free;', 'fifth guide status elements')
            s = replace_once(s, "var label=document.createElement('div');", "label=document.createElement('div');", 'fifth guide status label')
            s = replace_once(s, "var free=document.createElement('div');", "free=document.createElement('div');", 'fifth guide free label')
            s = replace_once(s, "var t=r.types.t26.instances.find(function(x){return x.cur_frame===1;});if(t){",
                "var targets=r.types.t26&&r.types.t26.instances,t=targets&&targets.find(function(x){return x.cur_frame===1;});if(!t){if(++missingTargetFrames>300){active=false;overlay.style.display='none';if(window.oneConnectHost){window.oneConnectHost.emit('tutorial.cancelled',{level:5});window.oneConnectHost.emit('candidate.tutorial5_target_missing',{level:5});}}else{highlight.style.display='none';label.textContent='Getting hint ready...';free.style.display='none';overlay.style.display='block';}if(active)schedule();return;}missingTargetFrames=0;highlight.style.display='block';label.textContent='Tap the hint to find a matching pair';free.style.display='block';if(t){",
                'fifth guide missing target escape')
            s = replace_once(s, "active=true;schedule();window.oneConnectHost.emit('tutorial.start',{level:5});",
                "missingTargetFrames=0;active=true;schedule();window.oneConnectHost.emit('tutorial.start',{level:5});", 'fifth guide reset missing target counter')
            s = replace_once(s, 'var missingTargetFrames=0;', 'var missingTargetMs=0,missingTargetLast=null;', 'fifth guide elapsed timeout state')
            s = replace_once(s, 'function frame(){frameQueued=false;', 'function frame(now){frameQueued=false;now=Number.isFinite(now)?now:Date.now();', 'fifth guide animation timestamp')
            s = replace_once(s, "r.running_layout.name==='game'&&!(pause&&pause.data)", "r.running_layout.name==='game'&&!document.hidden&&!(pause&&pause.data)", 'fifth guide foreground time only')
            s = replace_once(s, 'if(++missingTargetFrames>300)', 'if(missingTargetLast!==null)missingTargetMs+=Math.max(0,now-missingTargetLast);missingTargetLast=now;if(missingTargetMs>=5000)', 'fifth guide five second timeout')
            s = s.replace('missingTargetFrames=0;', 'missingTargetMs=0;missingTargetLast=null;')
            s = replace_once(s, "}else if(overlay)overlay.style.display='none';if(active)schedule();}", "}else{missingTargetLast=null;if(overlay)overlay.style.display='none';}if(active)schedule();}", 'fifth guide pause timeout')
            s = replace_once(s, 'function install(){if(installed)return;installed=true;', "function install(){if(installed)return;installed=true;if(document.addEventListener)document.addEventListener('visibilitychange',function(){if(document.hidden)missingTargetLast=null;});", 'fifth guide reset on background')
            s = replace_once(s, "highlight.style.height=Math.max(0,bottom-top)+'px';", "highlight.style.height=Math.max(0,bottom-top)+'px';free.style.left=((left+right)/2)+'px';free.style.top=Math.max(4,top-6)+'px';", 'fifth guide free label follows hint')
            s = replace_once(s, "position:absolute;top:30%;left:0;width:100%;text-align:center;color:#ffeb74;", "position:absolute;left:0;top:0;transform:translate(-50%,-100%);text-align:center;color:#ffeb74;", 'fifth guide free label anchor')
        if level == 10:
            s = replace_once(s, "var key='oneconnect.tutorial10", "var missingTargetMs=0,missingTargetLast=null;\n  var key='oneconnect.tutorial10", 'tenth guide elapsed timeout state')
            s = replace_once(s, 'active=false,installed=false,overlay,highlight;', 'active=false,installed=false,overlay,highlight,label,free;', 'tenth guide status elements')
            s = replace_once(s, "var label=document.createElement('div');", "label=document.createElement('div');", 'tenth guide status label')
            s = replace_once(s, "var free=document.createElement('div');", "free=document.createElement('div');", 'tenth guide free label')
            s = replace_once(s, 'function frame(){frameQueued=false;', 'function frame(now){frameQueued=false;now=Number.isFinite(now)?now:Date.now();', 'tenth guide animation timestamp')
            s = replace_once(s, "r.running_layout.name==='game'&&!(pause&&pause.data)", "r.running_layout.name==='game'&&!document.hidden&&!(pause&&pause.data)", 'tenth guide foreground time only')
            s = replace_once(s, "var t=r.types.t26.instances.find(function(x){return x.cur_frame===0;});if(t){",
                "var targets=r.types.t26&&r.types.t26.instances,t=targets&&targets.find(function(x){return x.cur_frame===0;});if(!t){if(missingTargetLast!==null)missingTargetMs+=Math.max(0,now-missingTargetLast);missingTargetLast=now;if(missingTargetMs>=5000){active=false;overlay.style.display='none';if(window.oneConnectHost){window.oneConnectHost.emit('tutorial.cancelled',{level:10});window.oneConnectHost.emit('candidate.tutorial10_target_missing',{level:10});}}else{highlight.style.display='none';label.textContent='Getting shuffle ready...';free.style.display='none';overlay.style.display='block';}if(active)schedule();return;}missingTargetMs=0;missingTargetLast=null;highlight.style.display='block';label.textContent='Tap shuffle to rearrange the tiles';free.style.display='block';if(t){",
                'tenth guide missing target escape')
            s = replace_once(s, "active=true;schedule();window.oneConnectHost.emit('tutorial.start',{level:10});", "missingTargetMs=0;missingTargetLast=null;active=true;schedule();window.oneConnectHost.emit('tutorial.start',{level:10});", 'tenth guide reset timeout')
            s = replace_once(s, "}else if(overlay)overlay.style.display='none';if(active)schedule();}", "}else{missingTargetLast=null;if(overlay)overlay.style.display='none';}if(active)schedule();}", 'tenth guide pause timeout')
            s = replace_once(s, 'function install(){if(installed)return;installed=true;', "function install(){if(installed)return;installed=true;if(document.addEventListener)document.addEventListener('visibilitychange',function(){if(document.hidden)missingTargetLast=null;});", 'tenth guide reset on background')
        if level in (5, 10):
            s = replace_once(s, 'var targets=r.types.t26&&r.types.t26.instances', 'var targets=r.types&&r.types.t26&&r.types.t26.instances', name + ' tolerate missing runtime types')
            s = replace_once(s, 't=targets&&targets.find(', "t=r.canvas&&typeof r.canvas.getBoundingClientRect==='function'&&r.canvas.width>0&&r.canvas.height>0&&targets&&targets.find(", name + ' tolerate unavailable canvas')
            frame = '1' if level == 5 else '0'
            s = replace_once(s, 'targets.find(function(x){return x.cur_frame===' + frame + ';})',
                             "targets.find(function(x){return x&&x.cur_frame===" + frame + "&&x.layer&&typeof x.layer.layerToCanvas==='function'&&Number.isFinite(x.x)&&Number.isFinite(x.y)&&Number.isFinite(x.width)&&Number.isFinite(x.height)&&x.width!==0&&x.height!==0;})", name + ' validate target geometry')
            s = replace_once(s, "highlight.style.display='none';label.textContent='Getting", "highlight.style.display='none';overlay.style.background='rgba(4,10,30,.72)';label.textContent='Getting", name + ' preserve dim when target missing')
            s = replace_once(s, "highlight.style.display='block';label.textContent='Tap", "highlight.style.display='block';overlay.style.background='';label.textContent='Tap", name + ' restore highlight without double dim')
        event_var = 'event' if level == 1 else 'x'
        s = replace_once(s, event_var + ".type==='game.level_fail'||" + event_var + ".type==='game.level_win'",
                         event_var + ".type==='screen.SCREEN_BONUS'||" + event_var + ".type==='game.level_fail'||" + event_var + ".type==='game.level_win'",
                         name + ' cancel on bonus screen')
        guide.write_text(s, encoding='utf8', newline='\n')
    second_guide = root / 'tutorial-second.js'
    second_text = second_guide.read_text(encoding='utf8')
    second_text = replace_once(second_text, "x.type==='game.shuffle'||x.type==='game.level_fail'",
                               "x.type==='game.shuffle'||x.type==='game.level_fail'||x.type==='game.level_win'||x.type==='screen.SCREEN_BONUS'",
                               'second guide cancel on round end')
    second_text = replace_once(second_text, 'var expectedTiles=0, waitingFrames=0, shuffling=false;',
                               'var expectedTiles=0, waitingFrames=0, shuffling=false, roundEnded=false;', 'second guide round state')
    second_text = replace_once(second_text, '    if(pending && game && !shuffling',
                               "    if(pending&&r&&r.running_layout&&(r.running_layout.name!=='game'||(level&&level.data!==2)))dismiss();\n    if(pending && game && !shuffling", 'second guide stop waiting outside level')
    second_text = replace_once(second_text, "if(x.type==='game.board_configured'&&x.detail.level===2){dismiss();",
                               "if(x.type==='game.board_configured'&&x.detail.level===2){roundEnded=false;dismiss();", 'second guide new round')
    second_text = replace_once(second_text, "else if(x.type==='game.hammer'&&x.detail&&x.detail.level===2)",
                               "else if(!roundEnded&&x.type==='game.hammer'&&x.detail&&x.detail.level===2)", 'second guide ignore late hammer')
    second_text = replace_once(second_text, "else if(x.type==='game.auto_shuffle_complete'){shuffling=false;",
                               "else if(!roundEnded&&x.type==='game.auto_shuffle_complete'){shuffling=false;", 'second guide ignore late shuffle')
    second_text = replace_once(second_text, "else if(x.type==='game.match'){if(x.detail.level===2",
                               "else if(!roundEnded&&x.type==='game.match'){if(x.detail.level===2", 'second guide ignore late match')
    second_text = replace_once(second_text, "else if(x.type==='game.shuffle'||x.type==='game.level_fail'||x.type==='game.level_win'||x.type==='screen.SCREEN_BONUS')dismiss();",
                               "else if(x.type==='game.level_fail'||x.type==='game.level_win'||x.type==='screen.SCREEN_BONUS'){roundEnded=true;dismiss();}else if(x.type==='game.shuffle')dismiss();", 'second guide end round state')
    second_guide.write_text(second_text, encoding='utf8', newline='\n')
    clean_tile_gutters(root)
    ramadan_png = root / 'images/ramadan-tiles.png'
    ramadan_path = root / 'images/ramadan-tiles.webp'
    build_ramadan_atlas(ramadan_png)
    with Image.open(ramadan_png) as source:
        rgba = source.convert('RGBA')
        rgba.save(ramadan_path, format='WEBP', lossless=True, method=6, exact=True)
        with Image.open(ramadan_path) as encoded:
            if encoded.convert('RGBA').tobytes() != rgba.tobytes():
                raise ValueError('Ramadan atlas conversion changed pixels')
    if ramadan_path.stat().st_size >= ramadan_png.stat().st_size:
        raise ValueError('Ramadan atlas conversion did not reduce size')
    ramadan_png.unlink()
    data_path = root / 'data.js'
    data = json.loads(data_path.read_text(encoding='utf8'))
    data = add_ramadan_animation(data, 'images/ramadan-tiles.webp', ramadan_path.stat().st_size, 987654321234567)
    (root / 'native-path-sids.js').write_text('window.oneConnectNativePathSids='+json.dumps(native_path_event_sids(data), separators=(',', ':'))+';', encoding='utf8')
    data = add_pause_close_wait(data, (root / 'c2runtime.js').read_text(encoding='utf8'))
    data = enable_native_dot_fade(data)
    data = shorten_no_match_transition(data)
    verify_gravity_native_actions(data)
    data_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    verify_original_fx(root, PROJECT / 'baseline')
    compress_ui_images(root)
    reuse_timeout_clock(root)
    compress_reserve_atlas(root)
    reuse_identical_particle_texture(root)
    synchronize_converted_texture_sizes(root)
    if optimized_images is not None:
        apply_verified_lossless_images(root, optimized_images)
    if visual_images is not None:
        if not visual_report or not visual_reference: raise ValueError('visual compression requires report and reference images')
        apply_verified_visual_images(root, visual_images, visual_report, visual_reference)
        # Refresh all affected C2 preload weights after the final compression.
        synchronize_all_texture_sizes(root)
    if experimental_starfield:
        # Isolated A/B candidate only: share the existing menu frame loop and
        # leave ordinary builds static until real-device cost is measured.
        shutil.copyfile(PROJECT / 'tools/menu_starfield_experiment.js', root / 'menu-starfield-experiment.js')
        menu = root / 'menu-progress.js'
        text = menu.read_text(encoding='utf8')
        needle = "t=r&&r.types.t25&&r.types.t25.instances[0];if(r&&r.running_layout"
        replacement = "t=r&&r.types.t25&&r.types.t25.instances[0];var now=performance.now(),dt=window.ocStarLast==null?0:(now-window.ocStarLast)/1000;window.ocStarLast=document.hidden?null:now;window.oneConnectMenuStarfieldExperiment.update(r,dt,!document.hidden);if(r&&r.running_layout"
        menu.write_text(replace_once(text, needle, replacement, 'experimental starfield menu tick'), encoding='utf8', newline='\n')
        page = root / 'game.html'
        html = page.read_text(encoding='utf8')
        html = replace_once(html, '<script src="menu-progress.js"></script>', '<script src="menu-starfield-experiment.js"></script>\n    <script src="menu-progress.js"></script>', 'experimental starfield script')
        page.write_text(html, encoding='utf8', newline='\n')
    verify_literal_image_references(root)
    if combi_sdk_zip is not None:
        import zipfile
        with zipfile.ZipFile(combi_sdk_zip) as sdk:
            wrapper = sdk.read('index.html')
        (destination / 'index.html').write_bytes(wrapper)
        shutil.copyfile(root / 'game.html', root / 'index.html')
    version, count = build(root)
    return root, version, count


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, help='new directory inside analysis')
    parser.add_argument('--pools', help='JSON object mapping generated level numbers to available tile IDs')
    parser.add_argument('--combi-sdk-zip', help='original CombiMons.zip; include its unchanged host wrapper')
    parser.add_argument('--optimized-images', help='lossless image outputs, verified against candidate pixels')
    parser.add_argument('--visual-images', help='quality-gated visual compression outputs')
    parser.add_argument('--visual-report', help='image-compress quality report')
    parser.add_argument('--visual-reference', help='original image directory used by the quality report')
    parser.add_argument('--experimental-starfield', action='store_true', help='build a separate starfield performance comparison candidate')
    args = parser.parse_args()
    candidate, version, count = prepare(args.output, args.pools, args.combi_sdk_zip, args.optimized_images, args.visual_images, args.visual_report, args.visual_reference, args.experimental_starfield)
    print(f'candidate {candidate}\noffline cache {version}; {count} files')
