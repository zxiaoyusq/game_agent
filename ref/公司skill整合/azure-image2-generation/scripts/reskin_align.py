#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reskin_align.py - GPT 生图换皮模块专用：Mask 对齐、质心回正、边缘出血与三道硬 QA 门禁
SOP 沉淀于 2026-09-14，解决异形黑缝、脏光晕、轴心脱臼、主体截断四大深水坑。
"""

import argparse
import os
import sys
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def calculate_centroid_and_bbox(alpha_channel, threshold=10):
    """计算 Alpha 通道的加权质心 (cx, cy) 与有效 Bbox [x_min, y_min, x_max, y_max]。"""
    arr = np.array(alpha_channel, dtype=np.float32)
    mask = arr > threshold
    total_mass = np.sum(arr[mask])
    
    if total_mass == 0:
        w, h = alpha_channel.size
        return (w / 2.0, h / 2.0), (0, 0, w, h), 0

    y_coords, x_coords = np.nonzero(mask)
    x_min, x_max = int(np.min(x_coords)), int(np.max(x_coords))
    y_min, y_max = int(np.min(y_coords)), int(np.max(y_coords))

    cx = float(np.sum(x_coords * arr[mask]) / total_mass)
    cy = float(np.sum(y_coords * arr[mask]) / total_mass)

    return (cx, cy), (x_min, y_min, x_max, y_max), int(np.sum(mask))


def bleed_edges(rgb_img, alpha_mask, bleed_px=15):
    """边缘色彩漫延防御（防止贴回 Alpha 时采样到底层杂色形成刺眼白光晕或黑脏边）。"""
    rgb_arr = np.array(rgb_img.convert("RGB"))
    alpha_arr = np.array(alpha_mask)
    solid_mask = (alpha_arr > 128).astype(np.uint8)

    if HAS_CV2:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (bleed_px * 2 + 1, bleed_px * 2 + 1))
        dilated = cv2.dilate(solid_mask, kernel, iterations=1)
        inpaint_mask = ((dilated > 0) & (solid_mask == 0)).astype(np.uint8) * 255
        
        if np.any(inpaint_mask):
            inpainted = cv2.inpaint(rgb_arr, inpaint_mask, inpaintRadius=bleed_px, flags=cv2.INPAINT_TELEA)
            return Image.fromarray(inpainted, "RGB")
        return rgb_img
    else:
        return rgb_img


def align_and_clamp(src_path, ai_path, out_path, bleed_px=15, align_mode="auto"):
    """
    核心 SOP 流水线：
    1. 尺寸校正 (保持原图尺寸 WxH)
    2. 质心与 Bbox 几何注册 (亚像素对齐 + 等比保形缩放)
    3. 边缘色彩漫延 (Bleed Inpainting)
    4. 逐字节回贴原图 Alpha 通道
    5. 三道硬 QA 门禁自检
    """
    src = Image.open(src_path).convert("RGBA")
    ai = Image.open(ai_path).convert("RGBA")
    w_src, h_src = src.size

    src_alpha = src.split()[-1]
    ai_alpha = ai.split()[-1]

    src_c, src_bbox, src_opaque_px = calculate_centroid_and_bbox(src_alpha)
    ai_c, ai_bbox, ai_opaque_px = calculate_centroid_and_bbox(ai_alpha)

    if align_mode in ["auto", "centroid", "bbox"] and ai_opaque_px > 0 and src_opaque_px > 0:
        src_bw = max(1, src_bbox[2] - src_bbox[0])
        src_bh = max(1, src_bbox[3] - src_bbox[1])
        ai_bw = max(1, ai_bbox[2] - ai_bbox[0])
        ai_bh = max(1, ai_bbox[3] - ai_bbox[1])

        scale = min(src_bw / float(ai_bw), src_bh / float(ai_bh)) * 0.96
        scale = max(0.2, min(scale, 3.0))

        new_ai_w = max(1, int(ai.width * scale))
        new_ai_h = max(1, int(ai.height * scale))
        ai_resized = ai.resize((new_ai_w, new_ai_h), Image.Resampling.LANCZOS)
        ai_resized_alpha = ai_resized.split()[-1]

        new_ai_c, _, _ = calculate_centroid_and_bbox(ai_resized_alpha)

        dx = int(round(src_c[0] - new_ai_c[0]))
        dy = int(round(src_c[1] - new_ai_c[1]))

        aligned_ai = Image.new("RGBA", (w_src, h_src), (0, 0, 0, 0))
        aligned_ai.paste(ai_resized, (dx, dy), ai_resized)
    else:
        aligned_ai = ai.resize((w_src, h_src), Image.Resampling.LANCZOS)

    rgb_bled = bleed_edges(aligned_ai, aligned_ai.split()[-1], bleed_px=bleed_px)

    final_img = rgb_bled.convert("RGBA")
    final_img.putalpha(src_alpha)

    qa_passed, qa_report = run_qa_gates(src, final_img, aligned_ai)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    final_img.save(out_path, format="PNG")

    print(f"[RESKIN] 输出成功: {out_path} ({w_src}x{h_src})")
    print(qa_report)

    if not qa_passed:
        print("[QA ALERT] 警告: 未能全部通过真实 QA 门禁，请根据报告检查！", file=sys.stderr)
        return False
    return True


def run_qa_gates(src_img, final_img, aligned_ai):
    """
    三道真实硬防线：
    1. 黑斑死斑检测 (black_fill_px == 0)
    2. 内部未覆盖率 (missing_coverage <= 5%)
    3. 轮廓交并比 (IoU >= 0.82)
    """
    src_a = np.array(src_img.split()[-1])
    final_arr = np.array(final_img)
    ai_a = np.array(aligned_ai.split()[-1])

    dim_match = (src_img.size == final_img.size)
    alpha_match = np.array_equal(src_a, final_arr[:, :, 3])

    solid_mask = src_a > 128
    r = final_arr[:, :, 0][solid_mask]
    g = final_arr[:, :, 1][solid_mask]
    b = final_arr[:, :, 2][solid_mask]
    black_pixels = int(np.sum((r < 5) & (g < 5) & (b < 5)))

    ai_mask = ai_a > 64
    intersection = np.logical_and(solid_mask, ai_mask)
    union = np.logical_or(solid_mask, ai_mask)
    
    union_sum = np.sum(union)
    iou = float(np.sum(intersection) / union_sum) if union_sum > 0 else 1.0
    
    solid_sum = np.sum(solid_mask)
    missing_coverage = float(np.sum(solid_mask & (~ai_mask)) / solid_sum) if solid_sum > 0 else 0.0

    passed = (
        dim_match and
        alpha_match and
        black_pixels == 0 and
        missing_coverage <= 0.05 and
        iou >= 0.82
    )

    report = (
        f"--- QA GATES REPORT ---\n"
        f"  1. 尺寸匹配 (Dimensions)       : {'PASS' if dim_match else 'FAIL'} ({src_img.size})\n"
        f"  2. Alpha 通道逐字节一致         : {'PASS' if alpha_match else 'FAIL'}\n"
        f"  3. 纯黑死斑像素数 (Black Pixels): {black_pixels} (目标: 0)\n"
        f"  4. 内部未覆盖率 (Missing Cov)   : {missing_coverage * 100:.2f}% (门禁: <= 5.0%)\n"
        f"  5. 轮廓交并比 (IoU)             : {iou:.3f} (门禁: >= 0.820)\n"
        f"  总体判定                       : {'[PASS 全绿]' if passed else '[FAIL 拦截]'}"
    )

    return passed, report


def main():
    parser = argparse.ArgumentParser(description="GPT 生图换皮专用：Mask 注册、质心对齐与 QA 门禁")
    parser.add_argument("--src", "-s", required=True, help="原始资源路径 (用于提取 Alpha 和几何约束)")
    parser.add_argument("--ai", "-a", required=True, help="AI 生成的素材路径")
    parser.add_argument("--out", "-o", required=True, help="最终导出的换皮 PNG 路径")
    parser.add_argument("--bleed", type=int, default=15, help="边缘色彩漫延出血像素半径 (默认 15)")
    parser.add_argument("--mode", choices=["auto", "centroid", "clamp", "bbox"], default="auto",
                        help="对齐模式 (auto: 自动质心+保形缩放, clamp: 仅回贴 Alpha)")
    args = parser.parse_args()

    success = align_and_clamp(args.src, args.ai, args.out, bleed_px=args.bleed, align_mode=args.mode)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
