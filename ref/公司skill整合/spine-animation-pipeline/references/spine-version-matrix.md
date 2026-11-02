# Spine version matrix

This is the load-bearing detail of the whole skill. A Spine export that uses the
wrong encoding does not degrade gracefully: the editor shows
`ERROR: Unable to import skeleton.` and nothing else.

## The two dialects

| | Spine 3.8 | Spine 4.x |
| --- | --- | --- |
| version string | `"3.8.75"` (3 parts) | `"4.2.0"` (3 parts; `"4.2"` also appears in the wild) |
| rotate key property | `angle` | `value` |
| bezier storage | four scalars on the segment-start keyframe: `curve`, `c2`, `c3`, `c4` | one array on the segment-start keyframe: `curve: [cx1, cy1, cx2, cy2]` |
| curve coordinates | normalised to the segment (0..1 across time and value) | absolute, in the property's own units |
| `noScaleOrReflection` | `noScale` | `noScaleOrReflection` |
| translate key property | `x` / `y` | `x` / `y` (same) |
| frames per curve array | n/a | 4 for one-property, 8 for two-property (translate/scale/shear), 12 for rgb, 16 for rgba, 24 for transform, 12 for path |

The curve always belongs to the keyframe that **starts** the segment. The last
keyframe of a timeline must not carry one - a curve on the final keyframe is a
common cause of a rejected file.

## Ground truth used

* 3.8 spelling from the shipped examples: `E:\Program Files\Spine\examples\alien\export\alien-ess.json`
  contains `{"time": 1.3667, "angle": -9.4, "curve": 0.232, "c2": 0.6, "c3": 0.67, "c4": 0.88}`.
  `hero-pro.json` / `spineboy-pro.json` declare `"spine": "3.8.55"` and use `angle`.
* The upstream projects declare `"spine": "4.2"` and write `value` with
  absolute 8-number translate curves.

## What was actually tested here

A variant sweep against the local Spine 3.8.75 CLI, importing one skeleton at a
time:

| variant | result |
| --- | --- |
| no animation at all | PASS |
| rotate timeline with no curve | PASS |
| rotate timeline with `angle` + scalar `curve/c2/c3/c4` | PASS |
| rotate timeline with `value` and no curve | PASS |
| any curved timeline in 4.x encoding | **FAIL** - `Error reading animation: idle` |
| same skeleton re-encoded by `spine_format` for 3.8 | PASS, and a re-export round trip is semantically identical |

The failure is the curve encoding, not the `value` key on its own. That is why
`spine_format.py` converts curves rather than just renaming keys.

## Verified CLI commands

```bash
# which editor is installed, and which version
Spine.com -v
Spine.com -i <skeleton.json> -o <project.spine> -r        # import = the gate
Spine.com -i project.spine -o out/ -e settings.json       # export
Spine.com -i <dir> -c <atlas> -o <out>                    # unpack atlas
Spine.com -i <images_dir> -o <out> -n name [-p pack.json]  # pack atlas
```

Export settings that produce an editable JSON:

```json
{"class": "json", "extension": ".json", "format": "JSON",
 "nonessential": true, "prettyPrint": true}
```

## Benign CLI noise

These lines appear on a normal, successful run and must not be reported as
failure:

* `WARNING: Welcome data download failed, server error: 410` - the editor cannot
  reach its welcome-data server.
* `Image for slot [slot: X, bone: Y, skeleton: Z] not found: X` - expected when
  the atlas page sits beside an export that was never given its images. Fix it in
  the editor by selecting the `Images` node and setting its `Path`.

## Choosing the target version

`spine_export.py` asks `spine_cli.find_cli()` for the installed editor's version
and writes for it. Detection order:

1. `--cli <path>` or `SPINE_CLI_PATH` - an explicit override always wins.
2. The user's Desktop shortcut (`Spine.lnk`, `Spine 4.lnk`, `Spine Trial.lnk`),
   resolved through the `.lnk` itself, so repointing the shortcut after an
   upgrade is enough. This is the intended source of truth.
3. The usual install folders (`D:\Spine3.8.75Pro\Spine.com`, `C:\Program Files\Spine\...`).
4. A shallow scan of the Spine home folders and the drive roots.

This machine resolves to
`C:\Users\nenghong.zhao\Desktop\Spine.lnk` -> `D:\Spine3.8.75Pro\Spine.exe`,
**Spine 3.8.75 Professional**. `Spine.exe` and `Spine.com` are both launchers
that take identical CLI arguments and print identical stdout; verified by running
`-v` and a full import/re-export round trip through each. The shortcut is checked
first so the skill follows the user's own entry point rather than a guess.

Override only when you know better:

```bash
python scripts/spine_export.py --layout layout.json --out out/ --spine-version 3.8.75
python scripts/spine_toolkit.py transform out/hero.json --to-version 3.8.75
```

`normalize_to_target` is idempotent and safe to run twice; `validate_curves`
catches a mismatched file before the editor has to.
