"""面向远程调用的授权检查和有限结果视图，不依赖 MCP 协议或 HTTP 路由。"""

from pathlib import Path
from typing import Collection

from app.services.workflow import engine, model_runtime


def _text(value, limit: int) -> str:
    """只投影预期的文本，不把意外嵌套对象、模型上下文或字节串转成可见正文。"""
    return value[:limit] if isinstance(value, str) else ""


def _text_list(value, count: int = 100, limit: int = 1024) -> list[str]:
    return [_text(item, limit) for item in value[:count] if isinstance(item, str)] if isinstance(value, list) else []


def require_project(project_id: str, allowed_projects: Collection[str]) -> dict:
    """每次操作重新检查项目权限，不能凭已知 run_id 绕过白名单。"""
    if "*" not in allowed_projects and project_id not in allowed_projects:
        raise PermissionError("无权访问该项目")
    return engine.load("projects", project_id)


def require_run(run_id: str, allowed_projects: Collection[str]) -> dict:
    """从持久运行记录解析所属项目，调用方不能自行声明归属。"""
    run = engine.load("runs", run_id)
    require_project(run["project_id"], allowed_projects)
    return run


def project_view(project: dict) -> dict:
    """只返回协调工作需要的字段，不展开冻结资料、服务端路径和内部提交元数据。"""
    result = {key: project.get(key) for key in (
        "id", "name", "created_at", "genre_id", "framework_id",
    )}
    result["stages"] = [{key: stage.get(key) for key in (
        "id", "label", "status", "run_id", "confirmed_at", "confirmed_by")}
        for stage in project.get("stages", []) if isinstance(stage, dict)]
    # 未记录模型来源的历史项目沿用原 Codex 登录契约，查询不能改写历史记录。
    result.update(model_provider=project.get("model_provider", "codex-login"),
                  model_id=project.get("model_id", model_runtime.DEFAULT_MODEL))
    result.update(references=_text_list(project.get("references")),
                  knowledge_paths=_text_list(project.get("knowledge_paths")))
    plan = project.get("production_plan")
    result["production_plan"] = None
    if isinstance(plan, dict):
        # 配置摘要足够协调方识别执行方式，不返回各阶段的大段提示词及冻结输入。
        result["production_plan"] = {
            "template_id": _text(plan.get("template_id"), 120),
            "art_requirements": _text(plan.get("art_requirements"), 2000),
            "autonomous": plan.get("autonomous") is True,
            "auto_publish": plan.get("auto_publish") is True,
            "publish_slug": _text(plan.get("publish_slug"), 64),
            "stages": {stage: {"skill_mode": _text(settings.get("skill_mode"), 20),
                               "skill_paths": _text_list(settings.get("skill_paths"), count=50)}
                       for stage, settings in (plan.get("stages") or {}).items()
                       if stage in dict(engine.STAGES) and isinstance(settings, dict)},
        }
    pipeline = project.get("pipeline")
    result["pipeline"] = None
    if isinstance(pipeline, dict):
        result["pipeline"] = {key: _text(pipeline.get(key), 128) for key in (
            "id", "status", "run_id", "current_stage", "approved_at", "updated_at", "completed_at")}
        result["pipeline"]["error"] = model_runtime.safe_error(ValueError(pipeline["error"])) if pipeline.get("error") else None
    publication = project.get("publication")
    result["publication"] = None
    if isinstance(publication, dict):
        result["publication"] = {key: _text(publication.get(key), 2048) for key in (
            "project_id", "run_id", "slug", "url", "published_at", "sha256")}
        result["publication"].update({key: publication[key] for key in ("bytes", "file_count")
                                      if type(publication.get(key)) is int})
    return result


def interrupt_page(run: dict, offset: int = 0, limit: int = 20) -> dict:
    """按页返回当前真正待回答的问题；已恢复运行中的历史中断不会再次当作待办。"""
    if offset < 0 or not 1 <= limit <= 50:
        raise ValueError("问题分页 offset 不能为负数，limit 须在 1 至 50 之间")
    pending = run.get("interrupts", []) if run.get("status") == "awaiting_input" else []
    start = min(offset, len(pending))
    selected = pending[start:start + limit]
    questions = []
    for item in selected:
        value = item.get("value") or {}
        questions.append({"id": _text(item.get("id"), 200), "value": {
            "kind": _text(value.get("kind"), 80), "question": _text(value.get("question"), 2000),
            "context": _text(value.get("context"), 4000), "options": _text_list(value.get("options"), count=8, limit=500),
        }})
    end = start + len(selected)
    return {"run_id": run["id"], "status": run["status"], "interrupts": questions, "total": len(pending),
            "offset": start, "next_offset": end, "has_more": end < len(pending)}


async def runtime_view(provider: str, model_id: str) -> dict:
    """远程只展示模型配置状态与能力；用字段白名单避免服务地址、凭据进入 MCP。"""
    runtime = await model_runtime.inspect_runtime(provider, model_id)
    result = {key: runtime.get(key) for key in (
        "provider", "model", "upstream_model", "framework", "configured", "available", "connection_checked", "transport",
    )}
    result["capabilities"] = {key: bool(runtime.get("capabilities", {}).get(key)) for key in (
        "reference_archives", "web_validation", "publishing", "image_generation",
    )}
    result["models"] = [{key: model.get(key) for key in ("id", "name")}
                        for model in runtime.get("models", [])]
    if runtime.get("error"):
        result["error"] = model_runtime.safe_error(ValueError(str(runtime["error"])))
    return result


def run_view(run: dict) -> dict:
    """状态与正文分开获取；等待确认不等于已通过验收，恢复也不会替代确认。"""
    result = {key: run.get(key) for key in (
        "id", "project_id", "stage", "status", "progress", "attempt", "created_at", "updated_at",
    )}
    result.update(
        summary=_text(run.get("summary"), 4000),
        error=model_runtime.safe_error(ValueError(run["error"]))[:2000] if run.get("error") else None,
        event_cursor=run["events"][-1]["seq"] if run["events"] else 0,
        artifact_count=len(run["artifacts"]),
        requires_confirmation=run["status"] == "awaiting_confirmation",
        poll_after_seconds=3 if run["status"] in engine.ACTIVE else None,
        skill_paths=run.get("skill_paths", []), skill_selection=run.get("skill_selection"),
        skill_snapshot=run.get("skill_snapshot", []),
        model_provider=run.get("provider", "codex-login"),
        model_id=run.get("model", model_runtime.DEFAULT_MODEL),
        autonomous=run.get("autonomous") is True,
        pipeline_id=run.get("pipeline_id"),
        requires_input=run["status"] == "awaiting_input",
    )
    questions = interrupt_page(run)
    result.update(interrupts=questions["interrupts"], interrupt_count=questions["total"],
                  has_more_interrupts=questions["has_more"])
    # 远程协调者也能核对实际读取版本；不返回工具正文或配套资源的完整输入清单。
    reads = {(event["data"].get("path"), event["data"].get("sha256")): event["data"]
             for event in run["events"] if event["type"] == "skill_read"}
    result["skill_reads"] = [{key: value.get(key) for key in ("path", "sha256", "version", "frozen")}
                            for value in reads.values()]
    return result


def event_page(run: dict, after: int, limit: int) -> dict:
    """按持久序号分页；保留精简消息，避免把模型上下文和整份工具正文重复传输。"""
    remaining = [item for item in run["events"] if item["seq"] > after]
    selected = remaining[:limit]
    events = [{"seq": item["seq"], "time": item["time"], "type": item["type"],
               "message": str(item["message"])[:1000]} for item in selected]
    return {"run_id": run["id"], "status": run["status"], "events": events,
            "next_cursor": selected[-1]["seq"] if selected else after, "has_more": len(remaining) > limit}


def artifact_view(run_id: str, artifact: dict, public_url: str) -> dict:
    """文件通过专用认证入口交付；不返回无鉴权的旧 REST 链接或服务端绝对路径。"""
    result = {key: artifact.get(key) for key in ("id", "name", "path", "kind", "size", "sha256", "provenance")}
    result["download_url"] = f"{public_url.rstrip('/')}/artifacts/{run_id}/{artifact['id']}"
    result["authentication"] = "下载时携带与 MCP 相同的 Authorization: Bearer 令牌"
    return result


def artifact_file(run_id: str, artifact_id: str, allowed_projects: Collection[str]) -> tuple[dict, Path]:
    """授权后复用引擎的路径与快照哈希检查，读取和下载共用同一入口。"""
    run = require_run(run_id, allowed_projects)
    path = engine.artifact_file(run_id, artifact_id)
    artifact = next(item for item in run["artifacts"] if item["id"] == artifact_id)
    return artifact, path


def text_page(path: Path, offset: int, limit: int) -> dict:
    """按字符分页读取 UTF-8 文本；分块跳过前缀，避免整份大文件进入内存。"""
    with path.open(encoding="utf-8", errors="replace") as source:
        remaining = offset
        while remaining:
            skipped = source.read(min(remaining, 8192))
            if not skipped:
                break
            remaining -= len(skipped)
        content = source.read(limit + 1)
    return {"text": content[:limit], "offset": offset, "next_offset": offset + len(content[:limit]),
            "has_more": len(content) > limit}
