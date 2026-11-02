# Positioning generated parts on the character

The parts arrive from the image model at their own sizes, in no particular
order, cut to their own content. Two things have to be worked out for each one:
**where it goes** and **how big it should be**. Getting this wrong is the single
most visible failure in the whole pipeline - a collar across the muzzle, a leg
over the eye - so it is worth doing deliberately.

## The problem with fitting parts to the art

The obvious approach is to match each part against the reference art: SIFT
features, or template matching on colour. Both fail here, for reasons worth
understanding before you try to improve them:

* **A generated part is not the art.** It was drawn by a different model in the
  same style; its colours are close but not equal, and its outline is its own.
  Pixel matching therefore has a weak, noisy signal.
* **Flat cartoon parts have no features.** A tan leg with a white paw and a dark
  outline is almost featureless; SIFT finds little, and what it finds it matches
  confidently in the wrong place.
* **The silhouette cannot say which part is which.** Every sub-shape "fits" a
  large blob equally well, so a score like `IoU(part, character_silhouette)` is
  maximised almost anywhere inside the body. Worse, a *whole-character*
  silhouette is a meaningless target for one part: the score is bounded by
  `part_area / character_area` no matter where the part goes.
* **Colour alone confuses small parts.** A gold bell matches tan fur better than
  it matches the brown collar it is supposed to hang from. A collar can slide up
  onto the face if the face has a warmer patch.

## What works: boxes first, geometry second, pixels never

### 1. Read a part-box map off the art (once per character)

Draw a numbered grid over the reference and have a vision model report a box per
part. This is the one reliable way for an agent that cannot see to learn *which
region* belongs to which part.

```bash
python scripts/make_grid.py --image reference.png --out grid.png --cells 20
python scripts/qa_vision.py --prompt "..." --image grid.png     # ask for cell boxes
```

Cell numbers, not pixels. Vision models are good at "the head spans columns 3 to
17 and rows 1 to 9" and bad at "x0=176, y0=76". A 20x20 grid is 5% per cell,
which is plenty: the box only has to be roughly right.

Save the answer as JSON:

```json
{
  "grid": 20,
  "image": "reference.png",
  "parts": {
    "head":  [3, 1, 17, 9],
    "torso": [2, 9, 18, 19],
    "collar": [4, 8.2, 16, 11.2],
    "bell": {"follow": "collar", "anchor": [0.5, 1.0], "offset": [0, 12], "width": 165}
  }
}
```

### 2. Place by box, not by search

```bash
python scripts/position_parts.py --parts parts/ --reference reference.png \
    --out layout.json --name puppy --boxes boxes.json --fit box --order anatomy
```

`--fit box` scales each part uniformly to fit its box and centres it there. That
sounds crude and it is exactly right: the boxes came from looking at the art, so
matching their nesting is worth more than any pixel score. In particular a head
box whose bottom edge is the torso box's top edge makes the two parts *meet*,
where a colour search puts them at opposite edges of their boxes and leaves a
hole where the neck should be.

Use `--fit search` only when you have no boxes and must guess from the art
alone; it refines inside the region it is given.

### 3. Hang attached parts off their parent

Some parts are not "somewhere in the art", they are *attached*: a bell hangs
from a collar, a collar sits at the base of a head. Search cannot get these
right, so describe the relationship instead:

```json
{"follow": "collar", "anchor": [0.5, 1.0], "offset": [0, 12], "width": 165}
```

* `follow` - the part this one is attached to (must be placed first; the driver
  sorts the parts so that it is).
* `anchor` - the point on the parent's placed box, `[0.5, 1.0]` = bottom centre.
* `offset` - pixels from that point, y downwards.
* `width` (or `scale`) - how wide the part should be drawn.

The part's **pivot** is put on that point, not its box centre, because the pivot
*is* the rig's attachment point: a bell's pivot is its loop, a collar's is the
back of the neck. That is what makes "hang from the collar" one line of
geometry.

### 4. Take the draw order from the rig rules

```bash
--order anatomy     # default
--order evidence    # pairwise occlusion voting
```

`anatomy` uses `rig_rules.draw_order_for()`: tail 5, torso 14, legs 24, head 45,
ears 51, collar 60, bell 62. For a character whose limbs hang outside its own
silhouette that is correct, it is deterministic, and it cannot be talked out of
it by a noisy colour comparison.

It is **wrong for a chibi whose limbs are tucked into a round body**, where the
body has to cover the top of each limb - and wrong for ears whose base the dome's
curve cuts. Both are per-part `draw_order` overrides in the box map, which win
over these defaults; see *Drawing limbs behind the body* below.

`evidence` votes on overlapping pairs - whichever part's colours match the art
better across the shared pixels must be in front - and topologically sorts the
result. It is worth trying when a limb genuinely crosses the body in the art,
but note the failure that shaped this default: counting *wins* per part (an
earlier version) gave the torso a win against everything it overlapped, because
it overlaps everything, and drew it on top of the head. Even with a correct
topological sort, small parts lose votes they should win.

## Bugs that produced exactly these symptoms

Keep these in mind, they all look like "the rigging is broken":

* **`image_scale`, not `scale`.** `spine_export.prepare_part` reads
  `part["image_scale"]`. `position_parts` used to compute a scale, use it for
  its own composite score, and write it under a name the exporter ignores - so
  every part was exported at native pixel size and an 878px collar covered the
  whole face. If a part is absurdly too big, check this key first.
* **A reference image the vision bridge silently drops.** `qa_vision.py
  --reference` only reached the model for `--task composite`; with a free-form
  `--prompt` it was dropped and the model then reviewed an image it had never
  seen, usually concluding the reference was missing.
* **Sampling the wrong end of the loop.** The motion report sampled
  `[0, duration)` and compared the last sample (2.2s) with the first (0s),
  reporting a pop in an animation that closed perfectly. Render `t = duration`
  explicitly to test the loop.
* **A whole-character silhouette as a placement target.** Do not score a part
  against the full silhouette; see above.

## Checking the result

```bash
python scripts/spine_export.py --layout layout.json --out out/ --gate
python scripts/make_preview.py --package out/puppy.json --reference reference.png
python scripts/qa_vision.py --task composite --image out/preview/setup_pose.png \
    --reference reference.png
```

Read the numbers first (`positioning_score`, `reference: IoU`, the loop delta),
but trust the composite check for assembly: it is the one that says "the collar
is on the muzzle". Ask it for the *worst problem* rather than a pass/fail if you
want something actionable to fix.

## Conforming a part to its box

Boxes come from the artwork; parts come from an image model that draws whatever
proportions it feels like. On a three-view chibi cat the model returned a leg
2.7x taller than wide where the reference leg is 0.7, a torso taller than it is
wide where the reference body is a squat barrel, and arms half the width they
needed to be. Placed by uniform scale into correct boxes, that character
assembles into a skinny scarecrow: the torso came out 60% of its intended width
and the legs 53%.

```bash
--fit conform     # reshape each part to its box's aspect, then place it
--fit box         # uniform scale only (leaves the part's own proportions)
```

Conform stretches one axis so the art matches the box exactly, which is what
makes an assembly match the character it came from. Three things to know:

* **Only ever upscale.** The smaller of the two axis factors is applied as an
  upscale first, so the axis that would have been shrunk never loses resolution.
* **Refuse absurd stretches.** `max_stretch` (2.5x) leaves a part that is wildly
  wrong-shaped untouched rather than smearing it; regenerate that part instead.
* **Write the reshaped art out and reference it in the layout.** Reshaping in
  memory while the layout still names the original file is a silent disaster:
  the positioning score improves, the preview looks right, and the exported
  atlas still contains the un-conformed art. `position_parts.py` now saves
  conformed parts to `conformed/` next to the layout and points the layout at
  them.

## Two more traps, both invisible until you zoom

**Chroma residue lives on the outermost ring.** Segmentation leaves the outer
row/column of a cut-out with the key colour at full alpha - a whole 1px green
column down the edge of a part. `parts_lib.despill_edges` clears it, but note
that its erosion must pad rather than `np.roll`: a roll wraps the first row and
last column around and classifies exactly the ring you are trying to clean as
"interior".

**`fringe_distance` is calibrated for flat keyed art.** A soft-shaded 3D render
legitimately has a rim that differs from its interior, so a clean part can score
0.18-0.23 against a 0.16 limit. Look at the edge before you "fix" it: zoom three
points on a silhouette and check for green or a hard halo. If the edge is clean,
the number is measuring the render's rim light.

## Drawing limbs behind the body

`rig_rules` puts limbs in front of the torso, which is right for a character
whose arms hang outside its silhouette. It is wrong for a chibi whose limbs are
stubby tubes tucked into a round body: drawn in front, the limb's hidden
shoulder end shows as a straight cut edge floating on the belly, and the body's
own outline gets a bite taken out of it.

```json
{"box": [4.9, 24.9, 11.2, 33.3], "pivot_px": [235, 1130], "draw_order": 12}
```

Pin `draw_order` so the limbs sit *behind* the torso. The body's own silhouette
then covers the seam, exactly as the reference art does it. Read the override
per part by name from the box map - the placement loop's `spec` variable is a
leaked loop variable holding whichever part was placed last, and using it
applies that part's order to everything.

Ears raise the same question, and the answer is in the reference art rather
than in taste. A cat's ear is not joined by a straight line: the dome's curve is
what cuts its base, so the ears belong *behind* the head (16/17 against a head
at 50). Drawn in front, the ear's own bottom edge lies across the forehead as a
horizontal line - exactly what the user reported as a layering fault.

## Measure the boxes, do not read them by eye

A 20-cell grid (5% per cell) is not accurate enough to place a part: on this
cat one cell is 91px tall, and every box read off it came out 20-100px wrong -
the collar 55% too wide, the legs 80px too far out. Two cheap measurements beat
any amount of squinting:

* **Per-row silhouette runs** of the reference alpha (`np.diff` on a row, keep
  runs longer than a few px). That gives the true left and right edge at every
  height, so a box becomes a number instead of a guess; the same runs measured
  on your own render show which part is still too wide, and at which height.
* **Colour masks** for anything the silhouette cannot show. A collar worn on the
  body sits inside the outline and is invisible to an alpha mask - key on the
  gold and the blue and take the bbox, and the band comes out at its true
  445x135 instead of the 689x154 it was read as by eye.

**A limb's box runs from its joint to its tip**, not over the part of the limb
you can see. The art is occlusion-complete, so an arm image contains the whole
arm; fit that image into just the visible strip and the visible part comes out
about 30% too small. Start the box at the joint - the shoulder, the hip, the
base of the ear - and the hidden root lands behind the body where it belongs.

## Put the joints in the box map

`PIVOT_BY_KIND` stores fractions of the image - `ear` is (0.5, 0.85), "85% of
the way down". That is only correct when the box hugs the part, and a limb's
box deliberately does not, because it runs from the joint to the tip. Give the
joint in canvas pixels instead and the placement converts it, in `box` and
`conform` mode:

```json
{"ear_l": {"box": [2.3, 0.5, 15.0, 8.8],    "pivot_px": [247, 292]},
 "arm_l": {"box": [4.9, 24.9, 11.2, 33.3],  "pivot_px": [235, 1130]},
 "leg_l": {"box": [12.2, 31.9, 18.5, 39.6], "pivot_px": [397, 1450]}}
```

Read them the way an animator would: the base of the ear, the top of the arm,
the top of the leg, the neck under the chin. Then *look* at them instead of
trusting the arithmetic - `bone_overlay.py` draws every bone over the setup
pose, and a joint in the wrong place stops being an argument and starts being
a picture.

## Facial features

Face parts are measured in canvas pixels rather than grid cells, their pivots
are joints rather than centres (whiskers at the cheek, the mouth at its top
edge), and they draw in their own band in front of the plate - spots 51,
whiskers 52, mouth 53, nose 54, eyes 55. The kind rules, the two features the
image model cannot produce directly, and the expression check are in
[facial-features.md](facial-features.md).
