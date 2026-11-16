<script setup>
import { computed, ref } from 'vue'
import { statusLabels, workflowSteps } from '../data/gameWorkflow.js'
import WorkflowHumanInput from './WorkflowHumanInput.vue'
const props = defineProps({ project: Object, runs: { type: Array, default: () => [] }, busy: Boolean })
const emit = defineEmits(['start', 'resume', 'cancel', 'answer', 'view-stage'])
const approved = ref(false)
const pipeline = computed(() => props.project.pipeline)
const pending = computed(() => props.runs.find(item => item.id === pipeline.value.run_id))
const currentName = computed(() => workflowSteps.find(item => item.id === pipeline.value.current_stage)?.name)
</script>

<template>
  <section class="pipeline-panel panel" aria-label="全流程执行">
    <div class="pipeline-heading"><h2>全流程制作</h2><strong role="status">{{ statusLabels[pipeline.status] || pipeline.status }}</strong></div>
    <p>{{ project.model_provider === 'api-key' ? 'API Key 网关' : 'Codex CLI（服务器登录）' }} · {{ project.model_id }} · DeepAgents</p>
    <p>已保存统一需求与美术配置。四阶段通过产物校验后自动衔接，需要补充信息时会暂停提问。</p>
    <p v-if="currentName">当前阶段：<button class="text-button" @click="emit('view-stage', pipeline.current_stage)">{{ currentName }} · 查看产物与事件 →</button></p>
    <details><summary>查看已确认的制作要求</summary><p class="saved-art">{{ project.production_plan.art_requirements }}</p><p>完成后：{{ project.production_plan.auto_publish ? '测试通过自动发布独立试玩地址' : '保留预览，手动发布' }}</p></details>
    <p v-if="pipeline.error" class="error-text" role="alert">{{ pipeline.error }}</p>
    <WorkflowHumanInput v-if="pipeline.status === 'awaiting_input'" :run="pending" :busy="busy" @answer="emit('answer', pending.id, $event)" />
    <div v-if="pipeline.status === 'draft'" class="start-confirmation">
      <label><input v-model="approved" type="checkbox" />我已确认需求、模型、美术与交付设置，开始执行全流程。</label>
      <button class="button primary" :disabled="!approved || busy" @click="emit('start')">确认并开始全流程</button>
    </div>
    <div class="pipeline-actions">
      <button v-if="['failed', 'interrupted', 'cancelled'].includes(pipeline.status)" class="button primary" :disabled="busy" @click="emit('resume')">继续全流程</button>
      <button v-if="['running', 'awaiting_input', 'failed', 'interrupted'].includes(pipeline.status)" class="button" :disabled="busy" @click="emit('cancel')">取消全流程</button>
      <a v-if="project.publication?.url" class="button primary" :href="project.publication.url" target="_blank" rel="noopener">打开试玩游戏 ↗</a>
    </div>
    <p v-if="pipeline.status === 'running'" class="muted">关闭或刷新网页不会终止服务端执行。可以随时返回查看进度。</p>
  </section>
</template>

<style scoped>
.pipeline-panel { margin: 20px 0; border: 1px solid #bdcfac; }.pipeline-heading { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; justify-content: space-between; }
.pipeline-heading strong { color: #4d682f; }.pipeline-panel p { line-height: 1.7; }.saved-art { white-space: pre-wrap; }
.pipeline-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }.start-confirmation { display: grid; gap: 15px; margin-top: 16px; }
.pipeline-panel details { margin-bottom: 16px; }.pipeline-panel summary { cursor: pointer; }
</style>
