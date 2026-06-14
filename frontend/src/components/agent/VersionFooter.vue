<script setup>
defineProps({
  label: { type: String, default: '版本' },
  versions: { type: Array, default: () => [] },
  currentVersionIndex: { type: Number, default: null },
  saveLabel: { type: String, default: '保存' },
})

const emit = defineEmits(['load', 'save', 'delete'])
</script>

<template>
  <div class="version-footer">
    <div class="footer-head">
      <span class="footer-label">{{ label }}</span>
      <div class="footer-actions">
        <button
          v-if="currentVersionIndex !== null"
          class="action-btn danger"
          title="删除此版本"
          @click="emit('delete')"
        >
          🗑
        </button>
        <!-- 父组件可在保存按钮旁注入额外操作（如"导出到知识库"） -->
        <slot name="actions-pre" />
        <button class="action-btn primary" @click="emit('save')">
          💾 {{ saveLabel }}
        </button>
      </div>
    </div>
    <div class="version-list">
      <button
        v-for="(_, index) in versions"
        :key="index"
        class="version-chip"
        :class="{ active: index === currentVersionIndex }"
        @click="emit('load', index)"
      >
        {{ index + 1 }}
      </button>
      <span v-if="versions.length === 0" class="empty-text">暂无保存版本</span>
    </div>
  </div>
</template>

<style scoped>
.version-footer {
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.footer-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  padding: 4px 10px;
  font-size: 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.action-btn.primary {
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
}

.action-btn.primary:hover {
  background: #4a93eb;
  filter: brightness(1.05);
}

.action-btn.danger {
  color: #f85149;
}

.action-btn.danger:hover {
  background: rgba(248, 81, 73, 0.1);
  border-color: rgba(248, 81, 73, 0.3);
}

.version-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  min-height: 28px;
}

.version-chip {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.version-chip:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.version-chip.active {
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2);
}

.empty-text {
  font-size: 12px;
  color: var(--text-tertiary);
  font-style: italic;
}
</style>
