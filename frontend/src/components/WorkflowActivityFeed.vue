<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { statusLabels, workflowSteps } from '../data/gameWorkflow.js'
import { elapsedTime, runActivity } from '../utils/workflowActivity.js'
import { renderMarkdown } from '../utils/markdown.js'
import StudioIcon from './StudioIcon.vue'

const props = defineProps({
  runs: { type: Array, default: () => [] },
  activeId: String,
  brief: String,
  stage: String,
  revisionMessages: { type: Array, default: () => [] },
})
const emit = defineEmits(['details'])
const scroller = ref(null),
  following = ref(true),
  unread = ref(false)
const toolStatus = {
  running: '进行中',
  completed: '已完成',
  failed: '失败',
  awaiting_input: '待补充',
  unfinished: '未完成',
}
const groups = computed(() =>
  [...props.runs]
    .sort((a, b) => a.created_at.localeCompare(b.created_at))
    .filter((run) => !props.stage || run.stage === props.stage)
    .map((run) => ({
      run,
      step: workflowSteps.find((item) => item.id === run.stage),
      entries: runActivity(run),
    })),
)
const signature = computed(() =>
  props.runs
    .map((run) => `${run.id}:${run.events?.length}:${run.status}`)
    .join('|'),
)
function trackScroll() {
  const element = scroller.value
  following.value =
    element.scrollHeight - element.scrollTop - element.clientHeight < 90
  if (following.value) unread.value = false
}
function toLatest() {
  const element = scroller.value
  if (element) element.scrollTop = element.scrollHeight
  following.value = true
  unread.value = false
}
watch(signature, async () => {
  const shouldFollow = following.value
  await nextTick()
  if (shouldFollow) toLatest()
  else unread.value = true
})
// 用户主动提交建议时将讨论滚到可见位置，真实制作记录仍沿用原有跟随规则。
watch(() => props.revisionMessages.length, async () => {
  await nextTick()
  toLatest()
})
watch(
  () => props.stage,
  async () => {
    await nextTick()
    toLatest()
  },
)
onMounted(() => nextTick(toLatest))
</script>

<template>
  <div class="activity-feed-wrap">
    <div
      ref="scroller"
      class="activity-feed"
      aria-label="Agent 制作记录"
      tabindex="0"
      @scroll="trackScroll"
    >
      <div v-if="brief && !stage" class="user-brief">
        <span>你的游戏想法</span>
        <p>{{ brief }}</p>
      </div>
      <div v-if="!groups.length" class="activity-empty">
        <StudioIcon name="spark" :size="23" />
        <p>
          {{
            stage
              ? '这个阶段还没有执行记录。'
              : '需求已保存，Agent 的制作过程会出现在这里。'
          }}
        </p>
      </div>
      <details
        v-for="group in groups"
        :key="group.run.id"
        v-memo="[
          group.run.updated_at,
          group.run.events?.length,
          group.run.status,
          activeId,
          stage,
        ]"
        class="run-group"
        :open="
          group.run.id === activeId ||
          !!stage ||
          group.run.id === groups.at(-1)?.run.id
        "
      >
        <summary class="run-group-heading">
          <span class="run-avatar">
            <StudioIcon
              :name="group.run.status === 'completed' ? 'check' : 'layers'"
              :size="16"
            />
          </span>
          <strong>{{ group.step?.name || group.run.stage }}</strong>
          <span class="run-badge" :class="group.run.status">
            {{ statusLabels[group.run.status] || group.run.status }}
          </span>
          <StudioIcon name="chevron" :size="14" />
        </summary>
        <div class="run-group-body">
          <div class="run-context">
            <span>{{ group.step?.owner || '游戏 Agent' }}</span>
            <span>
              {{ group.run.provider === 'api-key' ? 'API Key' : 'Codex CLI' }} ·
              {{ group.run.model || '项目模型' }}
            </span>
          </div>
          <template v-for="entry in group.entries" :key="entry.id">
            <article
              v-if="entry.kind === 'message'"
              class="agent-message"
              v-html="renderMarkdown(entry.text)"
            />
            <details
              v-else-if="entry.kind === 'tool'"
              class="activity-tool"
              :class="entry.status"
            >
              <summary>
                <StudioIcon
                  :name="
                    entry.status === 'completed'
                      ? 'check'
                      : entry.status === 'failed'
                        ? 'alert'
                        : 'code'
                  "
                  :size="14"
                />
                <span>
                  <strong>{{ entry.title }}</strong>
                  <code v-if="entry.detail" :title="entry.detail">
                    {{ entry.detail.split('\n')[0] }}
                  </code>
                </span>
                <small>
                  {{
                    entry.status === 'failed' && entry.continued
                      ? '历史失败'
                      : toolStatus[entry.status]
                  }}
                </small>
                <StudioIcon name="chevron" :size="12" />
              </summary>
              <div class="tool-result">
                <p v-if="entry.continued">
                  这次调用未成功；此后已有其他成功操作，流程已继续。
                </p>
                <p v-if="entry.time">
                  发生时间：{{
                    new Date(entry.time).toLocaleString('zh-CN', {
                      hour12: false,
                    })
                  }}
                </p>
                <p v-if="entry.finishedAt">
                  耗时 {{ elapsedTime(entry.time, entry.finishedAt) }}
                </p>
                <pre v-if="entry.detail">{{ entry.detail }}</pre>
                <pre v-if="entry.output">{{ entry.output }}</pre>
                <p v-else>尚未收到工具执行结果。</p>
              </div>
            </details>
            <div v-else class="activity-notice" :class="entry.status">
              <StudioIcon
                :name="entry.status === 'failed' ? 'alert' : entry.status === 'autonomous' ? 'spark' : 'check'"
                :size="14"
              />
              <div>
                <strong>{{ entry.title }}</strong>
                <p v-if="entry.text">{{ entry.text }}</p>
              </div>
            </div>
          </template>
          <p v-if="!group.entries.length" class="waiting-events">
            任务已创建，等待执行事件…
          </p>
          <div v-if="group.run.artifacts?.length" class="activity-artifacts">
            <StudioIcon name="file" :size="14" />
            <span>已归档 {{ group.run.artifacts.length }} 份产物</span>
            <button @click="emit('details', group.run.stage)">
              查看产物
              <StudioIcon name="diagonal" :size="12" />
            </button>
          </div>
          <p v-if="group.run.error" class="activity-run-error">
            {{ group.run.error }}
          </p>
        </div>
      </details>
      <div class="feed-end">
        <i />
        {{
          runs.some((run) => ['running', 'queued'].includes(run.status))
            ? '制作继续中，进展将自动出现在这里'
            : '以上为已记录的制作过程'
        }}
      </div>
      <section v-if="revisionMessages.length" class="revision-discussion" aria-label="修改讨论">
        <h3>修改讨论 <span>前端演示</span></h3>
        <div role="log" aria-live="polite" aria-label="修改建议记录">
          <article v-for="(message, index) in revisionMessages" :key="index" class="revision-message" :class="message.role">
            <span><StudioIcon :name="message.role === 'user' ? 'file' : 'spark'" :size="13" />{{ message.role === 'user' ? '你的修改建议' : '演示助手' }}</span>
            <p>{{ message.text }}</p>
          </article>
        </div>
      </section>
    </div>
    <button v-if="unread" class="latest-activity" @click="toLatest">
      <StudioIcon name="chevron" :size="14" />
      查看最新进展
    </button>
  </div>
</template>

<style scoped>
.revision-discussion { border-top: 1px solid #ffffff0c; padding-top: 20px; }
.revision-discussion h3 { display: flex; align-items: center; gap: 10px; margin: 0 0 16px; font-size: 12px; font-weight: 500; color: #9dbeb0; }
.revision-discussion h3 > span { font-size: 9px; font-weight: 400; color: #759d8b; }
.revision-message { margin: 0 20px 15px 0; padding: 12px 14px; border-radius: 10px 10px 10px 3px; background: #ffffff03; border: 1px solid #ffffff08; }
.revision-message.user { margin: 0 0 12px 20px; background: #234b3b61; border-color: #70ceb425; border-radius: 10px 10px 3px 10px; }
.revision-message > span { display: flex; align-items: center; gap: 6px; color: #8fc5ae; font-size: 10px; }
.revision-message p { margin: 7px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; color: #c4d9cf; line-height: 1.8; font-size: 12px; }
.activity-feed-wrap {
  flex: 1;
  min-height: 0;
  position: relative;
}
.activity-feed {
  height: 100%;
  overflow: auto;
  overscroll-behavior: contain;
  padding: 27px 25px 24px;
  scrollbar-width: thin;
  scrollbar-color: #3b4549 transparent;
}
.user-brief {
  margin: 0 0 28px 25px;
  border: 1px solid #4bceb131;
  background: linear-gradient(130deg, #16443c, #193c37);
  border-radius: 13px 13px 3px 13px;
  padding: 16px 18px;
}
.user-brief > span {
  font-size: 10px;
  color: #80bcae;
}
.user-brief p {
  margin-top: 7px;
  font-size: 13px;
  line-height: 1.9;
  color: #c6ece1;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.run-group {
  margin-bottom: 24px;
}
.run-group-heading {
  display: flex;
  align-items: center;
  gap: 10px;
  list-style: none;
  cursor: pointer;
  color: #c9d4d7;
  font-size: 12px;
  padding: 4px 0;
}
.run-group-heading::-webkit-details-marker,
.activity-tool summary::-webkit-details-marker {
  display: none;
}
.run-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: #79c4ad;
  background: #26362e;
  border: 1px solid #6b9e8230;
}
.run-group-heading strong {
  font-weight: 500;
}
.run-group-heading > svg:last-child {
  margin-left: auto;
  color: #718481;
  transition: transform 0.15s;
}
.run-group:not([open]) .run-group-heading > svg:last-child {
  transform: rotate(-90deg);
}
.run-badge {
  font-size: 10px;
  color: #778e86;
  margin-left: 4px;
}
.run-badge.running {
  color: #76c8b2;
}
.run-badge.awaiting_input {
  color: #d1b27c;
}
.run-badge.failed {
  color: #d6998c;
}
.run-group-body {
  margin: 12px 0 0 13px;
  border-left: 1px solid #5c817529;
  padding-left: 22px;
}
.run-context {
  display: flex;
  gap: 12px;
  align-items: center;
  color: #6c8480;
  font-size: 9px;
  margin: 0 0 17px;
  flex-wrap: wrap;
}
.agent-message {
  font-size: 13px;
  line-height: 1.95;
  color: #c3cece;
  overflow-wrap: anywhere;
  margin: 18px 0;
}
.agent-message :deep(p) {
  margin: 12px 0;
}
.agent-message :deep(h1),
.agent-message :deep(h2),
.agent-message :deep(h3) {
  font-size: 15px;
  color: #dbe9e4;
  margin: 18px 0 10px;
}
.agent-message :deep(ul),
.agent-message :deep(ol) {
  padding-left: 20px;
  margin: 12px 0;
  list-style: revert;
}
.agent-message :deep(li) {
  margin: 5px 0;
}
.agent-message :deep(code) {
  background: #ffffff06;
  color: #add1c4;
  border-radius: 4px;
  padding: 2px 5px;
  font-size: 11px;
}
.agent-message :deep(pre) {
  overflow: auto;
  background: #0f1519;
  padding: 14px;
  border: 1px solid #ffffff0a;
  border-radius: 8px;
  max-height: 300px;
}
.agent-message :deep(pre code) {
  background: none;
  padding: 0;
}
.agent-message :deep(a) {
  color: #77cbb4;
  text-decoration: underline;
}
.agent-message :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}
.agent-message :deep(.md-table-wrap) {
  overflow: auto;
}
.agent-message :deep(table) {
  border-collapse: collapse;
}
.agent-message :deep(td),
.agent-message :deep(th) {
  border: 1px solid #ffffff18;
  padding: 6px;
}
.activity-tool {
  border: 1px solid #ffffff08;
  border-radius: 7px;
  background: #ffffff02;
  margin: 7px 0;
  overflow: hidden;
}
.activity-tool summary {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  list-style: none;
  padding: 10px 11px;
  color: #8b9d9b;
}
.activity-tool summary > span {
  flex: 1;
  min-width: 0;
  display: flex;
  gap: 10px;
  align-items: center;
}
.activity-tool strong {
  font-size: 11px;
  font-weight: 400;
  white-space: nowrap;
  color: #a9b7b6;
}
.activity-tool code {
  font-size: 10px;
  color: #6d8b81;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.activity-tool small {
  flex-shrink: 0;
  font-size: 9px;
}
.activity-tool.completed summary > svg:first-child {
  color: #64b69c;
}
.activity-tool.failed {
  border-color: #b9755e38;
}
.activity-tool.failed small {
  color: #d4a194;
}
.activity-tool.running small {
  color: #8cceba;
}
.tool-result {
  border-top: 1px solid #ffffff08;
  padding: 12px;
  font-size: 10px;
  color: #7b928a;
}
.tool-result pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  max-height: 260px;
  overflow: auto;
  color: #a4b6b0;
  font-size: 11px;
  line-height: 1.7;
  margin-top: 8px;
}
.activity-notice {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  color: #8cb5a6;
  font-size: 11px;
  margin: 16px 0;
  line-height: 1.8;
}
.activity-notice strong {
  font-weight: 400;
}
.activity-notice p {
  white-space: pre-wrap;
  margin-top: 4px;
  overflow-wrap: anywhere;
  color: #81998f;
}
.activity-notice.failed,
.activity-run-error {
  color: #d9a493;
}
.activity-run-error {
  font-size: 12px;
  line-height: 1.8;
  margin-top: 15px;
  overflow-wrap: anywhere;
}
.activity-artifacts {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 10px;
  color: #8da49c;
  margin-top: 20px;
}
.activity-artifacts button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  color: #79c8b0;
  font-size: 10px;
}
.waiting-events,
.feed-end {
  font-size: 10px;
  color: #69837a;
  line-height: 1.8;
}
.feed-end {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  padding: 8px 0;
}
.feed-end i {
  width: 4px;
  height: 4px;
  background: #577d6e;
  border-radius: 50%;
}
.activity-empty {
  color: #789c8d;
  text-align: center;
  padding: 50px 15px;
}
.activity-empty p {
  margin-top: 14px;
  line-height: 1.8;
  font-size: 12px;
}
.latest-activity {
  display: flex;
  align-items: center;
  gap: 7px;
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  border-radius: 20px;
  border: 1px solid #578f754d;
  background: #263e33;
  color: #b6d9c6;
  padding: 8px 16px;
  font-size: 11px;
  box-shadow: 0 8px 24px #0004;
}
@media (max-width: 1100px) {
  .activity-feed {
    padding: 22px 17px;
  }
  .run-group-body {
    padding-left: 16px;
  }
  .activity-tool summary > span {
    gap: 4px;
    flex-wrap: wrap;
  }
  .activity-tool code {
    max-width: 100%;
  }
}
@media (max-width: 700px) {
  .activity-feed {
    padding: 20px 17px;
  }
  .user-brief {
    margin-left: 15px;
  }
  .agent-message {
    font-size: 14px;
  }
}
</style>
