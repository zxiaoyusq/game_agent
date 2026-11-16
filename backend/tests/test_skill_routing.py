"""Skill 路由回归：配置矩阵、任务意图、人工控制与实际工具边界。"""

import copy
import unittest

from app.services import production_library
from app.services.workflow import skill_routing as routing


class SkillRoutingTests(unittest.TestCase):
    def setUp(self):
        paths = [routing.GENERAL, routing.COCOS, routing.ART, routing.ART_STYLE, routing.IMAGE,
                 routing.COMPETITOR, routing.H5_RESKIN, routing.SKINNING, routing.CREATOR, routing.HARVEST,
                 "gpt52-vision-router/SKILL.md", "custom/SKILL.md"]
        self.skills = [{"path": path, "name": path.split("/")[-2], "sha256": "fixture"} for path in paths]

    def project(self, genre="general", framework="canvas-web", brief="制作新的休闲游戏"):
        return {"production_profile": production_library.resolve_profile(genre, framework), "brief": brief,
                "references": ["公司skill整合/AHAgames/82251_Just_Ludo/gameInfo.json"]}

    def plan(self, project=None, stage="prototype", prompt="", **kwargs):
        return routing.plan_skill_selection(project or self.project(), stage, prompt, self.skills, **kwargs)

    def test_all_genres_frameworks_four_stages_use_actual_profile(self):
        """逐品类知识决定玩法差异，不把排序或 Creator 工程要求强加给所有游戏。"""
        for genre in production_library.GENRES:
            for framework in production_library.FRAMEWORKS:
                for stage in routing.STAGES:
                    with self.subTest(genre=genre["id"], framework=framework["id"], stage=stage):
                        project = self.project(genre["id"], framework["id"])
                        result = self.plan(project, stage)
                        expected = {routing.GENERAL}
                        if stage == "art":
                            expected.update([routing.ART, routing.ART_STYLE])
                        if framework["id"] == "cocos-web":
                            expected.add(routing.COCOS)
                        self.assertEqual(set(result["selected_paths"]), expected)
                        self.assertEqual(result["context"]["genre_id"], genre["id"])
                        self.assertIn(f"genre/docs/{genre['id']}.md", result["context"]["knowledge_paths"])
                        self.assertTrue(all(item["reason"] for item in result["items"]))

    def test_canvas_reskin_is_limited_to_relevant_stages_and_framework(self):
        for stage in routing.STAGES:
            canvas = self.plan(self.project(brief="按已有原包做美术换皮"), stage)
            cocos = self.plan(self.project(framework="cocos-web", brief="按已有原包做美术换皮"), stage)
            self.assertIn(routing.H5_RESKIN, canvas["selected_paths"])
            self.assertNotIn(routing.H5_RESKIN, cocos["selected_paths"])
            self.assertEqual(routing.SKINNING in cocos["selected_paths"], stage != "prototype")

    def test_reskin_direction_is_available_from_prototype_with_stage_specific_resources(self):
        """无效果图的换皮需求在立项即可用，后续阶段读取各自资料而非重复问卷。"""
        for framework in ["canvas-web", "native-web"]:
            project = self.project(framework=framework, brief="给现有游戏换皮，风格方向还没定")
            for stage in routing.STAGES:
                plan = self.plan(project, stage)
                entry = next(item for item in plan["items"] if item["path"] == routing.H5_RESKIN)
                self.assertEqual(entry["usage"], "workflow")
                self.assertTrue(entry["resource_paths"])
                if stage == "prototype":
                    self.assertIn(routing.ART_STYLE, plan["selected_paths"])
                    self.assertTrue(any(path.endswith("intake-and-direction.md") for path in entry["resource_paths"]))
                else:
                    self.assertFalse(any(path.endswith("intake-and-direction.md") for path in entry["resource_paths"]))

    def test_existing_h5_restoration_uses_workflow_without_requesting_harvest(self):
        for prompt in ["对已有 H5 原版还原并持续迭代", "保留原码进行二次开发", "还原现有H5游戏", "restore existing H5"]:
            for stage in routing.STAGES:
                plan = self.plan(stage=stage, prompt=prompt)
                entry = next(item for item in plan["items"] if item["path"] == routing.HARVEST)
                self.assertEqual(entry["usage"], "workflow")
                self.assertFalse(any("harvest-pipeline" in path for path in entry["resource_paths"]))
                self.assertTrue(any("不重复采集" in warning for warning in plan["warnings"]))
        self.assertNotIn(routing.HARVEST, self.plan(prompt="仅参考原版，不需要原版还原")["selected_paths"])

    def test_package_optimization_respects_framework_stage_and_current_negation(self):
        for framework in ["canvas-web", "native-web"]:
            project = self.project(framework=framework, brief="对现有 H5 进行包体优化和加载优化")
            for stage in ["prototype", "code", "test"]:
                plan = self.plan(project, stage)
                item = next(item for item in plan["items"] if item["path"] == routing.HARVEST)
                self.assertEqual(item["usage"], "workflow")
                self.assertTrue(any(path.endswith("h5-package-runtime-optimization.md") for path in item["resource_paths"]))
            self.assertNotIn(routing.HARVEST, self.plan(project, "art")["selected_paths"])
            self.assertNotIn(routing.HARVEST, self.plan(project, "code", "本轮不做包体优化，也不需要加载优化")["selected_paths"])
        self.assertNotIn(routing.HARVEST, self.plan(self.project(framework="cocos-web"), "code", "包体优化")["selected_paths"])

    def test_new_routes_still_respect_manual_choices_and_exclusions(self):
        project = self.project(brief="现有 H5 原版还原、包体优化并换皮")
        plan = self.plan(project, "prototype", exclude_paths=[routing.HARVEST, routing.H5_RESKIN])
        self.assertNotIn(routing.HARVEST, plan["selected_paths"])
        self.assertNotIn(routing.H5_RESKIN, plan["selected_paths"])
        self.assertEqual(self.plan(project, mode="manual")["selected_paths"], [])

    def test_current_request_can_negate_old_brief_intent(self):
        project = self.project(brief="制作 AI 生图方案并完成换皮")
        for prompt in ["无需生图，不需要换皮，仅整理清单", "不要换皮，不用生图", "换皮不需要，生图暂不执行", "不换皮，不生图"]:
            with self.subTest(prompt=prompt):
                result = self.plan(project, "art", prompt)
                self.assertNotIn(routing.H5_RESKIN, result["selected_paths"])
                self.assertNotIn(routing.IMAGE, result["selected_paths"])
        result = self.plan(project, "art", "不要修改玩法，只做美术换皮")
        self.assertIn(routing.H5_RESKIN, result["selected_paths"])

    def test_generation_requires_art_intent_and_checks_configured_tool(self):
        result = self.plan(stage="art", prompt="为方块游戏生成图片")
        self.assertIn(routing.IMAGE, result["selected_paths"])
        item = next(item for item in result["items"] if item["path"] == routing.IMAGE)
        self.assertEqual(item["usage"], "workflow")
        self.assertTrue(any("generate_art_image" in warning and "未配置" in warning for warning in result["warnings"]))
        self.assertNotIn(routing.IMAGE, self.plan(stage="code", prompt="生成图片")['selected_paths'])

    def test_explicit_transparency_reference_edits_and_locked_reskin_route_image_guidance(self):
        """只识别明确制作任务，不把已有透明素材或被否定的制作需求当生图授权。"""
        for prompt in ["制作透明素材", "生成真透明贴图", "参考图编辑", "编辑参考图", "结构锁定换皮"]:
            with self.subTest(prompt=prompt):
                self.assertIn(routing.IMAGE, self.plan(stage="art", prompt=prompt)["selected_paths"])
                self.assertNotIn(routing.IMAGE, self.plan(stage="code", prompt=prompt)["selected_paths"])
                self.assertNotIn(routing.IMAGE, self.plan(stage="art", prompt="不需要" + prompt)["selected_paths"])
        self.assertNotIn(routing.IMAGE, self.plan(stage="art", prompt="整理已有透明素材")["selected_paths"])

    def test_existing_aha_reference_does_not_request_harvest_or_competitor_research(self):
        ordinary = self.plan()
        self.assertNotIn(routing.HARVEST, ordinary["selected_paths"])
        self.assertNotIn(routing.COMPETITOR, ordinary["selected_paths"])
        research = self.plan(prompt="根据本地资料进行竞品分析，并采集托管小游戏原包")
        self.assertIn(routing.HARVEST, research["selected_paths"])
        self.assertIn(routing.COMPETITOR, research["selected_paths"])
        self.assertTrue(any("没有联网检索工具" in warning for warning in research["warnings"]))
        self.assertTrue(any("不会执行采集" in warning for warning in research["warnings"]))
        self.assertNotIn(routing.HARVEST, self.plan(stage="art", prompt="采集托管小游戏原包")["selected_paths"])
        self.assertNotIn(routing.HARVEST, self.plan(prompt="不用下载小游戏")["selected_paths"])

    def test_creator_is_only_selected_for_explicit_review_and_remains_reference(self):
        project = self.project(framework="cocos-web")
        self.assertNotIn(routing.CREATOR, self.plan(project, "code")["selected_paths"])
        self.assertNotIn(routing.CREATOR, self.plan(project, "code", "使用 Cocos Creator")["selected_paths"])
        result = self.plan(project, "code", "审查 Cocos Creator 工程规范")
        self.assertIn(routing.CREATOR, result["selected_paths"])
        self.assertEqual(next(item for item in result["items"] if item["path"] == routing.CREATOR)["usage"], "reference")
        self.assertTrue(any("先体检" in warning and "不能推断使用 CFW" in warning for warning in result["warnings"]))
        self.assertNotIn(routing.CREATOR, self.plan(project, "code", "不用 Creator，只检查现有规范")["selected_paths"])

    def test_creator_intent_accepts_adjacent_chinese_but_not_identifier_suffixes(self):
        """真实 REST 预览发现 Unicode 单词边界会漏掉中文紧邻的 Creator，不能靠给用户输入补空格修复。"""
        for prompt in ["审查Creator工程规范", "Cocos Creator工程体检", "附录审查Creator工程规范，并整理托管小游戏采集流程的输入与验收要求。"]:
            with self.subTest(prompt=prompt):
                self.assertIn(routing.CREATOR, self.plan(stage="prototype", prompt=prompt)["selected_paths"])
        for prompt in ["审查CreatorX工程规范", "审查MyCreator工程规范", "审查Creator_model工程规范"]:
            with self.subTest(prompt=prompt):
                self.assertNotIn(routing.CREATOR, self.plan(stage="prototype", prompt=prompt)["selected_paths"])

    def test_auto_inclusions_exclusions_and_manual_override_are_explicit(self):
        automatic = self.plan(stage="art", include_paths=["custom/SKILL.md", routing.ART], exclude_paths=[routing.ART])
        self.assertIn(routing.ART, automatic["recommended_paths"])
        self.assertNotIn(routing.ART, automatic["selected_paths"])
        self.assertIn("custom/SKILL.md", automatic["selected_paths"])
        self.assertEqual(next(item for item in automatic["items"] if item["path"] == "custom/SKILL.md")["source"], "manual")
        manual = self.plan(stage="art", mode="manual", include_paths=[routing.ART_STYLE, routing.ART_STYLE])
        self.assertEqual(manual["selected_paths"], [routing.ART_STYLE])
        self.assertEqual(manual["items"][0]["source"], "manual")
        self.assertIn(routing.GENERAL, manual["recommended_paths"])
        self.assertEqual(self.plan(mode="manual")["selected_paths"], [])

    def test_deleted_auto_candidates_are_visible_as_warnings_and_not_restored(self):
        skills = [item for item in self.skills if item["path"] != routing.ART_STYLE]
        result = routing.plan_skill_selection(self.project(), "art", "", skills)
        self.assertNotIn(routing.ART_STYLE, result["selected_paths"])
        self.assertTrue(any(routing.ART_STYLE in warning and "已跳过" in warning for warning in result["warnings"]))
        with self.assertRaisesRegex(ValueError, "不存在"):
            routing.plan_skill_selection(self.project(), "art", "", skills, include_paths=[routing.ART_STYLE])

    def test_manual_special_skills_still_show_capability_limits(self):
        result = self.plan(mode="manual", include_paths=[routing.COCOS, routing.CREATOR, "gpt52-vision-router/SKILL.md", routing.HARVEST])
        self.assertTrue(all(item["usage"] == "reference" for item in result["items"]))
        self.assertTrue(any("不会切换模型" in warning for warning in result["warnings"]))
        self.assertTrue(any("当前项目未配置 Cocos" in warning for warning in result["warnings"]))

    def test_invalid_inputs_and_legacy_configuration_do_not_guess_cocos(self):
        for arguments in [{"stage": "unknown"}, {"mode": "other"}, {"include_paths": ["../secret"]}, {"exclude_paths": ["missing/SKILL.md"]}]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.plan(**arguments)
        legacy = {"brief": "旧项目的名字包含 Cocos，但尚无技术配置"}
        result = self.plan(legacy, "code")
        self.assertEqual(result["selected_paths"], [routing.GENERAL])
        self.assertEqual(result["context"]["framework_id"], "")

    def test_planning_is_deterministic_and_does_not_mutate_inputs(self):
        project = self.project("physics", "cocos-web", {"idea": "玩法时机", "scope": ["规范", "换皮"]})
        original_project, original_skills = copy.deepcopy(project), copy.deepcopy(self.skills)
        first = self.plan(project, "test")
        self.assertEqual(first, self.plan(project, "test"))
        self.assertEqual(project, original_project)
        self.assertEqual(self.skills, original_skills)


if __name__ == "__main__":
    unittest.main()
