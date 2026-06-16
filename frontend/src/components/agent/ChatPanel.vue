<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { ensureModelsLoaded, modelStore } from '../../api/models.js'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  isThinking: { type: Boolean, default: false },
  // 当前选中的模型 id；由父组件持有，方便跨任务/子模块切换时保持一致
  modelId: { type: String, default: '' },
})

const emit = defineEmits(['send', 'update:modelId'])

// 进入工作台时拉一次模型清单，并在加载完成后给个默认值
onMounted(async () => {
  await ensureModelsLoaded()
  if (!props.modelId && modelStore.list.length) {
    emit('update:modelId', modelStore.list[0].id)
  }
})

function onModelChange(e) {
  emit('update:modelId', e.target.value)
}

const input = ref('')
const messagesEnd = ref(null)

watch(
  () => [props.messages.length, props.isThinking],
  async () => {
    await nextTick()
    messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
  }
)

function submit() {
  const v = input.value.trim()
  if (!v || props.isThinking) return
  emit('send', v)
  input.value = ''
}
</script>

<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span class="dot"></span>
      <h2>设计助手</h2>
      <!-- 模型选择：清单从 /api/models 拉，全部 agent 共用 -->
      <select
        class="model-select"
        :value="modelId"
        :disabled="!modelStore.loaded || isThinking"
        :title="modelStore.error ? '加载失败：' + modelStore.error : '切换模型'"
        @change="onModelChange"
      >
        <option v-if="!modelStore.loaded && !modelStore.error" value="">
          加载中…
        </option>
        <option v-if="modelStore.error" value="">⚠ 加载失败</option>
        <option v-for="m in modelStore.list" :key="m.id" :value="m.id">
          {{ m.label }}
        </option>
      </select>
    </div>

    <div class="messages">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="msg-row"
        :class="msg.role"
      >
        <div class="avatar" :class="msg.role">
          {{ msg.role === 'user' ? 'U' : 'AI' }}
        </div>
        <div class="bubble" :class="msg.role">{{ msg.content }}</div>
      </div>

      <div v-if="isThinking" class="msg-row model">
        <div class="avatar model">AI</div>
        <div class="bubble model thinking">
          <span class="dot-anim"></span>
          <span class="dot-anim"></span>
          <span class="dot-anim"></span>
        </div>
      </div>
      <div ref="messagesEnd"></div>
    </div>

    <form class="input-bar" @submit.prevent="submit">
      <input
        v-model="input"
        type="text"
        placeholder="描述玩法、规则或想要修改的部分..."
        :disabled="isThinking"
      />
      <button type="submit" class="send-btn" :disabled="!input.trim() || isThinking">
        ➤
      </button>
    </form>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-secondary);
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1.5px solid var(--border-color);
  background: var(--bg-tertiary);
}

.chat-header h2 {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-green);
  box-shadow: 0 0 8px var(--accent-green);
}

.badge {
  margin-left: auto;
  font-size: 11px;
  color: var(--accent-blue);
  background: var(--accent-blue-dim);
  border: 1px solid rgba(77, 158, 255, 0.3);
  padding: 2px 8px;
  border-radius: 3px;
  letter-spacing: 0.04em;
  font-weight: 600;
}

.model-select {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-primary);
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  outline: none;
  transition: border-color 0.15s;
  font-family: inherit;
  font-weight: 500;
}

.model-select:hover {
  border-color: var(--accent-blue);
}

.model-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.msg-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.msg-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
  color: #fff;
}

.avatar.user {
  background: linear-gradient(135deg, var(--accent-pink), var(--accent-orange));
}

.avatar.model {
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
}

.bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble.user {
  background: rgba(77, 158, 255, 0.1);
  color: var(--text-primary);
  border: 1px solid rgba(77, 158, 255, 0.2);
  border-bottom-right-radius: 4px;
}

.bubble.model {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1.5px solid var(--border-color);
  border-bottom-left-radius: 4px;
}

.bubble.thinking {
  display: inline-flex;
  gap: 4px;
  align-items: center;
}

.dot-anim {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-blue);
  animation: bounce 1.2s infinite ease-in-out;
}

.dot-anim:nth-child(2) {
  animation-delay: 0.15s;
}
.dot-anim:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-4px); opacity: 1; }
}

.input-bar {
  padding: 12px;
  border-top: 1.5px solid var(--border-color);
  background: var(--bg-tertiary);
  display: flex;
  gap: 8px;
}

.input-bar input {
  flex: 1;
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  font-size: 13px;
  color: var(--text-primary);
  outline: none;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.input-bar input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(77, 158, 255, 0.1);
}

.input-bar input:disabled {
  opacity: 0.6;
}

.send-btn {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 700;
  border: 1.5px solid rgba(77, 158, 255, 0.5);
  box-shadow: 2px 2px 0 var(--shadow-blue);
  transition: all 0.15s;
}

.send-btn:hover:not(:disabled) {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 var(--shadow-blue);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
