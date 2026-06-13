<script setup>
import { reactive, watch } from 'vue'
import VersionFooter from './VersionFooter.vue'
import KnowledgeRefBlock from './KnowledgeRefBlock.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: true },
  modelValue: { type: String, default: '' },
  versions: { type: Array, default: () => [] },
  currentVersionIndex: { type: Number, default: null },
  // 已引用的知识库条目 key 列表，由父级 stateCache 维护
  knowledgeRefs: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'toggle',
  'update:modelValue',
  'update:knowledgeRefs',
  'save',
  'delete',
  'load',
])

const form = reactive({
  type: '',
  isCasual: false,
  hasPvp: false,
  playtime: '',
  description: '',
})

let internalUpdate = false

function parseContent(content) {
  const newState = {
    type: '',
    isCasual: false,
    hasPvp: false,
    playtime: '',
    description: '',
  }
  const lines = (content || '').split('\n')
  let inDesc = false
  const descLines = []
  for (const line of lines) {
    if (line.trim() === '[详细设定]') {
      inDesc = true
      continue
    }
    if (inDesc) {
      descLines.push(line)
      continue
    }
    if (line.startsWith('游戏类型:')) newState.type = line.split(':')[1]?.trim() || ''
    else if (line.startsWith('休闲向:')) newState.isCasual = (line.split(':')[1] || '').trim() === '是'
    else if (line.startsWith('PVP:')) newState.hasPvp = (line.split(':')[1] || '').trim() === '是'
    else if (line.startsWith('游玩时长:')) newState.playtime = line.split(':')[1]?.trim() || ''
  }
  newState.description = descLines.join('\n').trim()
  return newState
}

function serialize(s) {
  return `[游戏设置]
游戏类型: ${s.type}
休闲向: ${s.isCasual ? '是' : '否'}
PVP: ${s.hasPvp ? '是' : '否'}
游玩时长: ${s.playtime}
----------------
[详细设定]
${s.description}`
}

watch(
  () => props.modelValue,
  (val) => {
    if (internalUpdate) {
      internalUpdate = false
      return
    }
    Object.assign(form, parseContent(val))
  },
  { immediate: true }
)

function update(patch) {
  Object.assign(form, patch)
  internalUpdate = true
  emit('update:modelValue', serialize(form))
}
</script>

<template>
  <div v-if="isOpen" class="input-panel">
    <div class="panel-header">
      <h2>游戏配置</h2>
      <button class="icon-btn" title="收起" @click="emit('toggle')">‹</button>
    </div>
    <div class="panel-body">
      <div class="form-section">
        <div class="section-label">核心设置</div>

        <div class="form-row">
          <label>游戏类型 / 题材</label>
          <input
            type="text"
            :value="form.type"
            placeholder="例如：休闲、麻将、三消、连连看"
            @input="update({ type: $event.target.value })"
          />
        </div>

        <div class="form-row-double">
          <div class="form-row">
            <label>休闲向</label>
            <div class="toggle-group">
              <button
                class="toggle"
                :class="{ active: form.isCasual }"
                @click="update({ isCasual: true })"
              >
                是
              </button>
              <button
                class="toggle"
                :class="{ active: !form.isCasual }"
                @click="update({ isCasual: false })"
              >
                否
              </button>
            </div>
          </div>
          <div class="form-row">
            <label>PVP 对战</label>
            <div class="toggle-group">
              <button
                class="toggle"
                :class="{ active: form.hasPvp }"
                @click="update({ hasPvp: true })"
              >
                是
              </button>
              <button
                class="toggle"
                :class="{ active: !form.hasPvp }"
                @click="update({ hasPvp: false })"
              >
                否
              </button>
            </div>
          </div>
        </div>

        <div class="form-row">
          <label>单局/日游玩时长</label>
          <input
            type="text"
            :value="form.playtime"
            placeholder="例如：30分钟, 2小时"
            @input="update({ playtime: $event.target.value })"
          />
        </div>
      </div>

      <div class="hr"></div>

      <div class="form-section flex-fill">
        <div class="section-label">详细描述与约束</div>
        <textarea
          :value="form.description"
          placeholder="描述游戏世界观、美术风格、具体机制或任何其他约束条件..."
          @input="update({ description: $event.target.value })"
        ></textarea>
      </div>

      <div class="hr"></div>

      <div class="form-section">
        <div class="section-label">知识库引用</div>
        <KnowledgeRefBlock
          dense
          :model-value="knowledgeRefs"
          @update:model-value="emit('update:knowledgeRefs', $event)"
        />
      </div>
    </div>

    <VersionFooter
      label="保存的配置"
      :versions="versions"
      :current-version-index="currentVersionIndex"
      @save="emit('save')"
      @delete="emit('delete')"
      @load="(i) => emit('load', i)"
    />
  </div>

  <button v-else class="reopen-btn" title="展开配置面板" @click="emit('toggle')">
    ›
  </button>
</template>

<style scoped>
.input-panel {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
}

.panel-header {
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.panel-header h2 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.icon-btn {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  font-size: 16px;
  line-height: 1;
}

.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-tertiary);
  letter-spacing: 0.8px;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.form-section {
  display: flex;
  flex-direction: column;
}

.form-section.flex-fill {
  flex: 1;
  min-height: 0;
}

.form-section.flex-fill textarea {
  flex: 1;
  min-height: 180px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.form-row label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.form-row input,
.form-row textarea {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  font-size: 13px;
  color: var(--text-primary);
  font-family: inherit;
  transition: border-color 0.15s;
  outline: none;
}

.form-row textarea {
  resize: none;
  line-height: 1.6;
}

.form-row input:focus,
.form-row textarea:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.15);
}

.form-row-double {
  display: flex;
  gap: 12px;
}

.form-row-double > .form-row {
  flex: 1;
}

.toggle-group {
  display: flex;
  gap: 6px;
}

.toggle {
  flex: 1;
  padding: 6px 10px;
  font-size: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.toggle:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.toggle.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: #fff;
}

.hr {
  height: 1px;
  background: var(--border-color);
}

.reopen-btn {
  position: absolute;
  left: 0;
  top: 76px;
  z-index: 30;
  padding: 8px 6px;
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-left: none;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 16px;
  line-height: 1;
}

.reopen-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
</style>
