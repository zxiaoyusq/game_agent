"""Clear only atlas pixels outside every referenced tile frame, in a copy."""
from pathlib import Path
import json
from PIL import Image, ImageChops, ImageDraw


def clean(root):
    root = Path(root)
    source = (root / 'data.js').read_text(encoding='utf8').strip()
    data = json.loads(source[source.index('{'):].rstrip(';'))
    regions = {}
    for animation in data['project'][3][5][7]:
        for frame in animation[7]:
            name, x, y, width, height = frame[0], *frame[2:6]
            if name in ('images/tiles-reserve-test.png', 'images/tiles-reserve-test.webp', 'images/ramadan-tiles.webp'):
                continue
            if not name.startswith('images/tiles-sheet'):
                raise ValueError('unexpected tile atlas: ' + name)
            regions.setdefault(name, set()).add((x, y, width, height))
    changed = []
    for name, rects in regions.items():
        path = root / name
        image = Image.open(path).convert('RGBA')
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        for x, y, width, height in rects:
            if x < 0 or y < 0 or width < 1 or height < 1 or x + width > image.width or y + height > image.height:
                raise ValueError('tile frame outside atlas')
            draw.rectangle((x, y, x + width - 1, y + height - 1), fill=255)
        alpha = image.getchannel('A')
        cleaned = ImageChops.multiply(alpha, mask)
        if ImageChops.difference(alpha, cleaned).getbbox() is not None:
            image.putalpha(cleaned)
            # Keep alpha lossless while compressing RGB; q94 was selected by
            # measuring visible RGB error against the current WebP input.
            image.save(path, format='WEBP', quality=94, exact=True, method=6)
            changed.append(name)
    return changed
