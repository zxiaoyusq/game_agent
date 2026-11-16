<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { statusLabels, workflowSteps } from '../data/gameWorkflow.js'
import { currentActivity, elapsedTime } from '../utils/workflowActivity.js'
import StudioIcon from './StudioIcon.vue'
import WorkflowActivityFeed from './WorkflowActivityFeed.vue'
import WorkflowLivePreview from './WorkflowLivePreview.vue'
import WorkflowHumanInput from './WorkflowHumanInput.vue'
import WorkflowRevisionChat from './WorkflowRevisionChat.vue'
import WorkflowPublishDemo from './WorkflowPublishDemo.vue'
import WorkflowTaskControls from './WorkflowTaskControls.vue'

const props = defineProps({
  project: Object,
  runs: { type: Array, default: () => [] },
  busy: Boolean,
  error: String,
  controlAction: String,
  controlError: String,
})
const emit = defineEmits([
  'back',
  'details',
  'start',
  'task-action',
  'answer',
  'refresh',
])
const stageFilter = ref(''),
  mobilePanel = ref('activity'),
  approved = ref(false),
  now = ref(Date.now())
const revisionMessages = ref([])
let clock
onMounted(() => {
  clock = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})
onBeforeUnmount(() => clearInterval(clock))
const pipeline = computed(() => props.project.pipeline)
const orderedRuns = computed(() =>
  [...props.runs].sort((a, b) => b.created_at.localeCompare(a.created_at)),
)
const activeRun = computed(
  () =>
    orderedRuns.value.find((run) => run.id === pipeline.value?.run_id) ||
    orderedRuns.value.find((run) =>
      ['running', 'queued', 'awaiting_input'].includes(run.status),
    ) ||
    orderedRuns.value[0],
)
const status = computed(
  () => pipeline.value?.status || activeRun.value?.status || 'pending',
)
const isRunning = computed(() => ['running', 'queued'].includes(status.value))
// 旧阶段的历史运行可能已被替换，只有当前阶段引用的任务才允许继续。
const resumable = computed(() => !!pipeline.value || props.project.stages?.some(stage => stage.run_id === activeRun.value?.id))
const statusLabel = computed(() => status.value === 'cancelled' ? '已停止' : statusLabels[status.value] || status.value)
const activity = computed(() => currentActivity(activeRun.value))
const duration = computed(() => {
  const run = activeRun.value
  // 发布重试也会追加运行日志；已完成阶段的耗时应截止于确认，不能累加等待发布的时间。
  const finishedAt = run?.status === 'completed'
    ? [...(run.events || [])].reverse().find((event) => event.type === 'confirmed')?.time
    : null
  return elapsedTime(run?.created_at, isRunning.value ? now.value : finishedAt || run?.updated_at)
})
const brief = computed(() =>
  typeof props.project.brief === 'string'
    ? props.project.brief
    : props.project.brief?.idea || props.project.brief?.scope || '',
)
const pendingRun = computed(() =>
  props.runs.find((run) => run.status === 'awaiting_input'),
)
const finished = computed(
  () =>
    props.project.stages?.filter((stage) => stage.status === 'completed')
      .length || 0,
)
const stageStatus = (id) =>
  props.project.stages?.find((stage) => stage.id === id)?.status || 'pending'
</script>

<template>
  <section class="run-workspace" aria-label="游戏实时制作工作台">
    <header class="run-topbar">
      <button
        class="run-back"
        aria-label="返回我的项目"
        title="返回我的项目"
        @click="emit('back')"
      >
        <StudioIcon name="back" :size="19" />
      </button>
      <div class="run-project-title">
        <span>
          AHA
          <b>创造</b>
          <i>/</i>
        </span>
        <h1 :title="project.name">{{ project.name }}</h1>
      </div>
      <span class="run-global-status" :class="status">
        <i />
        {{ statusLabel }}
      </span>
      <button class="run-details-button" aria-label="项目详情" @click="emit('details')">
        <StudioIcon name="layers" :size="15" />
        <span>项目详情</span>
      </button>
      <WorkflowPublishDemo :key="project.id" :project-name="project.name" />
    </header>
    <div class="run-mobile-switch" role="tablist" aria-label="工作台视图">
      <button
        role="tab"
        :aria-selected="mobilePanel === 'activity'"
        aria-controls="run-activity-panel"
        @click="mobilePanel = 'activity'"
      >
        制作进展
        <span>{{ finished }}/4</span>
      </button>
      <button
        role="tab"
        :aria-selected="mobilePanel === 'preview'"
        aria-controls="run-preview-panel"
        @click="mobilePanel = 'preview'"
      >
        游戏预览
        <i v-if="project.preview?.status === 'ready'" />
      </button>
    </div>
    <div class="run-columns">
      <section
        id="run-activity-panel"
        class="run-activity-panel"
        :class="{ 'mobile-hidden': mobilePanel !== 'activity' }"
        aria-label="制作进展"
      >
        <header class="activity-panel-title">
          <div>
            <StudioIcon name="spark" :size="17" />
            <strong>和 Agent 一起，把游戏做出来</strong>
          </div>
          <span>{{ project.production_plan?.autonomous ? 'AI 自主决策 · 自动同步' : '每 2 秒同步' }}</span>
        </header>
        <nav class="run-stage-strip" aria-label="制作阶段筛选">
          <button
            v-for="(step, index) in workflowSteps"
            :key="step.id"
            :class="[
              stageStatus(step.id),
              { selected: stageFilter === step.id },
            ]"
            :aria-pressed="stageFilter === step.id"
            @click="stageFilter = stageFilter === step.id ? '' : step.id"
          >
            <span>
              <StudioIcon
                v-if="stageStatus(step.id) === 'completed'"
                name="check"
                :size="12"
              />
              <template v-else>
                {{ String(index + 1).padStart(2, '0') }}
              </template>
            </span>
            <strong>{{ step.name }}</strong>
            <small>{{ statusLabels[stageStatus(step.id)] }}</small>
          </button>
        </nav>
        <div
          class="current-activity"
          :class="{ working: isRunning, waiting: status === 'awaiting_input' }"
          role="status"
        >
          <span class="activity-indicator">
            <StudioIcon
              :name="
                status === 'completed'
                  ? 'check'
                  : status === 'awaiting_input'
                    ? 'pause'
                    : 'spark'
              "
              :size="15"
            />
          </span>
          <div>
            <strong>
              {{
                (status === 'cancelled' ? '生成任务已停止，可以稍后继续' : activity) ||
                (status === 'completed'
                  ? '制作已完成，可以在右侧试玩'
                  : statusLabel || '等待开始制作')
              }}
            </strong>
            <small>
              {{ activeRun ? `本阶段历时 ${duration}` : '四阶段自动衔接' }}
            </small>
          </div>
          <button v-if="stageFilter" @click="stageFilter = ''">看全部</button>
        </div>
        <div
          v-if="error || (pipeline?.error && status !== 'cancelled')"
          class="workspace-sync-error"
          role="alert"
        >
          {{ error || pipeline.error }}
          <button v-if="error" @click="emit('refresh')">重新同步</button>
        </div>
        <WorkflowActivityFeed
          :runs="runs"
          :active-id="activeRun?.id"
          :brief="brief"
          :stage="stageFilter"
          :revision-messages="revisionMessages"
          @details="emit('details', $event)"
        />
        <div class="run-interaction">
          <div v-if="pendingRun || pipeline?.status === 'draft'" class="run-action-context">
            <WorkflowHumanInput
              v-if="pendingRun"
              compact
              :run="pendingRun"
              :busy="busy"
              @answer="emit('answer', pendingRun.id, $event)"
            />
            <div v-else-if="pipeline?.status === 'draft'" class="run-start-choice">
              <label>
                <input v-model="approved" type="checkbox" />
                确认需求与美术配置，开始制作
              </label>
              <button
                class="run-primary"
                :disabled="!approved || busy"
                @click="emit('start')"
              >
                开始全流程
                <StudioIcon name="arrow" :size="15" />
              </button>
            </div>
          </div>
          <WorkflowRevisionChat :project-id="project.id" @messages="revisionMessages = $event" />
          <WorkflowTaskControls
            :status="status" :resumable="resumable" :busy="busy"
            :action="controlAction" :error="controlError"
            @action="emit('task-action', { action: $event, runId: pipeline ? null : activeRun?.id })"
          />
          <div class="run-control-bar">
            <span>
              <i :class="{ ready: !error }" />
              {{ error ? '同步暂时中断' : '进度已同步' }}
            </span>
            <div>
              <button
                v-if="!pipeline"
                @click="emit('details', activeRun?.stage)"
              >
                阶段设置与确认
                <StudioIcon name="arrow" :size="12" />
              </button>
            </div>
          </div>
        </div>
      </section>
      <section
        id="run-preview-panel"
        class="run-preview-panel"
        :class="{ 'mobile-hidden': mobilePanel !== 'preview' }"
        aria-label="游戏试玩区域"
      >
        <WorkflowLivePreview
          :preview="project.preview"
          :name="project.name"
          :publication="project.publication"
        />
      </section>
    </div>
  </section>
</template>

<style scoped>
.run-workspace {
  height: 100dvh;
  min-height: 450px;
  display: flex;
  flex-direction: column;
  background: #121719;
  color: #c2ceca;
  font-size: 13px;
  color-scheme: dark;
  --bg-primary: #121719;
  --bg-secondary: #1d2827;
}
.run-workspace :deep(button),
.run-workspace :deep(a),
.run-workspace :deep(summary) {
  -webkit-tap-highlight-color: transparent;
}
.run-workspace :deep(:is(button, a, summary, input, textarea):focus-visible) {
  outline: 2px solid #70ceb4;
  outline-offset: 3px;
}
.run-workspace :deep(button:disabled) {
  opacity: 0.4;
  cursor: not-allowed;
}
.run-topbar {
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 0 24px 0 19px;
  border-bottom: 1px solid #ffffff0c;
  background: #171b1e;
}
.run-back {
  display: flex;
  color: #8caaa0;
  padding: 8px;
  border: 1px solid #ffffff0a;
  border-radius: 8px;
}
.run-project-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
  min-width: 0;
}
.run-project-title > span {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 17px;
  color: #6bd4ba;
  font-weight: 650;
  white-space: nowrap;
}
.run-project-title b {
  font-size: 12px;
  color: #a7bab2;
  font-weight: 400;
}
.run-project-title i {
  font-size: 15px;
  color: #3d514b;
  font-style: normal;
  margin: 0 7px;
  font-weight: 400;
}
.run-project-title h1 {
  font-size: 14px;
  font-weight: 500;
  color: #cbd7d3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.run-global-status {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  color: #97aaa2;
  white-space: nowrap;
  margin-left: auto;
}
.run-global-status i {
  width: 5px;
  height: 5px;
  background: #87a392;
  border-radius: 50%;
}
.run-global-status.running {
  color: #8bd0b9;
}
.run-global-status.running i {
  background: #72d0ae;
}
.run-global-status.awaiting_input {
  color: #d4ba87;
}
.run-global-status.awaiting_input i {
  background: #c4a66f;
}
.run-global-status.failed {
  color: #d19a89;
}
.run-details-button {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 7px;
  color: #8daba0;
  font-size: 11px;
  padding: 7px 10px;
  border: 1px solid #ffffff0b;
  border-radius: 6px;
}
.run-columns {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(410px, 43%) minmax(0, 1fr);
}
.run-activity-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  border-right: 1px solid #ffffff10;
  background: #121719;
}
.run-preview-panel {
  min-width: 0;
  min-height: 0;
}
.activity-panel-title {
  height: 61px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 25px;
  border-bottom: 1px solid #ffffff07;
}
.activity-panel-title > div {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #8eb3a5;
}
.activity-panel-title strong {
  font-size: 12px;
  font-weight: 500;
  color: #b7cdc3;
}
.activity-panel-title > span {
  color: #627d71;
  font-size: 9px;
}
.run-stage-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  padding: 19px 25px 15px;
  gap: 9px;
  flex-shrink: 0;
}
.run-stage-strip button {
  text-align: left;
  border-bottom: 2px solid #ffffff09;
  padding: 0 0 12px;
  color: #647c71;
}
.run-stage-strip button > span {
  display: flex;
  align-items: center;
  justify-content: center;
  font: 9px monospace;
  width: 20px;
  height: 20px;
  border: 1px solid #ffffff0d;
  background: #ffffff03;
  border-radius: 6px;
  margin-bottom: 9px;
}
.run-stage-strip strong {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: #93aaa0;
  white-space: nowrap;
}
.run-stage-strip small {
  display: block;
  font-size: 9px;
  margin-top: 4px;
}
.run-stage-strip button.completed > span {
  background: #36735422;
  color: #74b795;
  border-color: #6eab7833;
}
.run-stage-strip button.running,
.run-stage-strip button.selected,
.run-stage-strip button.awaiting_input {
  border-bottom-color: #68c7a5;
}
.run-stage-strip button.running strong,
.run-stage-strip button.selected strong {
  color: #a0d7bd;
}
.run-stage-strip button.awaiting_input strong {
  color: #d5bf8e;
}
.current-activity {
  display: flex;
  align-items: center;
  gap: 11px;
  flex-shrink: 0;
  margin: 0 25px 5px;
  padding: 12px 13px;
  border: 1px solid #ffffff09;
  background: #1c272344;
  border-radius: 9px;
}
.activity-indicator {
  display: flex;
  color: #80af99;
}
.current-activity strong {
  display: block;
  color: #a6c7b7;
  font-size: 11px;
  font-weight: 500;
}
.current-activity small {
  display: block;
  font-size: 9px;
  color: #687f72;
  margin-top: 3px;
}
.current-activity button {
  font-size: 10px;
  color: #85bda4;
  margin-left: auto;
  white-space: nowrap;
}
.current-activity.working .activity-indicator {
  animation: activity-pulse 2s ease-in-out infinite;
}
.current-activity.waiting {
  border-color: #bfa46f2e;
  background: #433a201c;
}
.current-activity.waiting strong,
.current-activity.waiting .activity-indicator {
  color: #c9b487;
}
.workspace-sync-error {
  font-size: 11px;
  color: #e0b4a0;
  background: #4b30273d;
  padding: 10px 25px;
  line-height: 1.7;
  max-height: 110px;
  overflow: auto;
}
.workspace-sync-error button {
  color: #efc8ae;
  text-decoration: underline;
  margin-left: 10px;
}
.run-interaction {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-top: 1px solid #ffffff0a;
  padding: 17px 23px 12px;
  background: #171e1e;
  max-height: 60%;
}
.run-action-context {
  min-height: 0;
  overflow-y: auto;
  margin-bottom: 14px;
}
.run-interaction :deep(.revision-composer) {
  flex-shrink: 0;
}
.run-control-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 13px;
  font-size: 9px;
  color: #6b8777;
}
.run-control-bar > span,
.run-control-bar > div,
.run-control-bar button {
  display: flex;
  align-items: center;
  gap: 6px;
}
.run-control-bar > div {
  gap: 12px;
}
.run-control-bar i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #bd926d;
}
.run-control-bar i.ready {
  background: #609e7e;
}
.run-control-bar button {
  font-size: 10px;
  color: #a1b0a3;
}
.run-start-choice {
  display: flex;
  align-items: center;
  gap: 13px;
  font-size: 11px;
  flex-wrap: wrap;
}
.run-start-choice label {
  display: flex;
  align-items: center;
  gap: 8px;
}
.run-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  background: #6ac6a5;
  color: #133526;
  border-radius: 7px;
  font-size: 11px;
}
.run-start-choice input {
  accent-color: #71c5a5;
}
.run-interaction :deep(.human-input) {
  padding: 16px;
  background: #30332355;
  border: 1px solid #b5a56c3d;
  border-radius: 10px;
}
.run-interaction :deep(.human-input h3) {
  font-size: 13px;
  color: #ddce9c;
  font-weight: 500;
}
.run-interaction :deep(.human-input p) {
  font-size: 11px;
  color: #a6a78b;
  margin: 8px 0;
}
.run-interaction :deep(.human-input legend) {
  font-size: 12px;
  color: #ddd8bd;
}
.run-interaction :deep(.human-input textarea) {
  background: #151d1b;
  color: #c9d8c7;
  border: 1px solid #566348;
  border-radius: 7px;
  font-size: 13px;
}
.run-interaction :deep(.answer-options button) {
  background: #2d3d2e;
  color: #c2cfaa;
  border-color: #5b69463b;
  border-radius: 6px;
  font-size: 11px;
}
.run-interaction :deep(.human-input .button.primary) {
  position: sticky;
  bottom: 0;
  background: #81bd9c;
  color: #172e1c;
  border: 0;
  border-radius: 6px;
  padding: 9px 13px;
  font-size: 12px;
}
.run-interaction :deep(.human-context) { margin: 8px 0 12px; color: #b3b397; font-size: 11px; }
.run-interaction :deep(.human-context summary) { cursor: pointer; }
.run-mobile-switch {
  display: none;
}
@keyframes activity-pulse {
  50% {
    opacity: 0.3;
  }
}
@media (min-width: 1800px) {
  .run-columns {
    grid-template-columns: minmax(500px, 39%) minmax(0, 1fr);
  }
}
@media (max-width: 1100px) {
  .run-columns {
    grid-template-columns: minmax(350px, 45%) minmax(0, 1fr);
  }
  .activity-panel-title,
  .run-stage-strip {
    padding-inline: 18px;
  }
  .current-activity {
    margin-inline: 18px;
  }
  .run-interaction {
    padding-inline: 17px;
  }
  .activity-panel-title > span {
    display: none;
  }
}
@media (max-width: 700px) {
  .run-workspace {
    min-height: 360px;
  }
  .run-topbar {
    height: 56px;
    padding: 0 13px;
    gap: 10px;
  }
  .run-project-title > span {
    display: none;
  }
  .run-project-title h1 {
    font-size: 13px;
  }
  .run-details-button {
    padding: 7px;
  }
  .run-details-button > span {
    display: none;
  }
  .run-global-status {
    font-size: 10px;
  }
  .run-columns {
    display: flex;
  }
  .run-activity-panel,
  .run-preview-panel {
    width: 100%;
  }
  .mobile-hidden {
    display: none;
  }
  .run-mobile-switch {
    display: flex;
    flex-shrink: 0;
    border-bottom: 1px solid #ffffff0a;
    background: #1a2221;
  }
  .run-mobile-switch button {
    display: flex;
    gap: 8px;
    align-items: center;
    justify-content: center;
    width: 50%;
    padding: 12px;
    color: #7d9c8c;
    font-size: 12px;
    border-bottom: 2px solid transparent;
  }
  .run-mobile-switch button[aria-selected='true'] {
    color: #b1d7c2;
    border-color: #75c19e;
  }
  .run-mobile-switch span {
    font-size: 9px;
    color: #6f9680;
  }
  .run-mobile-switch i {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #70c79b;
  }
  .activity-panel-title {
    height: 42px;
  }
  .run-stage-strip {
    padding-top: 12px;
    padding-bottom: 10px;
  }
  .run-stage-strip button > span {
    margin-bottom: 5px;
  }
  .run-stage-strip button {
    padding-bottom: 9px;
  }
  .run-stage-strip small {
    font-size: 9px;
  }
  .current-activity {
    padding-block: 8px;
  }
  .run-interaction {
    max-height: 60%;
    padding-top: 12px;
  }
  .run-interaction :deep(.human-input textarea) {
    font-size: 16px;
  }
}
@media (max-width: 500px) {
  .run-global-status { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .current-activity.working .activity-indicator {
    animation: none;
  }
}
</style>
