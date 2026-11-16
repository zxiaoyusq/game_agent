<script setup>
import { computed, ref, watch } from 'vue'
import StudioIcon from './StudioIcon.vue'

const props = defineProps({ projectId: { type: String, required: true } })
const emit = defineEmits(['messages'])
const draft = ref('')
const messages = ref([])
const storageAvailable = ref(true)
const canSend = computed(() => !!draft.value.trim())
const storageKey = computed(() => `workflow-revision-demo:${props.projectId}`)

// 演示讨论按项目存入当前标签页，重新进入工作台时恢复；不写入真实执行记录。
watch(() => props.projectId, () => {
  draft.value = ''
  messages.value = []
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey.value) || 'null')
    if (typeof saved?.draft === 'string') draft.value = saved.draft.slice(0, 2000)
    if (Array.isArray(saved?.messages)) {
      messages.value = saved.messages.filter(item =>
        ['user', 'assistant'].includes(item?.role) && typeof item.text === 'string',
      )
    }
  } catch { storageAvailable.value = false }
  emit('messages', messages.value)
}, { immediate: true })

watch([draft, messages], () => {
  try {
    sessionStorage.setItem(storageKey.value, JSON.stringify({
      draft: draft.value, messages: messages.value,
    }))
    storageAvailable.value = true
  } catch { storageAvailable.value = false }
})

function sendSuggestion() {
  if (!canSend.value) return
  // 本地回执明确说明演示边界，避免让用户误以为已调用模型或修改游戏。
  messages.value = [...messages.value,
    { role: 'user', text: draft.value.trim() },
    { role: 'assistant', text: '已记录这条修改建议。当前为前端演示，尚未执行游戏修改；你可以继续补充细节。' },
  ]
  draft.value = ''
  emit('messages', messages.value)
}

function handleKeydown(event) {
  // 中文输入法选词时不发送；Shift + Enter 保留多行输入。
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing || event.keyCode === 229) return
  event.preventDefault()
  sendSuggestion()
}
</script>

<template>
  <form class="revision-composer" aria-label="游戏修改建议" @submit.prevent="sendSuggestion">
    <div class="revision-heading">
      <label for="workflow-revision-input"><StudioIcon name="spark" :size="15" />继续打磨你的游戏</label>
      <span>前端演示</span>
    </div>
    <div class="revision-input-box">
      <textarea
        id="workflow-revision-input"
        v-model="draft"
        aria-label="修改建议"
        aria-describedby="revision-demo-note"
        placeholder="输入修改建议，比如：把开始按钮调大，增加掷骰子的动画…"
        rows="3"
        maxlength="2000"
        @keydown="handleKeydown"
      />
      <div class="revision-input-actions">
        <span>Enter 发送 · Shift + Enter 换行</span>
        <small>{{ draft.length }}/2000</small>
        <button type="submit" :disabled="!canSend" aria-label="发送修改建议">
          <StudioIcon name="arrow" :size="15" />发送
        </button>
      </div>
    </div>
    <p id="revision-demo-note">
      {{ storageAvailable ? '建议仅保存在当前标签页，暂不执行游戏修改。' : '建议仅在当前页面可见，暂不执行游戏修改。' }}
    </p>
  </form>
</template>

<style scoped>
.revision-composer { min-width: 0; }
.revision-heading, .revision-heading label, .revision-input-actions, .revision-input-actions button {
  display: flex;
  align-items: center;
}
.revision-heading { justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.revision-heading label { gap: 7px; font-size: 12px; color: #c1d9cf; }
.revision-heading label svg { color: #80cbb1; }
.revision-heading > span { font-size: 10px; color: #8bb8a7; padding: 3px 7px; background: #70ceb40c; border: 1px solid #70ceb421; border-radius: 5px; }
.revision-input-box { border: 1px solid #73af982e; background: #121a19; border-radius: 11px; overflow: hidden; transition: border-color .15s; }
.revision-input-box:focus-within { border-color: #70ceb482; }
.revision-input-box textarea { display: block; width: 100%; min-height: 68px; max-height: 120px; resize: none; border: 0; background: transparent; padding: 12px 13px 6px; color: #d3e6de; font: inherit; font-size: 12px; line-height: 1.7; }
.revision-composer .revision-input-box textarea:focus-visible { outline: none; }
.revision-input-box textarea::placeholder { color: #718b80; }
.revision-input-actions { gap: 8px; padding: 6px 10px 10px; }
.revision-input-actions > span { color: #6e897d; font-size: 9px; }
.revision-input-actions small { margin-left: auto; color: #769486; font-size: 9px; }
.revision-input-actions button { gap: 5px; padding: 7px 11px; border-radius: 7px; background: #70ceb4; color: #143d30; font-size: 11px; font-weight: 600; }
.revision-input-actions button:hover:not(:disabled) { background: #8bddc6; }
.revision-composer > p { margin: 7px 0 0; color: #7c9a8b; font-size: 10px; line-height: 1.5; }
@media (max-width: 380px) {
  .revision-input-actions > span { font-size: 8px; }
}
</style>
