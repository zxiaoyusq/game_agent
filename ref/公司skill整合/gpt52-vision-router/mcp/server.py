#!/usr/bin/env python3
"""MCP stdio server wrapping the gpt52-vision-router skill.

Exposes the skill's external MiMo vision call (scripts/vision_call.py) as
Model Context Protocol tools, so an agent whose active LLM has no native vision
(e.g. gpt-5.2 -> deepseek-v4-flash-offcial via the HiModels relay) can still
"see" local images through the configured cheap_vision model.

Tools:
  recognize_image  - send one or more local images + a prompt to the vision model
  check_image      - validate local image files (existence, type, size) without calling the model
  vision_config    - show the effective vision model config (API key masked)

Transport: stdio, newline-delimited JSON-RPC 2.0 (MCP spec). No third-party deps.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import vision_call  # noqa: E402  (reuses the skill's helper + vision config)

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "gpt52-vision-router"
SERVER_VERSION = "0.1.0"


def _tool_definitions():
    return [
        {
            "name": "recognize_image",
            "description": (
                "Route image understanding to the external MiMo vision model "
                "(skill-local vision_config.json, currently mimo-v2.5). Use this "
                "ONLY when the active LLM cannot see images natively. Returns the "
                "model's text answer."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "images": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "description": "Local image file paths (png/jpg/jpeg/gif/webp).",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Vision question / instruction for the model.",
                    },
                    "model": {
                        "type": "string",
                        "description": "Optional model id override.",
                    },
                    "maxTokens": {
                        "type": "integer",
                        "default": 2048,
                        "description": "Max output tokens.",
                    },
                },
                "required": ["images", "prompt"],
            },
        },
        {
            "name": "check_image",
            "description": (
                "Validate one or more local image files (exists, readable, sniffed "
                "format, byte size) WITHOUT calling any model. Use before "
                "recognize_image to fail fast on bad paths."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "images": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                },
                "required": ["images"],
            },
        },
        {
            "name": "vision_config",
            "description": (
                "Show the effective vision model configuration (skill-local "
                "vision_config.json takes priority over "
                "~/.gameartagent/user_models.json). API key is masked. No images "
                "are sent."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]


def _validate_images(images):
    """Return (ok_list, errors). Also expands ~ and rejects non-files."""
    ok, errors = [], []
    for raw in images:
        path = os.path.expanduser(str(raw))
        if not os.path.isfile(path):
            errors.append(f"{raw}: not a file")
            continue
        ok.append(path)
    return ok, errors


def _sniff_image(path):
    with open(path, "rb") as fh:
        head = fh.read(16)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        fmt = "png"
    elif head[:3] == b"\xff\xd8\xff":
        fmt = "jpeg"
    elif head[:6] in (b"GIF87a", b"GIF89a"):
        fmt = "gif"
    elif head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        fmt = "webp"
    else:
        fmt = "unknown"
    return fmt, os.path.getsize(path)


def _handle_recognize_image(params):
    images = params.get("images") or []
    prompt = params.get("prompt") or ""
    if not images:
        return {"error": "images is required", "code": -32602}
    if not prompt.strip():
        return {"error": "prompt is required", "code": -32602}
    ok, errors = _validate_images(images)
    if errors:
        return {"error": "invalid image paths: " + "; ".join(errors), "code": -32602}
    try:
        result = vision_call.call_vision(
            ok,
            prompt,
            max_tokens=int(params.get("maxTokens") or 2048),
            model_override=params.get("model") or None,
            as_json=True,
        )
    except Exception as exc:  # network / API / payload failures
        return {"error": f"vision call failed: {exc}", "code": -32000}
    text = result.get("text", "")
    return {
        "result": {
            "text": text,
            "model": result.get("model", ""),
            "imageCount": len(ok),
        }
    }


def _handle_check_image(params):
    images = params.get("images") or []
    if not images:
        return {"error": "images is required", "code": -32602}
    ok, errors = _validate_images(images)
    items = [{"path": p, "format": fmt, "bytes": size} for p, fmt, size in
             ((p,) + _sniff_image(p) for p in ok)]
    return {
        "result": {
            "images": items,
            "errors": errors,
        }
    }


def _mask_key(key):
    if not key:
        return ""
    if len(key) <= 8:
        return "***"
    return key[:6] + "…" + key[-4:]


def _handle_vision_config(_params):
    cfg = vision_call.load_vision_config()
    source = (
        vision_call.VISION_CONFIG_PATH
        if os.path.isfile(vision_call.VISION_CONFIG_PATH)
        else vision_call.GAMERT_USER_MODELS
    )
    return {
        "result": {
            "baseUrl": cfg.get("base_url", ""),
            "model": cfg.get("model", ""),
            "apiKeyMasked": _mask_key(cfg.get("api_key", "")),
            "configSource": source,
        }
    }


HANDLERS = {
    "recognize_image": _handle_recognize_image,
    "check_image": _handle_check_image,
    "vision_config": _handle_vision_config,
}


def _respond(req_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    _write(msg)


def _write(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _dispatch(req):
    method = req.get("method")
    req_id = req.get("id")
    if req_id is None:
        return  # notification, no response
    if method == "initialize":
        return _respond(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
    if method == "ping":
        return _respond(req_id, {})
    if method == "tools/list":
        return _respond(req_id, {"tools": _tool_definitions()})
    if method == "tools/call":
        name = (req.get("params") or {}).get("name")
        args = (req.get("params") or {}).get("arguments") or {}
        handler = HANDLERS.get(name)
        if not handler:
            return _respond(req_id, error={
                "code": -32601, "message": f"unknown tool: {name}",
            })
        try:
            out = handler(args)
        except Exception as exc:  # unexpected internal failure
            traceback.print_exc(file=sys.stderr)
            return _respond(req_id, error={
                "code": -32603, "message": f"internal error: {exc}",
            })
        if "error" in out:
            return _respond(req_id, error={
                "code": out.get("code", -32602), "message": out["error"],
            })
        result = out["result"]
        text = result.get("text", json.dumps(result, ensure_ascii=False))
        return _respond(req_id, {
            "content": [{"type": "text", "text": text}],
            "structuredContent": result,
            "isError": False,
        })
    return _respond(req_id, error={
        "code": -32601, "message": f"method not found: {method}",
    })


def main():
    try:
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            _dispatch(req)
        except Exception:
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
