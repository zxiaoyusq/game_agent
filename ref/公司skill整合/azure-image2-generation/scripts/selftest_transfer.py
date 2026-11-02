#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_transfer.py — transfer.py 离线自测（不调 API，零额度）

模拟素材：256x256 卡通狗（棕毛 + 红项圈 + 右上浮动爪子图标，带 alpha）。
模拟模型输出的三种典型情况：
  cand_good    全结构都在，仅换毛色（棕→灰白）+ 轻微平移/缩放/形变（模型固有漂移）
  cand_nopaw   丢了浮动爪子图标 —— 但 preserve_rect 硬保护区域用原图像素回贴救回 → 应 PASS
  cand_bad     丢了尾巴（保护区域之外的真结构丢失）→ missing_coverage 门禁必须 FAIL
另验证三层约束 prompt 的关键句。

运行：python selftest_transfer.py   （在 scripts/ 目录或任意目录均可）
"""
import json, os, sys, tempfile, traceback
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rebuild as rb
import transfer as tf

SRC_SIZE = (256, 256)
FAILURES = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("  [%s] %s%s" % (tag, name, ("  <- " + str(detail)) if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(name)
    return cond


# ----------------------------------------------------------------------------- 素材绘制
BROWN, DARKBROWN, LIGHT = (168, 124, 86), (140, 96, 60), (214, 186, 150)
GRAY, DARKGRAY, WHITE = (135, 135, 140), (110, 110, 116), (240, 240, 240)
RED, ICONC, EYEC = (200, 44, 44), (222, 178, 120), (40, 32, 28)

# src 坐标系下的形状: (rect, color)
BODY = ((56, 120, 200, 214), BROWN)
HEAD = ((76, 36, 196, 140), BROWN)
EAR_L = ((70, 30, 100, 72), DARKBROWN)
EAR_R = ((172, 30, 202, 72), DARKBROWN)
MUZZLE = ((108, 96, 164, 134), LIGHT)
EYE_L = ((104, 70, 116, 82), EYEC)
EYE_R = ((148, 70, 160, 82), EYEC)
TAIL = ((196, 148, 246, 198), DARKBROWN)
COLLAR = ((92, 128, 168, 146), RED)
PAW = ((216, 16, 248, 48), ICONC)

PRESERVE_RECTS = [
    {"rect": [88, 124, 84, 26], "key": list(RED), "tol": 90},  # 项圈：色键限定（项圈叠在身体上，
                                                              # 整块回贴会把旧棕底贴回来形成接缝）
    {"rect": [206, 6, 50, 50]},                                # 浮动图标：透明背景上整块回贴
]


def preserve_restored(fa, sa, r):
    """按色键语义检查保护区像素级复原。"""
    x, y, w, h = r["rect"]
    sreg, freg = sa[y:y + h, x:x + w], fa[y:y + h, x:x + w]
    m = tf.preserve_mask(sreg, r)
    if m is None:
        return bool(np.array_equal(sreg, freg))
    return bool((not m.any()) or np.array_equal(sreg[m], freg[m]))


def draw_shapes(draw, shapes, tx=0, ty=0, sx=1.0, sy=1.0, inflate=1.0):
    for rect, color in shapes:
        x0, y0, x1, y1 = rect
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        w, h = (x1 - x0) * sx * inflate, (y1 - y0) * sy * inflate
        box = [cx - w / 2 + tx, cy - h / 2 + ty, cx + w / 2 + tx, cy + h / 2 + ty]
        draw.ellipse(box, fill=color + (255,))


def make_source(path):
    im = Image.new("RGBA", SRC_SIZE, (0, 0, 0, 0))
    d = None
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    draw_shapes(d, [TAIL, BODY, HEAD, EAR_L, EAR_R, MUZZLE, EYE_L, EYE_R, COLLAR, PAW])
    im.save(path)
    return im


def make_reference(path):
    """外观参考（真实流程喂给模型；自测只验证文件与 prompt 组装）：灰白毛色分布示意。"""
    from PIL import ImageDraw
    im = Image.new("RGBA", SRC_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((30, 40, 226, 220), fill=GRAY + (255,))
    d.ellipse((90, 110, 170, 190), fill=WHITE + (255,))   # 白胸
    d.ellipse((100, 90, 160, 130), fill=WHITE + (255,))   # 白口鼻
    d.ellipse((96, 56, 126, 74), fill=WHITE + (255,))     # 白眉
    d.ellipse((146, 56, 176, 74), fill=WHITE + (255,))
    im.save(path)
    return im


def make_candidate(path, coat, include_tail=True, include_paw=True):
    """模拟模型输出：换毛色 + 位置/缩放漂移（sx=1.10, sy=1.13, 形状膨胀 1.06），画在 320 画布上。"""
    from PIL import ImageDraw
    im = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shapes = [
        (BODY[0], coat["body"]), (HEAD[0], coat["body"]),
        (EAR_L[0], coat["ear"]), (EAR_R[0], coat["ear"]),
        (MUZZLE[0], coat["muzzle"]), (EYE_L[0], EYEC), (EYE_R[0], EYEC),
        ((104, 52, 128, 66), coat["mark"]), ((146, 52, 170, 66), coat["mark"]),  # 白眉
        ((100, 150, 160, 202), coat["mark"]),                                    # 白胸
        (COLLAR[0], RED),
    ]
    if include_tail:
        shapes += [
            ((TAIL[0][0], TAIL[0][1], TAIL[0][2] - 20, TAIL[0][3]), coat["ear"]),  # 尾根
            ((TAIL[0][2] - 24, TAIL[0][1], TAIL[0][2], TAIL[0][3] - 16), WHITE),   # 白尾尖
        ]
    if include_paw:
        shapes.append(PAW)
    draw_shapes(d, shapes, tx=20, ty=20, sx=1.10, sy=1.13, inflate=1.06)
    im.save(path)
    return im


# ----------------------------------------------------------------------------- 用例
def run_all():
    print("== selftest_transfer ==")
    tmp = tempfile.mkdtemp(prefix="transfer_selftest_")
    src_p = os.path.join(tmp, "dog.png")
    ref_p = os.path.join(tmp, "coat_ref.png")
    make_source(src_p)
    make_reference(ref_p)

    src_stats = rb.png_stats(src_p)
    src_img = Image.open(src_p).convert("RGBA")

    # ---- 1) 三层约束 prompt
    print("-- prompt 组装")
    cfg = {
        "reference": "coat_ref.png",   # 有图2 -> 双参考图分支
        "appearance": ["cool medium-gray and white coat with soft furry texture",
                       "white fluffy eyebrow patches above both eyes",
                       "white muzzle and chest patch; white paws and tail tip"],
        "preserve_objects": ["small floating paw icon on the right", "simple brown collar"],
        "forbid_from_reference": ["bell"],
    }
    prompt = tf.build_prompt(cfg)
    check("LAYER 1 结构继承句", "[LAYER 1 - STRUCTURE INHERITANCE" in prompt)
    check("Image 1 是直接编辑对象", "Image 1 is the direct edit target" in prompt)
    check("LAYER 2 禁止新增配饰", "Do not add any new accessory" in prompt)
    check("LAYER 3 图2仅外观参考", "Image 2 is the appearance reference ONLY" in prompt)
    check("外观映射到原图形状", "onto the EXACT original shapes of Image 1" in prompt)
    check("preserve 对象句", "floating paw icon" in prompt and "brown collar" in prompt)
    check("forbid 铃铛句", "bell" in prompt)
    check("透明背景要求", "fully transparent" in prompt)
    check("外观描述注入", "cool medium-gray and white coat" in prompt)

    # ---- 1b) 无参考图分支：纯文字描述外观，不许出现 Image 2
    print("-- prompt 组装（无参考图）")
    cfg_nr = {"appearance": ["weathered dark iron material with a matte finish and subtle scratches"]}
    prompt_nr = tf.build_prompt(cfg_nr)
    check("无参考图 prompt 不出现 Image 2", "Image 2" not in prompt_nr)
    check("无参考图 prompt 仍锁结构", "EXACT original shapes of Image 1" in prompt_nr)
    check("无参考图外观注入", "weathered dark iron" in prompt_nr)
    check("无参考图 prompt 无 forbid 句", "do NOT bring any of" not in prompt_nr)

    # ---- 2) 正常候选：换毛色 + 漂移 -> 全门禁 PASS
    print("-- cand_good（换毛色+漂移）")
    good_p = os.path.join(tmp, "cand_good.png")
    make_candidate(good_p, {"body": GRAY, "ear": DARKGRAY, "muzzle": WHITE, "mark": WHITE})
    final, info = tf.register_and_composite(good_p, src_img, src_stats, PRESERVE_RECTS, bleed_px=12)
    checks, metrics, passed = tf.qa_transfer(src_img, final, PRESERVE_RECTS, {}, missing_coverage=info["missing_coverage"], shape_deviation=info["body_shape_deviation"])
    check("总体 PASS", passed, json.dumps({"checks": checks, "metrics": metrics}))
    check("尺寸不变", checks["size_same"])
    check("alpha 逐字节一致", checks["alpha_identical"])
    check("preserve 区域逐字节一致", checks["preserve_identical"])
    check("透明区干净", checks["clean_transparent"])
    check("毛色确实迁移了", checks["transfer_applied"], "changed_pct=%s" % metrics["changed_pct"])
    check("无结构丢失(missing<=5%)", checks["no_missing_structure"],
          "missing=%.3f" % info["missing_coverage"])
    check("无纯黑死斑", checks["no_black_blobs"], "black_pct=%s" % metrics["black_visible_pct"])
    check("主体形变度<=8%", checks["shape_deviation_ok"], "dev=%s" % metrics["body_shape_deviation"])

    # 项圈/图标区域像素级等于原图（硬保护证据）
    fa = np.array(final)
    sa = np.array(src_img)
    check("preserve 回贴像素级复原", all(preserve_restored(fa, sa, r) for r in PRESERVE_RECTS))
    # 色键接缝检查：项圈矩形内非红色的身体像素必须保留生成色（灰），不能被旧棕底覆盖
    px = fa[147, 95]   # (x=95, y=147)：项圈下缘、矩形内的身体像素
    sx = sa[147, 95]
    seam = abs(int(px[0]) - int(sx[0])) + abs(int(px[1]) - int(sx[1])) + abs(int(px[2]) - int(sx[2]))
    check("色键不贴回旧底色(项圈周围仍是新毛色)", seam > 90,
          "src=%s out=%s dist=%d" % (sx[:3].tolist(), px[:3].tolist(), seam))

    # ---- 3) 丢图标候选：preserve 硬保护救回 -> 仍应 PASS
    print("-- cand_nopaw（模型丢了浮动图标，preserve 回贴救回）")
    nopaw_p = os.path.join(tmp, "cand_nopaw.png")
    make_candidate(nopaw_p, {"body": GRAY, "ear": DARKGRAY, "muzzle": WHITE, "mark": WHITE},
                   include_paw=False)
    final2, info2 = tf.register_and_composite(nopaw_p, src_img, src_stats, PRESERVE_RECTS, bleed_px=12)
    checks2, metrics2, passed2 = tf.qa_transfer(src_img, final2, PRESERVE_RECTS, {}, missing_coverage=info2["missing_coverage"], shape_deviation=info2["body_shape_deviation"])
    check("preserve 保护下仍 PASS", passed2, json.dumps({"checks": checks2, "metrics": metrics2}))
    fa2 = np.array(final2)
    check("图标区域被原图像素复原", preserve_restored(fa2, sa, PRESERVE_RECTS[1]))

    # ---- 4) 丢尾巴候选（保护区域之外的真结构丢失）-> 门禁必须 FAIL
    print("-- cand_bad（丢尾巴，保护区域之外）")
    bad_p = os.path.join(tmp, "cand_bad.png")
    make_candidate(bad_p, {"body": GRAY, "ear": DARKGRAY, "muzzle": WHITE, "mark": WHITE},
                   include_tail=False, include_paw=True)
    final3, info3 = tf.register_and_composite(bad_p, src_img, src_stats, PRESERVE_RECTS, bleed_px=12)
    checks3, metrics3, passed3 = tf.qa_transfer(src_img, final3, PRESERVE_RECTS, {}, missing_coverage=info3["missing_coverage"], shape_deviation=info3["body_shape_deviation"])
    check("丢尾巴被拦截 FAIL", not passed3, json.dumps(checks3))
    check("FAIL 原因是结构丢失", not checks3["no_missing_structure"],
          "missing=%.3f" % info3["missing_coverage"])
    check("丢尾巴被形变门禁拦截(dev>8%)", not checks3["shape_deviation_ok"],
          "dev=%s" % metrics3.get("body_shape_deviation"))

    # ---- 5) alpha 回写的像素级证明：final alpha 与原图逐字节一致（三种候选都要）
    for name, f in (("good", final), ("nopaw", final2), ("bad", final3)):
        check("alpha 回写逐字节(%s)" % name,
              np.array_equal(np.array(f)[:, :, 3], sa[:, :, 3]))

    # ---- 6) 报告可序列化
    print("-- 报告序列化")
    try:
        json.dumps({"info": info, "checks": checks, "metrics": metrics,
                    "src_stats": src_stats}, ensure_ascii=False)
        check("QA 结果可 JSON 序列化", True)
    except Exception as e:
        check("QA 结果可 JSON 序列化", False, e)

    print()
    if FAILURES:
        print("自测失败 %d 项: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("自测全部通过 ✔")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run_all())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
