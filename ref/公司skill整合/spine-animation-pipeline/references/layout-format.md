# Layout schema

The layout is the hand-off between "here is the art and where it sits" and "here
is a Spine export". `spine_export.py` reads it; `position_parts.py` writes it.
Keep it in version control: it is the only piece a human needs to edit to nudge
the rig.

## Minimal example

```json
{
  "name": "hero",
  "canvas": {"width": 512, "height": 512},
  "idle": {"duration": 2.4, "root_translate_y": 1.0},
  "parts": [
    {"name": "torso", "file": "parts/torso.png", "x": 0,    "y": 40},
    {"name": "head",  "file": "parts/head.png",  "x": 0,    "y": 120},
    {"name": "arm_l", "file": "parts/arm_l.png", "x": -88,  "y": 29}
  ]
}
```

## Coordinates

`x` / `y` are the position of the part's **pivot**, not of its top-left corner.

The canonical space is origin at the canvas centre, x right, **y up**. If you
would rather read numbers straight off the reference image (origin top-left, y
down), say so and the exporter converts:

```json
{"coordinate_system": "pixels-top-left", "canvas": {"width": 512, "height": 512}}
```

`pivot` is a fraction of the part's own image, after trimming:
`[0.5, 0.9]` is "half way across, 90 % down" - the neck for a head part.
Omitted, it comes from `rig_rules.pivot_for(name)`. The exporter turns the pivot
into the attachment offset, so the art lands where the layout says while the bone
sits at the joint.

## Fields

Top level:

| key | default | meaning |
| --- | --- | --- |
| `name` | required | skeleton name, used for the output filenames |
| `canvas` | required | `{width, height}` of the composition |
| `coordinate_system` | `canvas-center` | or `pixels-top-left` |
| `spine_version` | detected CLI | force the encoding, e.g. `3.8.75` |
| `idle` | `{duration: 2.4, root_translate_y: 1.0}` | the generated idle animation |
| `decontaminate_edges` | `false` | default for parts that do not set it |
| `keep_largest_component` | `false` | drop disconnected islands per part |
| `extra_bones` | `[]` | helper bones with explicit `parent`, `x`, `y`, `length` |
| `draw_order` | by `rig_rules` | global override list of part names, back to front |

Per part:

| key | default | meaning |
| --- | --- | --- |
| `name` | required | also the bone, slot, attachment and atlas region name |
| `file` | required | PNG path, resolved relative to the layout file |
| `x`, `y` | `0` | pivot position in canvas space |
| `pivot` | from the part kind | fraction of the part image |
| `parent` | from the part kind | parent bone name |
| `bone` | `name` | bone name when it must differ from the part name |
| `draw_order` | from the part kind | higher draws in front |
| `image_scale` | `1.0` | resize the image before export |
| `idle_rotate` | from the part kind | idle rotation amplitude in degrees |
| `idle_translate_y` | from the part kind | idle vertical amplitude in canvas units |
| `idle_phase` | from the part kind | 0..1 fraction of the loop |
| `decontaminate_edges` | top-level | per-part override |

Unknown keys are ignored, so a layout can carry your own notes.

## What the exporter writes

For `{"name": "hero"}` into `out/`:

```
out/hero.json          the skeleton
out/hero.atlas         the atlas descriptor
out/hero.png           the packed page
out/images/<part>.png  the per-part images actually packed
out/manifest.json      part -> region -> bone mapping
out/export_report.json version, gate result, curve issues, warnings
```

The attachment name, the atlas region name and the part name are the same, and
the exporter does not write `path` or `type` on the attachment. That keeps the
`Images` node in Spine pointing at one folder and removes a whole class of
"missing image" failures.

## How a rig gets assembled

`rig_rules.build_rig` gives every part a kind (from its name, English or
Chinese), a parent, a pivot and a draw order, and `spine_export` emits bones
parent-before-child. If a natural parent is missing it walks a chain
(`thigh -> pelvis -> torso -> root`) rather than leaving a dangling reference,
and it repairs parent cycles with a warning in `export_report.json`.

Inspect the rules without running anything:

```bash
python scripts/rig_rules.py --list
python scripts/rig_rules.py --classify "head,手臂,腿,尾巴,arm_l"
```

## Idle animation

One `idle` clip, authored for both dialects by `spine_format`. Defaults: 2.4 s,
subtle body sway plus breathing, with per-part amplitudes from `IDLE_BY_KIND`
(ears and hats lag, a bell swings more, legs barely move). Curve easing is a
standard ease-out on the segment starting at each keyframe.

Keep flips and attack animations out of this file: export the idle, confirm it
in the editor, then add clips in Spine itself where the curves are visible.
