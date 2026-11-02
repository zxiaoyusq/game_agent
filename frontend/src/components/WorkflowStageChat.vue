<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  stageName: { type: String, required: true },
  owner: { type: String, required: true },
  messages: { type: Array, default: () => [] },
  draft: { type: String, default: '' },
  suggestions: { type: Array, default: () => [] },
  busy: Boolean,
  disabled: Boolean,
  version: { type: Number, default: 0 },
})
const emit = defineEmits(['update:draft', 'send', 'cancel'])
const thread = ref(null)
const canSend = computed(
  () => props.draft.trim() && !props.busy && !props.disabled,
)

// 仅滚动对话容器，避免新回复把用户正在查看的成果区域带离屏幕。
watch(
  () => [props.messages.length, props.busy],
  async () => {
    await nextTick()
    if (thread.value) thread.value.scrollTop = thread.value.scrollHeight
  },
  { immediate: true },
)

function submit() {
  if (canSend.value) emit('send')
}

function onKeydown(event) {
  // 保留中文输入法确认操作；普通 Enter 换行，组合键发送。
  if (
    event.isComposing ||
    !(event.ctrlKey || event.metaKey) ||
    event.key !== 'Enter'
  )
    return
  event.preventDefault()
  submit()
}
</script>

<template>
  <section class="stage-chat" :aria-label="`${stageName}需求对话`">
    <header>
      <div>
        <span class="chat-icon">✧</span>
        <h2>{{ stageName }} · 需求对话</h2>
      </div>
      <span class="chat-mode">{{ owner }} · DeepAgents · 真实执行</span>
    </header>
    <div
      ref="thread"
      class="chat-thread"
      role="log"
      aria-live="polite"
      aria-label="阶段对话记录"
    >
      <div class="chat-message assistant">
        <span class="message-avatar">AI</span>
        <div class="message-body">
          <strong>一起完善{{ stageName }}</strong>
          <p>
            告诉我本阶段的需求，或指出当前产出需要调整的地方。你可以连续追加意见，满意后再确认进入下一阶段。
          </p>
        </div>
      </div>
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="chat-message"
        :class="message.role"
      >
        <span class="message-avatar">{{
          message.role === 'user'
            ? '你'
            : message.role === 'system'
              ? '↻'
              : 'AI'
        }}</span>
        <div class="message-body">
          <strong
            >{{
              message.role === 'user'
                ? '你的需求'
                : message.role === 'system'
                  ? '流程提示'
                  : `${owner} · 执行反馈`
            }}<span v-if="message.version">v{{ message.version }}.0</span
            ><span v-if="message.status === 'cancelled'">已取消</span
            ><span v-if="message.status === 'superseded'"
              >历史基线</span
            ></strong
          >
          <p>{{ message.content }}</p>
          <details v-if="message.references?.length" class="message-sources">
            <summary>
              {{ message.role === 'user' ? '随需求发送' : '本轮参考来源' }} ·
              {{ message.references.length }} 份资料
            </summary>
            <div
              v-for="(source, sourceIndex) in message.references"
              :key="source.id"
            >
              <strong>[{{ sourceIndex + 1 }}] {{ source.title }}</strong>
              <small>{{ source.library }} · 执行参考资料</small>
              <p>{{ source.content }}</p>
            </div>
          </details>
        </div>
      </div>
      <div v-if="busy" class="chat-message assistant">
        <span class="message-avatar">AI</span>
        <div class="message-body thinking" role="status">
          后端正在执行本阶段任务，请查看下方运行事件…
        </div>
      </div>
    </div>
    <div class="chat-suggestions">
      <button
        v-for="suggestion in suggestions"
        :key="suggestion"
        :disabled="busy || disabled"
        @click="emit('update:draft', suggestion)"
      >
        {{ suggestion }}
      </button>
    </div>
    <slot />
    <form class="chat-composer" @submit.prevent="submit">
      <label :for="`stage-prompt-${stageName}`">本阶段需求或修改意见</label>
      <textarea
        :id="`stage-prompt-${stageName}`"
        :value="draft"
        :disabled="busy || disabled"
        rows="3"
        maxlength="3000"
        :placeholder="`描述${stageName}的要求，也可以继续说“调整…”、“增加…”或“保留…”`"
        @input="emit('update:draft', $event.target.value)"
        @keydown="onKeydown"
      ></textarea>
      <div class="composer-footer">
        <small>{{
          disabled
            ? '当前阶段暂不可执行，请检查上游确认和运行环境'
            : 'Ctrl / ⌘ + Enter 发送 · Enter 换行'
        }}</small
        ><button
          v-if="busy"
          type="button"
          class="cancel-button"
          @click="emit('cancel')"
        >
          取消运行</button
        ><button v-else class="send-button" :disabled="!canSend" type="submit">
          {{ version ? '发送并重新执行' : '发送需求并执行' }} ↑
        </button>
      </div>
    </form>
    <p class="chat-note">
      需求将提交给真实后端执行，运行事件与产物保存在服务端；完成后需人工评审确认。
    </p>
  </section>
</template>

<style scoped>
.message-sources {
  margin-top: 12px;
  border-top: 1px solid #dce4f1;
  padding-top: 9px;
  font-size: 10px;
  color: #6580a5;
}
.message-sources summary {
  cursor: pointer;
}
.message-sources > div {
  margin-top: 12px;
}
.message-sources small {
  display: block;
  font-size: 9px;
  margin-bottom: 6px;
}
.stage-chat {
  background: #fff;
  border: 1px solid #cbd8ef;
  border-radius: 9px;
  margin-bottom: 22px;
  overflow: hidden;
}
header,
header > div {
  display: flex;
  align-items: center;
  gap: 10px;
}
header {
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid #e6ecf6;
  background: #f5f8fd;
}
h2 {
  font-size: 14px;
}
.chat-icon {
  color: #3565dc;
  font-size: 22px;
}
.chat-mode {
  font-size: 10px;
  color: #697995;
}
.chat-thread {
  max-height: 310px;
  overflow-y: auto;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.chat-message {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.message-avatar {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  background: #eaf0fb;
  color: #4168a9;
  display: grid;
  place-content: center;
  border-radius: 6px;
  font-size: 10px;
}
.message-body {
  background: #f4f6f9;
  padding: 12px 15px;
  border-radius: 0 9px 9px;
  min-width: 0;
  max-width: 90%;
}
.message-body strong {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  font-size: 11px;
  color: #5d7195;
  font-weight: 500;
  margin-bottom: 6px;
}
.message-body strong span {
  font-size: 9px;
  padding: 1px 6px;
  background: #e1e9f7;
  border-radius: 3px;
}
.message-body p {
  font-size: 12px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  color: #526077;
  line-height: 1.9;
}
.user {
  flex-direction: row-reverse;
}
.user .message-avatar {
  background: #3565dc;
  color: #fff;
}
.user .message-body {
  background: #edf3ff;
  border-radius: 9px 0 9px 9px;
}
.system .message-body {
  background: #fbf5e8;
}
.thinking {
  font-size: 12px;
  color: #6882ad;
}
.chat-suggestions {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
  padding: 0 22px 14px;
}
.chat-suggestions button {
  font-size: 10px;
  color: #617a9e;
  border: 1px solid #dbe4f2;
  padding: 5px 9px;
  border-radius: 5px;
  background: #fafcff;
  text-align: left;
}
.chat-composer {
  margin: 0 22px;
  border: 1px solid #cbd8ed;
  border-radius: 7px;
  padding: 12px;
}
.chat-composer:focus-within {
  border-color: #6485c6;
}
.chat-composer label {
  font-size: 10px;
  color: #7484a0;
}
textarea {
  display: block;
  width: 100%;
  padding: 8px 0;
  resize: vertical;
  border: 0;
  background: transparent;
  font: 12px/1.8 var(--font-ui);
  color: #344761;
}
textarea:focus {
  outline: none;
}
textarea::placeholder {
  color: #96a4b8;
}
.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
}
.composer-footer small {
  font-size: 9px;
  color: #8290a6;
}
.send-button,
.cancel-button {
  padding: 9px 13px;
  color: white;
  background: #3565dc;
  border-radius: 5px;
  font-size: 11px;
  white-space: nowrap;
}
.cancel-button {
  background: #eef2f8;
  color: #536b91;
}
button:disabled,
textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
button:focus-visible {
  outline: 3px solid #799af1;
  outline-offset: 3px;
}
.chat-note {
  font-size: 10px;
  color: #7e8da2;
  margin: 12px 22px 17px;
}
@media (max-width: 550px) {
  header {
    padding: 15px;
    align-items: flex-start;
  }
  header h2 {
    font-size: 12px;
  }
  .chat-mode {
    font-size: 9px;
    max-width: 90px;
    text-align: right;
  }
  .chat-thread {
    padding: 16px;
  }
  .message-body {
    padding: 10px;
  }
  .chat-suggestions {
    padding: 0 16px 12px;
  }
  .chat-composer {
    margin: 0 16px;
  }
  .composer-footer {
    flex-wrap: wrap;
  }
  .composer-footer button {
    margin-left: auto;
  }
  .chat-note {
    margin: 12px 16px 16px;
  }
}
</style>
