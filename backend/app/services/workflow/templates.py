"""可导入的生产模板：只保存需求与配置，不包含密钥、工作区或执行状态。"""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

STAGE_IDS = ("prototype", "art", "code", "test")


class StagePlan(BaseModel):
    """每阶段的预置输入，创建时一次保存，执行时仍冻结实际 Skill 正文。"""

    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=6000)
    skill_mode: Literal["auto", "manual"] = "auto"
    skill_paths: list[str] = Field(default_factory=list, max_length=50)


class ProductionPlan(BaseModel):
    """用户确认前的完整执行计划；发布权限随计划一起明确保存。"""

    model_config = ConfigDict(extra="forbid")
    template_id: str = Field(default="custom", max_length=120)
    art_requirements: str = Field(default="", max_length=12000)
    stages: dict[Literal["prototype", "art", "code", "test"], StagePlan]
    # 自主决策须由用户明确开启；旧项目和旧模板继续采用人工补充。
    autonomous: StrictBool = False
    auto_publish: bool = True
    publish_slug: str = Field(default="", pattern=r"^(?:[a-z0-9][a-z0-9-]{1,62}[a-z0-9])?$")

    @model_validator(mode="after")
    def complete_stages(self):
        if set(self.stages) != set(STAGE_IDS):
            raise ValueError("模板必须包含原型、美术、代码、测试四阶段配置")
        return self


class WorkflowTemplate(BaseModel):
    """版本化 JSON 交换格式；严格拒绝运行命令、密钥等额外字段。"""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    brief: dict[str, str]
    genre_id: str = "general"
    framework_id: str = "canvas-web"
    model_provider: Literal["api-key", "codex-login"] = "api-key"
    model_id: str = "gpt-6.1-sol"
    references: list[str] = Field(default_factory=list, max_length=100)
    knowledge_paths: list[str] = Field(default_factory=list, max_length=100)
    production_plan: ProductionPlan

    @model_validator(mode="after")
    def limit_brief(self):
        allowed = {"name", "genre", "platform", "engine", "audience", "cycle", "idea", "scope"}
        if set(self.brief) - allowed or any(len(value) > 12000 for value in self.brief.values()):
            raise ValueError("简报包含未知字段或单项内容超过 12000 字")
        return self


def list_templates() -> list[dict]:
    """模板随工程版本发布，读取时校验，不依赖浏览器写死的重复提示词。"""
    directory = Path(__file__).resolve().parents[4] / "resources" / "workflow-templates"
    return [WorkflowTemplate.model_validate(json.loads(path.read_text(encoding="utf-8"))).model_dump()
            for path in sorted(directory.glob("*.json"))]
