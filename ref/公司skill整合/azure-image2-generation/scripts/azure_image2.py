#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HiModels GPT-Image 生图/改图脚本（仅标准库）。

后端：https://api.himodels.ai/v1（OpenAI 兼容）
  - 文生图      POST /images/generations   JSON
  - 图生图/改图  POST /images/edits         multipart（单图字段 image，多图字段 image[]）

模型分档：
  标准档 gpt-image-2.5-flare     —— 默认，日常素材/批量出图
  进阶档 gpt-image-2.5-sunburst  —— 用户说「生成大图 / 精修 / 高清化 / 高精度」等进阶需求时切换
  可用 --tier advanced 显式指定，或 --model 直接写完整模型名

Key 解析顺序：--key > 环境变量 HIMODELS_API_KEY > ~/.dsh/.credentials.yaml
Key 只用于请求头，绝不写入 manifest / 日志 / 报告。

兼容旧 Azure 后端：--backend azure --html <ai_image_tool.html>

用法:
  python azure_image2.py --mode generation --prompt "一只卡通猫" --out ./out
  python azure_image2.py --mode edit --prompt "改成蓝色" --refs a.png b.png --out ./out
  python azure_image2.py --mode edit --prompt "生成大图精修" --refs a.png --tier advanced --out ./out

透明背景贴图（首选，2026-09-22 起 gpt-image-2.5 原生支持）:
  python azure_image2.py --mode generation --background transparent \
      --prompt "一个卡通小狗贴图，背景完全透明，只保留主体，边缘不要背景色描边" --size 1024x1024 --out ./out
  python azure_image2.py --mode edit --background transparent \
      --prompt "把图1抠成透明背景贴图，只保留主体" --refs a.png --out ./out
"""
import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import sys
import time
import uuid
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

BASE_URL = "https://api.himodels.ai/v1"
MODEL_STANDARD = "gpt-image-2.5-flare"
MODEL_ADVANCED = "gpt-image-2.5-sunburst"

# background 参数（2026-09-22 实测：gpt-image-2.5 已支持直接生成透明背景）
#   "transparent" -> 直接返回 RGBA + alpha 的透明背景贴图，不再需要本地 flood-fill 抠图
#   "opaque" / "auto" -> 交给服务端决定
# 网关/模型拒绝该字段时会自动去掉重试一次，并记录在 _EFFECTIVE_BACKGROUND
_EFFECTIVE_BACKGROUND = None
TRANSPARENT_HINTS = ("透明", "transparent", "alpha", "抠", "去背", "贴图", "去底")
CRED_FILE = Path(os.path.expanduser("~")) / ".dsh" / ".credentials.yaml"
HTML_DEFAULT = Path(r"E:\AI生图\ai_image_tool.html")

# 进阶档触发词：用户说这些话 -> 自动切 sunburst
ADVANCED_HINTS = (
    "生成大图", "出大图", "大图", "大尺寸", "更大尺寸", "放大尺寸",
    "精修", "精修图", "精细修", "精细", "高精度", "精细化",
    "高清", "高清化", "超清", "超高分辨率", "4k", "8k",
    "写真级", "商业级", "印刷级", "最终稿", "定稿图", "关键视觉",
)


def resolve_key(explicit=None):
    if explicit:
        return explicit
    env = os.environ.get("HIMODELS_API_KEY")
    if env:
        return env
    if CRED_FILE.exists():
        m = re.search(r"HIMODELS_API_KEY:\s*(\S+)", CRED_FILE.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    raise SystemExit("找不到 HIMODELS_API_KEY：请用 --key 传入，或设置环境变量，或在 %s 中配置" % CRED_FILE)


def detect_tier(prompt, explicit=None):
    """返回 (tier, 命中的触发词)。explicit 优先。"""
    if explicit in ("standard", "advanced"):
        return explicit, "显式指定"
    low = prompt.lower()
    for h in ADVANCED_HINTS:
        if h in low:
            return "advanced", h
    return "standard", ""


def resolve_model(args, prompt):
    if args.model:
        return args.model, "显式指定"
    tier, hit = detect_tier(prompt, args.tier)
    return (MODEL_ADVANCED if tier == "advanced" else MODEL_STANDARD), hit


# ---------- Azure 旧后端 ----------

def extract_const(html_text, name):
    m = re.search(rf'const\s+{name}\s*=\s*"([^"]+)"', html_text)
    if not m:
        raise RuntimeError(f"HTML 中缺少常量: {name}")
    return m.group(1)


def parse_html(html_path):
    text = Path(html_path).read_text(encoding="utf-8")
    return {
        "endpoint": extract_const(text, "AZURE_ENDPOINT"),
        "deployment": extract_const(text, "DEPLOYMENT"),
        "gen_version": extract_const(text, "GENERATION_API_VERSION"),
        "edit_version": extract_const(text, "EDIT_API_VERSION"),
        "api_key": extract_const(text, "API_KEY"),
    }


# ---------- 请求组装 ----------

def multipart_body(fields, file_paths, field_name):
    boundary = "----HimodelsImage" + uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        chunks += [
            f"--{boundary}\r\n".encode("ascii"),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("ascii"),
            str(value).encode("utf-8"),
            b"\r\n",
        ]
    for fp in file_paths:
        p = Path(fp)
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        chunks += [
            f"--{boundary}\r\n".encode("ascii"),
            f'Content-Disposition: form-data; name="{field_name}"; filename="{p.name}"\r\n'.encode("utf-8"),
            f"Content-Type: {mime}\r\n\r\n".encode("ascii"),
            p.read_bytes(),
            b"\r\n",
        ]
    chunks.append(f"--{boundary}--\r\n".encode("ascii"))
    return boundary, b"".join(chunks)


def _read_json(resp):
    return json.loads(resp.read().decode("utf-8"))


def call_himodels(key, mode, prompt, model, size, quality, refs, timeout=300, background=None):
    global _EFFECTIVE_BACKGROUND
    headers = {"Authorization": "Bearer " + key}
    if mode == "generation" and not refs:
        payload = {"model": model, "prompt": prompt, "size": size, "n": 1}
        if quality:
            payload["quality"] = quality
        if background:
            payload["background"] = background
        req = urlrequest.Request(BASE_URL + "/images/generations",
                                 data=json.dumps(payload).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/json")
    elif mode == "edit" and refs:
        wrapped = f"参考图按上传顺序编号为图1、图2、图3……。请严格按照用户描述理解这些编号。用户需求：{prompt}"
        fields = {"model": model, "prompt": wrapped, "size": size, "n": "1"}
        if quality:
            fields["quality"] = quality
        if background:
            fields["background"] = background
        # 单图用 image，多图用 image[]（均已实测可用）；失败时互相兜底
        field_name = "image[]" if len(refs) > 1 else "image"
        boundary, raw = multipart_body(fields, refs, field_name)
        req = urlrequest.Request(BASE_URL + "/images/edits", data=raw, method="POST")
        req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
    else:
        raise SystemExit(f"mode/refs 不匹配: generation 需无参考图, edit 需至少一张 (mode={mode}, refs={len(refs)})")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            _EFFECTIVE_BACKGROUND = background
            return _read_json(resp)
    except urlerror.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        low = detail.lower()
        # background 字段不被该模型/网关接受时，去掉它重试一次（退化为不透明输出）
        if background and e.code == 400 and "background" in low:
            print("WARN background=%s 被拒绝，改为不带 background 重试一次" % background, file=sys.stderr)
            return call_himodels(key, mode, prompt, model, size, quality, refs, timeout, None)
        # 字段名/quality 不被接受时兜底重试一次
        if mode == "edit" and refs and e.code == 400 and ("image" in low or "quality" in low):
            fields.pop("quality", None)
            alt = "image" if field_name == "image[]" else "image[]"
            boundary, raw = multipart_body(fields, refs, alt)
            req2 = urlrequest.Request(BASE_URL + "/images/edits", data=raw, method="POST")
            req2.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
            req2.add_header("Authorization", "Bearer " + key)
            try:
                with urlrequest.urlopen(req2, timeout=timeout) as resp:
                    _EFFECTIVE_BACKGROUND = background
                    return _read_json(resp)
            except urlerror.HTTPError as e2:
                raise SystemExit("HTTP %s: %s" % (e2.code, e2.read().decode("utf-8", "ignore")[:500]))
        raise SystemExit("HTTP %s: %s" % (e.code, detail[:500]))
    except urlerror.URLError as e:
        raise SystemExit("网络错误: %s" % e.reason)


def call_azure(cfg, mode, prompt, size, quality, refs, timeout=300, background=None):
    q = quality or "medium"
    if mode == "generation" and not refs:
        url = (f"{cfg['endpoint']}/openai/deployments/{cfg['deployment']}/images/generations"
               f"?api-version={cfg['gen_version']}")
        gen_body = {"prompt": prompt, "size": size, "quality": q,
                    "output_format": "png", "n": 1}
        if background:
            gen_body["background"] = background
        body = json.dumps(gen_body).encode("utf-8")
        req = urlrequest.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("api-key", cfg["api_key"])
    elif mode == "edit" and refs:
        wrapped = f"参考图按上传顺序编号为图1、图2、图3……。请严格按照用户描述理解这些编号。用户需求：{prompt}"
        url = (f"{cfg['endpoint']}/openai/deployments/{cfg['deployment']}/images/edits"
               f"?api-version={cfg['edit_version']}")
        fields = {"prompt": wrapped, "size": size, "n": "1", "quality": q, "output_format": "png"}
        if background:
            fields["background"] = background
        boundary, raw = multipart_body(fields, refs, "image[]")
        req = urlrequest.Request(url, data=raw, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        req.add_header("api-key", cfg["api_key"])
    else:
        raise SystemExit(f"mode/refs 不匹配 (mode={mode}, refs={len(refs)})")
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            return _read_json(resp)
    except urlerror.HTTPError as e:
        raise SystemExit("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "ignore")[:500]))
    except urlerror.URLError as e:
        raise SystemExit("网络错误: %s" % e.reason)


def probe_image_size(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.width, im.height
    except Exception:
        return None


def probe_image_alpha(path):
    """校验透明背景是否真的生效（只用 PIL，不需要 numpy）。

    返回 {"mode", "has_alpha", "corner_alpha", "transparent_pct"}；PIL 缺失或读取失败返回 None。
    """
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        with Image.open(path) as im:
            mode = im.mode
            rgba = im.convert("RGBA")
            w, h = rgba.size
            alpha = rgba.getchannel("A")
            total = float(w * h) or 1.0
            zero_pct = round(alpha.histogram()[0] / total * 100.0, 2)
            corners = [alpha.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
            return {"mode": mode, "has_alpha": mode in ("RGBA", "LA", "PA"),
                    "corner_alpha": corners, "transparent_pct": zero_pct}
    except Exception as e:
        return {"error": str(e)}


def main():
    ap = argparse.ArgumentParser(description="HiModels GPT-Image 生图/改图（标准库）")
    ap.add_argument("--mode", choices=["generation", "edit"], required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--backend", choices=["himodels", "azure"], default="himodels")
    ap.add_argument("--tier", choices=["standard", "advanced"], default=None,
                    help="standard=gpt-image-2.5-flare（默认）；advanced=gpt-image-2.5-sunburst（大图/精修）")
    ap.add_argument("--model", default=None, help="直接指定模型名，覆盖 --tier")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--quality", default=None, choices=["low", "medium", "high", "auto"])
    ap.add_argument("--background", default=None, choices=["transparent", "opaque", "auto"],
                    help="输出背景。transparent = 直接生成透明背景贴图（PNG+alpha，无需本地抠图）；"
                         "不传则不带该字段（默认不透明）")
    ap.add_argument("--refs", nargs="*", default=[], help="参考图路径，顺序即图1、图2…")
    ap.add_argument("--out", default="./agent_outputs")
    ap.add_argument("--filename", default=None)
    ap.add_argument("--key", default=None, help="HiModels API Key（默认自动解析）")
    ap.add_argument("--html", default=str(HTML_DEFAULT), help="仅 --backend azure 时使用")
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    for r in args.refs:
        if not Path(r).exists():
            sys.exit(f"参考图不存在: {r}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.backend == "azure":
        if not Path(args.html).exists():
            sys.exit(f"html 不存在: {args.html}")
        cfg = parse_html(Path(args.html))
        model, tier_hit, tier = cfg["deployment"], "azure 后端", "azure"
        cfg_label = {"endpoint": cfg["endpoint"], "deployment": cfg["deployment"]}
    else:
        model, tier_hit = resolve_model(args, args.prompt)
        tier = "advanced" if model == MODEL_ADVANCED else ("standard" if model == MODEL_STANDARD else "custom")
        cfg_label = {"endpoint": BASE_URL, "deployment": model}

    if args.background == "transparent" and not any(h in args.prompt.lower() for h in TRANSPARENT_HINTS):
        print("提示：已请求透明背景，但 prompt 里没有出现「透明/transparent/贴图」等字样。")
        print("      建议在 prompt 明确写「背景完全透明，只保留主体，不要黑底/白底，边缘不要残留背景色描边」，"
              "alpha 边缘会明显更干净。")

    start = time.time()
    if args.backend == "azure":
        data = call_azure(cfg, args.mode, args.prompt, args.size, args.quality, args.refs,
                          args.timeout, args.background)
    else:
        data = call_himodels(resolve_key(args.key), args.mode, args.prompt, model,
                             args.size, args.quality, args.refs, args.timeout, args.background)
    elapsed = round(time.time() - start, 2)

    resp_echo = {k: data.get(k) for k in ("size", "quality", "output_format", "background")
                 if data.get(k) is not None}
    item = (data.get("data") or [{}])[0]
    if item.get("b64_json"):
        raw = base64.b64decode(item["b64_json"])
    elif item.get("url"):
        with urlrequest.urlopen(item["url"], timeout=args.timeout) as resp:
            raw = resp.read()
    else:
        sys.exit("响应里没有图片数据: %s" % json.dumps(data, ensure_ascii=False)[:400])

    name = args.filename or f"image_{time.strftime('%Y%m%d%H%M%S')}"
    out_path = out_dir / f"{name}.png"
    out_path.write_bytes(raw)

    dims = probe_image_size(out_path)
    alpha_info = probe_image_alpha(out_path)
    effective_bg = _EFFECTIVE_BACKGROUND if args.backend != "azure" else args.background
    manifest = {
        "backend": args.backend,
        "model": model,
        "tier": tier,
        "tier_trigger": tier_hit,
        "mode": args.mode,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality or "(服务端默认)",
        "background_requested": args.background or "(未指定)",
        "background_effective": effective_bg or "(不透明)",
        "alpha": alpha_info,
        "response_echo": resp_echo or None,
        "reference_images": args.refs,
        "endpoint": cfg_label["endpoint"],
        "deployment": cfg_label["deployment"],
        "output_path": str(out_path),
        "elapsed_seconds": elapsed,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "width": dims[0] if dims else None,
        "height": dims[1] if dims else None,
        "status": "ok",
    }
    manifest_path = out_dir / f"IMAGE_{args.mode.upper()}_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK  output: {out_path}")
    print(f"    model: {model}  [{tier}]{'  触发词: ' + tier_hit if tier_hit else ''}")
    print(f"    size: {manifest['width']}x{manifest['height']}  quality: {manifest['quality']}")
    if args.background:
        print(f"    background: 请求 {args.background} -> 实际生效 {effective_bg or '(不透明)'}")
    if args.background == "transparent":
        if alpha_info is None:
            print("    WARN 已请求透明背景，但 PIL 不可用，无法校验 alpha —— 装好 pillow 后请复查。")
        elif not alpha_info.get("has_alpha"):
            print("    WARN 已请求透明背景，但输出 mode=%s（无 alpha 通道）。"
                  "兜底：scripts/postprocess.py --remove-bg" % alpha_info.get("mode"))
        elif alpha_info.get("transparent_pct", 0.0) < 5.0:
            print("    WARN 已请求透明背景，但透明像素只占 %.2f%% —— 模型可能没遵守。"
                  "请确认 prompt 写了「背景完全透明」。" % alpha_info["transparent_pct"])
        else:
            print("    alpha: 校验通过  透明像素 %.2f%%  四角 alpha %s"
                  % (alpha_info["transparent_pct"], alpha_info["corner_alpha"]))
    print(f"    elapsed: {elapsed}s  sha256: {manifest['sha256'][:16]}...")
    print(f"    manifest: {manifest_path}")


if __name__ == "__main__":
    main()
