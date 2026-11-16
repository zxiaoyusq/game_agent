"""一次确认的四阶段调度，复用 DeepAgents、检查点与原有证据门禁。

调度器只负责顺序和生命周期，不替模型生成产物。人工问题由图中的
interrupt 产生；网页回答经 Command(resume=...) 返回同一运行。
"""

import asyncio

from app.services.workflow import engine
from app.services.workflow.submissions import describe_submission
from app.services.workflow.templates import ProductionPlan

PIPELINES: dict[str, asyncio.Task] = {}
OWNED = {"running", "awaiting_input", "failed", "interrupted"}


def validate_plan(value: dict) -> dict:
    """提交时发现失效 Skill，避免执行到美术阶段才发现配置无法使用。"""
    plan = ProductionPlan.model_validate(value).model_dump()
    available = {item["path"] for item in engine.list_skills()}
    for stage in plan["stages"].values():
        missing = set(stage["skill_paths"]) - available
        if missing:
            raise ValueError("模板中的 Skill 不存在：" + "、".join(sorted(missing)))
    return plan


def require_owner(project: dict, pipeline_id: str | None) -> None:
    """全流程与手动阶段共享工作区，暂停提问时也不能并行覆盖检查点输入。"""
    pipeline = project.get("pipeline", {})
    if pipeline_id:
        if pipeline.get("id") != pipeline_id or pipeline.get("status") != "running":
            raise ValueError("全流程执行身份已失效，请刷新项目状态")
    elif pipeline.get("status") in OWNED:
        raise ValueError("项目由全流程任务管理，请在全流程面板继续、补充或取消")


def update_pipeline(project_id: str, **fields) -> dict:
    with engine.LOCK:
        project = engine.load("projects", project_id)
        project["pipeline"].update(**fields, updated_at=engine.now())
        engine.save("projects", project)
        return project


def launch(project_id: str) -> None:
    """同一项目最多一个调度协程，刷新页面或重复点击不会重复消费模型。"""
    if project_id not in PIPELINES or PIPELINES[project_id].done():
        PIPELINES[project_id] = asyncio.create_task(drive_pipeline(project_id))


def start_pipeline(project_id: str) -> dict:
    """此入口代表用户已阅读需求并明确授权连续执行和计划中的发布选项。"""
    with engine.LOCK:
        project = engine.load("projects", project_id)
        pipeline = project.get("pipeline")
        if not pipeline or not project.get("production_plan"):
            raise ValueError("项目未保存全流程计划，请使用模板创建新项目")
        if pipeline["status"] != "draft":
            return engine.get_project(project_id)
        validate_plan(project["production_plan"])
        engine.ensure_workspace_available(project)
        update_pipeline(project_id, status="running", approved_at=engine.now(), error=None, retries={})
        launch(project_id)
        return engine.get_project(project_id)


def stage_prompt(project: dict, stage_id: str) -> str:
    plan = project["production_plan"]
    return plan["stages"][stage_id]["prompt"] + "\n\n统一美术需求：\n" + plan["art_requirements"]


async def drive_pipeline(project_id: str) -> None:
    """逐阶段运行并校验；失败最多自动恢复一次，人工中断绝不自动回答。"""
    try:
        while True:
            project = engine.load("projects", project_id)
            pipeline = project["pipeline"]
            if pipeline["status"] != "running":
                return
            stage = next((item for item in project["stages"] if item["status"] != "completed"), None)
            if stage is None:
                plan = project["production_plan"]
                if plan["auto_publish"]:
                    # 默认唯一地址，恢复发布仍走原有归属、指纹和大小门禁。
                    engine.publish_project(project_id, plan["publish_slug"] or project_id)
                update_pipeline(project_id, status="completed", error=None, completed_at=engine.now())
                return
            update_pipeline(project_id, current_stage=stage["id"])
            run = engine.load("runs", stage["run_id"]) if stage.get("run_id") else None
            if run is None:
                settings = project["production_plan"]["stages"][stage["id"]]
                run = engine.start_run(project_id, stage["id"], stage_prompt(project, stage["id"]),
                                       settings["skill_paths"], skill_mode=settings["skill_mode"],
                                       pipeline_id=pipeline["id"])
            update_pipeline(project_id, run_id=run["id"])
            if run["status"] in engine.ACTIVE:
                worker = engine.WORKERS.get(run["id"])
                if worker is None:
                    raise ValueError("执行进程已中断，请从检查点继续")
                # 取消调度器与取消阶段分别处理，防止正在写检查点时提前发布状态。
                await asyncio.shield(worker)
                run = engine.load("runs", run["id"])
            if run["status"] == "awaiting_input":
                update_pipeline(project_id, status="awaiting_input", error=None)
                return
            if run["status"] == "awaiting_confirmation":
                engine.confirm_stage(project_id, stage["id"], "依据已确认计划自动校验并衔接下一阶段",
                                     pipeline_id=pipeline["id"])
                continue
            if run["status"] == "failed":
                retries = engine.load("projects", project_id)["pipeline"].get("retries", {})
                if retries.get(run["id"], 0) < 1:
                    update_pipeline(project_id, retries={**retries, run["id"]: 1})
                    engine.resume_run(run["id"], pipeline_id=pipeline["id"])
                    continue
                if stage["id"] == "test" and pipeline.get("repair_cycles", 0) < 1:
                    # 测试图不写上游源码；有限退回代码阶段，修复后重新验证整个下游。
                    update_pipeline(project_id, repair_cycles=1)
                    failures = [item["data"].get("output", "")[-3000:] for item in run["events"]
                                if item["type"] == "validation_completed" and item["data"].get("exit_code") != 0]
                    prompt = stage_prompt(project, "code") + "\n独立测试未通过，请读取 workflow/test.md（若存在）及验证脚本，针对以下实际错误修复后重验：\n" + (run.get("error") or "") + "\n" + "\n".join(failures[-3:])
                    settings = project["production_plan"]["stages"]["code"]
                    engine.start_run(project_id, "code", prompt, settings["skill_paths"],
                                     skill_mode=settings["skill_mode"], pipeline_id=pipeline["id"])
                    continue
            if run["status"] != "completed":
                update_pipeline(project_id, status=run["status"] if run["status"] in {"cancelled", "interrupted"} else "failed",
                                error=run.get("error") or "阶段未通过校验，请查看事件并重试")
                return
    except asyncio.CancelledError:
        # 显式取消与服务关闭由调用方落盘，不在这里覆盖其决定。
        raise
    except Exception as error:
        update_pipeline(project_id, status="failed", error=engine.model_runtime.safe_error(error))
    finally:
        PIPELINES.pop(project_id, None)


def resume_pipeline(project_id: str) -> dict:
    """用户明确继续失败或重启中断的计划，已通过阶段不重新生成。"""
    with engine.LOCK:
        project = engine.load("projects", project_id)
        pipeline = project.get("pipeline", {})
        if pipeline.get("status") not in {"failed", "interrupted", "cancelled"}:
            raise ValueError("只有失败、取消或中断的全流程可以继续")
        engine.ensure_workspace_available(project)
        update_pipeline(project_id, status="running", error=None)
        try:
            stage = next((item for item in project["stages"] if item["status"] != "completed"), None)
            if stage and stage.get("run_id"):
                run = engine.load("runs", stage["run_id"])
                if run["status"] in {"failed", "interrupted", "cancelled"}:
                    engine.resume_run(run["id"], pipeline_id=pipeline["id"])
            launch(project_id)
        except Exception:
            update_pipeline(project_id, status=pipeline["status"])
            raise
        return engine.get_project(project_id)


def _find_answer_submission(submission: dict | None) -> dict | None:
    """按调用方查持久答复记录；跨运行复用同一标识也必须拒绝改参数。"""
    if submission is None:
        return None
    for path in (engine.STORE / "runs").glob("*.json"):
        record = engine.load("runs", path.stem)
        for previous in record.get("answer_submissions", []):
            if (previous.get("scope"), previous.get("request_id")) != (submission["scope"], submission["request_id"]):
                continue
            if previous.get("sha256") != submission["sha256"]:
                raise ValueError("request_id 已用于不同参数；请为新答复生成新的标识")
            return record
    return None


def answer_run(run_id: str, answers: dict[str, str], *, request_id: str | None = None,
               request_scope: str = "rest") -> dict:
    """按问题 ID 提交全部回答；网络重试返回原运行，不重复写入回答或恢复检查点。"""
    if not isinstance(answers, dict) or not 1 <= len(answers) <= 100:
        raise ValueError("一次须提交 1 至 100 项回答")
    if any(not isinstance(key, str) or not key or not isinstance(value, str)
           or not value.strip() or len(value) > 12000 for key, value in answers.items()):
        raise ValueError("问题 ID 和回答不能为空，回答须为文本且每项最多 12000 字")
    submission = describe_submission(request_id, request_scope, {"run_id": run_id, "answers": answers})
    with engine.LOCK:
        run = engine.load("runs", run_id)
        previous = _find_answer_submission(submission)
        if previous is not None:
            return previous
        project = engine.load("projects", run["project_id"])
        stage = next(item for item in project["stages"] if item["id"] == run["stage"])
        if run["status"] != "awaiting_input" or stage["run_id"] != run_id:
            raise ValueError("该运行当前没有待回答的问题，或已被新运行取代")
        if run.get("pipeline_id") and project.get("pipeline", {}).get("status") != "awaiting_input":
            raise ValueError("全流程正在同步中断状态，请稍后提交回答")
        questions = run.get("interrupts", [])
        if not questions or set(answers) != {item["id"] for item in questions}:
            raise ValueError("请回答当前全部问题；问题已变化时先刷新页面")
        engine.verify_confirmed_dependencies(project, run["stage"])
        engine.ensure_workspace_available(project, exclude_run=run_id)
        # 同一回答留在项目上下文中，后续阶段也能看到用户的决定。
        project.setdefault("human_answers", []).extend(
            {"run_id": run_id, "id": item["id"], "question": item["value"], "answer": answers[item["id"]]}
            for item in questions)
        engine.save("projects", project)
        # 去重摘要与排队状态写入同一运行记录；重试不以客户端连接是否仍存在为依据。
        submissions = run.get("answer_submissions", []) + ([submission] if submission else [])
        engine.set_status(run_id, "queued", pending_answers=answers, error=None, answer_submissions=submissions)
        engine.event(run_id, "human_input_answered", "用户已补充，准备从原检查点继续", {"answers": answers})
        engine.WORKERS[run_id] = asyncio.create_task(engine.execute_run(run_id, resume=True))
        if run.get("pipeline_id"):
            update_pipeline(project["id"], status="running", error=None)
            launch(project["id"])
        return engine.load("runs", run_id)


async def cancel_pipeline(project_id: str) -> dict:
    project = engine.load("projects", project_id)
    if project.get("pipeline", {}).get("status") not in OWNED:
        raise ValueError("当前全流程没有可取消的任务")
    update_pipeline(project_id, status="cancelled", error="用户取消了全流程")
    task = PIPELINES.get(project_id)
    if task:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    for run in engine.project_runs(project_id):
        if run["status"] in engine.ACTIVE | {"awaiting_input"}:
            await engine.cancel_run(run["id"])
    return engine.get_project(project_id)


def recover_pipelines() -> None:
    """重启后保留人工问题；其他未完成计划显式等待继续，不重新计费启动。"""
    for project in engine.list_projects():
        if project.get("pipeline", {}).get("status") == "running":
            run_id = project["pipeline"].get("run_id")
            run = engine.load("runs", run_id) if run_id else {}
            status = "awaiting_input" if run.get("status") == "awaiting_input" else "interrupted"
            update_pipeline(project["id"], status=status, error=None if status == "awaiting_input" else "服务重启，点击继续全流程恢复")


async def shutdown_pipelines() -> None:
    tasks = list(PIPELINES.items())
    for _, task in tasks:
        task.cancel()
    await asyncio.gather(*(task for _, task in tasks), return_exceptions=True)
    for project_id, _ in tasks:
        update_pipeline(project_id, status="interrupted", error="服务关闭，等待继续全流程")
