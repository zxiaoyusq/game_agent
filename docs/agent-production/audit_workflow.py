"""只读核验真实四阶段交付，并导出可追溯摘要；不修改任务状态。

在工程根目录、conda base 环境执行：
python docs/agent-production/audit_workflow.py
只有四阶段已确认、证据有效且分发包与构建一致时才退出 0。
"""

import hashlib
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.workflow import engine


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    """以持久运行和实际文件为准，拒绝仅凭模型总结或旧测试报告放行。"""
    session = json.loads((ROOT / "logs/ball-sort-workflow-session.json").read_text())
    project = engine.get_project(session["project_id"])
    workspace = engine.resolve_workspace(project["workspace"])
    errors, stages = [], []
    final_fingerprint = engine.source_fingerprint(workspace)
    # 复用生产交接门禁，清单也必须对应已确认快照，不能只信当前清单自洽。
    try:
        engine.verify_confirmed_dependencies(project, "test")
    except ValueError as error:
        errors.append(f"已确认交接输入不一致：{error}")
    for stage in project["stages"]:
        record = {"stage": stage["id"], "status": stage["status"], "run_id": stage["run_id"]}
        stages.append(record)
        if stage["status"] != "completed" or not stage.get("confirmed_at"):
            errors.append(f"阶段尚未确认：{stage['label']}")
        if not stage["run_id"]:
            continue
        run = engine.load("runs", stage["run_id"])
        events = run["events"]
        if run["status"] != "completed":
            errors.append(f"阶段运行尚未确认：{run['id']}")
        record.update(model=run["model"], attempt=run.get("attempt", 1), event_count=len(events),
                      model_calls=sum(item["type"] == "model_completed" for item in events),
                      artifacts=len(run["artifacts"]),
                      artifact_provenance=dict(Counter(item.get("provenance", "unknown") for item in run["artifacts"])))
        if run["model"] != "gpt-6.1-sol" or record["model_calls"] == 0:
            errors.append(f"阶段缺少指定模型的实际推理：{stage['id']}")
        if not any(item["type"] == "runtime_checked" and item["data"].get("available") for item in events):
            errors.append(f"阶段缺少有效运行时核验：{stage['id']}")
        record["skills"] = [item["data"] for item in events if item["type"] == "skill_read"]
        # 摘要只保存入口与哈希，完整读取正文仍保留在原始运行事件中。
        record["skills"] = [{"path": item["path"], "sha256": item["sha256"]} for item in record["skills"]]
        if set(run["skill_paths"]) - {item["path"] for item in record["skills"]}:
            errors.append(f"阶段未实际读取所选技能：{stage['id']}")
        for artifact in run["artifacts"]:
            try:
                engine.artifact_file(run["id"], artifact["id"])
            except (ValueError, FileNotFoundError) as error:
                errors.append(f"产物校验失败：{artifact['path']}：{error}")
        report = next((item for item in run["artifacts"] if item["path"] == f"workflow/{stage['id']}.md"), None)
        if not report or digest(workspace / report["path"]) != report["sha256"]:
            errors.append(f"当前阶段报告与归档不一致：{stage['id']}")
        writes = engine.written_file_evidence(run)
        report_path = f"workflow/{stage['id']}.md"
        if report_path not in writes:
            errors.append(f"缺少阶段报告的真实成功文件工具结果：{stage['id']}")
        # 旧原型有成功 edit 结果但没有落盘哈希；如实记录，不倒推升级为作者证明。
        record["report_write_evidence"] = {
            "successful_tool_result": report_path in writes,
            "written_sha256": writes.get(report_path),
            "matches_archived_content": bool(report and writes.get(report_path) == report["sha256"]),
        }
        record["validations"] = [item["data"] for item in events if item["type"] == "validation_completed"]
        # 测试完整输出在运行中，摘要保留命令、退出码、尝试与源码指纹。
        record["validations"] = [{key: value for key, value in item.items() if key not in {"output", "changed_files"}} for item in record["validations"]]
        if stage["id"] in {"code", "test"}:
            try:
                engine.verify_validation_evidence(run, workspace)
            except ValueError as error:
                errors.append(f"最终源码与验证不一致：{stage['id']}：{error}")
            checks = [item for item in record["validations"] if item.get("command") == "npm run check"
                      and item.get("attempt") == run.get("attempt", 1)]
            check = checks[-1] if checks else {}
            if (check.get("exit_code") != 0 or check.get("source_before") != final_fingerprint
                    or check.get("source_after") != final_fingerprint):
                errors.append(f"阶段缺少对应最终源码的本次浏览器综合检查：{stage['id']}")
    manifest = json.loads((workspace / "workflow/art-manifest.json").read_text())
    for asset in manifest["assets"]:
        if digest(workspace / asset["path"]) != asset["sha256"]:
            errors.append(f"美术资源已变化：{asset['path']}")
    engine_evidence = json.loads((workspace / "evidence/engine-build.json").read_text())
    runtime_hash = digest(workspace / "dist/engine/cc.js")
    if not engine_evidence.get("sourceIdentityVerified") or runtime_hash != engine_evidence.get("runtimeSha256"):
        errors.append("实际引擎身份或运行时哈希不匹配")
    browser = json.loads((workspace / "evidence/browser-validation.json").read_text())
    if not browser.get("passed") or browser.get("errors") or browser.get("failedRequests"):
        errors.append("当前浏览器检查未通过")
    package = workspace / "releases/ball-sort-fusion-web.zip"
    with zipfile.ZipFile(package) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        packaged = {item.filename: hashlib.sha256(archive.read(item)).hexdigest() for item in files}
        built = {path.relative_to(workspace / "dist").as_posix(): digest(path)
                 for path in (workspace / "dist").rglob("*") if path.is_file()}
        if packaged != built:
            errors.append("Web 分发包与当前 dist 文件不一致，须重新打包")
    revisions = [item for run in engine.project_runs(project["id"]) for item in run["events"] if item["type"] == "skill_updated"]
    if not revisions:
        errors.append("缺少模型在真实阶段运行中修订 Skill 的记录")
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "passed": not errors,
            "project_id": project["id"], "workspace": project["workspace"], "stages": stages,
            "source_fingerprint": final_fingerprint, "assets": len(manifest["assets"]),
            "engine": {"version": engine_evidence["version"], "runtime_sha256": runtime_hash,
                       "source_files_checked": engine_evidence.get("sourceComparison", {}).get("checkedFiles")},
            "browser_checks": browser.get("checks", []), "package_sha256": digest(package),
            "model_skill_revisions": len(revisions), "errors": errors}


if __name__ == "__main__":
    report = audit()
    output = ROOT / "docs/agent-production/acceptance.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": report["passed"], "报告": str(output), "错误": report["errors"]}, ensure_ascii=False))
    sys.exit(0 if report["passed"] else 1)
