<script setup>
import { computed } from 'vue'
import StudioIcon from './StudioIcon.vue'

const props = defineProps({
  status: String,
  action: String,
  busy: Boolean,
  resumable: Boolean,
  error: String,
})
const emit = defineEmits(['action'])
const canStop = computed(() => ['queued', 'running', 'awaiting_input'].includes(props.status))
const canResume = computed(() => props.resumable && ['cancelled', 'interrupted', 'failed'].includes(props.status))
const isStopping = computed(() => props.action === 'stop' || (!props.action && canStop.value))
const title = computed(() => {
  if (props.action === 'stop') return '正在停止生成…'
  if (props.action === 'resume') return '正在继续任务…'
  return { cancelled: '生成任务已停止', interrupted: '生成任务已中断', failed: '生成任务执行失败',
    awaiting_input: '任务正在等待你的补充', queued: '生成任务排队中', running: '生成任务执行中',
  }[props.status] || '任务状态已更新'
})
const description = computed(() => {
  if (props.action) return '正在等待服务端确认，请稍候。'
  if (props.error) return '请检查下方提示，确认后重试。'
  if (canStop.value) return '停止后保留已生成内容，可稍后继续。'
  if (props.status === 'failed') return '可尝试继续；若仍失败，请查看项目详情。'
  if (canResume.value) return '点击继续，从已保存的检查点恢复。'
  return '以服务端同步的任务状态为准。'
})
</script>

<template>
  <div v-if="canStop || canResume || action || error" class="task-controls" aria-label="生成任务控制">
    <div class="task-control-row">
      <div class="task-control-caption" role="status">
        <strong>{{ title }}</strong>
        <p>{{ description }}</p>
      </div>
      <button
        v-if="canStop || canResume || action"
        class="task-action-button"
        :class="{ stop: isStopping }"
        :disabled="busy || !!action"
        :aria-busy="!!action"
        @click="emit('action', isStopping ? 'stop' : 'resume')"
      >
        <StudioIcon :name="action ? 'clock' : isStopping ? 'pause' : 'play'" :size="15" />
        {{ action === 'stop' ? '正在停止…' : action === 'resume' ? '正在继续…' : isStopping ? '停止生成' : '继续任务' }}
      </button>
    </div>
    <p v-if="error" class="task-control-error" role="alert">{{ error }}</p>
  </div>
</template>

<style scoped>
.task-controls { flex-shrink: 0; margin-top: 13px; padding-top: 12px; border-top: 1px solid #ffffff0a; }
.task-control-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.task-control-caption { min-width: 0; }
.task-control-caption strong { color: #b4cec0; font-size: 11px; font-weight: 500; }
.task-control-caption p { color: #7c9a8b; font-size: 10px; margin: 4px 0 0; line-height: 1.5; }
.task-action-button { display: flex; align-items: center; gap: 7px; flex-shrink: 0; min-height: 38px; padding: 8px 13px; border: 1px solid #80c6a93b; border-radius: 8px; background: #244a3b; color: #bee4d0; font-size: 12px; }
.task-action-button:hover:not(:disabled) { background: #305c49; }
.task-action-button.stop { border-color: #d4ac7c45; background: #493b292e; color: #e4c49c; }
.task-action-button.stop:hover:not(:disabled) { background: #59452d66; }
.task-control-error { color: #edb7a4; font-size: 11px; line-height: 1.6; overflow-wrap: anywhere; margin: 9px 0 0; max-height: 72px; overflow-y: auto; }
@media (max-width: 380px) {
  .task-control-row { gap: 7px; }
  .task-action-button { padding: 8px 10px; }
}
</style>
