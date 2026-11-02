# -*- coding: utf-8 -*-
"""离线自测：不调 API，用已有 1024 母版当候选，跑通 prepare / install / verify / single 链路。"""
import json, os, shutil, subprocess, sys, tempfile

SKILL = r"E:\Gameprogram\skill-pool\skills\gpt-image-gen"
RB = os.path.join(SKILL, "scripts", "rebuild.py")
MASTER = r"E:\Gameprogram\jigsawcard-godot\_tmp_icon_rebuild\book_edit_v2.png"
BROKEN = r"E:\Gameprogram\jigsawcard-godot\_tmp_icon_rebuild\ORIGINAL_broken_backup.png"
PY = sys.executable

def run(args, label):
    r = subprocess.run([PY, RB] + args, capture_output=True)
    out = (r.stdout or b"").decode("utf-8", "replace")
    err = (r.stderr or b"").decode("utf-8", "replace")
    print("=" * 70)
    print("### %s  exit=%s" % (label, r.returncode))
    print(out[-1500:])
    if err.strip():
        print("[stderr]", err[-800:])
    return r.returncode, out

root = tempfile.mkdtemp(prefix="arr_selftest_")
proj = os.path.join(root, "proj")
os.makedirs(proj)
target = os.path.join(proj, "icon.png")
shutil.copy(BROKEN, target)
print("自测根目录:", root)

# ---- 批量链路 ----
manifest = {
    "batch": "selftest", "project": proj, "style": "mediterranean-casual-3d",
    "work_root": os.path.join(root, "_art_rebuild"),
    "items": [{"id": "icon", "file": "icon.png",
               "prompt": "一本画着橄榄枝的古典书图标", "use_ref": "none",
               "candidates": 1, "pick": 1, "fit": "bbox"}],
}
mfp = os.path.join(root, "batch.json")
open(mfp, "w", encoding="utf-8").write(json.dumps(manifest, ensure_ascii=False, indent=2))

wd = os.path.join(root, "_art_rebuild", "selftest", "icon")
os.makedirs(wd, exist_ok=True)
shutil.copy(MASTER, os.path.join(wd, "cand1.png"))

run(["prepare", "--manifest", mfp], "prepare(batch)")
run(["install", "--manifest", mfp, "--dry-run"], "install(dry-run)")
code, _ = run(["install", "--manifest", mfp], "install(batch)")
run(["verify", "--target", target], "verify(target)")

# ---- single 链路（--skip-existing 复用同一份候选，不调 API）----
proj2 = os.path.join(root, "proj2")
os.makedirs(proj2)
target2 = os.path.join(proj2, "icon.png")
shutil.copy(BROKEN, target2)
work2 = os.path.join(root, "_single")
wd2 = os.path.join(work2, "single", "icon")
os.makedirs(wd2, exist_ok=True)
shutil.copy(MASTER, os.path.join(wd2, "cand1.png"))
code2, out2 = run(["single", "--project", proj2, "--target", target2, "--prompt", "橄榄枝古典书",
                   "--id", "icon", "--work", work2, "--batch", "single",
                   "--skip-existing", "--pick", "1", "--install"], "single --install")

# ---- 断言 ----
from PIL import Image
import numpy as np
checks = []
a = np.array(Image.open(target).convert("RGBA"))
b = np.array(Image.open(target2).convert("RGBA"))
bb = np.array(Image.open(BROKEN).convert("RGBA"))
checks.append(("batch 尺寸不变 96x96", Image.open(target).size == (96, 96)))
checks.append(("single 尺寸不变 96x96", Image.open(target2).size == (96, 96)))
checks.append(("batch 四角透明", max(a[0, 0, 3], a[0, -1, 3], a[-1, 0, 3], a[-1, -1, 3]) <= 16))
checks.append(("single 四角透明", max(b[0, 0, 3], b[0, -1, 3], b[-1, 0, 3], b[-1, -1, 3]) <= 16))
checks.append(("内容确实换掉(batch)", int(a.sum()) != int(bb.sum())))
checks.append(("内容确实换掉(single)", int(b.sum()) != int(bb.sum())))
checks.append(("batch 文件更小", os.path.getsize(target) < os.path.getsize(BROKEN)))
checks.append(("备份已生成", os.path.exists(os.path.join(wd, "ORIGINAL_icon.png"))))
checks.append(("对比图已生成", os.path.exists(os.path.join(wd, "compare.png"))))
checks.append(("报告已生成", os.path.exists(os.path.join(root, "_art_rebuild", "selftest", "report_install.md"))))
checks.append((".gdignore 已写", os.path.exists(os.path.join(root, "_art_rebuild", ".gdignore"))))
checks.append(("安装门禁全绿", json.load(open(os.path.join(root, "_art_rebuild", "selftest", "state_install.json"),
                                            encoding="utf-8"))["items"][0]["pass"] is True))
checks.append(("single 返回码 0", code2 == 0))

print("=" * 70)
bad = 0
for name, ok in checks:
    print(("[PASS] " if ok else "[FAIL] ") + name)
    bad += 0 if ok else 1
print("=" * 70)
print("SELFTEST", "ALL PASS" if bad == 0 else ("%d FAILED" % bad))
print("产物目录:", root)
sys.exit(1 if bad else 0)
