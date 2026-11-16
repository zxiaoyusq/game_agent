"""远程项目操作的持久去重；复用工作流，不直接改写阶段完成或校验结果。"""

from app.services.workflow import engine, pipeline
from app.services.workflow.submissions import describe_submission


def _previous_operation(submission: dict) -> bool:
    """同一客户端重试返回当前项目；换目标或参数必须使用新的请求标识。"""
    # 这里只读取操作收据，不计算其他项目的实时预览或构建指纹。
    for path in (engine.STORE / "projects").glob("*.json"):
        project = engine.load("projects", path.stem)
        for previous in project.get("remote_operations", []):
            if (previous.get("scope"), previous.get("request_id")) != (submission["scope"], submission["request_id"]):
                continue
            if previous.get("sha256") != submission["sha256"]:
                raise ValueError("request_id 已用于不同参数；请为新请求生成新的标识")
            return True
    return False


async def perform_project_action(project_id: str, operation: str, request_id: str, scope: str,
                                 **parameters) -> dict:
    """由 MCP 应用的异步锁串行调用，取消时不持有跨 await 的线程锁。

    成功标识随项目保存，普通断线及服务重启不会重复调度已成功的操作。
    权限由入口每次重新检查；参数摘要绑定具体操作和目标项目。
    """
    submission = describe_submission(request_id, scope, {"operation": operation, "project_id": project_id, **parameters})
    with engine.LOCK:
        project = engine.load("projects", project_id)
        if _previous_operation(submission):
            return engine.get_project(project_id)
        if operation == "start_pipeline":
            pipeline.start_pipeline(project_id)
        elif operation == "resume_pipeline":
            pipeline.resume_pipeline(project_id)
        elif operation == "confirm_stage":
            stage = next(item for item in project["stages"] if item["id"] == parameters["stage"])
            if stage.get("run_id") != parameters["run_id"]:
                raise ValueError("确认目标已被新的运行取代，请重新读取项目与产物")
            engine.confirm_stage(project_id, parameters["stage"], parameters.get("note", ""))
        elif operation == "publish_project":
            engine.publish_project(project_id, parameters["slug"])
        elif operation != "cancel_pipeline":
            raise ValueError("未知的远程项目操作")

    if operation == "cancel_pipeline":
        state = project.get("pipeline", {}).get("status")
        if state in pipeline.OWNED:
            await pipeline.cancel_pipeline(project_id)
        elif state not in {"cancelled", "completed"}:
            raise ValueError("当前没有可取消的全流程")

    with engine.LOCK:
        project = engine.load("projects", project_id)
        project.setdefault("remote_operations", []).append({**submission, "operation": operation})
        engine.save("projects", project)
        return engine.get_project(project_id)
