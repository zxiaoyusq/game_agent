# -*- coding: utf-8 -*-
"""atlas 模式离线自测（v2）：元数据 fail-closed + 像素级切片 + 漂移仿真下的图集不失效证明。"""
import argparse, json, os, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw

SKILL = r"E:\Gameprogram\skill-pool\skills\gpt-image-gen"
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import rebuild as R

PROJ = r"E:\Gameprogram\jigsawcard-godot"
SPINE = os.path.join(PROJ, "assets", "spine")
checks = []
tmp = tempfile.mkdtemp(prefix="arr_atlas2_")

# ---------- A. 元数据体检（fail-closed 依据）----------
atlas_files = []
for root, _, files in os.walk(SPINE):
    for f in sorted(files):
        if f.endswith(".atlas"):
            atlas_files.append(os.path.join(root, f))

bad_meta, good_meta, total_regs, oob_total = [], [], 0, 0
for ap in atlas_files:
    regs = R.parse_spine_atlas(ap)
    if not regs:
        continue
    png = os.path.join(os.path.dirname(ap), regs[0].get("page") or "")
    if not os.path.exists(png):
        continue
    ok, reasons = R.validate_metadata_regions(ap, png, regs)
    total_regs += len(regs)
    if ok:
        good_meta.append((ap, png, regs))
    else:
        bad_meta.append((ap, png, regs, reasons))
print("图集元数据体检：可信 %d | 不可信 %d | region 总数 %d" % (len(good_meta), len(bad_meta), total_regs))
checks.append(("存在不可信元数据的图集(证明必须 fail-closed)", len(bad_meta) > 0))
checks.append(("存在可信元数据的图集", len(good_meta) > 0))

if bad_meta:
    ap, png, regs, reasons = bad_meta[0]
    print("  例:", os.path.basename(ap), "->", reasons[0][:80])

# 显式验证：不可信元数据必须被拒绝
ap_bad, png_bad, regs_bad, _ = bad_meta[0]
ns = argparse.Namespace(rect=None, at=None, auto_index=None, auto_top=None, auto_regions=False,
                        atlas_file=[ap_bad], region=None, allow_untrusted_atlas=False)
try:
    R.resolve_regions({}, ns, png_bad)
    refused = False
except SystemExit as e:
    refused = True
    print("  拒绝信息:", str(e).split(chr(10))[0][:110])
checks.append(("不可信 .atlas 被拒绝使用(fail-closed)", refused))

# 可信元数据放行
if good_meta:
    ap_ok, png_ok, regs_ok = good_meta[0]
    ns_ok = argparse.Namespace(rect=None, at=None, auto_index=None, auto_top=None, auto_regions=False,
                               atlas_file=[ap_ok], region=None, allow_untrusted_atlas=False)
    got = R.resolve_regions({}, ns_ok, png_ok)
    checks.append(("可信 .atlas 正常放行", len(got) == len(regs_ok)))

# ---------- B. 像素级切片 ----------
def find_sliceable():
    """找一页真正按透明切片排布的图集页：>=2 个连通域，且有一个尺寸适中、窗口放得下的目标。"""
    seen = set()
    for ap in atlas_files:
        regs0 = R.parse_spine_atlas(ap)
        if not regs0:
            continue
        png = os.path.join(os.path.dirname(ap), regs0[0].get("page") or "")
        if not os.path.exists(png) or png in seen:
            continue
        seen.add(png)
        W, H = Image.open(png).size
        if W * H > 4_200_000:
            continue
        comps = R.alpha_regions(png)
        if len(comps) < 2:
            continue
        for c in comps:
            need_w, need_h = c["w"] + 2 * (16 + 96), c["h"] + 2 * (16 + 96)
            if 32 <= c["w"] <= 600 and 32 <= c["h"] <= 600 and need_w <= W and need_h <= H:
                return ap, png, comps, c
    return None

found = find_sliceable()
if not found:
    print("[SKIP] 没找到可直接像素切片的图集，改用合成图集")
    png = os.path.join(tmp, "synth_atlas.png")
    im = Image.new("RGBA", (768, 768), (0, 0, 0, 0))
    s = Image.open(os.path.join(PROJ, "_tmp_icon_rebuild", "book_edit_v2.png")).convert("RGBA").resize((128, 128), Image.LANCZOS)
    pos = [(48, 48), (420, 60), (80, 430), (430, 430)]
    for x, y in pos:
        im.alpha_composite(s, (x, y))
    im.save(png)
    comps = R.alpha_regions(png)
    target = sorted(comps, key=lambda c: (c["y"], c["x"]))[0]
else:
    ap, png, comps, target = found
    print("像素级切片目标页: %s（%d 块）" % (os.path.relpath(png, PROJ), len(comps)))

W, H = Image.open(png).size
print("像素级切片 %s: %d 块（最大 %dx%d）" % (os.path.basename(png), len(comps),
                                        comps[0]["w"] if comps else 0, comps[0]["h"] if comps else 0))
checks.append(("像素级自动切片可用", len(comps) > 0))
checks.append(("自动切片全部在画布内",
               all(0 <= c["x"] and 0 <= c["y"] and c["x"] + c["w"] <= W and c["y"] + c["h"] <= H for c in comps)))

cx, cy = target["x"] + target["w"] // 2, target["y"] + target["h"] // 2
picked = R.pick_region_by_point(comps, cx, cy)
checks.append(("点选能命中包含该点的切片", picked is not None and picked["x"] == target["x"] and picked["y"] == target["y"]))

rects = [dict(target, name="auto_target")]
api = R.pick_api_size(W, H, allow_upscale=True) or (1024, 1024)
win = R.build_window((W, H), rects, 16, 96, api)
if not R.window_covers(win, rects, 16, (W, H)):
    win = [0, 0, W, H]
checks.append(("窗口完整覆盖 region+bleed", R.window_covers(win, rects, 16, (W, H))))
checks.append(("窗口不是退化的整页（说明目标选得合理）", win[2] * win[3] < W * H))
print("目标切片:", target, "| 窗口:", win, "| API:", api)

mask = R.make_mask(win, rects, 16)
ma = np.array(mask)
checks.append(("mask 透明=重绘区", int(ma[:, :, 3].min()) == 0 and int(ma[:, :, 3].max()) == 255))
redraw = int((ma[:, :, 3] == 0).sum())
checks.append(("mask 透明面积 ≈ region+bleed",
               0.4 < redraw / float((target["w"] + 32) * (target["h"] + 32)) < 2.5))

# ---------- C. 漂移仿真：模型把东西画歪了，图集依然不失效 ----------
win_orig = Image.open(png).convert("RGBA").crop(tuple(win))
fake = Image.new("RGBA", (win[2], win[3]), (0, 0, 0, 0))
fake.alpha_composite(win_orig, (23, -17))           # 模拟位置漂移
d = ImageDraw.Draw(fake)
d.ellipse([10, 10, 80, 80], fill=(200, 60, 40, 255))  # 模拟"重绘"了内容
p_fake = os.path.join(tmp, "fake_ai.png")
fake.resize(api, Image.LANCZOS).save(p_fake)          # 模拟 API 输出画幅

orig = Image.open(png).convert("RGBA")
out = R.harvest(orig, p_fake, win, rects, 16, "original")
p_out = os.path.join(tmp, "cand1_fit.png")
out.save(p_out)

gates, ok = R.atlas_gates(png, p_out, rects, 16, True)
print("门禁:", json.dumps(gates, ensure_ascii=False))
checks.append(("门禁全绿（模型画歪也不失效）", ok))
for k, v in gates.items():
    checks.append(("gate:" + k, v))

a = np.array(orig); b = np.array(Image.open(p_out).convert("RGBA"))
keep = np.zeros(a.shape[:2], bool)
r0 = rects[0]
keep[max(0, r0["y"] - 16):min(H, r0["y"] + r0["h"] + 16),
     max(0, r0["x"] - 16):min(W, r0["x"] + r0["w"] + 16)] = True
checks.append(("区域外逐字节一致", bool((a[~keep] == b[~keep]).all())))
checks.append(("区域内 alpha 与原图逐字节一致", bool((a[keep][:, 3] == b[keep][:, 3]).all())))
checks.append(("区域内 RGB 确实被重绘", bool((a[keep][:, :3] != b[keep][:, :3]).any())))
checks.append(("图集总尺寸不变", a.shape == b.shape))
checks.append(("全图 alpha 100% 重合（轮廓/位置由我们保证）", bool((a[:, :, 3] == b[:, :, 3]).all())))
checks.append(("alpha 质量守恒", int(a[:, :, 3].sum()) == int(b[:, :, 3].sum())))

legacy = np.array(Image.open(p_fake).convert("RGBA").resize((W, H), Image.LANCZOS))
diff = int((a[~keep] != legacy[~keep]).sum())
print("反证：旧流程(整图替换) 会改坏区域外 %d 个像素" % diff)
checks.append(("旧流程确实破坏图集（反证成立）", diff > 0))

print("=" * 74)
bad = 0
for name, okk in checks:
    print(("[PASS] " if okk else "[FAIL] ") + str(name))
    bad += 0 if okk else 1
print("=" * 74)
print("ATLAS SELFTEST v2", "ALL PASS (%d)" % len(checks) if bad == 0 else "%d FAILED" % bad)
print("产物:", tmp)
sys.exit(1 if bad else 0)
