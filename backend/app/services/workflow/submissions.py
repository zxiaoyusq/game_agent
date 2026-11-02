"""提交去重：把请求身份随业务记录保存，避免额外索引与记录不一致。"""

import hashlib
import json
import re
from pathlib import Path


def describe_submission(request_id: str | None, scope: str, payload: dict) -> dict | None:
    """同一调用方的同一请求只能对应同一组参数；旧调用不传标识时保持原行为。"""
    if request_id is None:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", request_id):
        raise ValueError("request_id 须为 1 至 128 位字母、数字或 _ . : -")
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"request_id": request_id, "scope": scope, "sha256": hashlib.sha256(encoded.encode()).hexdigest()}


def find_submission(directory: Path, submission: dict | None) -> dict | None:
    """在引擎锁内查询持久记录；重启后重试仍返回原记录，不重新调度任务。"""
    if submission is None:
        return None
    for path in directory.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        previous = record.get("submission") or {}
        if (previous.get("scope"), previous.get("request_id")) != (submission["scope"], submission["request_id"]):
            continue
        if previous.get("sha256") != submission["sha256"]:
            raise ValueError("request_id 已用于不同参数；请为新请求生成新的标识")
        return record
    return None
