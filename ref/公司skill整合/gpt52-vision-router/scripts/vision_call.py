#!/usr/bin/env python3
"""Route an image-understanding request to the external MiMo vision model.

This is the companion script for the `gpt52-vision-router` skill. It exists
because the active LLM is **gpt-5.2**, which (via the HiModels relay) resolves to
the text-only `deepseek-v4-flash-offcial` and therefore cannot see images.

Vision model config priority:
  1. Skill-local `vision_config.json` (this repo) — explicit override, so the
     Codex copy of this skill always uses the configured MiMo `mimo-v2.5`
     endpoint regardless of other clients' shared settings.
  2. GameArtAgent's `~/.gameartagent/user_models.json` (`cheap_vision` role).
  3. Built-in defaults (MiMo `mimo-v2.5`).

Usage:
    python3 vision_call.py --image shot.png --prompt "Describe this UI."
    python3 vision_call.py --image a.png --image b.png --prompt "..." --json
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Windows 控制台默认 GBK/CP936，直接 print 中文会乱码导致重跑。
# 强制 stdout/stderr 使用 UTF-8，无论从哪个 shell 调用都不会乱码。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---- defaults (override via skill-local vision_config.json) -----------------
DEFAULT_BASE_URL = "https://api.xiaomimimo.com/v1"
DEFAULT_MODEL = "mimo-v2.5"
DEFAULT_API_KEY = os.environ.get("MIMO_API_KEY", "YOUR_API_KEY_HERE")
GAMERT_USER_MODELS = os.path.join(
    os.path.expanduser("~"), ".gameartagent", "user_models.json"
)
VISION_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "vision_config.json",
)


def load_vision_config() -> dict:
    """Return {base_url, model, api_key} for the vision model.

    Priority:
      1. Skill-local vision_config.json (explicit override for this copy).
      2. GameArtAgent's `cheap_vision` instance.
      3. Built-in defaults (MiMo mimo-v2.5).
    """
    cfg = {
        "base_url": DEFAULT_BASE_URL,
        "model": DEFAULT_MODEL,
        "api_key": DEFAULT_API_KEY,
    }
    # 1) skill-local explicit override (Codex copy -> MiMo mimo-v2.5)
    try:
        with open(VISION_CONFIG_PATH, "r", encoding="utf-8") as fh:
            local = json.load(fh)
        for key in ("base_url", "model", "api_key"):
            if local.get(key):
                cfg[key] = local[key]
        return cfg
    except Exception:
        pass

    # 2) GameArtAgent shared config
    try:
        with open(GAMERT_USER_MODELS, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return cfg

    # role -> alias
    roles = data.get("roles", {})
    alias = roles.get("cheap_vision")
    inst = next(
        (i for i in data.get("instances", []) if i.get("alias") == alias), None
    )
    if not inst:
        # fall back: first instance that advertises vision-ish naming
        inst = next(
            (i for i in data.get("instances", []) if "vision" in i.get("alias", "")),
            None,
        )
    if not inst:
        return cfg

    cfg["base_url"] = inst.get("base_url", cfg["base_url"])
    cfg["model"] = inst.get("model", cfg["model"])
    cfg["api_key"] = inst.get("api_key", cfg["api_key"])
    return cfg


def _b64_image(path: str) -> str:
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
        ext = "png"
    with open(path, "rb") as fh:
        raw = fh.read()
    return f"data:image/{ext};base64,{base64.b64encode(raw).decode('ascii')}"


CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".vision_cache")


def _cache_key(image_paths, prompt, max_tokens, model_override):
    """对 图片内容+prompt+参数 做 sha256，作为缓存键。"""
    h = hashlib.sha256()
    for p in sorted(image_paths):
        try:
            with open(p, "rb") as fh:
                h.update(fh.read())
        except OSError:
            pass
    h.update(prompt.encode("utf-8"))
    h.update(str(max_tokens).encode("ascii"))
    h.update((model_override or "").encode("utf-8"))
    return h.hexdigest()


def _cache_load(key):
    path = os.path.join(CACHE_DIR, key + ".json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("text")
    except Exception:
        return None


def _cache_save(key, text):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        path = os.path.join(CACHE_DIR, key + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"text": text}, fh, ensure_ascii=False)
    except Exception:
        pass


def call_vision(image_paths, prompt, *, max_tokens=2048, temperature=0.1,
                model_override=None, as_json=False, use_cache=True):
    cfg = load_vision_config()
    if model_override:
        cfg["model"] = model_override

    cache_hit = False
    if use_cache:
        key = _cache_key(image_paths, prompt, max_tokens, model_override)
        cached = _cache_load(key)
        if cached is not None:
            cache_hit = True
            text = cached
            model_name = cfg["model"]
    if not cache_hit:
        content = [{"type": "text", "text": prompt}]
        for p in image_paths:
            content.append({"type": "image_url", "image_url": {"url": _b64_image(p)}})

        payload = {
            "model": cfg["model"],
            "messages": [{"role": "user", "content": content}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        url = cfg["base_url"].rstrip("/") + "/chat/completions"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg['api_key']}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            sys.exit(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:400]}")
        except urllib.error.URLError as e:
            sys.exit(f"网络错误: {e.reason}")

        text = ""
        for ch in body.get("choices", []):
            msg = ch.get("message", {})
            if isinstance(msg.get("content"), str):
                text += msg["content"]
            elif isinstance(msg.get("content"), list):
                for part in msg["content"]:
                    if part.get("type") == "text":
                        text += part.get("text", "")
            if not text and isinstance(msg.get("reasoning_content"), str):
                # mimo-v2.5 is a reasoning model: if max_tokens ran out before the
                # visible answer, surface the reasoning text rather than nothing.
                text = msg["reasoning_content"]
        text = text.strip()
        model_name = body.get("model", cfg["model"])
        if use_cache:
            _cache_save(key, text)

    result = {"model": model_name, "text": text, "cache_hit": cache_hit,
              "raw": body if not cache_hit else None}
    return result if as_json else text


def main():
    ap = argparse.ArgumentParser(description="MiMo vision call for gpt-5.2")
    ap.add_argument("--image", action="append", required=True,
                    help="image path (repeatable)")
    ap.add_argument("--prompt", required=True, help="vision prompt / question")
    ap.add_argument("--model", dest="model_override", default=None,
                    help="override vision model id")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--json", action="store_true", help="emit JSON result")
    ap.add_argument("--no-cache", action="store_true",
                    help="disable disk cache (default: cache by image+prompt sha256)")
    ap.add_argument("--out", default=None,
                    help="also write result text to this UTF-8 file")
    args = ap.parse_args()

    start = time.time()
    result = call_vision(
        args.image, args.prompt,
        max_tokens=args.max_tokens, model_override=args.model_override,
        as_json=True, use_cache=not args.no_cache,
    )
    elapsed = time.time() - start
    text = result["text"]
    print(f"[vision {elapsed:.1f}s {'cache-hit' if result['cache_hit'] else 'api'}]",
          file=sys.stderr)

    if args.json:
        payload = {"model": result["model"], "text": text,
                   "cache_hit": result["cache_hit"],
                   "elapsed_seconds": round(elapsed, 2)}
        out = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        out = text

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"written: {args.out}", file=sys.stderr)
    print(out)


if __name__ == "__main__":
    main()
