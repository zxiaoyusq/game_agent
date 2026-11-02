# gpt-5.2 Vision Routing — Request Format

`gpt-5.2` resolves (via the HiModels relay) to the **text-only**
`deepseek-v4-flash-offcial`, so it cannot interpret images. When a vision task
arises on `gpt-5.2`, route it to the external MiMo vision model instead of
asking `gpt-5.2` to "look" (it will hallucinate or fail).

## Source of the vision model

This Codex copy reads the skill-local `vision_config.json`
(`C:\Users\nenghong.zhao\.codex\skills\gpt52-vision-router\vision_config.json`),
which takes priority over GameArtAgent's shared
`~/.gameartagent/user_models.json` (`cheap_vision` role). Current content:

```json
{
  "base_url": "https://api.xiaomimimo.com/v1",
  "model": "mimo-v2.5",
  "api_key": "YOUR_API_KEY_HERE"
}
```

To swap the vision model for this Codex copy later, edit that file — other
clients (workbuddy / opencode / GameArtAgent) are not affected.

## OpenAI-compatible vision request

Endpoint: `POST {base_url}/chat/completions`

```json
{
  "model": "mimo-v2.5",
  "messages": [
    {
      "role": "user",
      "content": [
        { "type": "text", "text": "<vision prompt / structured checklist>" },
        { "type": "image_url", "image_url": { "url": "data:image/png;base64,<...>" } }
      ]
    }
  ],
  "temperature": 0.1,
  "max_tokens": 1024
}
```

- Images are sent as **inline base64 data URLs** (`data:image/png;base64,...`).
  Multiple images = multiple `image_url` content blocks.
- MiMo is OpenAI-compatible, so the same payload works as-is. Do **not** send
  `thinking` as a bare string — omit the field for a plain vision call; only pass
  `thinking` as a JSON object (e.g. `{"type":"disabled"}`) if the endpoint
  explicitly supports that form.
- Reference shape (GameArtAgent, from `phases/qa_auto.py`):
  ```python
  messages = [Message(role="user", content=(
      [{"type": "text", "text": vision_text}] +
      [{"type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{base64.b64encode(img).decode()}"}}
       for _ in ("contact",)]))]
  resp = await client.chat(messages, max_tokens=512, temperature=0.1,
                           thinking="disabled", ...)
  ```
  `concept_gen.py` / `concept_analyze.py` use the identical `image_url` block.

## CLI (via the helper)

```bash
python3 scripts/vision_call.py --image shot.png --prompt "Describe this UI layout."
python3 scripts/vision_call.py --image a.png --image b.png --prompt "Compare." --json
```

## Guardrail (read SKILL.md)

Only invoke this skill when the **active model is gpt-5.2** (text-only). For
GPT-5.6 Sol / Terra / Luna and any other vision-capable model, do **not** use it —
they have native vision and routing through an external model would discard or
override their built-in image understanding.
