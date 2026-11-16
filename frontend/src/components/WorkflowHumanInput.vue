<script setup>
import { computed, reactive, watch } from 'vue'
const props = defineProps({ run: Object, busy: Boolean, compact: Boolean })
const emit = defineEmits(['answer'])
const answers = reactive({})
const questions = computed(() => props.run?.interrupts || [])
watch(() => questions.value.map(item => item.id).join(','), () => {
  // 轮询相同问题不会清空正在输入的回答；新中断使用新的问题 ID。
  for (const key of Object.keys(answers)) if (!questions.value.some(item => item.id === key)) delete answers[key]
})
const ready = computed(() => questions.value.length && questions.value.every(item => answers[item.id]?.trim()))
</script>

<template>
  <form v-if="run?.status === 'awaiting_input'" class="human-input" aria-label="Agent 需要你的补充" @submit.prevent="emit('answer', { ...answers })">
    <h3>需要你补充后继续</h3>
    <p>任务已暂停并保存进度。回答后从原检查点继续，不用重新输入整份需求。</p>
    <fieldset v-for="item in questions" :key="item.id">
      <legend>{{ item.value.question || '请确认以下事项' }}</legend>
      <details v-if="item.value.context && compact" class="human-context"><summary>查看背景说明</summary><p>{{ item.value.context }}</p></details>
      <p v-else-if="item.value.context">{{ item.value.context }}</p>
      <div class="answer-options"><button v-for="option in item.value.options || []" :key="option" type="button" :disabled="busy" @click="answers[item.id] = option">{{ option }}</button></div>
      <textarea v-model="answers[item.id]" :aria-label="item.value.question || '补充回答'" rows="3" maxlength="12000" placeholder="选择上方建议，或直接输入你的回答…" :disabled="busy" required />
    </fieldset>
    <button class="button primary" :disabled="!ready || busy">{{ busy ? '正在提交…' : '提交回答并继续' }}</button>
  </form>
</template>

<style scoped>
.human-input { padding: 20px; background: #fff9ec; border: 1px solid #dfc480; border-radius: 8px; }
.human-input p { line-height: 1.7; color: #6b6048; }.human-input fieldset { border: 0; padding: 12px 0; min-width: 0; }
.human-input legend { font-weight: 600; line-height: 1.6; }.human-input textarea { width: 100%; box-sizing: border-box; padding: 10px; font: inherit; margin: 10px 0; }
.answer-options { display: flex; flex-wrap: wrap; gap: 8px; }.answer-options button { padding: 7px 12px; border: 1px solid #d7c8a8; background: white; cursor: pointer; }
</style>
