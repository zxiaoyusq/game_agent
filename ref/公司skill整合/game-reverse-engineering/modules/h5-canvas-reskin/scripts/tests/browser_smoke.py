"""Exercise the actual download/import loop in an isolated local project."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SCRIPT = Path(__file__).resolve().parents[1] / "render_workbench.py"
spec = importlib.util.spec_from_file_location("workbench", SCRIPT)
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True)
    args = parser.parse_args()
    dest = Path(args.work).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    project = dest / "loop-project"
    state_path = wb.initialize(project, "HTML interaction verification", wb.load_catalog())
    page_path = project / "index.html"
    report = {"browser_errors": [], "steps": []}

    def adopt(page, action):
        with page.expect_download() as info:
            page.locator("#download").click()
        submission = dest / (action + ".json")
        info.value.save_as(submission)
        request = wb.read_json(submission)
        assert request["action"] == action
        proc = subprocess.run([sys.executable, str(SCRIPT), "import", "--state", str(state_path),
                               "--submission", str(submission)], capture_output=True, text=True, encoding="utf8")
        assert proc.returncode == 0, proc.stderr
        page.goto(page_path.as_uri())
        page.wait_for_load_state("networkidle")
        report["steps"].append({"action": action, "result": json.loads(proc.stdout)})
        return submission

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 1000}, accept_downloads=True)
        page.set_default_timeout(8000)
        page.on("pageerror", lambda err: report["browser_errors"].append(str(err)))
        page.goto(page_path.as_uri())
        page.wait_for_load_state("networkidle")
        assert "100%" not in page.locator("#coverage").inner_text()
        assert not page.locator("#market").input_value()
        page.locator("#market").select_option(index=4)
        page.locator("#audience").select_option(index=1)
        page.locator("#position").select_option(index=2)
        page.locator("#brief-form button").click()
        first = adopt(page, "save_brief")
        assert wb.read_json(state_path)["phase"] == "direction"
        assert page.locator("#style-grid input").count() == len(wb.read_json(state_path)["catalog"]["styles"])
        page.locator("input[name=style][value=T04]").check()
        page.locator("#palette").select_option("CUSTOM")
        page.locator("#palette-note").fill("Custom palette for the selected market")
        page.locator("#theme").fill("Coastal everyday life")
        for width in (1200, 736, 360, 320):
            page.set_viewport_size({"width": width, "height": 1000})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        page.set_viewport_size({"width": 1200, "height": 1000})
        page.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager')")
        page.wait_for_function("Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)")
        page.screenshot(path=str(dest / "direction-screen.png"), full_page=True)
        page.locator("#direction-form button").click()
        adopt(page, "choose_direction")
        current = wb.read_json(state_path)
        assert current["revision"] == 3 and current["phase"] == "concept"
        assert not current["approvals"]
        before = state_path.read_bytes()
        stale = subprocess.run([sys.executable, str(SCRIPT), "import", "--state", str(state_path),
                                "--submission", str(first)], capture_output=True)
        assert stale.returncode != 0 and before == state_path.read_bytes()
        report["steps"].append({"action": "reject_stale_submission", "ok": True})
        page.locator("#pause").click()
        adopt(page, "pause")
        assert wb.read_json(state_path)["paused"] and page.locator("#paused").is_visible()
        page.locator("#resume").click()
        adopt(page, "resume")
        assert not wb.read_json(state_path)["paused"]
        assert not report["browser_errors"]
        browser.close()
    report["ok"] = True
    (dest / "browser-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps({"ok": True, "steps": len(report["steps"]), "report": str(dest / "browser-report.json")}))


if __name__ == "__main__":
    main()
