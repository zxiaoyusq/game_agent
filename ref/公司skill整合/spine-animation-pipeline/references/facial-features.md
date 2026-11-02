# Splitting a face into a plate and its features

A face shipped as one picture can only be animated as one rigid mask. Splitting
it is what turns a still into a pet: a blink, a wink, a glance, a talking mouth,
a whisker twitch are each a transform on one small part, and each is also the
cheapest way to swap an expression later.

## The part list

| part | what it contains | parent |
| --- | --- | --- |
| `head` | the clean plate: silhouette, shading, forehead gear, any static marking that must never move | neck |
| `eye_l` / `eye_r` | the WHOLE eye as one layer: sclera, pupil, upper lid arc, lashes | head |
| `nose` | the nose, including the part covered by the muzzle above it | head |
| `mouth` | the mouth mark, including the vertex hidden under the nose | head |
| `whisker_l` / `whisker_r` | one group of strokes per cheek | head |
| `cheek_l` / `cheek_r` | faint spots, freckles or blush, one cluster per cheek | head |
| `brow_l` / `brow_r` | eyebrows, when the character has them | head |

The plate must be **clean**. Every feature above is now its own layer, so a
plate that still carries eye sockets, a nose or whisker lines shows a ghost of
them sliding under the moving parts. Ask the generator for the empty face
explicitly and list what to remove; it complies, and it happily keeps the static
decoration you tell it to keep (the cat's model kept the forehead plate and its
cheek spots).

## Rules that are not obvious

* **Occlusion completeness applies to features too.** The mouth's vertex sits
  behind the nose in every reference view, so the mouth's art *and* its box run
  up under the nose. A feature whose art stops at its visible edge tears open
  the moment its bone moves it.
* **The eyes own their lashes.** Lash strokes that dip over the lid or float
  outside the sclera belong to the eye part, not to the plate.
* **Whiskers pivot at the cheek, not at their middle.** With the pivot on the
  inner end a twitch rotates about the cheek; with the pivot in the centre the
  whole stroke swings away from the face.
* **The eyes stay still in the idle.** A drifting eye reads as a bug. The eyes
  ride the head bone and the head's idle carries them; `rig_rules` gives the eye
  and cheek kinds an empty idle for exactly this reason.
* **Ears are not part of the plate.** They stay separate parts *behind* the
  head, so the head can turn inside them.

## Kind rules that are already in rig_rules

| kind | parent | pivot | draw order | idle |
| --- | --- | --- | --- | --- |
| `cheek` | head | (0.5, 0.5) | 51 | none |
| `whisker` | head | (0.0, 0.5), mirrored per side | 52 | rotate 1.2 |
| `mouth` | head | (0.5, 0.15): hinged at the top edge | 53 | rotate 0.8 |
| `nose` | head | (0.5, 0.85) | 54 | translate_y 0.8 |
| `brow` | head | (0.5, 0.9) | 54 | translate_y 1.5 |
| `eye` | head | (0.5, 0.5): a glance is a translation, not a rotation | 55 | none |

The facial patterns are matched before the body patterns, so `eye_l`, `nose`,
`mouth`, `whisker_l` and `cheek_l` never fall through to `accessory` - whose
parent is the torso, where a facial feature cannot follow the head.

## Measure the feature boxes in pixels

Features are placed with **pixel boxes**, not grid cells: they are small and
their positions are exact. `pivot_px` and `draw_order` ride along in the same
entry.

```json
{"eye_l":     {"px": [196, 632, 505, 815],  "draw_order": 55.0},
 "mouth":     {"px": [528, 812, 636, 905],  "draw_order": 53.0},
 "whisker_l": {"px": [68, 828, 180, 927],   "draw_order": 52.0, "pivot_px": [176, 845]}}
```

Three measurement notes from the cat:

* **Dark marks** need a neutrality filter as well as a brightness one:
  `grey < 110 & (max-min) < 45`. A plain brightness threshold swallows the
  character's blue collar and its dark body edges, and the connected components
  come back as one huge blob at the centre of the canvas.
* **The nose is the bright blob, not the dark one.** A brightness mask inside
  the muzzle region (`grey > 190`) isolates it; the dark component under it is
  the nose's shaded underside plus the mouth.
* **Faint spots need the tightest threshold of all.** `grey < 190` returned a
  whole 155x463 band of face shading as one "spot". When nothing isolates them,
  use the decal route in Step 3d of SKILL.md.

`--fit conform` reshapes the art to the box's aspect, so a box that does not
match the artifact distorts it. The cat's mouth box (108x93, aspect 1.16)
stretched the generated chevron (aspect 1.71) 1.47x taller - which is why the
placed mouth reads slightly bolder than the reference's. Match the aspect when
the mark's weight matters; accept the stretch when only the position matters.

## Verifying the split

Numbers first, then eyes:

* Render the setup pose, measure each feature's bounding box in the render, and
  compare it with the reference's. The cat came out at `(196,632,309,183)` for
  the left eye against the reference's `(196,632,305,183)`, and
  `(527,819,109,88)` for the mouth against `(528,812,108,93)` - a few pixels,
  not a few dozen.
* Render an expression sheet: blink, wink, glance, talk, and one exploded frame
  (Step 7 in SKILL.md).
* Count interior holes across the idle frames. A feature that moves off its own
  art punches a hole in the silhouette; the cat held 0-2 stray pixels over 12
  frames.

## Worked example: the cat

18 slots, 19 bones, canvas 1143x1816, silhouette IoU 0.903 against the
reference, Spine 3.8.75 import gate PASS.

| part | px box | pivot | draw order |
| --- | --- | --- | --- |
| `head` | grid cells 0.4-39.6 x, 4.1-23.5 y | - | 50.0 |
| `cheek_l` | 35, 600, 110, 800 | centre | 51.0 |
| `cheek_r` | 1040, 600, 1100, 815 | centre | 51.5 |
| `whisker_l` | 68, 828, 180, 927 | 176, 845 (inner end) | 52.0 |
| `whisker_r` | 976, 826, 1084, 924 | 982, 845 (inner end) | 52.5 |
| `mouth` | 528, 812, 636, 905 | centre | 53.0 |
| `nose` | 526, 753, 647, 822 | centre | 54.0 |
| `eye_l` | 196, 632, 505, 815 | centre | 55.0 |
| `eye_r` | 660, 632, 965, 815 | centre | 55.5 |

Write the provenance of each feature down for the next person, because two of
them were not straight generations:

* plate, eyes, nose, mouth: generated, chroma-keyed, despilled;
* whiskers: **one** generated stroke, composited twice per cheek at the two
  measured angles, then mirrored for the other cheek;
* cheek spots: a generated white-background decal sheet, keyed white with
  `strip_solid_background(tolerance=26)`, trimmed, alpha dropped to 55%.
