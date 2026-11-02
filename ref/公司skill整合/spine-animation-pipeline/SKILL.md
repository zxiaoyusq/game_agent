---
name: spine-animation-pipeline
description: Build a Spine 2D skeletal animation package (skeleton JSON + texture atlas + PNG) from reference art, using the local GPT 生图 / gpt生图 (Azure GPT-Image-2) skill for the artwork and a text-only model as the driver. Covers character part inventory, occlusion-complete part prompts, green-screen chroma keying and edge decontamination, SIFT auto-positioning, bone/pivot/draw-order rigging, idle animation, Spine 3.8 vs 4.x keyframe encoding, texture atlas packing, Spine CLI import gate, numeric QA plus optional vision-model QA, and validation/transform/diff of existing exports. Use when asked for 骨骼动画, Spine 动画, 切图, 拆件, 立绘拆分, 2D character rigging, sprite animation export, idle 呼吸动画, or when a spine JSON must be made to open in a specific Spine editor version.
whenToUse: The user wants a Spine (Spine 2D / Esoteric Software) skeleton exported from reference art, or wants to generate/rig/animate a 2D character as separated parts, or needs an existing Spine JSON validated, converted between Spine 3.8 and 4.x, or fixed so a specific Spine editor version can open it.
metadata:
  version: 1.0.0
  drives: azure-image2-generation
  optional: gpt52-vision-router
---

# Spine animation pipeline

Turn reference art into a Spine package that actually opens in the user's editor,
when the driving model is text-only and the art comes from the local image tool.

Two upstream projects were adapted for this (see `references/upstream.md`):
`GenielabsOpenSource/spine-animation-ai` (auto-positioning + part pipeline) and
`Attrom/spine-mpc-attrom` (Spine CLI wrapping, validation, transforms). Both
assume a vision model and an MCP host. This skill keeps the process and drops
those dependencies.

## The one rule that overrides everything

**Nothing is "done" because the files exist.** The gate is: the Spine CLI
imports the JSON, the preview's numbers are in range, and the user opens it in
their editor. Report the numbers, not an opinion.

## Before anything: prove the environment

```bash
python <skill>/scripts/selfcheck.py
```

It reports Python/Pillow/numpy/OpenCV, the detected Spine CLI and its exact
version, the gpt生图 tool, the vision route, and runs the unit tests. Do not
start a task with a `FAIL` in that list.

## Step 1 - Know the target Spine version

The version decides the file encoding, and Spine refuses the wrong one with a
bare `ERROR: Unable to import skeleton.` Ask nothing; detect it:

```bash
python <skill>/scripts/spine_cli.py --find
# -> {"version": "3.8.75", "cli": "D:\Spine3.8.75Pro\Spine.exe",
#     "shortcut": "C:\Users\...\Desktop\Spine.lnk"}
```

Detection order is `--cli` / `SPINE_CLI_PATH` (an explicit override is never
ignored) then the user's own Desktop shortcut, resolved through the `.lnk`, then
the usual install folders, then a shallow scan. The Desktop shortcut is checked
first on purpose: it is the path the user maintains, so repointing it after an
upgrade is enough and nothing here has to change. Both `Spine.com` and
`Spine.exe` accept the same CLI arguments - verified on this machine.

* Spine **3.8**: rotation keys use `angle`; a bezier is four normalised scalars
  `curve`/`c2`/`c3`/`c4` on the keyframe that **starts** the segment; the last
  keyframe carries no curve.
* Spine **4.x**: rotation keys use `value`; a bezier is one absolute array
  (`0.25,0.75` handles), 4 numbers per single-property timeline, 8 for a
  two-property timeline, still on the segment-start keyframe.

Never hand-write these. `scripts/spine_format.py` is the single source of truth
and the exporter writes for the detected version automatically; use
`spine_toolkit.py transform --to-version` to convert afterwards.
Details and the verified commands: `references/spine-version-matrix.md`.

## Step 2 - Inventory the parts

Decide the part list from the reference art before generating anything. A
typical biped:

```
head, torso, arm_l, arm_r, leg_l, leg_r
```

Add `pelvis`, `neck`, `lower_arm_l`, `hand_l`, `upper_leg_l`, `lower_leg_l`,
`foot_l`, `hair`, `hat`, `ear_l`, `tail`, `collar`, `bell` when the character
has them. More bones mean better motion; fewer parts mean fewer generations.

`scripts/rig_rules.py` maps each name to a kind, a parent, a pivot and a draw
order (English and Chinese names both work: `手臂`, `腿`, `头`, `尾巴`). List the
accepted names with:

```bash
python <skill>/scripts/rig_rules.py --list
```

**Split the face.** A face is not one part. Ask for a clean base plate plus
one part per feature:

```
head (clean plate) + eye_l eye_r nose mouth whisker_l whisker_r cheek_l cheek_r
```

`rig_rules` already knows those names: they hang off the head bone rather than
the torso, and they draw in front of the plate. A face that ships as a single
picture cannot blink, glance or talk - the only motion left is smearing the
whole head - which is exactly the defect a reviewer sees first. The plate
itself must be *clean*: no sockets, no nose, no mouth line, no whisker lines,
no spots, because every one of them is now its own layer. Ears are not part of
the plate; they stay separate parts behind the head. Details, kind rules and
a worked example: `references/facial-features.md`.

**Occlusion completeness.** Each part must be drawn as if the character were
exploded: the torso includes the area hidden behind the arms, the upper arm
includes the shoulder hidden behind the torso. A part cut to its *visible*
silhouette tears open the moment its bone rotates. This is the single most
common cause of a rig that looks broken in motion while the setup pose looks
fine.

## Step 3 - Generate the parts with the local image tool

Always dry-run first: it prints every prompt and command and spends nothing.

```bash
python <skill>/scripts/gen_parts.py \
  --reference reference.png \
  --parts head,torso,arm_l,arm_r,leg_l,leg_r \
  --out work/ --quality low --dry-run
```

Then drop `--dry-run`. The bridge drives the gpt生图 skill's
`azure_image2.py` in edit mode (`--refs` = the reference art, plus any
`--style-ref`), so the part inherits the reference's style, then chroma-keys the
result and publishes `work/parts/<name>.png` with `work/parts_manifest.json`.

* `--quality low` while exploring the breakdown, `medium` for the real run,
  `high` only when the user asks for it. Each part is one generation.
* `--strategy sheet` spends one call for the whole breakdown and segments it by
  connected components. Cheaper, but parts merge often; prefer `per-part`.
* The API key lives in the gpt生图 skill's own config. **Never** print it, and
  never write it into a report, manifest or log.
* Keep the raw generations: `work/raw_generations/` lets you redo the chroma
  key or a single part without paying for another generation.

If the reference is a multi-view sheet, crop the view you want first; the tool
needs one clear character to imitate.

For per-part wording the defaults cannot guess (a naming convention, a detail to
preserve, something the model keeps adding), pass a spec file instead of a name
list - see `references/parts-spec-example.json` for every supported key
(`label`, `kind`, `extra`, `negative`, `occlusion`).

## Step 3b - Layer the parts, never re-cut them

Occlusion between parts is a **draw-order** question. The parts are
occlusion-complete on purpose - an arm carries the whole arm, including the
shoulder end that sits behind the body - because the moment that arm rotates
the shoulder has to be there. Nothing about the art decides which part shows
where they overlap: only `draw_order` does.

`rig_rules` stacks limbs **in front of** the torso, which is right for a
character whose limbs hang outside its silhouette and wrong for a chibi whose
stubby limbs are tucked into a round body. Override it per part, by name, in
the box map:

```json
{"torso": {"draw_order": 30}, "arm_l": {"draw_order": 12}, "ear_l": {"draw_order": 16}}
```

Read the order off the reference like an animator, not from taste. The cat's
reference has the body covering the top of each arm and leg, its chin covering
the collar, and each ear's base cut by the curve of the dome - so limbs 12-15,
torso 30, collar 40, head 50, and the ears 16-17 *behind* the head. Get it wrong
and the symptom is unmistakable: a straight cut edge floating on the belly, or
an ear whose base is a horizontal line across the forehead.

**Do not solve the same problem by cutting the parts out of the reference.** A
cut part is a picture of what happened to be visible in that one view: it has
no shoulder and no hip, so the first rotation opens a hole, and the rig cannot
animate however good the assembled still looks. That was tried on this cat and
the user rejected it in one line - cutting only reproduces the reference, it
does not produce an animation. If a generated part is off in shape or width,
constrain it in the box (or scale the attachment in Spine); do not replace it
with a slice of the reference.

The face has its own stack, back to front: cheek spots 51, whiskers 52, mouth
53, nose 54, eyes 55 - all of them in front of the head plate (50) and behind
nothing else. Two rules follow. The mouth's vertex is hidden behind the nose in
the reference, so the mouth's art and its box both run up *under* the nose: a
feature whose art stops at its visible edge tears open the moment its bone moves
it. And the eyes are the topmost thing on the face - a lash line that dips over
the lid still belongs to the eye part.

## Step 3c - Check the art the model returned

Generate-and-place is only as good as the parts, and two defects the image
model produced here were invisible in every summary number and obvious on
screen. Both are caught by a per-row width profile of the part itself:

* **A neck stub.** The generated head was a ball with a narrow stem at the
  bottom - 39% of the image width at 95% down, where the reference has wide
  jowls. Placed in the head's box, that stem pushed out under the chin as a
  grey cylinder between the head and the collar.
* **A mirrored limb.** Both arms came back leaning the same way, so on one
  side the paw hung inboard instead of outboard and the arm's silhouette
  missed the reference by 120px. Flipping that one PNG horizontally fixed it.
  Nothing in the pipeline detects this: measure the centre of the silhouette
  at 5% and at 95% of the height and compare it with the reference's limb.

Ask for the defect in the prompt as well - "the underside is WIDE, do not draw
a neck", "the shoulder end is at the top right, the paw at the bottom left" -
and the model usually complies.

## Step 3d - Hairline marks and faint markings need a different route

Two kinds of facial feature defeat the image model, and both need a detour
instead of another retry.

**Hairline marks** (whisker lines, a mouth line). Asked for "two thin strokes
with a gap between them" the model returns one fat bar every time; asked for a
small V it returns a bold chevron four times running - and as the last
paragraph below explains, that chevron's *shape* was right while its weight was
not. Do not fight it: ask for **one** stroke, generate that, then place two
copies of it yourself at the two
endpoints measured off the reference, each at its own angle, and mirror the
result for the other side. A single stroke is what the model is actually good
at, and two strokes on one part still animate together the way a whisker group
should.

**Faint markings on skin** (cheek spots, freckles, blush). The model cannot
separate a low-contrast marking from the skin it sits on: asked for "soft
darker grey spots on green" it paints a filled patch of cheek, twice. Ask
instead for a **decal sheet on flat white** - "freckle decals, dots only, no
skin, no fur, no shading" - and key the white out afterwards with
`parts_lib.strip_solid_background(image, tolerance=26)`. Then trim to alpha, and
for a marking that should whisper scale the alpha down (the cat's spots read
right at 55% of the opacity the model returned).

Re-run `parts_lib.despill_edges` on the **final** PNG after any compositing or
resampling. The single stroke arrived with a green fringe; rotating and
resampling it spread that fringe *inside* the stroke, where the export-time
boundary decontamination can no longer reach it. `band=4, threshold=10,
kill=35` took 67 green pixels per whisker to zero.

**Read the shape of a tiny mark from pixels, not from the picture.** The cat's
mouth looks like a V at a glance and is in fact a `Λ` - vertex up, legs splaying
down - which one row-by-row projection of the reference settles immediately and
which the eye got wrong twice:

```bash
python - <<'EOF'
import numpy as np
from PIL import Image
a = np.asarray(Image.open("reference_flat.png").convert("RGB")).astype(int)
grey, sat = a.mean(axis=2), a.max(axis=2) - a.min(axis=2)
dark = (grey < 110) & (sat < 45)      # neutral dark only: this drops the blue collar
for y in range(843, 905, 3):
    print(y, "".join("#" if dark[y, x] else "." for x in range(528, 636, 3)))
EOF
```

A "wrong shape" verdict on a twenty-pixel mark needs the projection before it
needs a regeneration - the model's chevron was right and the eye was wrong.

## Step 4 - Clean and check every part

`gen_parts.py` already does this, but a part arriving from anywhere else must go
through the same treatment, and the numbers must be read:

| metric | meaning | healthy |
| --- | --- | --- |
| `opaque_ratio` | visible pixels | > 0.01 |
| `chroma_residue` | visible pixels still near pure green | 0 |
| `fringe_distance` | matte-zone colour vs interior colour | < 0.16 |

`fringe_distance` is the one that matters and the one alpha statistics miss: a
part can be fully opaque and still carry a green outline, because a pixel that
is 60 % art and 40 % green screen is "far from pure green". `decontaminate_edges`
re-colours that outer band from the interior.

```bash
python <skill>/scripts/parts_lib.py check work/parts/*.png
```

Then look at it, honestly. If the driving model cannot see images, use the
vision route (`references/vision-qa.md`):

```bash
python <skill>/scripts/qa_vision.py --task parts \
  --image work/parts/head.png --image work/parts/torso.png
```

## Step 5 - Position the parts

Generated parts are **not** the artwork: they were drawn by a different model in
the same style, so their outlines and exact colours differ, and feature matching
against the reference finds confident matches in the wrong place. A tan leg is
featureless; a gold bell matches tan fur better than the brown collar it hangs
from. Do not fit parts by pixels first.

**Read the regions off the art, then place by box.** One grid image, one vision
call, after which placement is geometry instead of guesswork:

```bash
# 1. a numbered grid over the reference (5% per cell at --cells 20)
python <skill>/scripts/make_grid.py --image work/reference.png --out work/grid.png

# 2. ask the vision bridge for a box per part in CELL numbers, save as boxes.json
python <skill>/scripts/qa_vision.py --image work/grid.png --prompt "<ask for [col0,row0,col1,row1] per part>"

# 3. place every part inside its box; draw order comes from the rig rules
python <skill>/scripts/position_parts.py   --parts work/parts --reference work/reference.png --boxes work/boxes.json   --out work/layout.json --name hero --fit conform --order anatomy
```

A limb's box runs from its **joint to its tip**, not over the strip of it you
can see: the art is occlusion-complete, so fitting the whole limb image into
the visible strip makes the visible part about 30% too small. Give the joint
itself as canvas pixels and the placement honours it:

```json
{"arm_l": {"box": [4.9, 24.9, 11.2, 33.3], "pivot_px": [235, 1130], "draw_order": 12}}
```

`--fit conform` reshapes each part to its box's aspect before placing it. Use it
by default: the image model returns parts at its own proportions (a leg 2.7x
taller than wide where the reference leg is 0.7) and a uniform scale then
assembles a skinny scarecrow - on a real run the torso came out 60% of its
intended width. It writes the reshaped art to `conformed/` and the layout
references that, so the export matches what the preview showed.

```json
{"grid": 20, "parts": {
  "head":  [3, 1, 17, 9],
  "torso": [2, 9, 18, 19],
  "bell":  {"follow": "collar", "anchor": [0.5, 1.0], "offset": [0, 12], "width": 165}}}
```

Attached pieces are **described, not searched for** - a bell hangs from a
collar, a collar sits at the base of a head. The spec puts the part's **pivot**
on that point, because the pivot *is* the rig's attachment point. Without it a
bell drifts down to the hind leg and a collar slides onto the muzzle.

A box whose bottom edge is another box's top edge makes the two parts meet:
that is what stops the head from floating 80px above the torso with a hole where
the neck is.

Read `positioning_score` and the per-part `method` (`box-fit`, `attached`,
`region-fit`, `sift`, `template`, `centered-fallback`). `centered-fallback`
means that part is a guess - fix it before exporting. `--fit search` refines
inside the boxes by colour and silhouette when there is no box map; `--order
evidence` votes on overlapping pairs instead of trusting the anatomy defaults.
Both are worth knowing and both are the *second* choice. The failure modes, and
why a silhouette can never decide which part is which, are in
`references/positioning.md`.

## Step 6 - Export, then gate it against the real editor

```bash
python <skill>/scripts/spine_export.py --layout work/layout.json --out out/ --gate
```

It writes `<name>.json`, `<name>.atlas`, `<name>.png`, `images/<part>.png`,
`manifest.json` and `export_report.json`, choosing the encoding of the detected
Spine version. `--gate` imports the export into a throwaway `<name>.spine`
project with the Spine CLI. Read the report:

* `PASS` means the editor parsed the file - the hard gate.
* `clean`/`issues` from `validate_curves` means the timeline encoding is right.
* Benign CLI noise that is **not** a failure: `welcome data download failed,
  server error: 410`, and `Image for slot [...] not found` (the atlas page is not
  next to a project that was never given its images).

The strongest proof available without a human is a full round trip: import the
export, have the editor **re-export** it, and compare the two semantically.

```bash
python <skill>/scripts/spine_cli.py --roundtrip out/hero.json --work out/.rt --json
```

`"detail": "identical"` means the editor parsed the file, held every bone,
attachment and bezier, and wrote back the same thing. Spine drops fields that
equal their defaults (`time: 0`, `angle: 0`, `c2: 0`, `c4: 1`) on re-export, so
the comparison is made on canonical forms; a real change to a keyframe or a
curve is still reported as a difference.

## Step 7 - Prove it animates, and look at it

```bash
python <skill>/scripts/make_preview.py \
  --package out/hero.json --reference reference.png --samples 12
```

A dependency-light runtime (Pillow only) plays the real skeleton JSON and the
atlas, then checks, as numbers:

* `IoU` - rendered setup pose vs the reference silhouette. Below `--min-iou`
  (0.55) the parts are misplaced; it fails the run.
* `max frame delta` - if a sampled animation barely changes, it is not animating.
* `loop closes` - the last sample must return to the first.

It writes `preview.html` (a scrubber you can send to the user),
`preview.gif`, `filmstrip.png`, `compare_reference.png`, `setup_pose.png` and
`preview_report.json`.

Then get a second opinion that is not your own arithmetic - show someone
pixels:

```bash
python <skill>/scripts/qa_vision.py --task composite \
  --image out/preview/setup_pose.png --reference reference.png
python <skill>/scripts/qa_vision.py --task loop --image out/preview/filmstrip.png
```

Both print `VERDICT: PASS` or `VERDICT: FAIL` plus evidence. A FAIL is not
decorative: fix the cause and re-run, or hand the user a specific caveat.

A face split has to be proved the same way. Override bone transforms on top of
`setup_pose()` and render the same rig again:

```python
import spine_runtime as sr
skel, atlas, _ = sr.load_package("out/cat.json")
pose = skel.setup_pose()
for bone, values in {"eye_l": {"scaleY": 0.12}, "eye_r": {"scaleY": 0.12}}.items():
    for key, value in values.items():
        # setup_pose() gives absolute local values: add for x/y, assign for the rest
        pose[bone][key] = pose[bone][key] + value if key in ("x", "y") else value
img = sr.render(skel, atlas, pose)
```

Blink (`eye scaleY 0.12`), wink (one eye only), glance (`eye x/y`), talk
(`mouth scaleY`), and one **exploded** frame that displaces every feature
outwards. The exploded frame is the picture that proves the split to a human
reviewer - it shows each feature sitting on its own slot, and it is the first
thing they look at.

## Step 8 - Deliver

Tell the user: where the package is, which Spine version it was written for, the
gate result, the QA numbers, and the one command that opens it. Then the human
step, which no script can replace:

1. Spine -> `Import Data` -> choose `<name>.json`; Spine creates a `.spine`
   project.
2. Select the `Images` node in the tree and set its **Path** to the folder
   holding the atlas and page (`out/`). Without this the slots draw empty.
3. Press play on `idle`.

Hand over `preview.html` as well - it opens with no editor installed, so the
user can see the result before installing anything.

## Working with an existing export

`scripts/spine_toolkit.py` (adapted from `spine-mpc-attrom`) covers the rest:

```bash
python <skill>/scripts/spine_toolkit.py validate out/hero.json --atlas out/hero.atlas
python <skill>/scripts/spine_toolkit.py inspect  out/hero.json
python <skill>/scripts/spine_toolkit.py doc      out/hero.json --out hero-spine-doc.md
python <skill>/scripts/spine_toolkit.py diff     before.json after.json
python <skill>/scripts/spine_toolkit.py transform out/hero.json --set prefix_bones=hero_ --preview
python <skill>/scripts/spine_toolkit.py roundtrip out/hero.json --gate --to-version 3.8.75
python <skill>/scripts/spine_toolkit.py report work/
```

`validate` runs four layers (syntax, structure, references, version) and
cross-checks the atlas when one sits beside the JSON. `transform` renames bones
and slots *and every reference to them*, so a renamed bone does not silently
orphan its animation or skin - preview the diff, then confirm with
`roundtrip --gate`. Transforms carry a risk class (`SAFE`, `BEST_EFFORT`,
`EXPERIMENTAL`); `--risk permissive` is required for the last one.

## Reporting to the user

* Lead with what the user asked for, then the evidence: version, gate result,
  IoU, motion, verdicts.
* Show the preview HTML/GIF paths - a picture beats a paragraph.
* If a part failed or was placed by fallback, say which and what it means.
* Never paste the image tool's API key, and never claim the editor opened a file
  you only validated on disk.
* Do not present an unverified rig as finished; say which step is unverified.

## Files

| Path | Purpose |
| --- | --- |
| `scripts/selfcheck.py` | environment + unit-test check, run this first |
| `scripts/gen_parts.py` | drives the gpt生图 skill, chroma-keys the parts |
| `scripts/parts_lib.py` | chroma key, edge decontamination, alpha/fringe metrics |
| `scripts/position_parts.py` | SIFT/RANSAC/template auto-positioning -> layout |
| `scripts/rig_rules.py` | part classification -> parent, pivot, draw order, idle |
| `scripts/spine_export.py` | layout -> skeleton + atlas + page + report |
| `scripts/spine_format.py` | Spine 3.8 <-> 4.x encoding (the load-bearing module) |
| `scripts/spine_cli.py` | locate and drive the official Spine CLI |
| `scripts/spine_runtime.py` | minimal JSON+atlas renderer used for QA |
| `scripts/make_preview.py` | preview assets and numeric animation QA |
| `scripts/bone_overlay.py` | draws the rig's bones over the pose, to check pivots |
| `scripts/qa_vision.py` | vision-model QA with a PASS/FAIL verdict |
| `scripts/spine_toolkit.py` | validate / inspect / doc / diff / transform / roundtrip |
| `references/facial-features.md` | clean face plate + one part per feature, with worked numbers |
| `references/` | upstream adaptation, version matrix, layout schema, vision QA |
