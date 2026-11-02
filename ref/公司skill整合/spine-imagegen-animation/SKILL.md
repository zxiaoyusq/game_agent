---
name: spine-imagegen-animation
description: Create Spine-ready transparent character parts and idle animation exports from reference art using ImageGen.
---

# Spine ImageGen Animation

Use this skill when a character image needs to become an editable 2D Spine animation: transparent source parts, a packed atlas, Skeleton JSON, and a small idle loop.

## Workflow

1. Inspect the reference pose and list the layer stack before generating art.
2. Preserve occlusion-complete construction. Generate the **full head** behind ears, the **full torso** behind limbs/haunches, and every limb including its naturally hidden continuation. Do not cut parts to their visible silhouette.
3. When a missing part must be generated, use the built-in `image_gen` tool. Request a flat solid `#00ff00` background, no ground shadow, no text, no crop, and one centered part at the final viewing angle. Then run `scripts/remove_chroma_key.py` to make `#00ff00` transparent. Never use Gemini or require a cloud API key.
4. Inspect each generated PNG at normal scale: it must be RGBA, contain both transparent and opaque pixels, retain its full intended volume, and have no obvious chroma halo. When a cutout carries a pale matte or white fringe, set `"decontaminate_edges": true` at the layout root so the exporter replaces edge RGB with nearby interior colours while preserving the silhouette and alpha.
5. Create a layout JSON that declares source file, slot, bone, draw order, position, pivot, and optional idle transform values for every part.
6. Set `spine_version` in the layout to the exact target editor version, then run `scripts/spine_export.py --layout <layout.json> --out <directory>` to create `<name>.png`, `<name>.atlas`, `<name>.json`, `images/`, and `manifest.json`. The `images/` directory contains the unpacked RGBA parts used by the Spine editor; the atlas and page PNG are for runtime delivery.
7. Run `scripts/make_preview.py --layout <layout.json> --out <directory>` for a local visual QA page. The preview is only a QA aid; import the JSON/atlas/page PNG in Spine to validate the real asset.

## Required layer order

Use back-to-front slots unless the reference dictates otherwise:

`tail -> complete body -> rear limbs -> back front limb -> front front limb -> full head -> ears -> collar -> bell`.

The body must not include duplicated thigh geometry. For a sitting animal, the body is an unbroken rounded diagonal underlay; the separate rear limbs create the haunch silhouette above it.

## Rig controls

Use `extra_bones` in the layout for non-image control joints such as pelvis, chest, neck, shoulder, hip, elbow, paw, and tail-tip. Parent every image bone to the nearest useful control joint and place its attachment offset so the setup pose stays unchanged. Add control bones in anatomical order: `root -> pelvis -> chest -> neck`, with limb and tail controls branching from the torso. A full limb contained in one PNG can rotate from its joint but cannot bend at the extra elbow or paw controls until it is split into segments or weighted as a mesh.

## Idle animation guidance

Keep movement restrained: 2.0-2.8 seconds, looped. Use slight breathing on body/head, small ear rotation, tail sway, and a delayed bell swing. Avoid large limb scale changes or visible joint gaps. Use a head-swap blink only when a matching closed-eye head image exists.

## Verification

Run the exporter tests, inspect the preview, then import the JSON in Spine. Spine's `Import Data` creates the skeleton before an image path is assigned, so `MISSING` placeholders are expected initially. Select the `Images` node in the Tree and set its `Path` to the package's `images` directory. Resolve any remaining attachment or version errors before declaring the package complete.

## Reference

The adapted workflow is documented in [references/upstream.md](references/upstream.md). It preserves the useful high-level process from the upstream project while replacing its Gemini generation step with Codex ImageGen.
