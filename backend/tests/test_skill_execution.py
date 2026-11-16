"""自动路由到真实读取工具的集成回归；模型调用用等待任务隔离。"""
import asyncio
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi import FastAPI

from app.api.routes.workflow import router
from app.services import knowledge, production_library
from app.services.workflow import engine
from app.services.workflow.prompts import build_run_prompts
from app.services.workflow.skill_routing import GENERAL, ART, ART_STYLE, H5_RESKIN, COCOS, HARVEST
from app.services.workflow.tools import create_workflow_tools


class SkillExecutionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.patches = [patch.object(engine, 'ROOT', self.root), patch.object(engine, 'STORE', self.root / 'state'),
                        patch.object(engine, 'KNOWLEDGE_DIR', self.root / 'knowledge'),
                        patch.object(knowledge, 'KNOWLEDGE_DIR', self.root / 'knowledge'),
                        patch.object(engine, 'execute_run', self.hold)]
        for item in self.patches:
            item.start()
        knowledge._sync_cache.clear()
        production_library.import_production_library()
        for relative in [GENERAL, ART, ART_STYLE, H5_RESKIN, COCOS]:
            path = engine.KNOWLEDGE_DIR / 'skill/docs' / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'---\nname: {path.parent.name}\ndescription: 临时夹具能力\nmetadata:\n  version: "1.0"\n---\n# 固定版本规范\n以实际资料和当前阶段执行。', encoding='utf-8')
        resource = engine.KNOWLEDGE_DIR / 'skill/docs/casual-game-production/references/guide.md'
        resource.parent.mkdir()
        resource.write_text('参考正文第一版', encoding='utf-8')
        self.project = engine.create_project('合成玩法', {'idea': '拖拽合成'}, 'games/demo', [], 'merge', 'canvas-web')
        app = FastAPI()
        app.include_router(router, prefix='/api')
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://test')

    async def asyncTearDown(self):
        await self.client.aclose()
        tasks = list(engine.WORKERS.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        engine.WORKERS.clear()
        for item in reversed(self.patches):
            item.stop()
        knowledge._sync_cache.clear()
        self.temporary.cleanup()

    async def hold(self, *args, **kwargs):
        """防止集成测试触发外部模型；其余路径均执行正式实现。"""
        await asyncio.Event().wait()

    async def start(self, **body):
        response = await self.client.post(f'/api/workflow/projects/{self.project["id"]}/runs',
                                          json={'stage': 'prototype', **body})
        self.assertEqual(response.status_code, 202, response.text)
        return response.json()

    def tools(self, run):
        return {tool.name: tool for tool in create_workflow_tools(
            root=self.root, knowledge_dir=engine.KNOWLEDGE_DIR,
            workspace=engine.resolve_workspace(self.project['workspace']), run=run,
            emit=lambda kind, message, data: engine.event(run['id'], kind, message, data),
            load_run=lambda: engine.load('runs', run['id']),
            skill_input_dir=engine.STORE / 'inputs' / run['id'] / 'skills')}

    async def test_preview_is_read_only_and_stage_sensitive(self):
        project_file = engine.STORE / 'projects' / f'{self.project["id"]}.json'
        before = project_file.read_bytes()
        response = await self.client.post(f'/api/workflow/projects/{self.project["id"]}/skill-selection',
                                          json={'stage': 'art', 'prompt': '对现有Canvas工程换皮'})
        self.assertEqual(response.status_code, 200, response.text)
        plan = response.json()
        self.assertEqual(set(plan['selected_paths']), {GENERAL, ART, ART_STYLE, H5_RESKIN})
        self.assertEqual(plan['context']['genre_id'], 'merge')
        self.assertNotIn(COCOS, plan['selected_paths'])
        self.assertEqual(project_file.read_bytes(), before)
        self.assertFalse((engine.STORE / 'inputs').exists())
        self.assertFalse((engine.STORE / 'runs').exists())

    async def test_start_read_gate_and_resume_keep_frozen_entry_and_resources(self):
        run = await self.start(request_id='freeze-1')
        self.assertEqual(run['skill_paths'], [GENERAL])
        with self.assertRaisesRegex(ValueError, '未实际读取'):
            engine.verify_skill_reads(run)
        tools = self.tools(run)
        entry = engine.KNOWLEDGE_DIR / 'skill/docs' / GENERAL
        entry.write_text('# 最新版本不可混入运行', encoding='utf-8')
        resource = engine.KNOWLEDGE_DIR / 'skill/docs/casual-game-production/references/guide.md'
        resource.unlink()
        content = await tools['read_skill'].ainvoke({'path': GENERAL})
        self.assertIn('固定版本规范', content)
        self.assertEqual(await tools['read_skill_resource'].ainvoke({'path': 'casual-game-production/references/guide.md'}), '参考正文第一版')
        current = engine.load('runs', run['id'])
        engine.verify_skill_reads(current, engine.STORE / 'inputs' / run['id'] / 'skills')
        event = next(item for item in current['events'] if item['type'] == 'skill_read')
        self.assertEqual(event['data']['sha256'], hashlib.sha256(content.encode()).hexdigest())
        self.assertTrue(event['data']['frozen'])
        with self.assertRaises(ValueError):
            await tools['read_skill'].ainvoke({'path': COCOS})
        await engine.cancel_run(run['id'])
        with patch.object(engine, 'plan_skill_selection', side_effect=AssertionError('恢复不能重选')), \
             patch.object(engine, 'freeze_skill_inputs', side_effect=AssertionError('恢复不能重建快照')):
            resumed = engine.resume_run(run['id'])
        self.assertEqual(resumed['skill_selection'], run['skill_selection'])
        self.assertEqual(resumed['skill_snapshot'], run['skill_snapshot'])
        self.assertEqual(await self.tools(resumed)['read_skill'].ainvoke({'path': GENERAL}), content)

    async def test_manual_empty_override_and_idempotency_preserve_intent(self):
        first = await self.start(request_id='manual-1', skill_mode='manual', skill_paths=[])
        self.assertEqual(first['skill_paths'], [])
        duplicate = await self.start(request_id='manual-1', skill_mode='manual', skill_paths=[])
        self.assertEqual(first['id'], duplicate['id'])
        conflict = await self.client.post(f'/api/workflow/projects/{self.project["id"]}/runs',
                                          json={'stage': 'prototype', 'request_id': 'manual-1', 'skill_mode': 'auto'})
        self.assertEqual(conflict.status_code, 409)
        await engine.cancel_run(first['id'])
        second = await self.start(skill_paths=[ART_STYLE], excluded_skill_paths=[GENERAL])
        self.assertEqual(second['skill_paths'], [ART_STYLE])
        self.assertEqual(second['skill_selection']['items'][0]['source'], 'manual')

    async def test_retry_uses_original_run_even_after_library_changes(self):
        first = await self.start(request_id='auto-1')
        (engine.KNOWLEDGE_DIR / 'skill/docs' / GENERAL).unlink()
        again = await self.start(request_id='auto-1')
        self.assertEqual(again['id'], first['id'])
        self.assertEqual(again['skill_snapshot'], first['skill_snapshot'])

    async def test_gate_rejects_wrong_hash_partial_read_and_tampered_archive(self):
        run = await self.start()
        snapshot = run['skill_snapshot'][0]
        for overrides in [{'sha256': '错误哈希'}, {'end': 1}, {'frozen': False}, {'offset': False}]:
            data = {'path': GENERAL, 'sha256': snapshot['sha256'], 'offset': 0,
                    'end': snapshot['total_chars'], 'frozen': True, **overrides}
            with self.assertRaisesRegex(ValueError, '未实际读取'):
                engine.verify_skill_reads({**run, 'events': [{'type': 'skill_read', 'data': data}]})
        await self.tools(run)['read_skill'].ainvoke({'path': GENERAL})
        archive = engine.STORE / 'inputs' / run['id'] / 'skills'
        (archive / GENERAL).write_text('篡改内容', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '哈希'):
            engine.verify_skill_reads(engine.load('runs', run['id']), archive)

    async def test_prompt_uses_metadata_reasons_and_explicit_capability_limits(self):
        run = await self.start(skill_paths=[ART_STYLE])
        system, prompt = build_run_prompts(run, self.project)
        self.assertIn('临时夹具能力', system)
        self.assertNotIn('# 固定版本规范', system)
        self.assertIn('没有联网搜索/采集', system)
        self.assertEqual(json.loads(prompt)['skill_selection']['selected_paths'], run['skill_paths'])
        legacy = {**run}
        legacy.pop('skill_snapshot')
        legacy_system, _ = build_run_prompts(legacy, self.project, True)
        self.assertIn('历史运行', legacy_system)
        self.assertNotIn('本轮Skill已按品类', legacy_system)

    async def test_updated_company_entries_and_guidance_reach_real_frozen_tools(self):
        """正式来源包进入路由、快照和工具，确保新参考不仅能在知识库列出来。"""
        source = Path(__file__).resolve().parents[2] / 'ref/公司skill整合/game-reverse-engineering'
        shutil.copytree(source, engine.KNOWLEDGE_DIR / 'skill/docs/game-reverse-engineering', dirs_exist_ok=True)
        run = await self.start(prompt='已有 H5 原版还原并换皮，进行包体优化')
        self.assertEqual(set(run['skill_paths']), {GENERAL, HARVEST, H5_RESKIN, ART_STYLE})
        tools = self.tools(run)
        for path in run['skill_paths']:
            await tools['read_skill'].ainvoke({'path': path})
        for item in run['skill_selection']['items']:
            for path in item.get('resource_paths', []):
                content = await tools['read_skill_resource'].ainvoke({'path': path})
                expected = (engine.KNOWLEDGE_DIR / 'skill/docs' / path).read_text(encoding='utf-8')
                self.assertEqual(content, expected)
        current = engine.load('runs', run['id'])
        engine.verify_skill_reads(current, engine.STORE / 'inputs' / run['id'] / 'skills')
        read_paths = {event['data']['path'] for event in current['events'] if event['type'] == 'skill_resource_read'}
        self.assertTrue(any(path.endswith('h5-package-runtime-optimization.md') for path in read_paths))
        self.assertTrue(any(path.endswith('intake-and-direction.md') for path in read_paths))
