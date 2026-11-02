#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gpt-image-gen / 换皮模块 / rebuild.py

在「原尺寸 + 原命名 + 原透明语义」不变的前提下，用 GPT 生图重绘美术资源并替换回项目。

子命令
------
  single    单张全流程：生成候选 -> 尺寸/构图适配 -> 对比图（可 --install 直接替换）
  gen       批量：按 manifest 生成候选（可断点续跑 --skip-existing）
  prepare   批量：候选 -> 适配到原尺寸 + 对比图（不调 API，离线可跑）
  install   批量：安装已确认候选（备份 -> 无损压缩 -> 硬门禁 -> 替换）
  verify    校验单个文件的尺寸/透明/内容框（替换前后都可跑）
  godot     触发并校验 Godot 重新导入（编辑器在跑就等它扫，不在跑就 headless --import）

设计铁律（踩过的坑，勿改）
--------------------------
1. 绝不让模型负责外轮廓/尺寸：候选一律先按 alpha 内容框裁切，再等比缩放，
   缩放到「原图内容框尺寸」并居中回原图内容框中心 —— 保证视觉体量与占位不变。
   fit=full 时才整幅缩放（用于不透明背景大图）。
2. 缩放必须走预乘 alpha（premultiplied），否则透明黑像素渗入边缘 -> 脏光晕/白边。
3. 安装前必须备份；无损压缩后要逐像素校验与原候选一致，不一致就拒绝写入。
4. 生成的 PNG 一律 --background transparent（图标/贴纸类），靠参数拿 alpha，不靠 prompt。
5. 工作目录放项目内时必须写 .gdignore，否则 Godot 会把中间产物全导进资源库。
"""
import argparse, hashlib, json, math, os, re, shutil, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
STYLES_PATH = os.path.join(HERE, "styles.json")

GPT_SCRIPT_CANDIDATES = [
    os.path.join(HERE, "gpt_image.py"),          # 同目录（本技能自带）
    r"C:\Users\Administrator\.dsh\skills\gpt-image-gen\scripts\gpt_image.py",
    r"E:\Gameprogram\skill-pool\skills\gpt-image-gen\scripts\gpt_image.py",
]
MAGICK_CANDIDATES = [
    r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe",
    "magick",
]
GODOT_CANDIDATES = [
    r"E:\Godot\Godot_v4.6.2-stable_win64_console.exe",
    r"E:\Godot\Godot_v4.6.2-stable_win64.exe",
]

# gpt-image 允许的画幅（长宽比必须从这里挑，最后再缩回原尺寸）
SUPPORTED_SIZES = [
    (1024, 1024), (1536, 1024), (1024, 1536), (1280, 720), (720, 1280),
    (2048, 1152), (1152, 2048), (2560, 1440), (1440, 2560),
    (3584, 2016), (2016, 3584), (1152, 2560),
]
ADVANCED_AREA = 1500000  # 超过这个像素量建议走 advanced(sunburst) 档


# ----------------------------------------------------------------------------- utils
def find_first(paths):
    for p in paths:
        if os.path.isabs(p):
            if os.path.exists(p):
                return p
        else:
            from shutil import which
            w = which(p)
            if w:
                return w
    return None


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_gdignore(folder):
    """项目内工作目录必须带 .gdignore，否则 Godot 会把候选图也导入资源库。"""
    try:
        os.makedirs(folder, exist_ok=True)
        gi = os.path.join(folder, ".gdignore")
        if not os.path.exists(gi):
            open(gi, "w").close()
    except Exception:
        pass


def log(msg):
    print(msg, flush=True)


def png_stats(path):
    im = Image.open(path)
    mode, size = im.mode, im.size
    rgba = im.convert("RGBA")
    a = np.array(rgba)[:, :, 3]
    total = a.size
    n_zero = int((a == 0).sum())
    n_solid = int((a >= 250).sum())
    ys, xs = (a > 8).nonzero()
    bbox = None if len(xs) == 0 else (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    corners = [int(a[0, 0]), int(a[0, -1]), int(a[-1, 0]), int(a[-1, -1])]
    return {
        "path": path, "size": list(size), "mode": mode, "bytes": os.path.getsize(path),
        "md5": md5_of(path), "has_alpha": "A" in mode,
        "transparent_pct": round(100.0 * n_zero / total, 2),
        "solid_pct": round(100.0 * n_solid / total, 2),
        "corners": corners, "content_bbox": list(bbox) if bbox else None,
    }


def is_transparent_asset(stats, threshold=2.0):
    """透明素材判定：有 alpha 通道且透明像素占比超过阈值。"""
    return bool(stats["has_alpha"]) and stats["transparent_pct"] > threshold


# ----------------------------------------------------------------------------- size / fit
def pick_api_size(w, h, allow_upscale=False):
    """按目标长宽比挑一个 gpt-image 支持的画幅：优先「面积 >= 目标面积」里最小的那个。"""
    ar = w / float(h)
    target_area = w * h
    scored = []
    for (aw, ah) in SUPPORTED_SIZES:
        err = abs(math.log((aw / float(ah)) / ar))
        if err > 0.09:  # 约 9% 比例误差以外直接淘汰
            continue
        scored.append((aw * ah, err, (aw, ah)))
    if not scored:
        return None
    big = [s for s in scored if s[0] >= target_area]
    if big:
        big.sort(key=lambda s: (s[0], s[1]))
        return big[0][2]
    if allow_upscale:
        scored.sort(key=lambda s: (-s[0], s[1]))
        return scored[0][2]
    return None


def premultiplied_resize(img, size):
    """预乘 alpha 的 LANCZOS 缩放：避免透明像素渗色产生黑边/白边。"""
    arr = np.array(img).astype(np.float32)
    a = arr[:, :, 3:4] / 255.0
    pm = np.concatenate([arr[:, :, :3] * a, arr[:, :, 3:4]], axis=2)
    small = Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8), "RGBA").resize(size, Image.LANCZOS)
    sp = np.array(small).astype(np.float32)
    al = sp[:, :, 3:4] / 255.0
    rgb = np.where(al > 1e-6, sp[:, :, :3] / np.maximum(al, 1e-6), 0.0)
    return Image.fromarray(np.concatenate([np.clip(rgb, 0, 255), sp[:, :, 3:4]], axis=2).astype(np.uint8), "RGBA")


def fit_to_canvas(candidate, tw, th, fit="bbox", anchor_bbox=None, thresh=8, margin=1):
    """
    bbox: 候选主体内容框 -> 缩放到原图内容框的尺寸，并对齐原图内容框中心（保体量、保占位）
    full: 整幅缩放到目标尺寸（不透明背景大图用）
    """
    cand = Image.open(candidate).convert("RGBA")
    if fit == "full":
        return cand.resize((tw, th), Image.LANCZOS), {"mode": "full"}

    a = np.array(cand)[:, :, 3]
    ys, xs = (a > thresh).nonzero()
    if len(xs) == 0:
        raise RuntimeError("候选图 alpha 全空: %s" % candidate)
    cbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    sub = cand.crop(cbox)

    if anchor_bbox:
        targ_w = max(1, anchor_bbox[2] - anchor_bbox[0])
        targ_h = max(1, anchor_bbox[3] - anchor_bbox[1])
        ccx = (anchor_bbox[0] + anchor_bbox[2]) / 2.0
        ccy = (anchor_bbox[1] + anchor_bbox[3]) / 2.0
    else:
        targ_w = tw - 2 * margin
        targ_h = th - 2 * margin
        ccx, ccy = tw / 2.0, th / 2.0

    scale = min(targ_w / float(sub.width), targ_h / float(sub.height))
    nw = max(1, int(round(sub.width * scale)))
    nh = max(1, int(round(sub.height * scale)))
    nw, nh = min(nw, tw - 2 * margin), min(nh, th - 2 * margin)
    small = premultiplied_resize(sub, (nw, nh))

    ox = int(round(ccx - nw / 2.0))
    oy = int(round(ccy - nh / 2.0))
    ox = max(margin, min(ox, tw - nw - margin))
    oy = max(margin, min(oy, th - nh - margin))

    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.alpha_composite(small, (ox, oy))
    return canvas, {"mode": "bbox", "candidate_content": list(cbox), "scale": round(scale, 4),
                    "placed": [ox, oy, nw, nh], "anchor_bbox": list(anchor_bbox) if anchor_bbox else None}


# ----------------------------------------------------------------------------- prompt
def load_style(name):
    with open(STYLES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if name not in data:
        raise SystemExit("未知风格 %r，可用：%s" % (name, ", ".join(sorted(data))))
    return data[name]


def build_prompt(style, subject, transparent, api_size, target_size, notes=""):
    parts = [style["style_block"].strip(), "", subject.strip()]
    if notes.strip():
        parts += ["", notes.strip()]
    parts += ["", "【构图与输出要求】"]
    parts += [
        "1) 主体完整居中，四周留出安全边距（不小于画面短边的 3%），主体任何部分都不允许被画面边缘裁切、切平或截断。",
        "2) 输出画幅 %dx%d，按该画幅构图；最终会等比缩放回 %dx%d，请保证主体比例与位置合理。" % (api_size[0], api_size[1], target_size[0], target_size[1]),
        "3) 单一主体，不要拼图、不要九宫格、不要多方案并列、不要分屏。",
    ]
    if transparent:
        parts += ["4) 纯透明背景：不要底色、不要地面、不要投影、不要背景色块、不要外描边、不要外发光、不要文字水印。"]
    else:
        parts += ["4) 满幅画面（可不透明）：不要留白边、不要画外框、不要文字水印、不要 UI 控件。"]
    parts += ["", style["negative_block"].strip()]
    return "\n".join(parts)


# ----------------------------------------------------------------------------- gpt-image
def call_gpt_image(prompt, out_path, size, transparent, tier=None, ref=None, gpt_script=None,
                   retries=1, timeout=900, mask=None):
    script = gpt_script or find_first(GPT_SCRIPT_CANDIDATES)
    if not script:
        raise SystemExit("找不到 gpt_image.py，请用 --gpt-script 指定")
    cmd = [sys.executable, script, "--prompt", prompt, "--size", "%dx%d" % size,
           "--background", "transparent" if transparent else "opaque",
           "--out", out_path]
    if tier:
        cmd += ["--tier", tier]
    if ref:
        cmd += ["--ref", ref]
    if mask:
        cmd += ["--mask", mask]
    last = None
    for attempt in range(retries + 1):
        log("  -> gpt-image 第 %d 次: %s" % (attempt + 1, os.path.basename(out_path)))
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        if r.returncode == 0 and os.path.exists(out_path):
            return True, "ok"
        last = "exit=%s %s" % (r.returncode, (r.stderr or b"").decode("utf-8", "replace")[-300:])
        log("     失败: %s" % last.strip())
        if os.path.exists(out_path) and r.returncode == 3:
            os.remove(out_path)
    return False, last


# ----------------------------------------------------------------------------- compress
def compress_best(img, out_path):
    """无损压缩：PIL 与 ImageMagick 各出一份，取更小者；返回 (path, bytes, method, pixels_identical)"""
    ref = np.array(img)
    base = out_path + ".pil.png"
    img.save(base, "PNG", optimize=True, compress_level=9)
    cands = [(os.path.getsize(base), base, "PIL optimize+zlib9")]
    magick = find_first(MAGICK_CANDIDATES)
    if magick:
        try:
            mag = out_path + ".magick.png"
            subprocess.run([magick, base, "-strip", "-define", "png:compression-level=9",
                            "-define", "png:compression-filter=5", mag],
                           capture_output=True, timeout=180)
            if os.path.exists(mag):
                cands.append((os.path.getsize(mag), mag, "ImageMagick -strip"))
        except Exception:
            pass
    ok = [(sz, p, m) for (sz, p, m) in cands
          if np.array_equal(np.array(Image.open(p).convert("RGBA")), ref)]
    if not ok:
        raise RuntimeError("无损压缩校验失败（解码像素与原图不一致）")
    ok.sort()
    size, best, method = ok[0]
    shutil.copyfile(best, out_path)
    for _, p, _ in cands:
        if os.path.abspath(p) != os.path.abspath(out_path):
            try:
                os.remove(p)
            except OSError:
                pass
    return out_path, size, method, True


# ----------------------------------------------------------------------------- sheets
def checkerboard(size, sq=12):
    board = Image.new("RGBA", size, (255, 255, 255, 255))
    d = ImageDraw.Draw(board)
    for y in range(0, size[1], sq):
        for x in range(0, size[0], sq):
            if ((x // sq) + (y // sq)) % 2:
                d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=(205, 205, 210, 255))
    return board


def build_sheet(tiles, out_path, zoom=5, bg="checker", labels=True):
    """tiles: [(label, PIL.Image)]，统一缩放展示。"""
    if not tiles:
        return None
    max_w = max(im.width for _, im in tiles)
    max_h = max(im.height for _, im in tiles)
    zoom = max(1, min(int(zoom), max(1, 900 // max(1, max_h))))
    cell_w, cell_h = max_w * zoom, max_h * zoom
    pad, lab = 10, (26 if labels else 0)
    sheet = Image.new("RGB", (len(tiles) * (cell_w + pad) + pad, cell_h + lab + 2 * pad), (30, 30, 36))
    dr = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(tiles):
        if bg == "dark":
            board = Image.new("RGBA", (cell_w, cell_h), (38, 42, 52, 255))
        elif bg == "light":
            board = Image.new("RGBA", (cell_w, cell_h), (238, 240, 244, 255))
        else:
            board = checkerboard((cell_w, cell_h))
        board.alpha_composite(im.convert("RGBA").resize((im.width * zoom, im.height * zoom), Image.NEAREST))
        x = pad + i * (cell_w + pad)
        sheet.paste(board.convert("RGB"), (x, pad))
        if labels:
            dr.text((x, pad + cell_h + 6), str(name)[:60], fill=(235, 235, 235))
    sheet.save(out_path)
    return out_path


# ----------------------------------------------------------------------------- godot
def godot_running(project):
    try:
        ps = subprocess.run(["powershell", "-NoProfile", "-Command",
                             "Get-CimInstance Win32_Process | Where-Object { $_.Name -like '*odot*' } | "
                             "Select-Object -ExpandProperty CommandLine"],
                            capture_output=True, timeout=60)
        out = (ps.stdout or b"").decode("utf-8", "replace")
        key = os.path.basename(os.path.abspath(project)).lower()
        return (key in out.lower()) or (os.path.abspath(project).lower() in out.lower()), out.strip()
    except Exception as e:
        return False, "查询失败: %s" % e


def project_root_of(png_path):
    d = os.path.dirname(os.path.abspath(png_path))
    while d and not os.path.exists(os.path.join(d, "project.godot")):
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
    return d


def import_md5_path(png_path):
    imp = png_path + ".import"
    if not os.path.exists(imp):
        return None
    txt = open(imp, encoding="utf-8", errors="replace").read()
    m = re.search(r'dest_files=\["res://([^"]+)"\]', txt)
    project = project_root_of(png_path)
    if not m or not project:
        return None
    return os.path.join(project, ".godot", "imported", os.path.basename(m.group(1)) + ".md5")


def godot_reimport(project, png_path, wait=90, godot_bin=None):
    """返回 (ok, 说明)。编辑器在跑就等它自动扫；没在跑就 headless --import。"""
    running, _ = godot_running(project)
    src_md5 = md5_of(png_path)
    md5f = import_md5_path(png_path)
    if running:
        log("  Godot 编辑器正在运行 -> 等它文件系统扫描自动重新导入")
        for _ in range(max(1, wait // 5)):
            if md5f and os.path.exists(md5f) and src_md5 in open(md5f).read():
                return True, "编辑器已自动重新导入"
            time.sleep(5)
        return False, "编辑器尚未扫描到改动：点一下 Godot 窗口即会重新导入（或 FileSystem 面板右键 Reimport）"
    binp = godot_bin or find_first(GODOT_CANDIDATES)
    if not binp:
        return False, "未找到 Godot 可执行文件，跳过导入校验"
    log("  headless 重新导入: %s" % binp)
    r = subprocess.run([binp, "--headless", "--path", project, "--import"],
                       capture_output=True, timeout=900)
    ok = r.returncode == 0
    if md5f and os.path.exists(md5f):
        ok = ok and (src_md5 in open(md5f).read())
    return ok, "headless --import exit=%s" % r.returncode


# ----------------------------------------------------------------------------- batch model
def load_manifest(path):
    with open(path, encoding="utf-8") as f:
        mf = json.load(f)
    mf.setdefault("style", "mediterranean-casual-3d")
    return mf


def project_of(mf):
    return mf.get("project") or os.getcwd()


def resolve_target(mf, item):
    p = item["file"]
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(project_of(mf), p))


def work_dir_for(mf, item):
    root = mf.get("work_root") or os.path.join(project_of(mf), "_art_rebuild")
    d = os.path.join(root, mf.get("batch", "batch"), item["id"])
    os.makedirs(d, exist_ok=True)
    ensure_gdignore(root)
    return d


def gen_item(mf, item, args):
    target = resolve_target(mf, item)
    if not os.path.exists(target):
        return {"id": item["id"], "error": "目标不存在: %s" % target}
    st = png_stats(target)
    transparent = is_transparent_asset(st)
    tw, th = st["size"]
    allow_up = bool(item.get("allow_upscale", args.allow_upscale))
    size = pick_api_size(tw, th, allow_up)
    if size is None:
        return {"id": item["id"], "error": "找不到匹配 %dx%d 的 API 画幅（可加 allow_upscale）" % (tw, th)}
    tier = item.get("tier", args.tier)
    if tier is None and size[0] * size[1] > ADVANCED_AREA:
        tier = "advanced"
    rmode = item.get("use_ref", args.use_ref)
    ref = target if rmode == "original" else (None if rmode in ("none", "", None) else rmode)
    style = load_style(item.get("style", mf.get("style", args.style)))
    prompt = build_prompt(style, item.get("prompt", item["id"]), transparent, size, (tw, th),
                          notes=item.get("notes", ""))
    wd = work_dir_for(mf, item)
    with open(os.path.join(wd, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(prompt)
    n = int(item.get("candidates", args.candidates))
    results = []
    for i in range(1, n + 1):
        out = os.path.join(wd, "cand%d.png" % i)
        if args.skip_existing and os.path.exists(out):
            log("[%s] cand%d 已存在，跳过生成" % (item["id"], i))
            results.append({"cand": i, "ok": True, "reused": True})
            continue
        ok, msg = call_gpt_image(prompt, out, size, transparent, tier=tier, ref=ref,
                                 gpt_script=args.gpt_script, retries=args.retries)
        results.append({"cand": i, "ok": ok, "msg": msg})
    return {"id": item["id"], "target": target, "stats_before": st, "transparent": transparent,
            "api_size": list(size), "tier": tier, "ref": ref, "work_dir": wd, "generated": results}


def prepare_item(mf, item, args):
    if item.get("mode") == "atlas":
        # atlas 候选在生成阶段就已按原 Rect 装配回原尺寸，无需再做等比适配
        wd = work_dir_for(mf, item)
        cands = [(os.path.basename(f), os.path.join(wd, f))
                 for f in sorted(os.listdir(wd)) if re.fullmatch(r"cand\d+_fit\.png", f)]
        sheet = build_atlas_sheet(resolve_target(mf, item), cands, resolve_regions(item, args),
                                  os.path.join(wd, "compare.png"), ctx=int(item.get("context", 96)))
        return {"id": item["id"], "mode": "atlas", "target": resolve_target(mf, item),
                "candidates": [{"cand": c, "fit_png": p} for c, p in cands], "sheet": sheet}
    target = resolve_target(mf, item)
    st = png_stats(target)
    transparent = is_transparent_asset(st)
    tw, th = st["size"]
    wd = work_dir_for(mf, item)
    anchor = st["content_bbox"]
    fit = item.get("fit", "bbox" if transparent else "full")
    tiles = [("ORIGINAL", Image.open(target).convert("RGBA"))]
    finals = []
    for cand in sorted(f for f in os.listdir(wd) if re.fullmatch(r"cand\d+\.png", f)):
        src = os.path.join(wd, cand)
        try:
            img, meta = fit_to_canvas(src, tw, th, fit=fit, anchor_bbox=(anchor if fit == "bbox" else None))
        except Exception as e:
            log("[%s] %s 适配失败: %s" % (item["id"], cand, e))
            continue
        out = os.path.join(wd, cand.replace(".png", "_fit.png"))
        img.save(out)
        finals.append({"cand": cand, "fit_png": out, "meta": meta,
                       "stats": png_stats(out), "source": src})
        tiles.append((cand.replace(".png", ""), img))
    sheet = os.path.join(wd, "compare.png")
    if len(tiles) > 1:
        build_sheet(tiles, sheet, zoom=int(item.get("zoom", 5)))
    else:
        sheet = None
    return {"id": item["id"], "target": target, "width": tw, "height": th,
            "transparent": transparent, "fit": fit, "content_bbox": anchor,
            "candidates": finals, "sheet": sheet}


def install_item(mf, item, args):
    target = resolve_target(mf, item)
    wd = work_dir_for(mf, item)
    pick = item.get("pick", args.pick)
    if pick in (None, 0):
        return {"id": item["id"], "error": "未指定候选编号（item.pick 或 --pick <n>）"}
    src = os.path.join(wd, "cand%d_fit.png" % pick)
    if not os.path.exists(src):
        return {"id": item["id"], "error": "找不到适配后的候选: %s" % src}
    st_before = png_stats(target)
    new_img = Image.open(src).convert("RGBA")
    if st_before["size"] != [new_img.width, new_img.height]:
        return {"id": item["id"], "error": "尺寸不一致，拒绝替换"}
    if args.dry_run:
        return {"id": item["id"], "dry_run": True, "would_install": src, "before": st_before}
    bak = os.path.join(wd, "ORIGINAL_" + os.path.basename(target))
    if not os.path.exists(bak):
        shutil.copy2(target, bak)
    tmp = os.path.join(wd, "install.tmp.png")
    _, _, method, identical = compress_best(new_img, tmp)
    if not identical:
        return {"id": item["id"], "error": "压缩后像素校验失败，拒绝替换"}
    shutil.copy2(tmp, target)
    os.remove(tmp)
    st_after = png_stats(target)
    gates = {
        "size_same": st_after["size"] == st_before["size"],
        "corners_transparent": (not st_after["has_alpha"]) or max(st_after["corners"]) <= 16,
        "smaller_or_equal": st_after["bytes"] <= st_before["bytes"],
        "md5_changed": st_after["md5"] != st_before["md5"],
    }
    bb = st_after["content_bbox"]
    if bb:
        m = min(bb[0], bb[1], st_after["size"][0] - bb[2], st_after["size"][1] - bb[3])
        gates["content_inside"] = m >= 0
    return {"id": item["id"], "target": target, "backup": bak, "candidate": src,
            "before": st_before, "after": st_after, "compress_method": method,
            "gates": gates, "pass": all(gates.values())}


def verify_target(path):
    st = png_stats(path)
    bb = st["content_bbox"]
    notes = []
    if st["has_alpha"]:
        if max(st["corners"]) > 16:
            notes.append("四角不透明，透明底可能有问题")
        if st["transparent_pct"] < 3:
            notes.append("透明像素占比 <3%")
        if st["solid_pct"] < 1:
            notes.append("实心主体 <1%")
    if bb:
        m = min(bb[0], bb[1], st["size"][0] - bb[2], st["size"][1] - bb[3])
        notes.append("主体四周最小留白 %dpx" % m)
        if m <= 0:
            notes.append("主体贴边（可能被裁切）")
    return st, notes


# ----------------------------------------------------------------------------- atlas 原位局部重绘
# 铁律：图集几何（region 坐标 / padding / bleed）绝不由模型决定。
# 模型只被要求"在窗口内重绘这一块"，产出的像素我们只按原 Rect 收割回来，
# 区域外一个字节都不写 —— 因此图集索引不可能失效。
SPINE_HEADER_KEYS = ("size", "format", "filter", "repeat", "pma", "scale")


def parse_spine_atlas(path):
    """解析 .atlas（兼容标准 Spine 与 flat/bounds 变体）-> [{name, page, x, y, w, h, rotate}]

    标准 Spine:  region 名 + 缩进的 xy:/size:/rotate:/orig:/offset:/index:
    本工程变体:  平铺的 name 行 + bounds:x,y,w,h + offsets:...
    两种都靠「key:value 且 key 是标识符」来识别属性行，其余非空行即 region 名。
    """
    regs, page, cur = [], None, None
    KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def nums(v):
        return [int(float(x)) for x in re.split(r"[,\s]+", v) if x != ""]

    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.lower().endswith(".png"):
                page, cur = line, None
                continue
            key, sep, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if sep and KEY_RE.match(key):
                k = key.lower()
                if cur is None:
                    continue                      # 页头（size/filter/pma/...）
                if k == "bounds":
                    p = nums(val)
                    if len(p) >= 4:
                        cur["x"], cur["y"], cur["w"], cur["h"] = p[0], p[1], p[2], p[3]
                elif k == "xy":
                    p = nums(val)
                    if len(p) >= 2:
                        cur["x"], cur["y"] = p[0], p[1]
                elif k == "size" and "w" not in cur:
                    p = nums(val)
                    if len(p) >= 2:
                        cur["w"], cur["h"] = p[0], p[1]
                elif k == "rotate":
                    cur["rotate"] = val.lower().startswith("true")
                # offsets/orig/offset/index 等一律忽略
                continue
            cur = {"name": line, "page": page}
            regs.append(cur)
    return [r for r in regs if "x" in r and "y" in r and "w" in r and "h" in r]


def declared_page_size(atlas_path):
    """读 .atlas 里声明的页尺寸 size:W,H"""
    for line in open(atlas_path, encoding="utf-8", errors="replace"):
        s = line.strip()
        if s.lower().startswith("size:"):
            try:
                a, b = s.split(":", 1)[1].split(",")
                return int(float(a)), int(float(b))
            except Exception:
                return None
    return None


def alpha_regions(png_path, alpha_thresh=8, min_side=6, min_pixels=64):
    """直接从 PNG 的 alpha 通道切出真实切片 bbox —— 不依赖任何元数据，像素级可信。"""
    im = Image.open(png_path).convert("RGBA")
    a = np.array(im)[:, :, 3]
    mask = (a > alpha_thresh).astype(np.uint8)
    comps = []
    try:
        import cv2
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        for i in range(1, n):
            x, y, w, h, area = (int(v) for v in stats[i])
            if area >= min_pixels and w >= min_side and h >= min_side:
                comps.append({"name": "auto_%d" % i, "x": x, "y": y, "w": w, "h": h, "area": area})
    except Exception:
        seen = np.zeros_like(mask, bool)
        Hs, Ws = mask.shape
        for y0 in range(Hs):
            for x0 in range(Ws):
                if mask[y0, x0] and not seen[y0, x0]:
                    stack = [(y0, x0)]; seen[y0, x0] = True
                    xs = [x0]; ys = [y0]; cnt = 0
                    while stack:
                        cy, cx = stack.pop(); cnt += 1
                        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < Hs and 0 <= nx < Ws and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True; stack.append((ny, nx)); xs.append(nx); ys.append(ny)
                    w = max(xs) - min(xs) + 1; h = max(ys) - min(ys) + 1
                    if cnt >= min_pixels and w >= min_side and h >= min_side:
                        comps.append({"name": "auto_%d" % len(comps), "x": min(xs), "y": min(ys),
                                      "w": w, "h": h, "area": cnt})
    comps.sort(key=lambda c: -c["area"])
    return comps


def pick_region_by_point(regs, px, py):
    """选包含该点的切片；没有就选中心最近的。"""
    for r in regs:
        if r["x"] <= px < r["x"] + r["w"] and r["y"] <= py < r["y"] + r["h"]:
            return r
    if not regs:
        return None
    return min(regs, key=lambda r: (r["x"] + r["w"] / 2.0 - px) ** 2 + (r["y"] + r["h"] / 2.0 - py) ** 2)


def validate_metadata_regions(atlas_path, png_path, regs):
    """使用 .atlas 元数据前的强制体检：声明尺寸必须等于实际、region 必须全在画布内。"""
    reasons = []
    W, H = Image.open(png_path).size
    dec = declared_page_size(atlas_path)
    if dec and tuple(dec) != (W, H):
        reasons.append("声明页尺寸 %dx%d 与 PNG 实际 %dx%d 不符（元数据坐标不可信）" % (dec[0], dec[1], W, H))
    oob = [r for r in regs if not (0 <= r["x"] and 0 <= r["y"] and r["x"] + r["w"] <= W and r["y"] + r["h"] <= H)]
    if oob:
        reasons.append("%d/%d 个 region 越出画布（例：%s @ %d,%d %dx%d）" % (
            len(oob), len(regs), oob[0].get("name"), oob[0]["x"], oob[0]["y"], oob[0]["w"], oob[0]["h"]))
    return (not reasons), reasons


def regions_from_json(path):
    data = json.load(open(path, encoding="utf-8"))
    regs = data.get("regions", data) if isinstance(data, dict) else data
    out = []
    for r in regs:
        if isinstance(r, dict) and "x" in r and "y" in r:
            out.append({"name": r.get("name", "region"), "x": int(r["x"]), "y": int(r["y"]),
                        "w": int(r.get("w", r.get("width"))), "h": int(r.get("h", r.get("height")))})
    return out


def parse_rect(s):
    parts = [int(float(x)) for x in re.split(r"[,\s]+", s.strip()) if x]
    if len(parts) != 4:
        raise SystemExit("--rect 需要 4 个数 x,y,w,h，收到 %r" % s)
    return {"name": "rect", "x": parts[0], "y": parts[1], "w": parts[2], "h": parts[3]}


def resolve_regions(item, args, png_path=None):
    """切片来源优先级：显式 rect > 像素级自动切片(点选/序号/最大N) > 元数据(必须通过体检)。"""
    regs, why = [], []
    for s in (getattr(args, "rect", None) or []):
        regs.append(parse_rect(s))
    for r in (item.get("regions") or []):
        regs.append({"name": r.get("name", "region"), "x": int(r["x"]), "y": int(r["y"]),
                     "w": int(r.get("w", r.get("width"))), "h": int(r.get("h", r.get("height")))})

    at = getattr(args, "at", None) or item.get("at")
    auto_index = getattr(args, "auto_index", None) if getattr(args, "auto_index", None) is not None else item.get("auto_index")
    auto_top = getattr(args, "auto_top", None) or item.get("auto_top")
    auto_files = (getattr(args, "atlas_file", None) or []) + list(item.get("atlas_files") or [])
    need_auto = bool(at or auto_index is not None or auto_top or getattr(args, "auto_regions", False))

    if at:
        px, py = [int(float(v)) for v in re.split(r"[,\s]+", at)]
        cands = alpha_regions(png_path)
        r = pick_region_by_point(cands, px, py)
        if r is None:
            raise SystemExit("在 %s 的 (%d,%d) 处没有找到任何切片" % (png_path, px, py))
        W0, H0 = Image.open(png_path).size
        if r["w"] * r["h"] > 0.6 * W0 * H0:
            log("  警告：(%d,%d) 命中的连通域占了整页 %d%% —— 这张图集不是透明切片图集，"
                "自动切片不可用，请改用 --rect x,y,w,h 显式指定" % (px, py, round(100.0 * r["w"] * r["h"] / (W0 * H0))))
        r = dict(r); r["name"] = "auto@%d,%d" % (px, py)
        regs.append(r)
    elif auto_index is not None:
        cands = alpha_regions(png_path)
        if auto_index >= len(cands):
            raise SystemExit("auto_index %d 越界（共 %d 个切片）" % (auto_index, len(cands)))
        regs.append(dict(cands[auto_index]))
    elif auto_top:
        regs += [dict(c) for c in alpha_regions(png_path)[:int(auto_top)]]
    elif auto_files:
        for p in auto_files:
            if p.lower().endswith(".atlas"):
                mr = parse_spine_atlas(p)
                if png_path:
                    ok, reasons = validate_metadata_regions(p, png_path, mr)
                    if not ok and not getattr(args, "allow_untrusted_atlas", False):
                        raise SystemExit(
                            "拒绝使用 .atlas 元数据：" + "；".join(reasons) +
                            "\n  改用像素级切片：--at %s 里该物品的任意一点" % png_path if png_path else
                            "拒绝使用 .atlas 元数据：" + "；".join(reasons) +
                            "\n  该页与元数据不一致，请改用 --at X,Y 或 --auto-index N")
                regs += mr
            else:
                regs += regions_from_json(p)

    names = set(item.get("region_names") or []) | set(getattr(args, "region", None) or [])
    if names:
        regs = [r for r in regs if r.get("name") in names]
    if not regs:
        raise SystemExit("atlas 模式需要 region：--rect x,y,w,h / --at X,Y / --auto-index N / --atlas-file x.atlas")
    return regs


def union_rect(rects):
    return (min(r["x"] for r in rects), min(r["y"] for r in rects),
            max(r["x"] + r["w"] for r in rects), max(r["y"] + r["h"] for r in rects))


def build_window(atlas_size, rects, bleed, ctx, api_size):
    """围绕目标 region 取一个尽量贴合 API 长宽比的窗口（含 bleed + 上下文）。"""
    W, H = atlas_size
    x0, y0, x1, y1 = union_rect(rects)
    x0 -= (bleed + ctx); y0 -= (bleed + ctx); x1 += (bleed + ctx); y1 += (bleed + ctx)
    ar = api_size[0] / float(api_size[1])
    w, h = x1 - x0, y1 - y0
    if w / float(h) < ar:
        need = int(math.ceil(h * ar))
        x0 -= (need - w) // 2
        x1 = x0 + need
    else:
        need = int(math.ceil(w / ar))
        y0 -= (need - h) // 2
        y1 = y0 + need
    w, h = x1 - x0, y1 - y0
    # 夹回画布（窗口只平移，不改变大小，保证长宽比）
    x0 = max(0, min(x0, max(0, W - w)))
    y0 = max(0, min(y0, max(0, H - h)))
    w = min(w, W); h = min(h, H)
    return [int(x0), int(y0), int(w), int(h)]


def window_covers(win, rects, bleed, canvas=None):
    """窗口是否覆盖 region+bleed 落在画布内的那部分（出血超出画布的部分本来就会被裁掉，不算不覆盖）。"""
    x0, y0, w, h = win
    for r in rects:
        rx0, ry0 = max(0, r["x"] - bleed), max(0, r["y"] - bleed)
        rx1, ry1 = r["x"] + r["w"] + bleed, r["y"] + r["h"] + bleed
        if canvas:
            rx1, ry1 = min(canvas[0], rx1), min(canvas[1], ry1)
        if not (x0 <= rx0 and y0 <= ry0 and x0 + w >= rx1 and y0 + h >= ry1):
            return False
    return True


def make_mask(win, rects, bleed):
    """透明=重绘区，不透明=保留（OpenAI images/edits 约定）。"""
    x0, y0, w, h = win
    m = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    d = ImageDraw.Draw(m)
    for r in rects:
        ax0 = max(0, r["x"] - bleed) - x0
        ay0 = max(0, r["y"] - bleed) - y0
        ax1 = min(x0 + w, r["x"] + r["w"] + bleed) - x0
        ay1 = min(y0 + h, r["y"] + r["h"] + bleed) - y0
        if ax1 > ax0 and ay1 > ay0:
            d.rectangle([ax0, ay0, ax1 - 1, ay1 - 1], fill=(0, 0, 0, 0))
    return m


def harvest(atlas_orig, ai_window, win, rects, bleed, alpha_from="original"):
    """只把目标区域的像素从 AI 结果搬回来；区域外一个字节都不动。"""
    x0, y0, w, h = win
    W, H = atlas_orig.size
    ai = Image.open(ai_window).convert("RGBA")
    if ai.size != (w, h):
        ai = premultiplied_resize(ai, (w, h))
    out = atlas_orig.copy()
    for r in rects:
        ax0 = max(0, r["x"] - bleed); ay0 = max(0, r["y"] - bleed)
        ax1 = min(W, r["x"] + r["w"] + bleed); ay1 = min(H, r["y"] + r["h"] + bleed)
        if ax1 <= ax0 or ay1 <= ay0:
            continue
        patch = ai.crop((ax0 - x0, ay0 - y0, ax1 - x0, ay1 - y0))
        if alpha_from == "original":
            keep = np.array(atlas_orig.crop((ax0, ay0, ax1, ay1)))[:, :, 3:4]
            arr = np.array(patch)
            arr[:, :, 3:4] = keep
            patch = Image.fromarray(arr, "RGBA")
        out.paste(patch, (ax0, ay0), patch)
    return out


def atlas_gates(orig_path, cand_path, rects, bleed, clamped):
    """图集专用硬门禁：区域外逐字节一致 是「图集不可能失效」的直接证明。"""
    a = np.array(Image.open(orig_path).convert("RGBA"))
    b = np.array(Image.open(cand_path).convert("RGBA"))
    if a.shape != b.shape:
        return {"size_same": False}, False
    H, W = a.shape[:2]
    keep = np.zeros((H, W), bool)
    for r in rects:
        x0 = max(0, r["x"] - bleed); y0 = max(0, r["y"] - bleed)
        x1 = min(W, r["x"] + r["w"] + bleed); y1 = min(H, r["y"] + r["h"] + bleed)
        if x1 > x0 and y1 > y0:
            keep[y0:y1, x0:x1] = True
    outside_same = bool((a[~keep] == b[~keep]).all())
    inside = b[keep]
    alpha_same = bool((a[keep][:, 3] == b[keep][:, 3]).all()) if clamped else True
    changed_inside = bool((a[keep] != b[keep]).any())
    solid_before = int((a[keep][:, 3] >= 250).sum())
    solid_after = int((inside[:, 3] >= 250).sum())
    gates = {
        "size_same": True,
        "outside_untouched": outside_same,
        "alpha_identical": alpha_same,
        "region_content_changed": changed_inside,
        "region_not_emptied": solid_after >= max(1, int(solid_before * 0.5)),
        "regions_in_canvas": True,
    }
    return gates, all(gates.values())


def build_atlas_sheet(orig_path, cand_paths, rects, out_path, bleed=24, ctx=48, zoom=3):
    x0, y0, x1, y1 = union_rect(rects)
    x0 = max(0, x0 - bleed - ctx); y0 = max(0, y0 - bleed - ctx)
    x1 += bleed + ctx; y1 += bleed + ctx
    tiles = [("ORIGINAL", Image.open(orig_path).convert("RGBA").crop((x0, y0, x1, y1)))]
    for label, p in cand_paths:
        tiles.append((label, Image.open(p).convert("RGBA").crop((x0, y0, x1, y1))))
    return build_sheet(tiles, out_path, zoom=zoom)


def atlas_generate(mf, item, args):
    target = resolve_target(mf, item)
    if not os.path.exists(target):
        return {"id": item["id"], "error": "目标不存在: %s" % target}
    st = png_stats(target)
    W, H = st["size"]
    transparent = is_transparent_asset(st)
    rects = resolve_regions(item, args, target)
    bleed = int(item.get("bleed", getattr(args, "bleed", 16)))
    ctx = int(item.get("context", getattr(args, "context", 96)))
    alpha_from = item.get("alpha_from", getattr(args, "alpha_from", "original"))
    style = load_style(item.get("style", mf.get("style", args.style)))
    wd = work_dir_for(mf, item)
    os.makedirs(wd, exist_ok=True)
    n = int(item.get("candidates", args.candidates))
    results, cand_paths = [], []
    for i in range(1, n + 1):
        # 每个候选单独选窗口（同一 region 下一致），窗口比例贴合 API 画幅
        api_size = pick_api_size(max(1, (union_rect(rects)[2] - union_rect(rects)[0]) + 2 * (bleed + ctx)),
                                 max(1, (union_rect(rects)[3] - union_rect(rects)[1]) + 2 * (bleed + ctx)),
                                 allow_upscale=True) or (1024, 1024)
        win = build_window((W, H), rects, bleed, ctx, api_size)
        if not window_covers(win, rects, bleed, (W, H)):
            log('  警告：窗口无法完整覆盖 region+bleed，退化为整页窗口（已由门禁兜底）')
            win = [0, 0, W, H]
        ref_p = os.path.join(wd, "window_orig.png")
        Image.open(target).convert("RGBA").crop(tuple(win)).save(ref_p)
        mask_p = os.path.join(wd, "window_mask.png")
        make_mask(win, rects, bleed).save(mask_p)
        prompt = build_atlas_prompt(style, item.get("prompt", item["id"]), api_size, win, transparent,
                                    bleed, item.get("notes", ""))
        with open(os.path.join(wd, "prompt.txt"), "w", encoding="utf-8") as f:
            f.write(prompt)
        raw = os.path.join(wd, "cand%d.png" % i)
        if getattr(args, "skip_existing", False) and os.path.exists(raw):
            log("[%s] cand%d 已存在，跳过生成" % (item["id"], i))
        else:
            ok, msg = call_gpt_image(prompt, raw, api_size, transparent, tier=item.get("tier", args.tier),
                                     ref=ref_p, mask=mask_p, gpt_script=args.gpt_script,
                                     retries=args.retries)
            if not ok:
                results.append({"cand": i, "ok": False, "msg": msg})
                continue
        assembled = harvest(Image.open(target).convert("RGBA"), raw, win, rects, bleed, alpha_from)
        fit_p = os.path.join(wd, "cand%d_fit.png" % i)
        assembled.save(fit_p)
        cand_paths.append(("cand%d" % i, fit_p))
        results.append({"cand": i, "ok": True, "window": win, "api_size": list(api_size),
                        "rects": rects, "alpha_from": alpha_from, "assembled": fit_p})
    sheet = None
    if cand_paths:
        sheet = build_atlas_sheet(target, cand_paths, rects, os.path.join(wd, "compare.png"),
                                  bleed=max(24, bleed), ctx=ctx)
    return {"id": item["id"], "mode": "atlas", "target": target, "size": [W, H], "transparent": transparent,
            "rects": rects, "bleed": bleed, "context": ctx, "alpha_from": alpha_from,
            "work_dir": wd, "generated": results, "candidates": cand_paths, "sheet": sheet,
            "gates": [atlas_gates(target, p, rects, bleed, alpha_from == "original")[0] for _, p in cand_paths]}


def build_atlas_prompt(style, subject, api_size, win, transparent, bleed, notes=""):
    parts = [style["style_block"].strip(), "", subject.strip()]
    if notes.strip():
        parts += ["", notes.strip()]
    parts += ["", "【本图是图集上的一个局部窗口，务必严格遵守】",
              "1) 只重绘蒙版（透明）区域内的这一个物品，把它按照上面的风格重新绘制。",
              "2) 该物品在画面中的位置、大小、比例、朝向、透视角度，必须与参考图完全一致，不允许移动、缩放、旋转或重排。",
              "3) 蒙版以外的区域保持参考图原样，不要新增、删除或改动任何其他元素。",
              "4) 输出画幅 %dx%d，窗口实际尺寸 %dx%d（最终会等比缩回该尺寸）。" % (api_size[0], api_size[1], win[2], win[3]),
              "5) 不要文字、水印、边框；不要拼接、不要九宫格、不要多方案。"]
    if transparent:
        parts += ["6) 保持透明背景：物品以外的空白处保持透明，不要填底色、不要加投影。"]
    else:
        parts += ["6) 保持底图连续：物品以外的区域继续沿用参考图的底色与纹理，不要留白边。"]
    parts += ["", style["negative_block"].strip()]
    return "\n".join(parts)


def cmd_atlas(args):
    mf = {"batch": args.batch or "atlas", "project": args.project, "style": args.style, "work_root": args.work}
    item = {"id": args.id or os.path.splitext(os.path.basename(args.target))[0], "file": args.target,
            "prompt": args.prompt, "candidates": args.candidates, "pick": args.pick, "mode": "atlas",
            "bleed": args.bleed, "context": args.context, "alpha_from": args.alpha_from}
    if args.atlas_file:
        item["atlas_files"] = args.atlas_file
    r = atlas_generate(mf, item, args)
    log(json.dumps({k: v for k, v in r.items() if k not in ("generated",)}, ensure_ascii=False, indent=1)[:2000])
    for g in r.get("gates", []):
        log("门禁: %s" % g)
    if args.install:
        i = install_item(mf, item, args)
        log(json.dumps(i, ensure_ascii=False, indent=1))
        return 0 if (i.get("pass") or i.get("dry_run")) else 1
    return 0


# ----------------------------------------------------------------------------- commands
def cmd_single(args):
    mf = {"batch": args.batch or "single", "project": args.project, "style": args.style,
          "work_root": args.work}
    item = {"id": args.id or os.path.splitext(os.path.basename(args.target))[0],
            "file": args.target, "prompt": args.prompt, "candidates": args.candidates,
            "use_ref": args.use_ref, "tier": args.tier, "pick": args.pick}
    if args.fit:
        item["fit"] = args.fit
    r = gen_item(mf, item, args)
    log(json.dumps(r.get("generated", r), ensure_ascii=False))
    p = prepare_item(mf, item, args)
    log("对比图: %s" % (p.get("sheet") or "(无)"))
    if args.install:
        i = install_item(mf, item, args)
        log(json.dumps(i, ensure_ascii=False, indent=1))
        return 0 if (i.get("pass") or i.get("dry_run")) else 1
    return 0


def cmd_gen(args):
    mf = load_manifest(args.manifest)
    items = [i for i in mf["items"] if not args.only or i["id"] in args.only]
    rep = []
    for it in items:
        log("[gen] %s" % it["id"])
        if it.get("mode") == "atlas":
            rep.append(atlas_generate(mf, it, args))
        else:
            rep.append(gen_item(mf, it, args))
    write_report(mf, args, "gen", rep)
    return 0


def cmd_prepare(args):
    mf = load_manifest(args.manifest)
    items = [i for i in mf["items"] if not args.only or i["id"] in args.only]
    rep = []
    for it in items:
        log("[prepare] %s" % it["id"])
        rep.append(prepare_item(mf, it, args))
    write_report(mf, args, "prepare", rep)
    return 0


def cmd_install(args):
    mf = load_manifest(args.manifest)
    items = [i for i in mf["items"] if not args.only or i["id"] in args.only]
    if args.pick is not None:
        for i in items:
            i["pick"] = args.pick
    rep, fail = [], 0
    for it in items:
        log("[install] %s" % it["id"])
        r = install_item(mf, it, args)
        rep.append(r)
        if r.get("error") or r.get("pass") is False:
            fail += 1
    write_report(mf, args, "install", rep)
    if args.godot:
        project = project_of(mf)
        for it in items:
            t = resolve_target(mf, it)
            ok, msg = godot_reimport(project, t, wait=args.wait)
            log("  godot: %s (%s)" % (msg, "OK" if ok else "PENDING"))
    return 1 if fail else 0


def cmd_verify(args):
    st, notes = verify_target(args.target)
    log(json.dumps(st, ensure_ascii=False, indent=1))
    for n in notes:
        log("  - %s" % n)
    return 0


def cmd_godot(args):
    ok, msg = godot_reimport(args.project, args.target, wait=args.wait)
    log(msg)
    return 0 if ok else 1


def write_report(mf, args, stage, rep):
    root = mf.get("work_root") or os.path.join(project_of(mf), "_art_rebuild")
    d = os.path.join(root, mf.get("batch", "batch"))
    os.makedirs(d, exist_ok=True)
    ensure_gdignore(root)
    path = os.path.join(d, "state_%s.json" % stage)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"batch": mf.get("batch"), "stage": stage,
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "style": mf.get("style"), "items": rep}, f, ensure_ascii=False, indent=2)
    lines = ["# 批量重绘报告 %s / %s" % (mf.get("batch"), stage), ""]
    for r in rep:
        if not isinstance(r, dict):
            continue
        if r.get("error"):
            lines.append("- %s 失败：%s" % (r.get("id"), r["error"]))
            continue
        if stage == "install" and "before" in r:
            b, a = r["before"], r["after"]
            lines.append("- %s  %s B -> %s B | gates=%s | 备份 %s" % (
                r["id"], b["bytes"], a["bytes"], r.get("pass"), os.path.basename(r.get("backup", ""))))
        elif stage == "gen":
            lines.append("- %s  api=%s tier=%s -> %s" % (
                r["id"], r.get("api_size"), r.get("tier"), r.get("generated")))
        else:
            lines.append("- %s  候选 %d 个；对比图 %s" % (
                r["id"], len(r.get("candidates", [])), r.get("sheet")))
    with open(os.path.join(d, "report_%s.md" % stage), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log("报告: %s" % path)


def main():
    ap = argparse.ArgumentParser(description="美术资源重绘替换流水线（尺寸/命名/透明语义不变）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--style", default="mediterranean-casual-3d")
        p.add_argument("--tier", default=None, choices=[None, "standard", "advanced"])
        p.add_argument("--candidates", type=int, default=2)
        p.add_argument("--use-ref", default="original", choices=["original", "none"])
        p.add_argument("--retries", type=int, default=1)
        p.add_argument("--gpt-script", default=None)
        p.add_argument("--skip-existing", action="store_true")
        p.add_argument("--allow-upscale", action="store_true")

    p = sub.add_parser("single"); common(p)
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--target", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--id", default=None)
    p.add_argument("--work", default=None)
    p.add_argument("--batch", default="single")
    p.add_argument("--fit", default=None, choices=[None, "bbox", "full"])
    p.add_argument("--pick", type=int, default=1)
    p.add_argument("--install", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_single)

    for name, fn in (("gen", cmd_gen), ("prepare", cmd_prepare), ("install", cmd_install)):
        p = sub.add_parser(name); common(p)
        p.add_argument("--manifest", required=True)
        p.add_argument("--only", nargs="*", default=None)
        p.add_argument("--dry-run", action="store_true")
        if name == "install":
            p.add_argument("--pick", type=int, default=None)
            p.add_argument("--godot", action="store_true")
            p.add_argument("--wait", type=int, default=90)
        p.set_defaults(func=fn)

    p = sub.add_parser("atlas"); common(p)
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--target", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--id", default=None)
    p.add_argument("--work", default=None)
    p.add_argument("--batch", default="atlas")
    p.add_argument("--rect", action="append", default=None, help="x,y,w,h 可重复")
    p.add_argument("--at", default=None, help="点选：取包含该点的真实切片，如 512,300")
    p.add_argument("--auto-index", type=int, default=None, help="按面积排序取第 N 个自动切片")
    p.add_argument("--auto-top", type=int, default=None, help="取面积最大的 N 个自动切片")
    p.add_argument("--auto-regions", action="store_true", help="列出/使用像素级自动切片")
    p.add_argument("--allow-untrusted-atlas", action="store_true", help="跳过 .atlas 元数据体检（不推荐）")
    p.add_argument("--region", action="append", default=None, help="按 region 名过滤（配 --atlas-file）")
    p.add_argument("--atlas-file", action="append", default=None, help=".atlas 或 regions.json")
    p.add_argument("--bleed", type=int, default=16)
    p.add_argument("--context", type=int, default=96)
    p.add_argument("--alpha-from", default="original", choices=["original", "ai"])
    p.add_argument("--pick", type=int, default=1)
    p.add_argument("--install", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_atlas)

    p = sub.add_parser("verify"); p.add_argument("--target", required=True); p.set_defaults(func=cmd_verify)
    p = sub.add_parser("godot")
    p.add_argument("--project", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--wait", type=int, default=90)
    p.set_defaults(func=cmd_godot)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
