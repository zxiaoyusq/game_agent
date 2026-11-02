---
name: gpt52-vision-router
description: "Route image-understanding to an external MiMo vision model when the active LLM is gpt-5.2 (which the HiModels relay rewrites to the text-only deepseek-v4-flash-offcial and therefore has no native vision). Use this skill ONLY for gpt-5.2. For GPT-5.6 Sol, Terra, Luna and any other vision-capable model, do NOT invoke this skill - rely on their native vision, because routing through an external model would overwrite or lose their built-in image understanding. The external vision model is mimo-v2.5 (MiMo), configured in the skill-local vision_config.json."
agent_created: true
---

# gpt-5.2 Vision Router

When the active model is **gpt-5.2**, image tasks must be offloaded to an external
vision model. `gpt-5.2` is an alias that the HiModels relay rewrites to the
**text-only** `deepseek-v4-flash-offcial`, so it cannot see images.

## ⚠️ Hard guardrail

- **Use this skill ONLY when the active model is gpt-5.2.**
- **Do NOT use it for GPT-5.6 Sol / Terra / Luna** or any other vision-capable
  model. Those have native vision; sending their images to an external model
  would override/discard that capability. In those cases, just answer the vision
  task directly with the model's own multimodal input.

## When to trigger (on gpt-5.2)

The user asks to look at / read / describe / analyze / compare / QA an image,
screenshot, diagram, UI mock, generated asset, chart, etc. — anything requiring
the model to actually *see* pixels.

## What to do

1. Confirm the active model is gpt-5.2. If not, stop — handle vision natively.
2. **If the agent has MCP access to `gpt52_vision`, prefer the `recognize_image`
   tool** (same logic, zero shell quoting issues):
   - `recognize_image(images=[...], prompt="...")` — local image paths + question
   - `check_image(images=[...])` — validate paths first
   - `vision_config` — see the live vision model (key masked)
3. Otherwise use the bundled helper (preferred) or replicate the request shape:
   ```bash
   python3 scripts/vision_call.py --image PATH --prompt "VISION QUESTION"
   # multiple images:
   python3 scripts/vision_call.py --image a.png --image b.png --prompt "Compare." --json
   ```
4. Feed the returned text back as the answer to the user's vision question.

The MCP wrapper lives in `mcp/` (pure-stdlib stdio server exposing
`recognize_image` / `check_image` / `vision_config`); see `mcp/README.md` for
registration and manual verification.

The helper reads the vision model config from the skill-local
`vision_config.json` (currently MiMo `mimo-v2.5`). That file takes priority over
GameArtAgent's shared `~/.gameartagent/user_models.json` (`cheap_vision`
instance), so this Codex copy always uses MiMo even if other clients' shared
config changes. If both are missing it falls back to the same MiMo defaults, so
the skill still works.

## Request shape (if replicating by hand)

OpenAI-compatible `POST {base_url}/chat/completions` with a `messages` array whose
`user` content is a list mixing one `text` block and one-or-more `image_url`
blocks (inline base64 `data:image/png;base64,...`). Send `temperature 0.1` and
`max_tokens` per task. **Do not** send `thinking` as a bare string (some
endpoints reject it with HTTP 400) — omit it. See
`references/vision-format.md` for the exact body and config source.

## Notes

- The vision model is **separate** from the relay: the relay handles text
  (`gpt-5.2` → deepseek); this skill handles pixels (→ MiMo `mimo-v2.5`).
- To change this Codex copy's vision model later, edit
  `vision_config.json` in the skill directory — no other client is affected.
- `deepseek-v4-flash-offcial` (the gpt-5.2 target) is confirmed text-only — that
  is precisely why this router exists.
