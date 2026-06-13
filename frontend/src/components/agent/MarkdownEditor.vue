<script setup>
import { ref, computed } from 'vue'
import VersionFooter from './VersionFooter.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  versions: { type: Array, default: () => [] },
  currentVersionIndex: { type: Number, default: null },
})

const emit = defineEmits(['update:modelValue', 'save', 'delete', 'load'])

const mode = ref('edit')

const wordCount = computed(
  () => (props.modelValue || '').replace(/\s+/g, '').length
)

const renderedHtml = computed(() => {
  const text = props.modelValue || ''
  const escape = (s) =>
    s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return escape(text)
    .replace(/^### (.*)$/gim, '<h3>$1</h3>')
    .replace(/^## (.*)$/gim, '<h2>$1</h2>')
    .replace(/^# (.*)$/gim, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^- (.*)$/gim, '<li>$1</li>')
    .replace(/(<li>.*?<\/li>)(?=\n|$)/gim, '<ul>$1</ul>')
    .replace(/<\/ul>\s*<ul>/g, '')
    .replace(/\n/g, '<br />')
})
</script>

<template>
  <div class="md-editor">
    <div class="toolbar">
      <div class="left">
        <span class="badge">MARKDOWN</span>
        <span class="meta">{{ wordCount }} 字</span>
      </div>
      <div class="mode-switch">
        <button
          class="mode-btn"
          :class="{ active: mode === 'edit' }"
          @click="mode = 'edit'"
        >
          ✎ 编辑
        </button>
        <button
          class="mode-btn"
          :class="{ active: mode === 'preview' }"
          @click="mode = 'preview'"
        >
          👁 预览
        </button>
      </div>
    </div>

    <div class="content">
      <textarea
        v-if="mode === 'edit'"
        class="editor"
        :value="modelValue"
        spellcheck="false"
        placeholder="# 在此开始撰写策划文档..."
        @input="emit('update:modelValue', $event.target.value)"
      ></textarea>
      <div v-else class="preview" v-html="renderedHtml"></div>
    </div>

    <VersionFooter
      label="版本存档"
      :versions="versions"
      :current-version-index="currentVersionIndex"
      @save="emit('save')"
      @delete="emit('delete')"
      @load="(i) => emit('load', i)"
    />
  </div>
</template>

<style scoped>
.md-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  min-width: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.badge {
  font-size: 10px;
  font-weight: 700;
  color: var(--accent-purple);
  background: rgba(188, 140, 255, 0.1);
  border: 1px solid rgba(188, 140, 255, 0.25);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.5px;
}

.meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.mode-switch {
  display: inline-flex;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 3px;
  gap: 2px;
}

.mode-btn {
  padding: 5px 14px;
  font-size: 12px;
  border-radius: 4px;
  color: var(--text-tertiary);
  transition: all 0.15s;
}

.mode-btn:hover {
  color: var(--text-primary);
}

.mode-btn.active {
  background: var(--bg-card);
  color: var(--accent-blue);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.editor {
  width: 100%;
  height: 100%;
  padding: 24px 32px;
  background: transparent;
  color: var(--text-primary);
  border: none;
  outline: none;
  resize: none;
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.7;
}

.editor::selection {
  background: rgba(88, 166, 255, 0.25);
}

.preview {
  width: 100%;
  height: 100%;
  padding: 24px 32px;
  overflow-y: auto;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.75;
}

.preview :deep(h1) {
  color: var(--text-primary);
  font-size: 26px;
  margin: 18px 0 12px;
  font-weight: 700;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
}

.preview :deep(h2) {
  color: var(--text-primary);
  font-size: 20px;
  margin: 16px 0 10px;
  font-weight: 600;
}

.preview :deep(h3) {
  color: var(--text-primary);
  font-size: 16px;
  margin: 12px 0 8px;
  font-weight: 600;
}

.preview :deep(strong) {
  color: var(--accent-blue);
  font-weight: 600;
}

.preview :deep(em) {
  color: var(--accent-purple);
}

.preview :deep(code) {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 1px 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--accent-cyan);
}

.preview :deep(ul) {
  margin: 6px 0;
  padding-left: 20px;
}

.preview :deep(li) {
  list-style: disc;
  margin: 4px 0;
}
</style>
