"""Behavior checks for the reusable, offline reskin workbench."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "render_workbench.py"
spec = importlib.util.spec_from_file_location("workbench", SCRIPT)
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalog_root = self.root / "image-skill"
        ref = self.catalog_root / "modules/casual-game-art-style/references"
        ref.mkdir(parents=True)
        (self.catalog_root / "SKILL.md").write_text("metadata:\n  version: 2.0.0\n", encoding="utf8")
        (ref / "style-masters.md").write_text(
            "|ID|Direction|Use|\n|---|---|---|\n"
            "|[T02](#T02)|Illustrated icons|Matching|\n"
            "|[T04](#T04)|Controlled volume|Match three|\n", encoding="utf8")
        (ref / "regional-palettes.json").write_text(json.dumps({"schemes": [
            {"id": "NG02", "region": "NG", "name": "Forest", "levels": [
                {"level": 1, "colors": ["#DCA218"]}]}]}), encoding="utf8")
        self.catalog = wb.load_catalog(self.catalog_root)
        self.state = wb.new_state("Test project", self.catalog)

    def tearDown(self):
        self.temp.cleanup()

    def submission(self, action, values, state=None):
        s = state or self.state
        return {"project_id": s["project_id"], "state_revision": s["revision"],
                "action": action, "values": values}

    def prepared(self):
        s = wb.apply_submission(self.state, self.submission("save_brief", {
            "market": "Latin America", "audience": "Adults", "position": "Localize",
            "platforms": ["H5"]}), self.root)
        return wb.apply_submission(s, self.submission("choose_direction", {
            "style_id": "T04", "palette_id": "CUSTOM", "palette_note": "Ocean",
            "theme": "Coast"}, s), self.root)

    def test_live_catalog_not_fixed_copy(self):
        self.assertEqual([s["id"] for s in self.catalog["styles"]], ["T02", "T04"])
        self.assertEqual(self.catalog["palettes"][0]["id"], "NG02")
        self.assertEqual(len(self.catalog["sources"]["styles_sha256"]), 64)

    def test_missing_catalog_is_explicit_and_does_not_invent_templates(self):
        c = wb.load_catalog(self.root / "absent")
        self.assertFalse(c["styles"])
        self.assertTrue(c["warnings"])

    def test_invalid_palette_keeps_intake_usable(self):
        palette = self.catalog_root / "modules/casual-game-art-style/references/regional-palettes.json"
        palette.write_text("{incomplete", encoding="utf8")
        catalog = wb.load_catalog(self.catalog_root)
        self.assertTrue(catalog["styles"])
        self.assertFalse(catalog["palettes"])
        self.assertTrue(catalog["warnings"])
        wb.initialize(self.root / "intake-with-warning", "continue intake", catalog)

    def test_initial_state_has_no_approval_or_fake_completion(self):
        self.assertEqual(self.state["phase"], "intake")
        self.assertFalse(self.state["approvals"])
        self.assertEqual(wb.counts(self.state)["total"], 0)
        self.assertIsNone(wb.counts(self.state)["qa_percent"])

    def test_import_brief_is_an_explicit_versioned_action(self):
        result = wb.apply_submission(self.state, self.submission("save_brief", {
            "market": "Custom", "audience": "Unsure, recommend", "position": "Reskin"
        }), self.root)
        self.assertEqual(result["phase"], "direction")
        self.assertEqual(result["revision"], 2)
        self.assertEqual(self.state["phase"], "intake")
        self.assertTrue(result["history"])

    def test_stale_or_wrong_project_submission_cannot_change_state(self):
        for field, val in [("state_revision", 99), ("project_id", "another")]:
            request = self.submission("feedback", {"text": "keep"})
            request[field] = val
            with self.assertRaises(ValueError):
                wb.apply_submission(self.state, request, self.root)
        self.assertEqual(self.state["revision"], 1)

    def test_unknown_template_and_empty_custom_palette_rejected(self):
        s = self.prepared()
        for values in [
            {"style_id": "M03", "palette_id": "CUSTOM", "palette_note": "x", "theme": "x"},
            {"style_id": "T04", "palette_id": "CUSTOM", "palette_note": "", "theme": "x"},
        ]:
            with self.assertRaises(ValueError):
                wb.apply_submission(s, self.submission("choose_direction", values, s), self.root)

    def test_design_confirmation_binds_current_file_hash_and_candidate(self):
        s = self.prepared()
        image = self.root / "concept.png"
        image.write_bytes(b"test-image-bytes")
        s["concepts"] = [{"id": "C1", "version": 1, "image": "concept.png",
                          "sha256": wb.sha256(image), "status": "candidate"}]
        req = self.submission("approve_design", {"concept_id": "C1", "sha256": wb.sha256(image)}, s)
        approved = wb.apply_submission(s, req, self.root)
        self.assertEqual(approved["phase"], "plan")
        self.assertEqual(approved["approvals"][-1]["target"], "C1")
        image.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            wb.apply_submission(s, req, self.root)

    def test_rejected_candidate_cannot_be_approved(self):
        s = self.prepared()
        s["concepts"] = [{"id": "C1", "version": 1, "image": "none.png", "sha256": "x", "status": "rejected"}]
        with self.assertRaises(ValueError):
            wb.apply_submission(s, self.submission("approve_design", {"concept_id": "C1", "sha256": "x"}, s), self.root)

    def ready_for_production(self):
        s = self.prepared()
        image = self.root / "C1.png"
        image.write_bytes(b"concept-one")
        s["concepts"] = [{"id": "C1", "version": 1, "image": "C1.png", "sha256": wb.sha256(image), "status": "candidate"}]
        s = wb.apply_submission(s, self.submission("approve_design", {"concept_id": "C1", "sha256": wb.sha256(image)}, s), self.root)
        s["plan"] = ["Representative screen", "Batch assets"]
        s = wb.apply_submission(s, self.submission("approve_plan", {"plan_sha256": wb.digest(s["plan"])}, s), self.root)
        s["checks"] = [{"phase": "representative", "status": "PASS", "evidence": ["runtime.png"],
                        "design_id": "C1", "design_sha256": s["concepts"][0]["sha256"], "plan_sha256": wb.digest(s["plan"])}]
        s["phase"] = "production"
        wb.validate_state(s)
        return s

    def test_switching_concept_invalidates_old_plan_and_representative_evidence(self):
        s = self.ready_for_production()
        image = self.root / "C2.png"
        image.write_bytes(b"concept-two")
        s["concepts"].append({"id": "C2", "version": 1, "image": "C2.png", "sha256": wb.sha256(image), "status": "candidate"})
        s["assets"] = [{"id": "old", "active": True}]
        result = wb.apply_submission(s, self.submission("approve_design", {"concept_id": "C2", "sha256": wb.sha256(image)}, s), self.root)
        self.assertFalse(any(a["action"] == "approve_plan" for a in result["approvals"]))
        self.assertFalse(result["checks"])
        self.assertFalse(result["assets"][0]["active"])

    def test_changed_plan_or_design_cannot_reuse_old_authorization(self):
        for change in ("plan", "hash", "check"):
            s = self.ready_for_production()
            if change == "plan":
                s["plan"].append("Extra scope")
            elif change == "hash":
                s["concepts"][0]["sha256"] = "modified"
            else:
                s["checks"][0]["design_id"] = "another"
            with self.assertRaises(ValueError):
                wb.validate_state(s)

    def test_resume_render_detects_overwritten_or_missing_selected_image(self):
        s = self.ready_for_production()
        image = self.root / "C1.png"
        image.write_bytes(b"overwritten-after-approval")
        with self.assertRaises(ValueError):
            wb.render(s, self.root)
        image.unlink()
        with self.assertRaises(ValueError):
            wb.validate_state(s, self.root)

    def test_generated_assets_are_not_counted_as_qa(self):
        self.state["assets"] = [{"id": "a", "generated": True, "technical": "PASS",
                                  "integrated": False, "qa": "BLOCKED", "evidence": []}]
        c = wb.counts(self.state)
        self.assertEqual((c["generated"], c["integrated"], c["qa_pass"]), (1, 0, 0))
        self.assertEqual(c["qa_percent"], 0)

    def test_qa_pass_without_evidence_not_accepted(self):
        self.state["assets"] = [{"id": "a", "qa": "PASS", "evidence": []}]
        with self.assertRaises(ValueError):
            wb.validate_state(self.state)

    def test_pause_and_resume_are_explicit(self):
        paused = wb.apply_submission(self.state, self.submission("pause", {}), self.root)
        self.assertTrue(paused["paused"])
        with self.assertRaises(ValueError):
            wb.apply_submission(paused, self.submission("save_brief", {
                "market": "x", "audience": "y", "position": "z"}, paused), self.root)
        resumed = wb.apply_submission(paused, self.submission("resume", {}, paused), self.root)
        self.assertFalse(resumed["paused"])

    def test_html_is_self_contained_and_script_safe(self):
        self.state["name"] = "</script><script>alert(9)</script>"
        html = wb.render(self.state, self.root)
        self.assertNotIn(self.state["name"], html)
        self.assertIn("\\u003c/script>", html)
        self.assertNotIn("__STATE_JSON__", html)
        self.assertIn("save_brief", html)

    def test_init_never_overwrites_existing_project(self):
        dest = self.root / "project"
        wb.initialize(dest, "one", self.catalog)
        with self.assertRaises(FileExistsError):
            wb.initialize(dest, "two", self.catalog)
        self.assertEqual(json.loads((dest / "reskin-state.json").read_text(encoding="utf8"))["name"], "one")


if __name__ == "__main__":
    unittest.main()
