# What was adapted from where

Two upstream projects were read and turned into one skill that runs on a
text-only model with the local GPT 生图 tool. Neither upstream is vendored: only
the process was reused, reimplemented against this skill's own data formats.

## GenielabsOpenSource/spine-animation-ai

A Claude skill that takes a character sheet and produces a rigged Spine export.
Licence: PolyForm Noncommercial 1.0.0, and it is built around Gemini for image
generation, so no code was copied.

| Upstream idea | What this skill does instead |
| --- | --- |
| `split_character.py` cuts a deconstructed sheet into parts | `gen_parts.py --strategy sheet` segments a GPT 生图 sheet by connected components; `--strategy per-part` is the default, because generated sheets often fuse parts |
| Part crops keep the crop box as the part origin | `gen_parts.py` chroma-keys, trims to alpha, decontaminates the edge, and reports `fringe_distance` |
| `position_parts.py`: SIFT + RANSAC maps each part into the reference, then occlusion votes decide z-order | kept, and reimplemented in `position_parts.py`. Changes: writes this skill's layout schema, adds a template-matching fallback, records which method won per part, and scores the result as silhouette overlap so "did it work" is a number |
| Gemini calls for art | the user's own `azure-image2-generation` (gpt生图) skill, always, in edit mode with the reference art as `image[]` |
| HTML5 player preview | `make_preview.py` writes a self-contained `preview.html` plus a GIF and a filmstrip |
| Claude reads the screenshots to judge the result | `qa_vision.py` asks a vision model over HTTP and returns `VERDICT: PASS/FAIL`, with the numeric checks in `make_preview.py` as the first line of defence |
| Its export writes `"spine": "4.2"` with 4.x curves | `spine_format.py` writes for the version the local Spine CLI reports (3.8.75 here). The upstream encoding cannot be imported by a 3.8 editor at all - verified: `ERROR: Unable to import skeleton.` |

## Attrom/spine-mpc-attrom

An MCP server (TypeScript) that wraps the official Spine CLI, plus a large
ingestion corpus. Research-oriented README. Its useful parts are process, not
code, so `spine_toolkit.py` reimplements the ideas in Python:

| Upstream idea | What this skill does instead |
| --- | --- |
| MCP tools `spine_export` / `spine_import` / `spine_validate` / `spine_diff` / `spine_transform` / `spine_roundtrip` | `spine_cli.py` + `spine_toolkit.py` as plain CLI, so any agent or human can drive them without an MCP host. `references/mcp-optional.md` explains how to put the MCP back if you want it |
| Multi-layer validation (syntax / structure / references / version) | `spine_toolkit.py validate`, four layers, plus an atlas/attachment cross-check that upstream does not have |
| `curveValidator` (correct 4.x bezier rules) | confirmed and folded into `spine_format.validate_curves`, which understands **both** encodings |
| `spine_build_skeleton_doc` (bone perturbation documentation) | `spine_toolkit.py doc` writes a Markdown skeleton document: hierarchy, what each bone drives, draw order, animation profiles |
| `spineVersion.ts` warning that cross-major conversion fails | reproduced as a hard finding, then solved: see `spine-version-matrix.md` |
| Transform pipeline with risk classes | `spine_toolkit.py transform` with `SAFE` / `BEST_EFFORT` / `EXPERIMENTAL` and a mandatory `--preview` diff |
| Ingestion corpus of many skeletons | dropped. It is a research artifact, not part of producing one rig |

## The Codex adaptation

`~/.codex/skills/spine-imagegen-animation/SKILL.md` is the earlier, Codex-side
version of this pipeline: it established the occlusion-complete part prompt, the
`#00ff00` chroma key, the layout JSON shape, and the verification note about
Spine's `Import Data` + `Images` node `Path`. Those are carried over verbatim in
spirit. What is new here is the version-aware encoder, the numeric QA gates, the
vision bridge, the auto-positioning, and the validation/transform toolkit.

## Hard constraints that shaped the design

* **No vision in the driving model.** Every quality judgement is either a number
  (chroma residue, opaque ratio, silhouette IoU, frame delta, loop closure) or an
  outbound call to a vision model. Nothing relies on the agent seeing an image.
* **No MCP host.** Everything is a CLI taking paths and printing JSON.
* **The editor is Spine 3.8.75.** Encoding is chosen at export time from the
  detected CLI, and the import gate proves it before delivery.
* **The image tool owns its own key.** This skill never reads, logs or copies the
  Azure key; it only invokes the gpt生图 skill's script.
