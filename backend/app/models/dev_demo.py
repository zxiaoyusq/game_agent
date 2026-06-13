"""研发 Agent - Demo 生成相关 Pydantic 模型。

两阶段：
- 阶段 1：plan —— 输入需求 + 模板/引擎 + 知识库引用，返回拆解后的 Plan 步骤
- 阶段 2：generate —— 在 plan 已确认的前提下，逐步生成代码工程产物（H5 游戏）
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """Plan 中的单个步骤。"""

    title: str = Field(..., description="步骤标题，简短可读")
    desc: str = Field(..., description="步骤说明，控制在 80 字内")


class DemoPlanReq(BaseModel):
    """阶段 1 请求体：根据需求生成 Plan。"""

    # task_id 在阶段 2 必填，用于决定落盘目录；阶段 1 只为关联日志，可选
    task_id: Optional[str] = Field(None, description="前端任务 id，用于关联落盘目录")
    model_id: str = Field(..., description="必传，前端选择的模型 id")
    requirement: str = Field(..., min_length=1, description="需求描述")
    template: Optional[str] = Field(None, description="模板，例如 '2D 卡牌 + 回合制'")
    engine: Optional[str] = Field(None, description="引擎，本期 Demo 固定 H5 工程")
    # 三段式 key 列表：module:category:itemId
    kb_refs: List[str] = Field(default_factory=list, description="知识库引用 key 数组")


class DemoArtifact(BaseModel):
    """阶段 2 产物。"""

    type: Literal["script", "config", "asset"] = Field(..., description="产物类型")
    # 工程内相对路径，例如 'src/game/main.js'，禁止以 / 开头或包含 ..
    path: str = Field(..., description="工程内相对路径")
    desc: str = Field(default="", description="简短说明")
    # script/config 提供文本；asset 仅占位说明
    content: Optional[str] = Field(None, description="文件文本内容（仅 script/config）")


class DemoGenerateReq(DemoPlanReq):
    """阶段 2 请求体：plan 由前端确认后回传。"""

    # task_id 在阶段 2 必填（落盘目录键）
    task_id: str = Field(..., min_length=1, description="任务 id，用于落盘目录")
    plan: List[PlanStep] = Field(..., min_length=1, description="用户确认后的 plan 步骤")
