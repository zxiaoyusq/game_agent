"""Pack already verified RGBA frame images into Construct 2 atlas copies.
Never writes the original atlas; every candidate must be present and exact size.
"""
from pathlib import Path
from PIL import Image
import argparse,csv

def pack_atlases(base, icons, output, rows):
    base, icons, output = Path(base).resolve(), Path(icons).resolve(), Path(output).resolve()
    if output.exists() or output==base or base in output.parents: raise ValueError('output must be a new directory outside original atlas directory')
    if not rows: raise ValueError('empty frame list')
    images, candidates, occupied = {}, [], {}
    for row in rows:
        atlas=Path(row['atlas']); icon=Path(row['icon'])
        if atlas.is_absolute() or icon.is_absolute() or '..' in atlas.parts or '..' in icon.parts: raise ValueError('unsafe path')
        source=base/atlas; candidate=icons/icon
        if not source.is_file() or not candidate.is_file(): raise ValueError('missing source or frame')
        if atlas not in images:
            with Image.open(source) as im: images[atlas]=im.convert('RGBA').copy()
        with Image.open(candidate) as im: frame=im.convert('RGBA').copy()
        x,y,w,h=(int(row[k]) for k in ('x','y','width','height'))
        if w<=0 or h<=0 or x<0 or y<0 or x+w>images[atlas].width or y+h>images[atlas].height or frame.size!=(w,h): raise ValueError('invalid frame size or bounds')
        box=(x,y,x+w,y+h)
        for old in occupied.setdefault(atlas,[]):
            if box[0]<old[2] and old[0]<box[2] and box[1]<old[3] and old[1]<box[3]:raise ValueError('overlapping frame boxes')
        occupied[atlas].append(box);candidates.append((atlas,box,frame))
    for atlas,box,frame in candidates: images[atlas].paste(frame,(box[0],box[1]))
    output.mkdir(parents=True)
    for atlas,image in images.items():
        dst=output/atlas;dst.parent.mkdir(parents=True,exist_ok=True);image.save(dst,format='PNG')
    return len(candidates)

def main():
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--icons',required=True);p.add_argument('--output',required=True);p.add_argument('--mapping',required=True);a=p.parse_args()
    with open(a.mapping,encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    print('packed frames:',pack_atlases(a.base,a.icons,a.output,rows))
if __name__=='__main__': main()
