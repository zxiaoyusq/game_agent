"""自主决策开关、工具语义与旧运行兼容；不调用真实模型服务。"""

import json
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app.services.workflow import human_input
from app.services.workflow.activity import activity_run
from app.services.workflow.prompts import build_run_prompts
from app.services.workflow.templates import ProductionPlan


def plan(**fields):
    """只提供必要的四阶段配置，旧调用不携带自主决策字段。"""
    return {"stages": {stage: {"prompt": "完成本阶段"} for stage in ("prototype", "art", "code", "test")}, **fields}


class WorkflowAutonomyTests(unittest.TestCase):
    def test_autonomous_defaults_off_and_requires_a_real_boolean(self):
        self.assertIs(ProductionPlan.model_validate(plan()).autonomous, False)
        self.assertIs(ProductionPlan.model_validate(plan(autonomous=True)).model_dump()["autonomous"], True)
        for value in ["true", "false", 1, 0, None, [], {}]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ProductionPlan.model_validate(plan(autonomous=value))

    def test_old_or_manual_tool_keeps_real_human_interrupt(self):
        for run in [{}, {"autonomous": False}]:
            events = []
            tool = human_input.create_user_input_tool(run, lambda *args: events.append(args))
            with patch.object(human_input, "interrupt", return_value="用户选择的蓝色") as interrupt:
                result = tool.invoke({"question": "选择棋盘配色", "options": ["紫色", "蓝色"]})
            interrupt.assert_called_once()
            self.assertEqual(json.loads(result)["用户补充"], "用户选择的蓝色")
            self.assertEqual(events, [])

    def test_autonomous_tool_records_model_choice_and_reason_without_human_answer(self):
        events = []
        tool = human_input.create_user_input_tool({"autonomous": True}, lambda *args: events.append(args))
        with patch.object(human_input, "interrupt", side_effect=AssertionError("自主模式不可触发人工中断")) as interrupt:
            result = tool.invoke({"question": "选择棋盘配色", "context": "用户要求冷色棋盘", "options": ["紫色", "蓝色"],
                                  "decision": "蓝色", "reason": "蓝色符合用户指定的冷色主题，保留棋子对比度。"})
        interrupt.assert_not_called()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], "autonomous_decision")
        decision = events[0][2]
        self.assertEqual(decision["question"], "选择棋盘配色")
        self.assertEqual(decision["decision"], "蓝色")
        self.assertIn("冷色主题", decision["reason"])
        self.assertIn("蓝色", result)
        self.assertNotIn("用户补充", json.loads(result), "AI 的选择不能冒充用户提供的回答")

    def test_missing_decision_or_reason_does_not_fabricate_an_answer(self):
        for fields in [{}, {"decision": "蓝色"}, {"reason": "符合需求"}, {"decision": " ", "reason": "符合需求"}]:
            with self.subTest(fields=fields):
                events = []
                tool = human_input.create_user_input_tool({"autonomous": True}, lambda *args: events.append(args))
                with patch.object(human_input, "interrupt") as interrupt:
                    result = tool.invoke({"question": "选择棋盘配色", "options": ["紫色", "蓝色"], **fields})
                interrupt.assert_not_called()
                self.assertEqual(events, [], "缺少模型决策时只能返回补全指引，不能自动选择候选项")
                self.assertEqual(json.loads(result)["status"], "decision_required")

    def test_autonomous_tool_rejects_empty_question_before_recording(self):
        events = []
        tool = human_input.create_user_input_tool({"autonomous": True}, lambda *args: events.append(args))
        with self.assertRaises(ValueError):
            tool.invoke({"question": " ", "decision": "蓝色", "reason": "符合需求"})
        self.assertEqual(events, [])

    def test_prompt_uses_frozen_run_mode_instead_of_changed_project_mode(self):
        base = {"stage": "prototype", "prompt": "制作棋盘游戏", "skill_paths": []}
        manual, _ = build_run_prompts(base, {"production_plan": {"autonomous": True}})
        self.assertIn("必须调用request_user_input暂停询问", manual)
        self.assertNotIn("decision", manual)
        autonomous, _ = build_run_prompts({**base, "autonomous": True}, {"production_plan": {"autonomous": False}})
        self.assertNotIn("必须调用request_user_input暂停询问", autonomous)
        self.assertIn("自主", autonomous)
        self.assertIn("decision", autonomous)
        self.assertIn("reason", autonomous)

    def test_activity_and_prompt_keep_ai_decision_provenance(self):
        decision = {"question": "选择棋盘配色", "context": "用户指定蓝色", "options": ["紫色", "蓝色"],
                    "decision": "蓝色", "reason": "遵从项目主题需求", "source": "ai"}
        run = {"stage": "art", "prompt": "制作蓝色主题美术", "skill_paths": [], "autonomous": True,
               "upstream_decisions": [{"stage": "prototype", **decision}], "events": [
                   {"seq": 1, "time": "2026-11-10T00:00:00Z", "type": "autonomous_decision",
                    "message": "AI 已自主决策", "data": {**decision, "internal_payload": "不应展示"}}]}
        activity = activity_run(run)
        self.assertIs(activity["autonomous"], True)
        self.assertEqual(activity["events"][0]["data"], decision)
        _, context = build_run_prompts(run, {"production_plan": {"autonomous": True}})
        self.assertEqual(json.loads(context)["upstream_decisions"], run["upstream_decisions"])
