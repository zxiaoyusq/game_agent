"""研发 Agent - Demo 生成业务核心。

本文件不感知 HTTP/SSE，只暴露两个 async generator：
- stream_plan(req)：阶段 1，流式生成可执行 Plan
- stream_generate(req)：阶段 2，按已确认 Plan 逐步生成 H5 代码工程并落盘

知识库读取 + vision 注入 + 流式拆包统一走 services/kb_context，
本文件只关心提示词内容、JSON 解析与代码落盘。

落盘策略：
- 阶段 2 流式生成时，artifact 一旦解析完成立即写入 data/dev_demo/<task_id>/<path>
- 路径校验：禁止绝对路径与 .. 越权
"""

from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from app.config import DEV_DEMO_DIR
from app.models.dev_demo import DemoArtifact, DemoGenerateReq, DemoPlanReq, PlanStep
from app.providers import get_chat_model
from app.services.kb_context import build_messages, extract_text, resolve_kb

logger = logging.getLogger(__name__)


# ---- 提示词 -----------------------------------------------------------------

# 阶段 1：把需求拆解为可执行 Plan
PLAN_SYSTEM_PROMPT = """你是一名资深 H5 游戏研发专家，擅长把模糊的玩法描述拆解为最小可运行 Demo 的工程任务。
请基于用户给出的需求 + 模板 + 引擎 + 知识库参考，输出一份用于驱动后续代码生成的 Plan。

要求：
1. 步骤数量 4~7 步，每步可独立产出 1~3 个文件
2. 每步必须包含 title（短）和 desc（≤80 字，明确该步要产出什么）
3. 步骤之间存在合理的依赖顺序：先骨架/入口 → 核心玩法 → 配置数据 → UI/资源
4. 严格输出 JSON，禁止 markdown 包裹。格式：
   {"steps":[{"title":"...","desc":"..."},...]}"""

# 阶段 2：按单步 Plan 生成 1~3 个文件
GENERATE_SYSTEM_PROMPT = """你是一名 H5 游戏研发工程师。当前任务已被拆解为一份 Plan，本轮请只完成其中「当前步骤」。
工程类型：纯前端 H5 游戏（HTML + JS + CSS，无构建工具，浏览器可直接打开 index.html 运行）。

要求：
1. 严格只产出与「当前步骤」相关的文件（1~3 个），不要重复别的步骤
2. 路径使用工程内相对路径，禁止以 / 或 ../ 开头。常见目录：
   - index.html         入口
   - src/main.js        主入口脚本
   - src/game/*.js      玩法脚本
   - src/config/*.json  配置数据
   - assets/css/*.css   样式
   - assets/img/*       图片占位（type=asset 时只给说明）
3. type 只允许 script / config / asset 三类：
   - script：所有需要被工程加载执行的源码，包含 .html / .js / .ts / .css（CSS 也算 script）
   - config：纯数据 / 配置文件，例如 .json / .csv / .yaml
   - asset：图片 / 音频等二进制占位资源，content 留空字符串
   script 与 config 必须给完整可运行 content；asset 仅给说明性 desc
4. 严格输出 JSON：
   {"artifacts":[{"type":"script|config|asset","path":"...","desc":"...","content":"..."}]}"""


# ---- 入口：阶段 1 -----------------------------------------------------------

async def stream_plan(req: DemoPlanReq) -> AsyncIterator[Dict[str, Any]]:
    """阶段 1：流式生成 Plan。

    Yields:
        - {"type":"thinking","text":"..."} —— 每个 token 增量
        - {"type":"plan","steps":[...]}    —— 整段流结束后解析出的 plan
        - {"type":"error","message":"..."} —— 解析失败时
    """
    # 1) 构造上下文（公共方法已处理 vision provider 判定）
    kb = resolve_kb(req.kb_refs)
    user_text = _build_plan_user_text(req, kb.text)
    messages = build_messages(
        system=PLAN_SYSTEM_PROMPT,
        user_text=user_text,
        kb=kb,
        model_id=req.model_id,
    )

    # 2) 调用模型并流式拆包
    model = get_chat_model(req.model_id, temperature=0.3)
    full_text = ""
    async for chunk in model.astream(messages):
        delta = extract_text(chunk)
        if delta:
            full_text += delta
            yield {"type": "thinking", "text": delta}

    # 3) 解析 plan
    parsed = _parse_json_block(full_text)
    if not parsed or "steps" not in parsed or not isinstance(parsed["steps"], list):
        yield {
            "type": "error",
            "message": "Plan 解析失败：模型未按 JSON 格式返回 steps 字段",
        }
        return

    steps_clean: List[Dict[str, str]] = []
    for s in parsed["steps"]:
        if not isinstance(s, dict):
            continue
        title = str(s.get("title", "")).strip()
        desc = str(s.get("desc", "")).strip()
        if title and desc:
            steps_clean.append({"title": title, "desc": desc})
    if not steps_clean:
        yield {"type": "error", "message": "Plan 解析失败：steps 为空或缺字段"}
        return

    yield {"type": "plan", "steps": steps_clean}


# ---- 入口：阶段 2 -----------------------------------------------------------

async def stream_generate(req: DemoGenerateReq) -> AsyncIterator[Dict[str, Any]]:
    """阶段 2：按 plan 逐步生成代码并落盘。

    Yields:
        - {"type":"step_start","index":i}
        - {"type":"step_thinking","index":i,"text":"..."}
        - {"type":"step_artifact","index":i,"artifact":{...}}
        - {"type":"step_done","index":i}
        - {"type":"step_error","index":i,"message":"..."}
        - 每个步骤之间不会因单步失败而中断；整流末尾由 route 层补 done
    """
    # 0) 工程根目录（每个任务一个）
    project_root = _ensure_project_root(req.task_id)

    # 1) 解析知识库（plan 阶段已组装过，但 generate 每步都会用到，这里也准备一份）
    kb = resolve_kb(req.kb_refs)

    # 2) 整体 plan 上下文（让模型知道当前步骤在整体中的位置）
    plan_overview = _format_plan_overview(req.plan)

    # 3) 逐步生成
    for i, step in enumerate(req.plan):
        yield {"type": "step_start", "index": i}

        try:
            # 每步独立调一次模型；错误捕获让单步失败不阻塞后续步骤
            user_text = _build_generate_user_text(
                req=req,
                kb_text=kb.text,
                plan_overview=plan_overview,
                step=step,
                step_index=i,
            )
            messages = build_messages(
                system=GENERATE_SYSTEM_PROMPT,
                user_text=user_text,
                kb=kb,
                model_id=req.model_id,
            )
            model = get_chat_model(req.model_id, temperature=0.2)

            full_text = ""
            async for chunk in model.astream(messages):
                delta = extract_text(chunk)
                if delta:
                    full_text += delta
                    yield {"type": "step_thinking", "index": i, "text": delta}

            parsed = _parse_json_block(full_text)
            if not parsed or "artifacts" not in parsed or not isinstance(parsed["artifacts"], list):
                yield {
                    "type": "step_error",
                    "index": i,
                    "message": "本步骤解析失败：模型未按 JSON 格式返回 artifacts",
                }
                continue

            # 4) 逐 artifact 落盘 + 推送
            for raw in parsed["artifacts"]:
                if not isinstance(raw, dict):
                    continue
                try:
                    art = _normalize_artifact(raw)
                except ValueError as ve:
                    yield {
                        "type": "step_error",
                        "index": i,
                        "message": f"产物字段校验失败：{ve}",
                    }
                    continue

                # 写盘：script/config 真写文本；asset 不写文件，仅返回路径占位
                if art.type in ("script", "config") and art.content is not None:
                    try:
                        _write_artifact(project_root, art.path, art.content)
                    except ValueError as we:
                        yield {
                            "type": "step_error",
                            "index": i,
                            "message": f"落盘失败：{we}",
                        }
                        continue

                yield {
                    "type": "step_artifact",
                    "index": i,
                    "artifact": art.model_dump(),
                }

            yield {"type": "step_done", "index": i}

        except Exception as e:
            logger.exception("dev_demo step %s failed", i)
            yield {
                "type": "step_error",
                "index": i,
                "message": f"{type(e).__name__}: {e}",
            }
            # 继续下一步，不中断整流


# ---- 工程目录管理 ---------------------------------------------------------

# task_id 仅允许字母/数字/下划线/连字符，避免目录穿越
_TASK_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def _ensure_project_root(task_id: str) -> Path:
    """返回该任务的工程根目录；首次写入前会清空旧文件，确保重新生成是干净的。"""
    if not _TASK_ID_RE.match(task_id or ""):
        raise ValueError(f"非法 task_id：{task_id}")
    root = DEV_DEMO_DIR / task_id
    # 先整体清掉再重建：「重新生成 Demo」语义就是清空重写
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_artifact(root: Path, rel_path: str, content: str) -> None:
    """把单个 artifact 文本写入 root/rel_path，做安全性校验。"""
    rel = (rel_path or "").strip().lstrip("/").lstrip("\\")
    if not rel:
        raise ValueError("path 不能为空")
    if ".." in Path(rel).parts:
        raise ValueError(f"path 含 ..：{rel_path}")
    target = (root / rel).resolve()
    # 必须落在 root 之内
    if root.resolve() not in target.parents and target != root.resolve():
        raise ValueError(f"path 越权：{rel_path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


# ---- 提示词文本构造 --------------------------------------------------------

def _build_plan_user_text(req: DemoPlanReq, kb_text: str) -> str:
    """组装阶段 1 的 human 文本。"""
    return (
        f"【需求】\n{req.requirement.strip()}\n\n"
        f"【模板】{req.template or '未指定'}\n"
        f"【引擎】{req.engine or 'H5（HTML/JS/CSS，无构建工具）'}\n\n"
        f"【知识库参考】\n{kb_text or '（本次未引用知识库）'}\n\n"
        "请按系统提示中的 JSON 格式输出 Plan，不要任何额外文字。"
    )


def _build_generate_user_text(
    *,
    req: DemoGenerateReq,
    kb_text: str,
    plan_overview: str,
    step: PlanStep,
    step_index: int,
) -> str:
    """组装阶段 2 单步的 human 文本。"""
    return (
        f"【整体需求】\n{req.requirement.strip()}\n\n"
        f"【模板】{req.template or '未指定'}\n"
        f"【引擎】{req.engine or 'H5'}\n\n"
        f"【整体 Plan 概览】\n{plan_overview}\n\n"
        f"【当前步骤 #{step_index + 1}】\n标题：{step.title}\n说明：{step.desc}\n\n"
        f"【知识库参考】\n{kb_text or '（无）'}\n\n"
        "请只完成「当前步骤」，按系统提示的 JSON 格式输出 artifacts，不要任何额外文字。"
    )


def _format_plan_overview(plan: List[PlanStep]) -> str:
    return "\n".join(f"{i + 1}. {s.title} — {s.desc}" for i, s in enumerate(plan))


# ---- 工具：从 LLM 返回中找 JSON --------------------------------------------

# 优先匹配 ```json ... ```；找不到再退到第一个 { ... } 的最大块
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def _parse_json_block(text: str) -> Optional[dict]:
    """从模型输出中提取首个 JSON 对象，失败返回 None。"""
    if not text:
        return None
    # 1) 围栏代码块
    m = _JSON_FENCE_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 2) 直接试整段
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    # 3) 取第一个 { 到最后一个 } 的最大段
    lo = text.find("{")
    hi = text.rfind("}")
    if lo != -1 and hi != -1 and hi > lo:
        candidate = text[lo : hi + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return None


def _normalize_artifact(raw: dict) -> DemoArtifact:
    """把模型返回的 artifact dict 适配到 DemoArtifact。"""
    art_type = str(raw.get("type", "")).strip().lower()
    if art_type not in {"script", "config", "asset"}:
        raise ValueError(f"非法 type：{art_type!r}")
    path = str(raw.get("path", "")).strip()
    if not path:
        raise ValueError("path 缺失")
    desc = str(raw.get("desc", "")).strip()
    content = raw.get("content")
    if content is not None and not isinstance(content, str):
        # 模型偶尔会塞 dict / list 进来，此处统一字符串化兜底
        content = json.dumps(content, ensure_ascii=False, indent=2)
    return DemoArtifact(type=art_type, path=path, desc=desc, content=content)
