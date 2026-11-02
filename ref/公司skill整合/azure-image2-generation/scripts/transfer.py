#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transfer.py — 结构锁定换皮 / 外观迁移（Structure-Locked Reskin，Pixel-Locked）

定位：带透明通道 PNG（角色部件、spine 图集切片、UI 素材、图标）的换皮主入口。
在**不改变任何结构、动作、轮廓、透明切边范围**的前提下重绘外观（材质/配色/花纹/风格）。
这是对旧换皮主流程「不够遵循原图结构」的替换；换毛色/花色只是典型场景，不是专用。
专治两类老毛病：
  1) 轮廓无法对齐 —— 生成图先按「原图 alpha 内容框」配准（等比缩放+中心对齐），
     再把原图 alpha 逐字节回写：轮廓/占位在像素层面由原图锁死，模型只贡献材质；
  2) 无法在原图基础上局部编辑 —— 不指望 API 的 mask 字段（HiModels 上游会忽略），
     「局部」由两层保证：prompt 三层约束 + 后端把 preserve_rects 区域用原图像素原样回贴。

参考图职责（铁律）：
  图1 = source  结构基准（必填）。决定 WHAT AND WHERE：结构/姿态/轮廓/配饰/透明切边。
  图2 = ref     外观参考（可选）。只决定 APPEARANCE：配色/花纹位置/材质/过渡。
                没有图2时用纯文字描述外观，两条路径的像素锁定管线完全相同。
  有图2时严禁把它的形状、姿态、配饰（如铃铛）带进结果。

像素锁定后处理（每个候选）：
  ① fit=bbox 配准：候选主体内容框 -> 等比缩放到原图内容框尺寸，居中回原图内容框中心
  ② 边缘出血修补：源图可见但候选透明的地方，用候选自身材质色 inpaint 漫延（防黑斑）
  ③ alpha := 原图 alpha（逐字节）；透明区 RGB 清零（防脏透明）
  ④ preserve_rects 区域回贴原图像素（不变对象保护；支持色键限定，防矩形接缝）
  ⑤ QA 门禁：size / alpha 逐字节 / preserve 逐字节 / missing_coverage / 纯黑死斑 /
     迁移量（changed_pct）/ 内容框残差 —— 任一不过即 FAIL，绝不静默放行

子命令
------
  run       全流程：组 prompt -> 参考图生成 N 候选 -> 配准合成 -> QA -> 对比图（不落地）
  install   从 work 目录选候选落地：备份 -> 无损压缩 -> 硬门禁 -> 覆盖
  prompt    只渲染 prompt（检查用，不调 API）
  selftest  离线自测（合成素材模拟模型输出，不调 API）

纪律：多候选/多花色时，每次都从同一张原图重新生成；绝不用上一轮结果当结构基准（防漂移）。
"""
import argparse, json, os, re, shutil, subprocess, sys, time
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rebuild as rb  # 复用 fit_to_canvas / png_stats / build_sheet / compress_best 等

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def log(msg):
    print(msg, flush=True)


# ----------------------------------------------------------------------------- prompt
PROMPT_TEMPLATE = """Edit Image 1. Output ONE single edited image.

[LAYER 1 - STRUCTURE INHERITANCE, HIGHEST PRIORITY]
Image 1 is the direct edit target. It must remain identical in: overall structure and anatomy, pose and action, all proportions, silhouette and the outline of every object, camera angle and framing, placement on canvas, facial features and expression, accessories / attached parts / separate icons, and the transparent cutout bounds.

[LAYER 2 - FORBIDDEN CHANGES]
Do not change Image 1's structure in any way: no new parts, no removed parts, no moved / resized / redrawn outlines; keep the transparent edge / canvas bounds exactly.
{preserve_lines}
Do not add any new accessory, object, text or watermark.{forbid_line}

[LAYER 3 - APPEARANCE ONLY]
{layer3}
TARGET APPEARANCE DESCRIPTION:
{appearance}

Keep every non-appearance element identical to Image 1.
Background must be fully transparent: no floor, no shadow, no backdrop, no glow, no outline halo. Clean anti-aliased edges.
Single image only - no collage, no grid, no side-by-side variants."""


def build_prompt(cfg):
    preserve_lines = "\n".join(
        "Preserve the %s exactly as in Image 1; do not remove, move, restyle or replace it." % o
        for o in (cfg.get("preserve_objects") or []))
    forbid_line = ""
    if cfg.get("reference"):  # 「禁止从图2带入」只在有外观参考图时有意义
        forbid = cfg.get("forbid_from_reference") or []
        if forbid:
            forbid_line = ("\nEspecially: the reference contains %s — do NOT bring any of "
                           "that into the result." % ", ".join(forbid))
    if cfg.get("reference"):
        layer3 = ("Image 2 is the appearance reference ONLY. From Image 2, transfer ONLY: "
                  "base colors, secondary colors, marking / pattern locations, contours and "
                  "distribution, material and texture, and the softness of color transitions.\n"
                  "Map that appearance onto the EXACT original shapes of Image 1, staying "
                  "inside Image 1's outlines.\n"
                  "Do NOT copy from Image 2: its shape, pose, anatomy, proportions, "
                  "accessories, expression, background or layout.")
    else:
        layer3 = ("No second reference image is provided; the target appearance is fully "
                  "specified in words below. Follow that description exactly.\n"
                  "Redraw only the surface appearance (colors, patterns, material and "
                  "texture) onto the EXACT original shapes of Image 1, staying inside "
                  "Image 1's outlines. Every shape, element and placement stays as in Image 1.")
    appearance = "\n".join("- " + a for a in (cfg.get("appearance") or [])) or "- (describe in spec)"
    return PROMPT_TEMPLATE.format(preserve_lines=preserve_lines,
                                  forbid_line=forbid_line,
                                  layer3=layer3,
                                  appearance=appearance)


# ----------------------------------------------------------------------------- spec
def parse_preserve_rect(r):
    """preserve 区域四种写法：
      'x,y,w,h'               整块回贴（适合透明背景上的独立对象）
      'x,y,w,h:R,G,B:tol'     色键限定：只回贴矩形内颜色距离<=tol 的原图像素
                              （适合叠在会变色区域上的对象，如项圈叠在身体上，
                              防止把旧底色一起贴回来形成矩形接缝）
      [x,y,w,h] / {"rect":[...],"key":[R,G,B],"tol":N}   spec JSON 写法
    """
    if isinstance(r, dict):
        rect = [int(v) for v in list(r.get("rect"))[:4]]
        key = r.get("key")
        key = [int(v) for v in key] if key else None
        tol = int(r.get("tol", 60))
    elif isinstance(r, str):
        parts = r.split(":")
        nums = [int(float(v)) for v in re.split(r"[,\s]+", parts[0].strip()) if v]
        if len(nums) != 4:
            raise SystemExit("preserve_rect 需要 x,y,w,h，收到 %r" % r)
        rect, key, tol = nums, None, 60
        if len(parts) >= 2 and parts[1].strip():
            key = [int(float(v)) for v in re.split(r"[,\s]+", parts[1]) if v]
            if len(key) != 3:
                raise SystemExit("preserve_rect 色键需要 R,G,B，收到 %r" % r)
        if len(parts) >= 3 and parts[2].strip():
            tol = int(float(parts[2]))
    else:
        rect, key, tol = [int(v) for v in list(r)[:4]], None, 60
    return {"rect": rect, "key": key, "tol": tol}


def preserve_mask(region, r):
    """矩形内需要回贴的像素掩码（色键模式=颜色匹配且原 alpha>128；整块模式=全部）。"""
    if not r.get("key"):
        return None
    dist = np.abs(region[:, :, :3].astype(np.int16) - np.array(r["key"], np.int16)).sum(axis=2)
    return (dist <= int(r.get("tol", 60))) & (region[:, :, 3] > 128)


def load_cfg(args):
    cfg = {}
    if args.spec:
        with open(args.spec, encoding="utf-8") as f:
            cfg = json.load(f)
    cli = {
        "source": args.source, "reference": args.ref,
        "appearance": args.appearance, "preserve_objects": args.preserve_object,
        "forbid_from_reference": args.forbid, "preserve_rects": args.preserve_rect,
        "candidates": args.candidates, "tier": args.tier, "api_size": args.api_size,
        "bleed": args.bleed, "background": args.background,
        "work": args.work, "gates": args.gates,
    }
    for k, v in cli.items():
        if v is not None and not (isinstance(v, (list, tuple)) and not v):
            cfg[k] = v
    if not cfg.get("source"):
        raise SystemExit("缺少 source（--source 或写进 spec）")
    if not os.path.exists(cfg["source"]):
        raise SystemExit("原图不存在: %s" % cfg["source"])
    if cfg.get("reference") and not os.path.exists(cfg["reference"]):
        raise SystemExit("外观参考图不存在: %s" % cfg["reference"])
    cfg.setdefault("appearance", [])
    cfg.setdefault("preserve_objects", [])
    cfg.setdefault("forbid_from_reference", [])
    cfg.setdefault("candidates", 2)
    cfg.setdefault("bleed", 12)
    cfg.setdefault("background", "transparent")
    cfg.setdefault("gates", {})
    if isinstance(cfg["gates"], str):  # 门禁阈值可以是 JSON 文件路径
        with open(cfg["gates"], encoding="utf-8") as f:
            cfg["gates"] = json.load(f)
    cfg["preserve_rects"] = [parse_preserve_rect(r) for r in (cfg.get("preserve_rects") or [])]
    return cfg


GATE_DEFAULTS = {
    "max_missing_coverage": 0.05,   # 原图实心处候选没画出来的占比（结构丢失）
    "max_dark_pct": 0.5,            # 可见区纯黑死斑占比 %
    "min_changed_pct": 2.0,         # 可见区至少迁移了多少颜色（太小=模型没干活）
    "max_residual_ratio": 0.08,     # 配准后内容框残差（形状漂移度）
}


# ----------------------------------------------------------------------------- 像素锁定合成
def register_and_composite(cand_path, src_img, src_stats, preserve_rects, bleed_px=12):
    """候选 -> 两步配准 -> 出血修补 -> alpha 回写 -> preserve 回贴。返回 (final_img, info)

    两步配准（关键设计）：
      粗配准：候选整体内容框 -> 原图整体内容框（fit_to_canvas）；
      精配准：在粗配准结果上，取「未保护区域」的内容框再对齐一次。
    为什么需要精配准：模型丢掉浮动图标/配饰时，整体内容框被缺角带偏，主体反而错位；
    而保护区域本来就用原图像素回贴，不参与也不该参与对齐锚定。锚定必须落在主体上。
    """
    src = src_img
    tw, th = src.size
    src_arr = np.array(src)
    src_a = src_arr[:, :, 3]
    full_bbox = tuple(src_stats["content_bbox"])

    protected = np.zeros((th, tw), bool)
    for r in preserve_rects:
        x, y, w, h = r["rect"]
        protected[int(y):int(y) + int(h), int(x):int(x) + int(w)] = True

    def body_bbox(alpha_arr):
        m = (alpha_arr > 8) & ~protected
        ys, xs = m.nonzero()
        if len(xs) == 0:
            return None
        return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)

    src_body = body_bbox(src_a)

    # 粗配准：整体内容框
    reg, meta = rb.fit_to_canvas(cand_path, tw, th, fit="bbox", anchor_bbox=full_bbox)
    reg_arr = np.array(reg)
    reg_body = body_bbox(reg_arr[:, :, 3])

    # 精配准：主体内容框 -> 原图未保护内容框（等比缩放 + 原位回贴）
    body_dev = 0.0
    if src_body and reg_body:
        bw = max(1, src_body[2] - src_body[0])
        bh = max(1, src_body[3] - src_body[1])
        rw = max(1, reg_body[2] - reg_body[0])
        rh = max(1, reg_body[3] - reg_body[1])
        body_dev = float(max(abs(rw / bw - 1.0), abs(rh / bh - 1.0)))  # 模型主体形变度
        sub = reg.crop(reg_body)
        scaled = rb.premultiplied_resize(sub, (bw, bh))
        canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        canvas.alpha_composite(scaled, (src_body[0], src_body[1]))
        reg = canvas

    arr = np.array(reg).astype(np.uint8).copy()
    gen_alpha = arr[:, :, 3]

    # 结构丢失度量：未保护区域里，原图实心、候选近乎全透明的像素占比（inpaint 之前算才是真信号）
    solid = (src_a >= 250) & ~protected
    missing = float((solid & (gen_alpha <= 64)).sum()) / max(1, int(solid.sum()))

    # 边缘出血修补：原图可见、候选透明/半透明处，用候选材质色向内漫延（防黑斑死穴）
    inpainted_px = 0
    if bleed_px > 0 and HAS_CV2:
        solid_gen = (gen_alpha > 128).astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (bleed_px * 2 + 1,) * 2)
        dilated = cv2.dilate(solid_gen, kernel, iterations=1)
        hole = ((dilated > 0) & (solid_gen == 0) & (src_a > 8) & ~protected).astype(np.uint8) * 255
        if hole.any():
            rgb = cv2.inpaint(arr[:, :, :3].copy(), hole, inpaintRadius=bleed_px,
                              flags=cv2.INPAINT_TELEA)
            arr[:, :, :3] = rgb
            inpainted_px = int((hole > 0).sum())
    elif bleed_px > 0 and not HAS_CV2:
        log("  提示：未装 cv2，跳过出血修补（黑斑风险升高，门禁会兜底）")

    # alpha 逐字节回写原图；透明区 RGB 清零
    final = Image.fromarray(arr, "RGBA")
    final.putalpha(Image.fromarray(src_a, "L"))
    f_arr = np.array(final)
    f_arr[src_a == 0] = 0

    # preserve_rects：回贴原图像素（不变对象保护）。无色键=整块；有色键=只贴匹配颜色的像素
    for r in preserve_rects:
        x, y, w, h = (int(v) for v in r["rect"])
        region = src_arr[y:y + h, x:x + w]
        m = preserve_mask(region, r)
        if m is None:
            f_arr[y:y + h, x:x + w] = region
        elif m.any():
            f_arr[y:y + h, x:x + w][m] = region[m]
    f_arr[src_a == 0] = 0  # 回贴后再次清透明区

    final = Image.fromarray(f_arr, "RGBA")
    info = {"fit": meta, "src_body_bbox": list(src_body) if src_body else None,
            "reg_body_bbox": list(reg_body) if reg_body else None,
            "body_shape_deviation": round(body_dev, 4),
            "missing_coverage": missing, "inpainted_px": inpainted_px}
    return final, info


def qa_transfer(src_img, final_img, preserve_rects, gates, missing_coverage=None,
                shape_deviation=None):
    """合成后硬门禁。返回 (gates_dict, metrics_dict, all_pass)"""
    g = {**GATE_DEFAULTS, **(gates or {})}
    s = np.array(src_img)
    f = np.array(final_img)
    src_a = s[:, :, 3]
    metrics = {}
    checks = {}

    checks["size_same"] = s.shape == f.shape
    checks["alpha_identical"] = bool((s[:, :, 3] == f[:, :, 3]).all())

    # preserve 区域必须与原图逐字节一致
    pv_ok = True
    for r in preserve_rects:
        x, y, w, h = (int(v) for v in r["rect"])
        sreg, freg = s[y:y + h, x:x + w], f[y:y + h, x:x + w]
        m = preserve_mask(sreg, r)
        if m is None:
            same = np.array_equal(sreg, freg)
        else:
            same = (not m.any()) or np.array_equal(sreg[m], freg[m])
        if not same:
            pv_ok = False
            break
    checks["preserve_identical"] = pv_ok

    # 结构丢失（register 阶段量得：保护区域之外，原图实心处候选没画出来）
    if missing_coverage is not None:
        metrics["missing_coverage"] = round(float(missing_coverage), 4)
        checks["no_missing_structure"] = float(missing_coverage) <= g["max_missing_coverage"]

    # 主体形变度（精配准前后的比例差）：模型把主体画变形了多少
    if shape_deviation is not None:
        metrics["body_shape_deviation"] = round(float(shape_deviation), 4)
        checks["shape_deviation_ok"] = float(shape_deviation) <= g["max_residual_ratio"]

    visible = src_a >= 250
    n_vis = max(1, int(visible.sum()))
    # 迁移量：可见区平均色距超过阈值才算真迁移了
    diff = np.abs(s[:, :, :3].astype(np.int16) - f[:, :, :3].astype(np.int16)).sum(axis=2)
    changed = visible & (diff > 90)  # 三通道差和 > 90（平均每通道 >30），棕→灰这类真实换色
    changed_pct = round(100.0 * int(changed.sum()) / n_vis, 2)
    metrics["changed_pct"] = changed_pct
    checks["transfer_applied"] = changed_pct >= g["min_changed_pct"]

    # 纯黑死斑（alpha 实心但 RGB 全黑）
    black = visible & (f[:, :, 0] < 8) & (f[:, :, 1] < 8) & (f[:, :, 2] < 8)
    black_pct = round(100.0 * int(black.sum()) / n_vis, 3)
    metrics["black_visible_px"] = int(black.sum())
    metrics["black_visible_pct"] = black_pct
    checks["no_black_blobs"] = black_pct <= g["max_dark_pct"]

    # 脏透明：原图透明处 RGB 必须为 0
    dirty = (src_a == 0) & (f[:, :, :3] != 0).any(axis=2)
    metrics["dirty_transparent_px"] = int(dirty.sum())
    checks["clean_transparent"] = int(dirty.sum()) == 0

    all_pass = all(checks.values())
    return checks, metrics, all_pass


# ----------------------------------------------------------------------------- 生成调用
def call_gpt_image_refs(prompt, out_path, api_size, cfg, retries=1, timeout=900):
    """参考图 edits：图1=source 必在，图2=ref 有则排后面。走 gpt_image.py 子进程（沿用其重试/manifest）。"""
    script = os.path.join(HERE, "gpt_image.py")
    refs = [cfg["source"]] + ([cfg["reference"]] if cfg.get("reference") else [])
    cmd = [sys.executable, script, "--prompt", prompt]
    for r in refs:
        cmd += ["--ref", r]
    cmd += ["--size", "%dx%d" % tuple(api_size),
           "--background", cfg.get("background", "transparent"),
           "--out", out_path]
    if cfg.get("tier"):
        cmd += ["--tier", cfg["tier"]]
    last = None
    for attempt in range(retries + 1):
        log("  -> gpt-image 参考图生成（%d 张）第 %d 次: %s"
            % (1 + (1 if cfg.get("reference") else 0), attempt + 1, os.path.basename(out_path)))
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        if r.returncode == 0 and os.path.exists(out_path):
            return True, "ok"
        err = (r.stderr or b"").decode("utf-8", "replace")
        if r.returncode == 3:
            err = "alpha 质检未达标（gpt_image 退出码 3）"
            if os.path.exists(out_path):
                os.remove(out_path)
        last = "exit=%s %s" % (r.returncode, err.strip()[-400:])
        log("     失败: %s" % last.strip())
    return False, last


# ----------------------------------------------------------------------------- work 目录
def work_dir_for(cfg, src_path):
    root = cfg.get("work") or os.path.join(os.path.dirname(os.path.abspath(src_path)),
                                           "_appearance_transfer")
    stem = os.path.splitext(os.path.basename(src_path))[0]
    d = os.path.join(root, "%s_%s" % (stem, time.strftime("%Y%m%d-%H%M%S")))
    os.makedirs(d, exist_ok=True)
    rb.ensure_gdignore(root)
    return d


# ----------------------------------------------------------------------------- 子命令
def cmd_run(args):
    cfg = load_cfg(args)
    src_path = os.path.abspath(cfg["source"])
    src_stats = rb.png_stats(src_path)
    src_img = Image.open(src_path).convert("RGBA")
    tw, th = src_stats["size"]
    if src_stats["content_bbox"] is None:
        raise SystemExit("原图没有可见主体（alpha 全空），无法做内容框配准")

    rects = [parse_preserve_rect(r) for r in (cfg.get("preserve_rects") or [])]
    for r in rects:
        x, y, w, h = r["rect"]
        if x < 0 or y < 0 or x + w > tw or y + h > th:
            raise SystemExit("preserve_rect %s 超出原图画布 %dx%d" % (r["rect"], tw, th))

    prompt = build_prompt(cfg)
    wd = work_dir_for(cfg, src_path)
    with open(os.path.join(wd, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(prompt)
    log("work 目录: %s" % wd)

    if args.api_size:
        api_size = tuple(int(v) for v in re.split(r"[x,\s]+", args.api_size))
    elif cfg.get("api_size"):
        api_size = tuple(int(v) for v in re.split(r"[x,\s]+", str(cfg["api_size"])))
    else:
        api_size = rb.pick_api_size(tw, th, allow_upscale=True) or (1024, 1024)
    log("API 画幅: %dx%d | 原图: %dx%d | 候选数: %d" % (api_size[0], api_size[1], tw, th,
                                                      cfg["candidates"]))

    report = {"source": src_path,
              "reference": os.path.abspath(cfg["reference"]) if cfg.get("reference") else None,
              "source_stats": src_stats, "api_size": list(api_size),
              "preserve_rects": rects,
              "work_dir": wd, "prompt_file": os.path.join(wd, "prompt.txt"),
              "candidates": []}
    tiles = [("ORIGINAL", src_img)]
    any_pass = False
    for i in range(1, int(cfg["candidates"]) + 1):
        raw = os.path.join(wd, "cand%d.png" % i)
        ok, msg = call_gpt_image_refs(prompt, raw, api_size, cfg, retries=args.retries)
        if not ok:
            report["candidates"].append({"cand": i, "ok": False, "msg": msg})
            continue
        final, info = register_and_composite(raw, src_img, src_stats, rects,
                                             bleed_px=int(cfg.get("bleed", 12)))
        checks, metrics, passed = qa_transfer(src_img, final, rects, cfg.get("gates"),
                                              missing_coverage=info["missing_coverage"],
                                              shape_deviation=info["body_shape_deviation"])
        locked = os.path.join(wd, "cand%d_locked.png" % i)
        final.save(locked)
        entry = {"cand": i, "ok": True, "raw": raw, "locked": locked,
                 "info": info, "qa": {"checks": checks, "metrics": metrics}, "pass": passed}
        report["candidates"].append(entry)
        tiles.append(("cand%d" % i, final))
        log("cand%d: %s | %s" % (i, "PASS" if passed else "FAIL",
                                 json.dumps({**{k: v for k, v in checks.items()},
                                             **metrics}, ensure_ascii=False)))
        any_pass = any_pass or passed

    if len(tiles) > 1:
        report["sheet"] = rb.build_sheet(tiles, os.path.join(wd, "compare.png"), zoom=args.zoom)
        log("对比图: %s" % report["sheet"])

    with open(os.path.join(wd, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    log("报告: %s" % os.path.join(wd, "report.json"))

    if args.install:
        pick = args.pick or (max((c["cand"] for c in report["candidates"] if c.get("pass")),
                                 default=None))
        if pick is None:
            log("没有通过门禁的候选，拒绝落地")
            return 1
        return do_install(wd, pick, src_path, report, dry_run=args.dry_run)
    return 0 if any_pass else 1


def do_install(wd, pick, target, report=None, dry_run=False):
    src = os.path.join(wd, "cand%d_locked.png" % pick)
    if not os.path.exists(src):
        log("找不到候选: %s" % src)
        return 1
    rep = report or json.load(open(os.path.join(wd, "report.json"), encoding="utf-8"))
    entry = next((c for c in rep["candidates"] if c.get("cand") == pick), None)
    if not entry or not entry.get("ok"):
        log("候选 %d 不存在或生成失败" % pick)
        return 1
    if not entry.get("pass"):
        log("候选 %d 未通过 QA 门禁，拒绝落地（--force 可跳过，不推荐）" % pick)
        return 1
    if dry_run:
        log("dry-run：将落地 cand%d -> %s" % (pick, target))
        return 0
    st_before = rb.png_stats(target)
    new_img = Image.open(src).convert("RGBA")
    if st_before["size"] != [new_img.width, new_img.height]:
        log("尺寸不一致，拒绝替换")
        return 1
    bak = os.path.join(wd, "ORIGINAL_" + os.path.basename(target))
    if not os.path.exists(bak):
        shutil.copy2(target, bak)
    tmp = os.path.join(wd, "install.tmp.png")
    _, _, method, identical = rb.compress_best(new_img, tmp)
    if not identical:
        log("压缩后像素校验失败，拒绝替换")
        return 1
    shutil.copy2(tmp, target)
    os.remove(tmp)
    st_after = rb.png_stats(target)
    gates = {
        "size_same": st_after["size"] == st_before["size"],
        "md5_changed": st_after["md5"] != st_before["md5"],
        "alpha_kept": st_after["corners"] == st_before["corners"],
    }
    log("已落地 cand%d -> %s（备份 %s，压缩 %s）| gates=%s" %
        (pick, target, os.path.basename(bak), method, gates))
    return 0 if all(gates.values()) else 1


def cmd_install(args):
    return do_install(args.work, args.pick, os.path.abspath(args.target),
                      dry_run=args.dry_run)


def cmd_prompt(args):
    cfg = load_cfg(args)
    print(build_prompt(cfg))
    return 0


def cmd_selftest(args):
    import selftest_transfer
    return selftest_transfer.run_all()


# ----------------------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(
        prog="transfer.py",
        description="结构锁定换皮/外观迁移：图1=原图锁结构（alpha 逐字节回写），图2=外观参考（可选，Pixel-Locked）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--spec", default=None, help="迁移规格 JSON（appearance/preserve/rects 等）")
        p.add_argument("--source", default=None, help="图1：原图（结构基准，alpha 锁定来源）")
        p.add_argument("--ref", default=None, help="图2：外观参考（只取颜色/花纹/纹理）")
        p.add_argument("--appearance", action="append", default=None,
                       help="外观描述行，可重复（ TARGET APPEARANCE DESCRIPTION 每行一条）")
        p.add_argument("--preserve-object", action="append", default=None,
                       help="必须原样保留的对象描述，可重复（如 'floating paw icon on the right'）")
        p.add_argument("--forbid", action="append", default=None,
                       help="禁止从图2带入的元素，可重复（如 'bell'）")
        p.add_argument("--preserve-rect", action="append", default=None,
                       help="原像素回贴区域 x,y,w,h[:R,G,B:tol]，可重复（色键=只贴匹配颜色的像素）")
        p.add_argument("--candidates", type=int, default=2)
        p.add_argument("--tier", default=None, choices=[None, "standard", "advanced"])
        p.add_argument("--api-size", default=None, help="覆盖 API 画幅，如 1024x1024")
        p.add_argument("--bleed", type=int, default=12, help="出血修补半径（0 关闭，需 cv2）")
        p.add_argument("--background", default="transparent", choices=["transparent", "opaque"])
        p.add_argument("--gates", default=None, help="门禁阈值 JSON 文件（键见 GATE_DEFAULTS）")
        p.add_argument("--work", default=None, help="work 目录（默认原图旁 _appearance_transfer/）")
        p.add_argument("--retries", type=int, default=1)

    p = sub.add_parser("run", help="生成 + 配准合成 + QA + 对比图（--install 可落地）")
    common(p)
    p.add_argument("--zoom", type=int, default=2, help="对比图放大倍数")
    p.add_argument("--install", action="store_true")
    p.add_argument("--pick", type=int, default=None, help="指定落地候选（默认第一个 PASS 的）")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("install", help="从 work 目录落地已 PASS 的候选")
    p.add_argument("--work", required=True)
    p.add_argument("--pick", type=int, required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("prompt", help="只渲染三层约束 prompt（不调 API）")
    common(p)
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("selftest", help="离线自测（合成素材，不调 API）")
    p.set_defaults(func=cmd_selftest)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
