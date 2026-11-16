#!/usr/bin/env python3
"""Versioned HTML intake/review for reskin projects. Standard library only."""
import argparse
import base64
import copy
import hashlib
import json
import mimetypes
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

PHASES = ["intake", "direction", "concept", "plan", "representative",
          "production", "integration", "qa", "delivery"]
STATUSES = {"PENDING", "PASS", "FAIL", "BLOCKED", "NEEDS_CONTEXT"}
MODULE = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_catalog(root=None):
    if root is None:
        root = Path(__file__).resolve().parents[4] / "azure-image2-generation"
    root = Path(root).resolve()
    ref = root / "modules/casual-game-art-style/references"
    styles_file = ref / "style-masters.md"
    palette_file = ref / "regional-palettes.json"
    result = {"styles": [], "palettes": [], "warnings": [], "sources": {"root": str(root)}}
    if styles_file.is_file():
        text = styles_file.read_text(encoding="utf-8-sig")
        result["sources"]["styles_sha256"] = sha256(styles_file)
        result["sources"]["styles"] = str(styles_file)
        for item in re.finditer(r"^\|\[(T\d+)\]\([^)]*\)\|([^|]+)\|([^|]+)\|", text, re.M):
            sid, name, use = item.groups()
            section = re.search(r"^## " + sid + r"[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
            evidence = re.search(r"\[(S\d+)\]", section.group(1)) if section else None
            image = root / "modules/casual-game-art-style/assets/style-study/evidence" / (evidence.group(1) + ".png") if evidence else None
            result["styles"].append({"id": sid, "name": name.strip(), "use": use.strip(),
                                     "evidence_image": str(image) if image and image.is_file() else "",
                                     "evidence_kind": "archived_store_crop"})
        if not result["styles"]:
            result["warnings"].append("风格目录格式未识别，请读取源文件；不要编造模板编号。")
    else:
        result["warnings"].append("未找到 GPT 生图风格目录；请定位该技能或选择自定义方向。")
    if palette_file.is_file():
        try:
            palettes = read_json(palette_file)
            schemes = palettes.get("schemes", []) if isinstance(palettes, dict) else None
            if not isinstance(schemes, list) or not all(isinstance(p, dict) and p.get("id") and p.get("name") for p in schemes):
                raise ValueError("Invalid palette structure")
            result["palettes"] = schemes
            result["sources"]["palettes_sha256"] = sha256(palette_file)
            result["sources"]["palettes"] = str(palette_file)
        except (ValueError, OSError) as exc:
            result["warnings"].append("地区配色目录读取失败，可继续填写简报或自定义：" + str(exc))
    else:
        result["warnings"].append("未找到地区配色目录；可先填写市场与定制需求。")
    entry = root / "SKILL.md"
    if entry.is_file():
        version = re.search(r"^\s*version:\s*[\"']?([\d.]+)", entry.read_text(encoding="utf-8-sig"), re.M)
        result["sources"]["version"] = version.group(1) if version else "unknown"
    return result


def new_state(name, catalog):
    return {"schema_version": 1, "project_id": uuid.uuid4().hex, "name": name,
            "revision": 1, "updated_at": now(), "timezone": "", "phase": "intake", "paused": False,
            "brief": {}, "direction": {}, "catalog": catalog, "recommendations": [],
            "concepts": [], "selected_concept": None, "plan": [], "assets": [],
            "checks": [], "screens": [], "approvals": [], "history": [],
            "unknowns": [], "feedback": [], "entrypoints": [], "next_action": "请先选择目标市场、目标用户和产品方向。"}


def counts(state):
    assets = [a for a in state.get("assets", []) if a.get("active", True)]
    total = len(assets)
    qa = sum(a.get("qa") == "PASS" and bool(a.get("evidence")) for a in assets)
    return {"total": total, "generated": sum(bool(a.get("generated")) for a in assets),
            "technical_pass": sum(a.get("technical") == "PASS" for a in assets),
            "integrated": sum(bool(a.get("integrated")) for a in assets), "qa_pass": qa,
            "qa_percent": round(100 * qa / total, 1) if total else None}


def validate_state(s, base_dir=None):
    if s.get("schema_version") != 1 or s.get("phase") not in PHASES:
        raise ValueError("Unknown schema version or phase")
    if not s.get("project_id") or not isinstance(s.get("revision"), int) or s["revision"] < 1:
        raise ValueError("Missing project identity or revision")
    ids = [a["id"] for a in s.get("assets", [])]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate asset IDs")
    for item in s.get("assets", []):
        for key in ("technical", "visual", "qa"):
            if key in item and item[key] not in STATUSES:
                raise ValueError("Unknown status: " + str(item[key]))
        if item.get("qa") == "PASS" and not item.get("evidence"):
            raise ValueError("QA PASS requires evidence")
    for check in s.get("checks", []):
        if check.get("status") not in STATUSES or (check.get("status") == "PASS" and not check.get("evidence")):
            raise ValueError("Checks require a known status and PASS evidence")
    if s.get("selected_concept") and base_dir is not None:
        selected = next((c for c in s["concepts"] if c["id"] == s["selected_concept"]), None)
        if not selected:
            raise ValueError("Selected design is not in the candidate list")
        image = Path(selected["image"])
        image = image if image.is_absolute() else Path(base_dir) / image
        if not image.is_file() or sha256(image) != selected.get("sha256"):
            raise ValueError("Selected image is missing or changed; restore it or select the current design explicitly")
    if PHASES.index(s["phase"]) >= PHASES.index("representative"):
        selected = next((c for c in s["concepts"] if c["id"] == s.get("selected_concept")), None)
        if not selected or selected.get("status") == "rejected":
            raise ValueError("Production requires a selected design and explicit plan authorization")
        valid_design = any(a["action"] == "approve_design" and a.get("target") == selected["id"]
                           and a.get("sha256") == selected["sha256"] for a in s["approvals"])
        valid_plan = any(a["action"] == "approve_plan" and a.get("target") == digest(s["plan"])
                         and a.get("design_id") == selected["id"] and a.get("design_sha256") == selected["sha256"]
                         for a in s["approvals"])
        if not valid_design or not valid_plan:
            raise ValueError("Design or plan changed; current approval evidence is required")
    if PHASES.index(s["phase"]) >= PHASES.index("production"):
        selected = next(c for c in s["concepts"] if c["id"] == s["selected_concept"])
        if not any(c.get("phase") == "representative" and c.get("status") == "PASS" and c.get("evidence")
                   and c.get("design_id") == selected["id"] and c.get("design_sha256") == selected["sha256"]
                   and c.get("plan_sha256") == digest(s["plan"]) for c in s["checks"]):
            raise ValueError("Batch production requires representative-screen evidence")
    return s


def require(values, *fields):
    for field in fields:
        if not isinstance(values.get(field), str) or not values[field].strip():
            raise ValueError("Required choice: " + field)


def invalidate_design(s):
    s["selected_concept"] = None
    s["approvals"] = []
    s["checks"] = []
    for asset in s["assets"]:
        asset["active"] = False


def apply_submission(state, request, base_dir):
    validate_state(state)
    if request.get("project_id") != state["project_id"] or request.get("state_revision") != state["revision"]:
        raise ValueError("Project or revision mismatch; reopen the current workbench")
    action, values = request.get("action"), request.get("values", {})
    if not isinstance(values, dict):
        raise ValueError("values must be an object")
    if state.get("paused") and action not in ("resume", "feedback"):
        raise ValueError("Project is paused; only an explicit resume can continue")
    s = copy.deepcopy(state)
    target = ""
    if action == "save_brief":
        require(values, "market", "audience", "position")
        allowed = {"market", "audience", "position", "languages", "platforms", "scope", "constraints", "candidate_limit", "source"}
        brief = {k: v for k, v in values.items() if k in allowed}
        if brief != s["brief"]:
            invalidate_design(s)
        s["brief"] = brief
        s["phase"] = "direction"
        s["next_action"] = "AI 根据产品简报推荐少量风格，补充地区配色与题材选项。"
    elif action == "choose_direction":
        require(values, "style_id", "palette_id", "theme")
        if not s["brief"]:
            raise ValueError("Record the product brief first")
        styles = {x["id"] for x in s["catalog"]["styles"]}
        palettes = {x["id"] for x in s["catalog"]["palettes"]}
        if values["style_id"] not in styles | {"CUSTOM", "RECOMMEND"}:
            raise ValueError("Unknown style; resolve legacy IDs against project context")
        if values["palette_id"] not in palettes | {"CUSTOM", "RECOMMEND"}:
            raise ValueError("Unknown palette")
        if values["style_id"] == "CUSTOM":
            require(values, "style_note")
        if values["palette_id"] == "CUSTOM":
            require(values, "palette_note")
        direction = {k: values.get(k, "") for k in ("style_id", "style_note", "palette_id", "palette_note", "theme", "localization")}
        if direction != s["direction"]:
            invalidate_design(s)
        s["direction"] = direction
        unresolved = "RECOMMEND" in (values["style_id"], values["palette_id"])
        s["phase"] = "direction" if unresolved else "concept"
        s["next_action"] = "AI 补充可比较的推荐方向，请用户选择。" if unresolved else "调用 GPT 生图制作同一代表屏的少量候选，在本页评审。"
    elif action == "approve_design":
        require(values, "concept_id", "sha256")
        candidate = next((c for c in s["concepts"] if c["id"] == values["concept_id"]), None)
        if not candidate or candidate.get("status") == "rejected":
            raise ValueError("Candidate is missing or rejected")
        image = Path(candidate["image"])
        image = image if image.is_absolute() else Path(base_dir) / image
        if not image.is_file() or sha256(image) != candidate.get("sha256") or values["sha256"] != candidate["sha256"]:
            raise ValueError("Concept image changed or hash mismatch")
        if candidate.get("brief_revision") is not None and candidate["brief_revision"] != digest([s["brief"], s["direction"]]):
            raise ValueError("Concept belongs to an earlier brief")
        previous = s.get("selected_concept")
        previous_hash = next((a.get("sha256") for a in reversed(s["approvals"])
                              if a["action"] == "approve_design" and a.get("target") == previous), None)
        if previous != candidate["id"] or previous_hash != candidate["sha256"]:
            invalidate_design(s)
            for other in s["concepts"]:
                if other.get("status") == "selected":
                    other["status"] = "candidate"
        s["selected_concept"] = candidate["id"]
        candidate["status"] = "selected"
        target = candidate["id"]
        s["phase"] = "plan"
        s["next_action"] = "展示接下来逐项实现的计划、交付范围和 QA 平台；已有执行授权则记录出处后连续推进。"
    elif action == "approve_plan":
        require(values, "plan_sha256")
        if not s["selected_concept"] or not s["plan"] or values["plan_sha256"] != digest(s["plan"]):
            raise ValueError("Plan is missing or changed")
        target = values["plan_sha256"]
        s["phase"] = "representative"
        s["next_action"] = "制作代表素材并实际回填游戏，完成代表屏三列对照后批量生产。"
    elif action == "reject_concept":
        require(values, "concept_id", "text")
        candidate = next((c for c in s["concepts"] if c["id"] == values["concept_id"]), None)
        if not candidate:
            raise ValueError("Unknown concept")
        candidate["status"] = "rejected"
        if candidate["id"] == s["selected_concept"]:
            invalidate_design(s)
            s["phase"] = "concept"
        s["feedback"].append({"target": candidate["id"], "text": values["text"], "at": now()})
    elif action == "accept_visual":
        c = counts(s)
        if s["phase"] != "delivery" or not c["total"] or c["qa_pass"] != c["total"] or c["integrated"] != c["total"]:
            raise ValueError("Visual acceptance requires integrated assets and QA evidence")
        target = s["selected_concept"]
    elif action == "feedback":
        require(values, "text")
        s["feedback"].append({"target": values.get("target", "project"), "text": values["text"], "at": now()})
    elif action in ("pause", "resume"):
        s["paused"] = action == "pause"
    else:
        raise ValueError("Unknown action")
    record = {"action": action, "source_revision": state["revision"], "target": target, "at": now()}
    if action.startswith("approve_") or action == "accept_visual":
        selected = next((c for c in s["concepts"] if c["id"] == s["selected_concept"]), None)
        if selected:
            record.update({"design_id": selected["id"], "design_sha256": selected["sha256"]})
        if action == "approve_design":
            record["sha256"] = selected["sha256"]
        s["approvals"].append(record)
    s["history"].append(record)
    s["revision"] += 1
    s["updated_at"] = now()
    validate_state(s, base_dir)
    return s


def image_uri(value, base_dir):
    if not value:
        return ""
    p = Path(value)
    p = p if p.is_absolute() else Path(base_dir) / p
    if p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"} or not p.is_file():
        return ""
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return "data:" + mime + ";base64," + base64.b64encode(p.read_bytes()).decode()


def render(state, base_dir):
    validate_state(state, base_dir)
    s = copy.deepcopy(state)
    for style in s["catalog"]["styles"]:
        style["preview"] = image_uri(style.get("evidence_image"), base_dir)
    for concept in s["concepts"]:
        concept["preview"] = image_uri(concept.get("image"), base_dir)
    for screen in s["screens"]:
        screen["previews"] = {key: image_uri(screen.get(key), base_dir) for key in ("original", "target", "current")}
    payload = {"state": s, "counts": counts(s), "plan_sha256": digest(s["plan"]),
               "brief_revision": digest([s["brief"], s["direction"]])}
    encoded = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return (MODULE / "assets/workbench.html").read_text(encoding="utf8").replace("__STATE_JSON__", encoded)


def save_state(path, state, backup=True):
    path = Path(path)
    validate_state(state)
    if backup and path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        atomic_write(path.parent / "history" / (path.stem + "-" + stamp + ".json"), path.read_text(encoding="utf-8-sig"))
    atomic_write(path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def initialize(out_dir, name, catalog, timezone_name=""):
    dest = Path(out_dir)
    state_path = dest / "reskin-state.json"
    if state_path.exists():
        raise FileExistsError("Project state already exists; use render to resume")
    state = new_state(name, catalog)
    state["timezone"] = timezone_name
    html = render(state, dest)
    save_state(state_path, state, backup=False)
    atomic_write(dest / "index.html", html)
    return state_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--out", required=True)
    init.add_argument("--name", required=True)
    init.add_argument("--image-skill-root")
    init.add_argument("--timezone", default="", help="Client IANA timezone; otherwise use the browser timezone")
    for name in ("render", "validate", "import"):
        p = sub.add_parser(name)
        p.add_argument("--state", required=True)
        if name == "render":
            p.add_argument("--out")
            p.add_argument("--image-skill-root", help="Explicitly refresh the source catalog snapshot")
        if name == "import":
            p.add_argument("--submission", required=True)
    args = parser.parse_args()
    if args.command == "init":
        path = initialize(args.out, args.name, load_catalog(args.image_skill_root), args.timezone)
        print(json.dumps({"ok": True, "state": str(path), "html": str(path.parent / "index.html")}, ensure_ascii=False))
        return
    path = Path(args.state).resolve()
    s = validate_state(read_json(path), None if args.command == "import" else path.parent)
    if args.command == "import":
        s = apply_submission(s, read_json(args.submission), path.parent)
        html = render(s, path.parent)
        save_state(path, s)
        atomic_write(path.parent / "index.html", html)
    elif args.command == "render":
        if args.image_skill_root:
            s["catalog"] = load_catalog(args.image_skill_root)
            s["revision"] += 1
            s["updated_at"] = now()
            save_state(path, s)
        atomic_write(args.out or path.parent / "index.html", render(s, path.parent))
    print(json.dumps({"ok": True, "project_id": s["project_id"], "revision": s["revision"],
                      "phase": s["phase"], "counts": counts(s)}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError, FileExistsError, KeyError) as exc:
        raise SystemExit(str(exc))
