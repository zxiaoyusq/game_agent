# Upstream adaptation note

This skill is a clean Codex adaptation inspired by [GenielabsOpenSource/spine-animation-ai](https://github.com/GenielabsOpenSource/spine-animation-ai).

That project demonstrates the useful overall sequence: derive independent body parts, estimate how they assemble, build a Spine skeleton and draw order, add animation, then preview and validate. Its source image-splitting step uses Gemini and its positioning step relies on computer vision.

This skill deliberately changes that boundary for Codex: source art is generated or edited with the built-in `image_gen` tool, `#00ff00` chroma is converted locally to alpha, and an explicit layout JSON supplies the intentional pivots/layering. No Gemini key, external image API, or copied upstream implementation is required.
