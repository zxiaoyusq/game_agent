# Vision QA when the driving model cannot see

`deepseek-v4-flash` reads text only. Art generation and rig QA are visual, so
every visual judgement has to leave the model, and it has to come back in a form
a text agent can act on.

## Two independent checks, in this order

1. **Numbers** (`make_preview.py`, `parts_lib.py --check`). Free, deterministic,
   and they catch most mistakes: a part that never got out of the green screen, a
   body part offset by 40 px, an animation that does not move, a loop that does
   not close.
2. **A vision model** (`qa_vision.py`). Not free, not deterministic, and the only
   way to catch what numbers cannot express: an art style that does not match, a
   face that came out wrong, a limb that is anatomically attached but looks
   broken.

Never skip step 2 for a deliverable and never let it contradict step 1 silently.
When they disagree, look at the disagreement rather than averaging it away - that
is exactly how the green-fringe bug below was found.

## The route

`qa_vision.py` reuses the `gpt52-vision-router` skill's `vision_call.py` when it
is installed (MiMo `mimo-v2.5` by default) and falls back to any
OpenAI-compatible endpoint given in that skill's `vision_config.json`. The key is
read from that file and is never printed.

```bash
python scripts/qa_vision.py --task parts \
  --image work/parts/head.png --image work/parts/torso.png

python scripts/qa_vision.py --task composite \
  --image out/preview/setup_pose.png --reference reference.png

python scripts/qa_vision.py --task loop --image out/preview/filmstrip.png

python scripts/qa_vision.py --prompt "Is the hat centred on the head?" \
  --image out/preview/setup_pose.png
```

Every prompt demands the answer start with `VERDICT: PASS` or `VERDICT: FAIL`, so
the caller gets a decision and a short evidence list instead of prose. Exit codes:
`0` pass, `2` fail, `3` no verdict, `2` with `ok: false` if the route is
unavailable. Add `--json` for a machine-readable result.

## Reading the verdicts

* `parts` - whole part present, clean silhouette, no coloured fringe, one
  consistent art style across parts.
* `composite` - the assembled rig is the same character as the reference, no
  floating or mirrored limbs.
* `loop` - restrained idle, parts stay attached, the last frame returns to the
  first.

A `FAIL` is a work item, not a formality. Fix the cause and re-run; if you decide
to ship anyway, say so explicitly and say which part is affected.

## Case study: the fringe the numbers missed

`parts_lib.alpha_report` reported `chroma_residue: 0.0` for a generated part,
which looked like a clean cut-out. `qa_vision.py --task parts` returned
`VERDICT: FAIL` with "leftover green / halo around the edges".

Both were right. A pixel that is 60 % art and 40 % green screen is *far* from
pure green, so the residue metric ignored it, and because it was blended above
the alpha threshold it stayed fully opaque - invisible to every alpha statistic.
It was visible to anyone looking at the image.

The fix is in `parts_lib.decontaminate_edges`: the outermost band of **opaque**
pixels within 3 px of transparency is now treated as matte too, and its colour is
pulled in from the interior. `fringe_distance` was added as the metric that would
have caught it (`0.187` before, `0.027` after, threshold `0.16`), and the same
vision prompt then returned `VERDICT: PASS` on the corrected file while confirming
the shape was unchanged.

## Cost discipline

Vision calls are cheap compared to image generation, but not free. Reasonable
use: one `parts` call per batch of parts, one `composite` call per export, one
`loop` call per animation. Reuse the same images for several questions in one
prompt where you can, and do not re-ask a question the numbers already answer.
