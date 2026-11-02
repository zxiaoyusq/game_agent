#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPT 生图 —— 默认后端 HiModels 网关，Azure OpenAI 作为 fallback 后端。

文本生图 / 带参考图编辑，支持智能尺寸识别、透明底生成与 alpha 自动质检。零第三方依赖（标准库）。

后端与模型分档（默认 himodels）：
  标准档 gpt-image-2.5-flare     默认；日常素材 / 批量出图 / 草图探索 / UI 稿 / 图标
  进阶档 gpt-image-2.5-sunburst  用户说「生成大图 / 精修 / 高清化 / 高精度 / 定稿图」等 → --tier advanced
  备用档 Azure gpt-image-2       仅当 HiModels 不可用时：--backend azure [--html <ai_image_tool.html>]

透明底（2026-09-22 实测，取代旧的「只能本地抠图」结论）：
  * 必须显式传 --background transparent（接口参数），**光在 prompt 里写「透明背景」拿不到 alpha**；
  * generations 与 edits（参考图）两条路径均实测返回真 RGBA（全透明占比 40%+，四角 alpha≈0）；
  * 服务端响应会回执 background 字段；脚本据此 + 本地 alpha 质检双重校验；
  * 出口 alpha 上限实测为 254 而非 255 → 质检按 >=250 计「实心」；
  * 仅当服务端未给 alpha 时，才回落到 postprocess.py --remove-bg（flood fill）本地兜底。

配置优先级：CLI 参数 > 环境变量 > 凭据/配置文件 > 脚本内 DEFAULTS
  himodels：HIMODELS_API_KEY（env）> ~/.dsh/.credentials.yaml（HIMODELS_API_KEY / _LINSHENG / _HONG）
            > E:\\hermes\\.env
  azure   ：AZURE_OPENAI_API_KEY / _ENDPOINT / _DEPLOYMENT
            （env > E:\\hermes\\.env > --html 解析 > 内置默认）
Key 只用于请求头，绝不写入 manifest / 日志 / 报告。
"""

import argparse
import base64
import datetime
import hashlib
import http.client
import json
import mimetypes
import os
import re
import socket
import struct
import sys
import time
import uuid
import urllib.error
import urllib.request

# Windows 控制台/管道默认 GBK：本脚本会输出中文与 ✓，必须显式改 UTF-8
# （否则 json.dumps 到 stdout 会因 GBK 无法编码而抛 UnicodeEncodeError，把成功的生图判成失败）
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 后端常量
# ---------------------------------------------------------------------------
HIMODELS_BASE_URL = "https://api.himodels.ai/v1"
MODEL_STANDARD = "gpt-image-2.5-flare"
MODEL_ADVANCED = "gpt-image-2.5-sunburst"
HIMODELS_KEY_NAMES = (
    "HIMODELS_API_KEY",
    "HIMODELS_API_KEY_LINSHENG",
    "HIMODELS_API_KEY_HONG",
)
CRED_FILE = os.path.join(os.path.expanduser("~"), ".dsh", ".credentials.yaml")
HERMES_ENV_FILE = r"E:\hermes\.env"

# 进阶档触发词（用户这么说 → 自动升 sunburst；与 SKILL.md 的判据保持一致）
ADVANCED_HINTS = (
    "生成大图", "出大图", "大图", "大尺寸", "更大尺寸", "放大尺寸",
    "精修", "精修图", "精细修", "精细", "高精度", "精细化",
    "高清", "高清化", "超清", "超高分辨率", "4k", "8k",
    "写真级", "商业级", "印刷级", "最终稿", "定稿图", "关键视觉",
)

DEFAULTS = {
    # Azure fallback 后端默认（保持本技能历史行为不变）
    "endpoint": "https://aha-inhouse-eastus2.cognitiveservices.azure.com",
    "deployment": "gpt-image-2",
    "api_key": "",
    "quality": "low",
    "gen_api_version": "2024-02-01",
    "edit_api_version": "2025-04-01-preview",
}

ALLOWED_SIZES = {
    "1024x1024", "1280x720", "2048x1152", "2560x1440", "3584x2016",
    "720x1280", "1152x2048", "1440x2560", "2016x3584",
    "1536x1024", "1024x1536",
    "1152x2560",  # 9:20 竖屏（2026-08-07 用户需求；HiModels 未实测，命中会告警）
}

# HiModels 实测可用尺寸列表里没有这一项，显式指定时仅告警不拦截
HIMODELS_UNVERIFIED_SIZES = {"1152x2560"}

KEYWORD_SIZE_RULES = [
    (["方图", "方形", "正方形", "头像", "图标", "icon", "square", "1:1"],
     "1024x1024", "方图"),
    (["16:9", "横屏", "视频封面", "youtube", "b站封面", "bilibili", "widescreen"],
     "2048x1152", "16:9 横屏"),
    (["9:16", "竖屏", "手机壁纸", "抖音", "快手", "小红书", "reels", "shorts", "tiktok"],
     "1152x2048", "9:16 竖屏"),
    (["横图", "横版", "横向", "宽图", "banner", "landscape", "3:2"],
     "1536x1024", "横图"),
    (["竖图", "竖版", "竖向", "长图", "海报", "portrait", "2:3"],
     "1024x1536", "竖图"),
]

# 透明底质检门禁（PIL 可选；仅当显式要求 transparent 时执行）
ALPHA_GATE = {
    "min_transparent_pct": 3.0,   # 背景确实被抠掉
    "max_corner_alpha": 16,       # 四角必须是（近）透明
    "min_opaque_pct": 1.0,        # 必须存在实心主体，防止整图全透明
}
OPAQUE_ALPHA_FLOOR = 250          # 出口 alpha 上限实测 254，故按 >=250 计实心

# 传输层重试：IncompleteRead / 超时 / 429 / 5xx（2026-09-22 sunburst 实测出现截断）
RETRY_ATTEMPTS = 3
RETRY_DELAY = 10
RETRY_STATUS = {429, 500, 502, 503, 504}


def log(msg):
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# 网络：按后端选择代理策略
#   - azure 内网端点必须直连（Clash fake-ip 劫持会 10061，2026-08-07 实测）
#   - himodels 走公网，沿用系统/环境代理
# ---------------------------------------------------------------------------
_OPENERS = {}


def get_opener(use_direct):
    key = "direct" if use_direct else "system"
    if key not in _OPENERS:
        if use_direct:
            _OPENERS[key] = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        else:
            _OPENERS[key] = urllib.request.build_opener()
    return _OPENERS[key]


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
def load_env_file(path):
    """读取 KEY=VALUE 形式的环境文件（E:\\hermes\\.env）。"""
    env_from_file = {}
    if path and os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env_from_file[k.strip()] = v.strip()
    return env_from_file


def parse_html_constants(html_path):
    """从本地 ai_image_tool.html 解析 Azure 常量（方式 B，便携部署用）。"""
    consts = {}
    try:
        text = open(html_path, encoding="utf-8", errors="replace").read()
    except Exception as e:
        log(f"无法读取 HTML 文件 {html_path}：{e}")
        return consts
    patterns = {
        "endpoint": r"AZURE_ENDPOINT\s*=\s*['\"]([^'\"]+)['\"]",
        "deployment": r"DEPLOYMENT\s*=\s*['\"]([^'\"]+)['\"]",
        "api_key": r"API_KEY\s*=\s*['\"]([^'\"]+)['\"]",
        "gen_api_version": r"GENERATION_API_VERSION\s*=\s*['\"]([^'\"]+)['\"]",
        "edit_api_version": r"EDIT_API_VERSION\s*=\s*['\"]([^'\"]+)['\"]",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            consts[key] = m.group(1)
    return consts


def credentials_lookup(names):
    """从 ~/.dsh/.credentials.yaml 依次查找 refs 里的 key，返回 (名字, 值)。"""
    if not os.path.exists(CRED_FILE):
        return None, None
    try:
        text = open(CRED_FILE, encoding="utf-8", errors="replace").read()
    except Exception:
        return None, None
    for name in names:
        m = re.search(rf"^\s*{re.escape(name)}\s*:\s*(\S+)", text, re.M)
        if m and m.group(1) and m.group(1) not in ("null", "~"):
            return name, m.group(1)
    return None, None


def resolve_himodels_key(args, env, env_from_file):
    """himodels key 解析：--api-key/--key > env > credentials.yaml > E:\\hermes\\.env。"""
    if args.api_key:
        return args.api_key, "CLI 参数"
    for name in HIMODELS_KEY_NAMES:
        if env.get(name):
            return env[name], f"环境变量 {name}"
    name, value = credentials_lookup(HIMODELS_KEY_NAMES)
    if value:
        return value, f"credentials.yaml {name}"
    for name in HIMODELS_KEY_NAMES:
        if env_from_file.get(name):
            return env_from_file[name], f"E:\\hermes\\.env {name}"
    return "", None


def get_azure_config(args, env, env_from_file):
    """Azure fallback 后端配置（本技能历史默认值原样保留）。"""
    cfg = dict(DEFAULTS)
    html_consts = parse_html_constants(args.html) if getattr(args, "html", None) else {}
    cfg["api_key"] = (args.api_key or env.get("AZURE_OPENAI_API_KEY")
                      or env_from_file.get("AZURE_OPENAI_API_KEY")
                      or html_consts.get("api_key") or DEFAULTS["api_key"])
    cfg["endpoint"] = (args.endpoint or env.get("AZURE_OPENAI_ENDPOINT")
                       or env_from_file.get("AZURE_OPENAI_ENDPOINT")
                       or html_consts.get("endpoint") or DEFAULTS["endpoint"])
    cfg["deployment"] = (env.get("AZURE_OPENAI_DEPLOYMENT")
                         or env_from_file.get("AZURE_OPENAI_DEPLOYMENT")
                         or html_consts.get("deployment") or DEFAULTS["deployment"])
    if html_consts.get("gen_api_version"):
        cfg["gen_api_version"] = html_consts["gen_api_version"]
    if html_consts.get("edit_api_version"):
        cfg["edit_api_version"] = html_consts["edit_api_version"]
    return cfg


# ---------------------------------------------------------------------------
# 模型分档
# ---------------------------------------------------------------------------
def detect_tier(prompt, explicit=None):
    """返回 (tier, 命中的触发词)。explicit 优先。"""
    if explicit in ("standard", "advanced"):
        return explicit, "显式指定"
    low = (prompt or "").lower()
    for hint in ADVANCED_HINTS:
        if hint in low:
            return "advanced", hint
    return "standard", ""


def resolve_model(args, prompt):
    """返回 (model, tier, 触发词)。--model 覆盖一切。"""
    if args.model:
        tier = ("advanced" if args.model == MODEL_ADVANCED
                else "standard" if args.model == MODEL_STANDARD else "custom")
        return args.model, tier, "显式指定"
    tier, hit = detect_tier(prompt, args.tier)
    return (MODEL_ADVANCED if tier == "advanced" else MODEL_STANDARD), tier, hit


# ---------------------------------------------------------------------------
# 尺寸识别
# ---------------------------------------------------------------------------
def detect_size_from_keywords(prompt):
    text = (prompt or "").lower()
    for words, size, label in KEYWORD_SIZE_RULES:
        if any(w in text for w in words):
            return size, f"关键词识别为{label}"
    return None, None


def image_dimensions(path):
    with open(path, "rb") as f:
        head = f.read(32)
    if path.lower().endswith(".png") or head[:8] == b"\x89PNG\r\n\x1a\n":
        if head[12:16] == b"IHDR":
            w, h = struct.unpack(">II", head[16:24])
            return w, h
        raise ValueError("无法解析 PNG IHDR")
    if head[:2] == b"\xff\xd8":
        with open(path, "rb") as f:
            f.seek(2)
            while True:
                marker = struct.unpack(">H", f.read(2))[0]
                if marker == 0xFFD8:
                    continue
                if marker in (0xFFC0, 0xFFC1, 0xFFC2, 0xFFC3, 0xFFC5,
                              0xFFC6, 0xFFC7, 0xFFC9, 0xFFCA, 0xFFCB,
                              0xFFCD, 0xFFCE, 0xFFCF):
                    f.read(3)
                    h, w = struct.unpack(">HH", f.read(4))
                    return w, h
                length = struct.unpack(">H", f.read(2))[0]
                f.seek(length - 2, os.SEEK_CUR)
        raise ValueError("无法定位 JPEG SOF 段")
    raise ValueError("仅支持 PNG / JPG 参考图")


def detect_size_from_first_ref(refs):
    w, h = image_dimensions(refs[0])
    ratio = w / h
    if ratio >= 1.55:
        return "2048x1152", f"图1比例 {w}x{h} 为 16:9 横屏"
    if ratio >= 1.1:
        return "1536x1024", f"图1比例 {w}x{h} 为横图"
    if ratio <= 0.65:
        return "1152x2048", f"图1比例 {w}x{h} 为 9:16 竖屏"
    if ratio <= 0.9:
        return "1024x1536", f"图1比例 {w}x{h} 为竖图"
    return "1024x1024", f"图1比例 {w}x{h} 为方图"


def resolve_size(size_arg, prompt, refs):
    if re.match(r"^\d+x\d+$", size_arg or ""):
        if size_arg not in ALLOWED_SIZES:
            raise ValueError(f"尺寸 {size_arg} 不在支持列表 {sorted(ALLOWED_SIZES)}")
        return size_arg, "用户手动指定"
    if size_arg in (None, "", "auto"):
        kw_size, kw_label = detect_size_from_keywords(prompt)
        if kw_size:
            return kw_size, kw_label
        if refs:
            try:
                return detect_size_from_first_ref(refs)
            except Exception as e:
                log(f"参考图尺寸识别失败，回退方图：{e}")
        return "1024x1024", "未识别到关键词/参考图比例，默认方图"
    raise ValueError(f"无法识别的尺寸参数: {size_arg}")


# ---------------------------------------------------------------------------
# alpha 质检（PIL 可选；只用 PIL，不引入 numpy）
# ---------------------------------------------------------------------------
def analyse_alpha(path):
    """检查输出 PNG 的透明底质量。PIL 缺失时返回 available=False（不拦截）。"""
    try:
        from PIL import Image
    except Exception as e:
        return {"available": False, "reason": f"PIL 不可用: {e}"}
    try:
        with Image.open(path) as im:
            mode = im.mode
            has_alpha = mode in ("RGBA", "LA")
            result = {"available": True, "mode": mode, "has_alpha": has_alpha}
            if not has_alpha:
                return result
            alpha = im.convert("RGBA").getchannel("A")
            w, h = alpha.size
            hist = alpha.histogram()
            total = float(w * h)
            result.update({
                "size": [w, h],
                "corner_alpha": [alpha.getpixel((0, 0)), alpha.getpixel((w - 1, 0)),
                                 alpha.getpixel((0, h - 1)), alpha.getpixel((w - 1, h - 1))],
                "alpha_max": max(i for i, c in enumerate(hist) if c) if total else 0,
                "alpha_mean": round(sum(i * c for i, c in enumerate(hist)) / total, 1),
                "transparent_pct": round(100.0 * hist[0] / total, 2),
                "opaque_pct": round(100.0 * sum(hist[OPAQUE_ALPHA_FLOOR:]) / total, 2),
            })
            return result
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}: {e}"}


def alpha_gate_report(alpha):
    """按门禁判定透明底是否达标，返回 (ok, 说明列表)。"""
    if not alpha.get("available"):
        return True, [f"跳过 alpha 质检（{alpha.get('reason', 'PIL 不可用')}）"]
    if not alpha.get("has_alpha"):
        return False, [f"输出为 {alpha.get('mode')}，没有 alpha 通道 → 透明底未生效"]
    notes, ok = [], True
    corners = alpha.get("corner_alpha") or []
    if max(corners or [255]) > ALPHA_GATE["max_corner_alpha"]:
        ok = False
        notes.append(f"四角 alpha {corners} 未接近 0（阈值 {ALPHA_GATE['max_corner_alpha']}）")
    else:
        notes.append(f"四角 alpha {corners} ✓")
    if alpha.get("transparent_pct", 0) < ALPHA_GATE["min_transparent_pct"]:
        ok = False
        notes.append(f"全透明像素仅 {alpha.get('transparent_pct')}%（阈值 ≥{ALPHA_GATE['min_transparent_pct']}%）")
    else:
        notes.append(f"全透明像素 {alpha['transparent_pct']}% ✓")
    if alpha.get("opaque_pct", 0) < ALPHA_GATE["min_opaque_pct"]:
        ok = False
        notes.append(f"实心主体仅 {alpha.get('opaque_pct')}%（阈值 ≥{ALPHA_GATE['min_opaque_pct']}%）")
    else:
        notes.append(f"实心主体 {alpha['opaque_pct']}%（alpha≥{OPAQUE_ALPHA_FLOOR}）✓")
    return ok, notes


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def build_multipart_body(form, file_parts):
    """file_parts: [(字段名, 文件名, 二进制, MIME)] —— 允许多张图重复同一字段名。"""
    boundary = "----gptimage-" + uuid.uuid4().hex
    parts = []
    for key, value in form.items():
        parts.append(
            (f"--{boundary}\r\n"
             f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
             f"{value}\r\n").encode("utf-8")
        )
    for field, filename, blob, ctype in file_parts:
        parts.append(
            (f"--{boundary}\r\n"
             f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
             f"Content-Type: {ctype}\r\n\r\n").encode("utf-8")
        )
        parts.append(blob)
        parts.append(b"\r\n")
    parts.append((f"--{boundary}--\r\n").encode("utf-8"))
    return boundary, b"".join(parts)


def load_ref_parts(refs, default_ctype):
    """读取参考图为 multipart 部件列表，保留用户传入顺序（顺序即图1/图2…）。"""
    parts = []
    for ref in refs:
        with open(ref, "rb") as f:
            blob = f.read()
        ctype = mimetypes.guess_type(ref)[0] or default_ctype
        parts.append((os.path.basename(ref), blob, ctype))
    return parts


def post_raw(url, body, headers, timeout, use_proxy=True):
    """POST 并在传输层抖动时重试（IncompleteRead / 超时 / 429 / 5xx）。"""
    last_error = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with get_opener(use_direct=not use_proxy).open(req, timeout=timeout) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            payload = e.read()
            if e.code in RETRY_STATUS and attempt < RETRY_ATTEMPTS:
                last_error = f"HTTP {e.code}"
                log(f"HTTP {e.code}（第 {attempt} 次），{RETRY_DELAY}s 后重试 ...")
                time.sleep(RETRY_DELAY)
                continue
            return e.code, payload
        except (http.client.IncompleteRead, socket.timeout, TimeoutError) as e:
            last_error = f"{type(e).__name__}: {e}"
            if attempt < RETRY_ATTEMPTS:
                log(f"响应被截断/超时（{last_error}，第 {attempt} 次），{RETRY_DELAY}s 后重试 ...")
                time.sleep(RETRY_DELAY)
                continue
            raise RuntimeError(f"传输层失败（已重试 {RETRY_ATTEMPTS} 次）: {last_error}")
        except urllib.error.URLError as e:
            last_error = f"{e.reason}"
            if attempt < RETRY_ATTEMPTS:
                log(f"网络错误（{last_error}，第 {attempt} 次），{RETRY_DELAY}s 后重试 ...")
                time.sleep(RETRY_DELAY)
                continue
            raise RuntimeError(f"网络请求失败（请检查公网/代理/内网连通性）: {last_error}")
    raise RuntimeError(f"请求失败: {last_error}")


def error_detail(body):
    text = body.decode("utf-8", errors="replace")
    detail = ""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            err = data.get("error") or {}
            if isinstance(err, dict):
                detail = err.get("message", "")
            detail = detail or data.get("message", "") or ""
    except Exception:
        pass
    return detail or text[:500]


def extract_image_bytes(status, body, timeout, use_proxy=True):
    text = body.decode("utf-8", errors="replace")
    if status != 200:
        raise RuntimeError(f"HTTP {status}\n{error_detail(body)}")
    data = None
    try:
        data = json.loads(text)
    except Exception:
        pass
    item = ((data or {}).get("data") or [{}])[0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    if item.get("url"):
        with get_opener(use_direct=not use_proxy).open(item["url"], timeout=timeout) as resp:
            return resp.read()
    raise RuntimeError("接口返回中没有图片数据（期望 data[0].b64_json 或 data[0].url）。")


def build_form(model, prompt, size, quality, background, output_format="png"):
    """组装 images 接口的业务字段；background/quality 为空则不下发。"""
    form = {"model": model, "prompt": prompt, "size": size, "n": 1,
            "output_format": output_format}
    if quality:
        form["quality"] = quality
    if background:
        form["background"] = background
    return form


# ---------------------------------------------------------------------------
# HiModels（默认后端）
# ---------------------------------------------------------------------------
def call_himodels(mode, prompt, model, size, quality, background, refs, mask, key, timeout):
    headers = {"Authorization": "Bearer " + key}
    form = build_form(model, prompt, size, quality, background)

    if mode == "generation":
        headers["Content-Type"] = "application/json"
        status, resp = post_raw(HIMODELS_BASE_URL + "/images/generations",
                                json.dumps(form, ensure_ascii=False).encode("utf-8"),
                                headers, timeout, use_proxy=True)
        return extract_image_bytes(status, resp, timeout, use_proxy=True)

    # edits：参考图按上传顺序编号
    wrapped = ("参考图按上传顺序编号为图1、图2、图3……。请严格按照用户描述理解这些编号。"
               f"用户需求：{prompt}")
    form["prompt"] = wrapped
    form["n"] = "1"
    ref_parts = load_ref_parts(refs, "image/png")
    mask_part = None
    if mask:
        with open(mask, "rb") as f:
            mask_part = (os.path.basename(mask), f.read(),
                         mimetypes.guess_type(mask)[0] or "image/png")

    primary = "image[]" if len(refs) > 1 else "image"
    fallback = "image" if primary == "image[]" else "image[]"
    attempts = [(primary, True), (fallback, True)]
    if mask:
        attempts.append((primary, False))  # 上游不吃 mask 时去掉 mask 再试一次
    last = None
    for idx, (field, keep_mask) in enumerate(attempts):
        parts = [(field, n, b, c) for n, b, c in ref_parts]
        if keep_mask and mask_part:
            parts.append(("mask", mask_part[0], mask_part[1], mask_part[2]))
        boundary, body = build_multipart_body(form, parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        status, resp = post_raw(HIMODELS_BASE_URL + "/images/edits", body, headers,
                                timeout, use_proxy=True)
        if status == 200:
            return extract_image_bytes(status, resp, timeout, use_proxy=True)
        detail = error_detail(resp)
        low = detail.lower()
        last = f"HTTP {status}\n{detail}"
        if idx + 1 >= len(attempts):
            break
        if "mask" in low and keep_mask:
            log("上游不接受 mask 字段，去掉 mask 重试一次 ...")
            continue
        if status == 400 and ("image" in low or "quality" in low):
            log(f"字段名 {field} 被拒（HTTP 400），改用 {fallback} 重试一次 ...")
            form.pop("quality", None)
            continue
        break
    raise RuntimeError(last or "参考图编辑失败")


# ---------------------------------------------------------------------------
# Azure（fallback 后端）
# ---------------------------------------------------------------------------
def azure_url(cfg, kind):
    base = cfg["endpoint"].rstrip("/")
    version = cfg["gen_api_version"] if kind == "generations" else cfg["edit_api_version"]
    return (f"{base}/openai/deployments/{cfg['deployment']}"
            f"/images/{kind}?api-version={version}")


def call_azure(mode, prompt, size, quality, background, refs, mask, cfg, timeout):
    headers = {"api-key": cfg["api_key"]}
    if mode == "generation":
        body = build_form(cfg["deployment"], prompt, size, quality, background)
        body["output_compression"] = 100
        headers["Content-Type"] = "application/json"
        status, resp = post_raw(azure_url(cfg, "generations"),
                                json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                headers, timeout, use_proxy=False)
        return extract_image_bytes(status, resp, timeout, use_proxy=False)

    wrapped = ("参考图按用户提供顺序编号为图1、图2、图3……。请严格按照用户描述理解这些编号。"
               f"用户需求：{prompt}")
    form = {"prompt": wrapped, "model": cfg["deployment"], "size": size, "n": "1",
            "output_format": "png"}
    if quality:
        form["quality"] = quality
    if background:
        form["background"] = background
    parts = [("image[]", name, blob, ctype)
             for name, blob, ctype in load_ref_parts(refs, "application/octet-stream")]
    if mask:
        with open(mask, "rb") as f:
            parts.append(("mask", os.path.basename(mask), f.read(),
                          mimetypes.guess_type(mask)[0] or "image/png"))
    boundary, body = build_multipart_body(form, parts)
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    status, resp = post_raw(azure_url(cfg, "edits"), body, headers,
                            timeout, use_proxy=False)
    return extract_image_bytes(status, resp, timeout, use_proxy=False)


# ---------------------------------------------------------------------------
# 输出与 Manifest
# ---------------------------------------------------------------------------
def save_png(raw, output_path):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(raw)
    log(f"已保存: {output_path} ({len(raw) / 1024:.1f} KB)")
    return output_path


def write_manifest(output, args, info, size, refs, alpha):
    """生成 IMAGE_<stem>_MANIFEST.json（记录配置与 alpha 质检，但不记录 key）。"""
    sha, w, h, mode_px = "", 0, 0, ""
    try:
        with open(output, "rb") as f:
            raw = f.read()
        sha = hashlib.sha256(raw).hexdigest()
        from PIL import Image  # 可选依赖：仅用于尺寸/模式校验
        with Image.open(output) as im:
            w, h = im.size
            mode_px = im.mode
    except Exception:
        pass
    stem = os.path.splitext(os.path.basename(output))[0]
    manifest = {
        "backend": info["backend"],
        "model": info["model"],
        "tier": info["tier"],
        "tier_trigger": info["tier_trigger"],
        "mode": "edit" if refs else "generation",
        "prompt": args.prompt,
        "size": size,
        "quality": info["quality"] if info["quality"] else "(服务端默认)",
        "background": info["background"] or "(未传)",
        "reference_images": refs,
        "mask": mask_path(args),
        "endpoint": info["endpoint"],
        "deployment": info["deployment"],
        "gen_api_version": info.get("gen_api_version", ""),
        "edit_api_version": info.get("edit_api_version", ""),
        "output_path": output,
        "sha256": sha,
        "width": w,
        "height": h,
        "img_mode": mode_px,
        "alpha_qa": alpha,
        "status": "ok",
    }
    path = os.path.join(os.path.dirname(os.path.abspath(output)), f"IMAGE_{stem}_MANIFEST.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    log(f"已写 Manifest: {path}")
    return path


def mask_path(args):
    return getattr(args, "mask", None) or ""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="gpt_image.py",
        description="GPT 生图：默认 HiModels（gpt-image-2.5-flare / sunburst），备用 Azure gpt-image-2",
    )
    p.add_argument("--prompt", "-p", required=True, help="提示词")
    p.add_argument("--ref", "-r", action="append", default=[], dest="ref",
                   help="参考图路径，可重复传入（顺序即图1/图2/图3...）")
    p.add_argument("--refs", nargs="*", default=None, dest="refs",
                   help="参考图路径（空格分隔多个），等价于多次 --ref")
    p.add_argument("--mask", default=None,
                   help="编辑蒙版 PNG（与图1同尺寸；透明区域=重绘区，不透明=保留）")
    p.add_argument("--mode", choices=["generation", "edit"], default=None,
                   help="不传则按是否带参考图自动判定")
    p.add_argument("--backend", choices=["himodels", "azure"], default="himodels",
                   help="himodels（默认，HiModels 网关）/ azure（备用后端）")
    p.add_argument("--tier", choices=["standard", "advanced"], default=None,
                   help="standard=gpt-image-2.5-flare（默认）；advanced=gpt-image-2.5-sunburst（大图/精修）")
    p.add_argument("--model", default=None, help="直接指定模型名，覆盖 --tier")
    p.add_argument("--size", "-s", default="auto",
                   help="auto / 1024x1024 / 1280x720 / 2048x1152 / 2560x1440 / "
                        "3584x2016 / 720x1280 / 1152x2048 / 1440x2560 / 2016x3584 / "
                        "1536x1024 / 1024x1536")
    p.add_argument("--quality", "-q", default=None,
                   help="low / medium / high / auto（himodels 默认不传，由服务端决定；azure 默认 low）")
    p.add_argument("--background", "-b", choices=["auto", "transparent", "opaque"], default="auto",
                   help="transparent=生成真透明底并做 alpha 质检（2026-09-22 实测可用）；"
                        "auto=不下发该参数；opaque=强制不透明")
    p.add_argument("--allow-opaque-output", action="store_true",
                   help="背景要求 transparent 但服务端没给 alpha 时，仅告警不失败（默认退出码 3）")
    p.add_argument("--html", default=None,
                   help="仅 --backend azure：从本地 ai_image_tool.html 解析 endpoint/deployment/key")
    p.add_argument("--out", "-o", default=None, help="输出 PNG 路径")
    p.add_argument("--api-key", "--key", default=None, dest="api_key",
                   help="覆盖 key（himodels 默认读 HIMODELS_API_KEY；azure 读 AZURE_OPENAI_API_KEY）")
    p.add_argument("--endpoint", default=None, help="仅 --backend azure：覆盖请求端点")
    p.add_argument("--timeout", type=int, default=600, help="请求超时秒数")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    env = os.environ
    env_from_file = load_env_file(HERMES_ENV_FILE)

    refs = list(args.ref or []) + list(args.refs or [])
    mode = args.mode or ("edit" if refs else "generation")
    if mode == "edit" and not refs:
        log("mode=edit 但没有参考图，请用 --ref 指定至少一张。")
        return 2
    if args.mode is None and refs:
        log(f"检测到 {len(refs)} 张参考图，走 edit 模式。")
        mode = "edit"
    if args.mask and not os.path.exists(args.mask):
        log(f"蒙版不存在: {args.mask}")
        return 2

    try:
        size, reason = resolve_size(args.size, args.prompt, refs)
        log(f"画布尺寸: {size}（{reason}）")
    except Exception as e:
        log(f"尺寸解析失败: {e}")
        return 2

    background = None if args.background == "auto" else args.background
    key = None
    cfg = None
    if args.backend == "azure":
        cfg = get_azure_config(args, env, env_from_file)
        if not cfg["api_key"]:
            log("未配置 Azure Key：设置 AZURE_OPENAI_API_KEY / E:\\hermes\\.env，"
                "或 --html 指向 ai_image_tool.html。（默认后端是 himodels，需要 HIMODELS_API_KEY）")
            return 2
        model = cfg["deployment"]
        quality = args.quality or DEFAULTS["quality"]
        info = {
            "backend": "azure", "model": model, "tier": "azure(备用)",
            "tier_trigger": "显式 --backend azure", "quality": quality,
            "background": background,
            "endpoint": cfg["endpoint"], "deployment": cfg["deployment"],
            "gen_api_version": cfg["gen_api_version"],
            "edit_api_version": cfg["edit_api_version"],
        }
    else:
        key, key_src = resolve_himodels_key(args, env, env_from_file)
        if not key:
            log("未配置 HiModels Key：--api-key 传入，或设置 HIMODELS_API_KEY，"
                f"或在 {CRED_FILE} 配置 HIMODELS_API_KEY。")
            return 2
        model, tier, hit = resolve_model(args, args.prompt)
        quality = args.quality  # 默认不传，交给服务端
        if size in HIMODELS_UNVERIFIED_SIZES:
            log(f"提示：尺寸 {size} 未在 HiModels 实测清单内，若被拒请改用 1152x2048。")
        log(f"后端: HiModels | 模型: {model} [{tier}]"
            + (f"  触发词: {hit}" if hit and hit != "显式指定" else "")
            + f" | background: {background or '(未传)'} | key 来源: {key_src}")
        info = {
            "backend": "himodels", "model": model, "tier": tier,
            "tier_trigger": "" if hit == "显式指定" else (hit or ""), "quality": quality,
            "background": background,
            "endpoint": HIMODELS_BASE_URL, "deployment": model,
        }

    if args.out is None:
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        args.out = f"gpt-image-{ts}.png"

    try:
        started = time.time()
        if args.backend == "azure":
            log(f"生成中（azure 备用后端）→ {size} (quality={info['quality']}) ...")
            raw = call_azure(mode, args.prompt, size, info["quality"], background,
                             refs, args.mask, cfg, args.timeout)
        elif mode == "edit":
            log(f"生成中（HiModels，{len(refs)} 张参考图"
                + ("，带 mask" if args.mask else "") + f"）→ {size} ...")
            raw = call_himodels("edit", args.prompt, info["model"], size,
                                info["quality"], background, refs, args.mask,
                                key, args.timeout)
        else:
            log(f"生成中（HiModels 文本生图）→ {size} ...")
            raw = call_himodels("generation", args.prompt, info["model"], size,
                                info["quality"], background, refs, None,
                                key, args.timeout)
        output = save_png(raw, args.out)
        elapsed = round(time.time() - started, 2)

        alpha = analyse_alpha(output) if background == "transparent" else {"checked": False}
        alpha_ok = True
        if background == "transparent":
            alpha_ok, notes = alpha_gate_report(alpha)
            log(f"alpha 质检 [{ 'PASS' if alpha_ok else 'FAIL'}]：" + "；".join(notes))
            alpha["gate"] = "pass" if alpha_ok else "fail"
            alpha["notes"] = notes

        try:
            write_manifest(output, args, info, size, refs, alpha)
        except Exception as e:
            log(f"Manifest 写入跳过：{e}")

        print(json.dumps({"status": "ok" if alpha_ok else "alpha_failed",
                          "backend": info["backend"], "model": info["model"],
                          "tier": info["tier"], "size": size, "out": output,
                          "background": background or "(未传)", "refs": len(refs),
                          "elapsed_seconds": elapsed,
                          "alpha": alpha}, ensure_ascii=False))

        if background == "transparent" and not alpha_ok:
            if args.allow_opaque_output:
                log("警告：透明底未达标，但 --allow-opaque-output 已指定，按成功返回。"
                    "如需本地兜底：postprocess.py --remove-bg --tol 30")
                return 0
            log("透明底未达标：可用 postprocess.py --remove-bg --tol 30 本地兜底，"
                "或加 --allow-opaque-output 降级为告警。")
            return 3
        return 0
    except Exception as e:
        log(f"生成失败: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
