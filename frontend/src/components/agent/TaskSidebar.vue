<script setup>
defineProps({
  tasks: { type: Array, required: true },
  activeTaskId: { type: String, default: null },
  title: { type: String, default: '任务列表' },
})

const emit = defineEmits(['select', 'add'])
</script>

<template>
  <aside class="task-sidebar">
    <div class="sidebar-header">
      <h2>{{ title }}</h2>
      <span class="count">{{ tasks.length }}</span>
    </div>
    <div class="task-list">
      <button
        v-for="task in tasks"
        :key="task.id"
        class="task-item"
        :class="{ active: task.id === activeTaskId }"
        @click="emit('select', task.id)"
      >
        <span class="task-dot"></span>
        <span class="task-name">{{ task.name }}</span>
      </button>
    </div>
    <button class="add-btn" @click="emit('add')">
      <span class="plus">+</span>
      <span>新增任务</span>
    </button>
  </aside>
</template>

<style scoped>
.task-sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-right: 1.5px solid var(--border-color);
}

.sidebar-header {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1.5px solid var(--border-color);
  background: var(--bg-secondary);
}

.sidebar-header h2 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.count {
  font-size: 11px;
  color: var(--text-tertiary);
  background: var(--bg-card);
  padding: 2px 8px;
  border-radius: 3px;
  border: 1px solid var(--border-color);
  font-weight: 600;
}

.task-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.task-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  text-align: left;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  border-left: 3px solid transparent;
  transition: all 0.15s;
}

.task-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.task-item.active {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-left-color: var(--accent-blue);
  font-weight: 700;
}

.task-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-tertiary);
  flex-shrink: 0;
}

.task-item.active .task-dot {
  background: var(--accent-blue);
  box-shadow: 0 0 10px var(--accent-blue);
}

.task-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.add-btn {
  margin: 16px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  color: #fff;
  border: 1.5px solid rgba(77, 158, 255, 0.5);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  box-shadow: 2px 2px 0 var(--shadow-blue);
  transition: all 0.15s;
}

.add-btn:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 var(--shadow-blue);
}

.plus {
  font-size: 16px;
  line-height: 1;
}
</style>
