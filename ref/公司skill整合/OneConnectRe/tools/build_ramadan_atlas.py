"""Build a lossless 20-frame atlas from the user-approved reserve manifest."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / '美术换皮准备/20261029_四主题换皮'
SOURCE = ART / '斋月_三处修正版_96px'
MANIFEST = ART / '斋月_备用切片清单.json'


def build(destination):
    entries = json.loads(MANIFEST.read_text(encoding='utf8'))['tiles']
    if len(entries) != 20:
        raise ValueError('expected exactly 20 approved frames')
    sheet = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    regions = []
    for index, entry in enumerate(entries):
        expected = f'斋月_{index + 1:02}.png'
        if entry['file'] != expected:
            raise ValueError('unexpected frame order')
        path = SOURCE / expected
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('approved source hash mismatch: ' + expected)
        with Image.open(path) as image:
            if image.mode != 'RGBA' or image.size != (96, 96):
                raise ValueError('invalid tile dimensions or alpha: ' + expected)
            x, y = 1 + (index % 5) * 98, 1 + (index // 5) * 98
            sheet.paste(image, (x, y))
            regions.append((x, y, 96, 96))
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, format='PNG', optimize=True)
    with Image.open(destination) as result:
        for entry, (x, y, w, h) in zip(entries, regions):
            with Image.open(SOURCE / entry['file']) as original:
                if result.crop((x, y, x + w, y + h)).tobytes() != original.tobytes():
                    raise ValueError('atlas pixels differ: ' + entry['file'])
    return regions


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(f'{len(build(args.output))} verified frames: {args.output}')
