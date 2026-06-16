<script setup>
import { computed, onMounted, ref } from 'vue'
import VersionFooter from './VersionFooter.vue'
import { uploadKbItem } from '../../api/knowledge.js'
import {
  KB_MODULES,
  ensureKbLoaded,
  getCategoryLabel,
  getFoldersOf,
  kbStore,
  refreshKb,
} from '../../data/knowledgeBase.js'

const props = defineProps({
  modelValue: { type: String, default: '' },
  versions: { type: Array, default: () => [] },
  currentVersionIndex: { type: Number, default: null },
  // 默认导出标题，父组件可传当前任务/子模块名进来
  defaultExportTitle: { type: String, default: '' },
  // 默认目标模块/分类（缺省定位到「策划/文档」）
  defaultExportModule: { type: String, default: 'planning' },
  defaultExportCategory: { type: String, default: 'docs' },
})

const emit = defineEmits(['update:modelValue', 'save', 'delete', 'load'])

const mode = ref('edit')

const wordCount = computed(
  () => (props.modelValue || '').replace(/\s+/g, '').length
)

// 极简版 markdown 渲染（与既有逻辑保持一致，未引入第三方解析库以维持简单）
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

// ---- 导出到知识库：弹窗与表单状态 ----------------------------------------

const exportOpen = ref(false)
const exporting = ref(false)
const exportError = ref('')
const exportSuccess = ref('')

// 表单字段
const exportModule = ref(props.defaultExportModule)
const exportCategory = ref(props.defaultExportCategory)
const exportFolder = ref('')
const exportTitle = ref('')
const exportTags = ref('')
const exportSummary = ref('')

// 当前模块的可选分类列表（来自后端 KB_MODULE_CATEGORIES）
const categoriesOfModule = computed(
  () => kbStore.modulesMap[exportModule.value] || []
)

// 当前 (module, category) 下所有已登记文件夹
const foldersOfCategory = computed(() =>
  getFoldersOf(exportModule.value, exportCategory.value)
)

// 打开弹窗：拉一次 KB store 以保证模块/分类/文件夹下拉有数据
function openExportDialog() {
  exportError.value = ''
  exportSuccess.value = ''
  // 标题默认值：父组件传进来的 defaultExportTitle，或回退到首行 # 标题
  exportTitle.value = (props.defaultExportTitle || _firstHeading() || 'untitled').trim()
  exportTags.value = ''
  exportSummary.value = ''
  // 模块/分类回到默认值，避免上次的选择残留干扰
  exportModule.value = props.defaultExportModule || 'planning'
  exportCategory.value = props.defaultExportCategory || 'docs'
  exportFolder.value = ''
  exportOpen.value = true
  ensureKbLoaded().then(() => {
    // 加载完成后若默认 category 不在列表中，回退到第一项，避免提交 400
    const cats = kbStore.modulesMap[exportModule.value] || []
    if (cats.length && !cats.includes(exportCategory.value)) {
      exportCategory.value = cats[0]
    }
  })
}

function closeExportDialog() {
  if (exporting.value) return
  exportOpen.value = false
}

// 切换 module 时把 category 校正到合法值
function onModuleChange() {
  const cats = kbStore.modulesMap[exportModule.value] || []
  if (cats.length && !cats.includes(exportCategory.value)) {
    exportCategory.value = cats[0]
  }
  exportFolder.value = ''
}

function onCategoryChange() {
  exportFolder.value = ''
}

// 取 markdown 第一行 # 标题（# / ## / ### 都可），失败返回 ''
function _firstHeading() {
  const txt = props.modelValue || ''
  const m = txt.match(/^#{1,6}\s+(.+)$/m)
  return m ? m[1].trim() : ''
}

// 把标题清洗成合法文件名，与后端 _safe_filename 规则一致
function _safeStem(name) {
  return (name || '').replace(/[^0-9A-Za-z_.\-一-龥 ]+/g, '_').slice(0, 80)
}

// 解析逗号分隔标签
function _parseTags() {
  return exportTags.value
    .replace(/，/g, ',')
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
}

async function submitExport() {
  if (!exportModule.value || !exportCategory.value) {
    exportError.value = '请选择目标模块与分类'
    return
  }
  const stem = _safeStem(exportTitle.value) || 'untitled'
  const filename = `${stem}.md`
  // markdown 字符串包成 File 直接走现有上传接口；后端会按 (folder, stored_name)
  // 自动登记到 index，无需额外接口
  const blob = new Blob([props.modelValue || ''], {
    type: 'text/markdown;charset=utf-8',
  })
  const file = new File([blob], filename, { type: 'text/markdown' })

  exporting.value = true
  exportError.value = ''
  exportSuccess.value = ''
  try {
    await uploadKbItem(exportModule.value, exportCategory.value, {
      file,
      title: exportTitle.value.trim(),
      summary: exportSummary.value.trim(),
      tags: _parseTags(),
      folder: exportFolder.value || '',
    })
    // 同步刷新前端 store，让知识库管理界面立即看到新条目
    await refreshKb()
    exportSuccess.value = '已导出到知识库'
    // 0.8 秒后自动关闭弹窗，给用户一点视觉反馈
    setTimeout(() => {
      exportOpen.value = false
    }, 800)
  } catch (e) {
    exportError.value = e?.message || '导出失败'
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  // 弹窗未打开时也预热一下 store，避免首次点开有空白
  ensureKbLoaded()
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
    >
      <!-- 在「保存」按钮左侧注入「导出到知识库」 -->
      <template #actions-pre>
        <button
          class="action-btn export"
          title="导出当前文档到知识库"
          :disabled="!modelValue"
          @click="openExportDialog"
        >
          📤 导出到知识库
        </button>
      </template>
    </VersionFooter>

    <!-- 导出弹窗：选择 module/category/folder + 元信息 ------------------- -->
    <div v-if="exportOpen" class="md-modal-mask" @click.self="closeExportDialog">
      <div class="md-modal">
        <div class="md-modal-head">
          <strong>导出到知识库</strong>
          <button class="md-modal-close" @click="closeExportDialog">×</button>
        </div>
        <div class="md-modal-body">
          <!-- 加载状态：分类列表还没就绪时给个提示 -->
          <div v-if="kbStore.loading && !kbStore.loaded" class="md-modal-tip">
            正在加载知识库分类信息…
          </div>
          <div v-else-if="kbStore.error" class="md-modal-error">
            ⚠ 加载失败：{{ kbStore.error }}
          </div>

          <div class="md-form">
            <label class="md-field">
              <span>模块</span>
              <select v-model="exportModule" @change="onModuleChange">
                <option
                  v-for="m in KB_MODULES"
                  :key="m.id"
                  :value="m.id"
                >
                  {{ m.icon }} {{ m.name }}
                </option>
              </select>
            </label>

            <label class="md-field">
              <span>分类</span>
              <select v-model="exportCategory" @change="onCategoryChange">
                <option
                  v-for="cat in categoriesOfModule"
                  :key="cat"
                  :value="cat"
                >
                  {{ getCategoryLabel(cat) }}
                </option>
              </select>
            </label>

            <label class="md-field full">
              <span>目标文件夹</span>
              <select v-model="exportFolder">
                <option value="">(根目录)</option>
                <option
                  v-for="f in foldersOfCategory"
                  :key="f.path"
                  :value="f.path"
                >
                  {{ f.path }}{{ f.desc ? ' — ' + f.desc : '' }}
                </option>
              </select>
            </label>

            <label class="md-field full">
              <span>标题（同时作为文件名 *.md）</span>
              <input
                v-model="exportTitle"
                placeholder="留空则使用 untitled"
              />
            </label>

            <label class="md-field full">
              <span>标签（逗号分隔，可选）</span>
              <input
                v-model="exportTags"
                placeholder="例如：玩法,策划案"
              />
            </label>

            <label class="md-field full">
              <span>摘要（可选）</span>
              <textarea
                v-model="exportSummary"
                rows="2"
                placeholder="一句话说明这份文档的用途，便于 RAG 检索"
              />
            </label>
          </div>

          <div v-if="exportError" class="md-modal-error">⚠ {{ exportError }}</div>
          <div v-if="exportSuccess" class="md-modal-ok">✓ {{ exportSuccess }}</div>
        </div>

        <div class="md-modal-foot">
          <button
            class="md-btn ghost"
            type="button"
            :disabled="exporting"
            @click="closeExportDialog"
          >
            取消
          </button>
          <button
            class="md-btn primary"
            type="button"
            :disabled="exporting || !modelValue"
            @click="submitExport"
          >
            {{ exporting ? '导出中…' : '导出' }}
          </button>
        </div>
      </div>
    </div>
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
  border-bottom: 1.5px solid var(--border-color);
  background: var(--bg-card);
}

.left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent-purple);
  background: var(--accent-purple-dim);
  border: 1px solid rgba(168, 124, 255, 0.3);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.05em;
}

.meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.mode-switch {
  display: inline-flex;
  background: var(--bg-tertiary);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 3px;
  gap: 2px;
}

.mode-btn {
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 4px;
  color: var(--text-tertiary);
  border: 1px solid transparent;
  transition: all 0.15s;
}

.mode-btn:hover {
  color: var(--text-primary);
}

.mode-btn.active {
  background: var(--bg-card);
  color: var(--accent-blue);
  border-color: var(--border-color);
  box-shadow: 1px 1px 0 var(--border-color);
}

.content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.editor {
  width: 100%;
  height: 100%;
  padding: 24px 36px;
  background: transparent;
  color: var(--text-primary);
  border: none;
  outline: none;
  resize: none;
  font-family: var(--font-mono);
  font-size: 14px;
  line-height: 1.7;
}

.editor::selection {
  background: rgba(77, 158, 255, 0.25);
}

.preview {
  width: 100%;
  height: 100%;
  padding: 24px 36px;
  overflow-y: auto;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.75;
}

.preview :deep(h1) {
  color: var(--text-primary);
  font-size: 26px;
  margin: 18px 0 12px;
  font-weight: 800;
  border-bottom: 1.5px solid var(--border-color);
  padding-bottom: 8px;
  letter-spacing: -0.02em;
}

.preview :deep(h2) {
  color: var(--text-primary);
  font-size: 20px;
  margin: 16px 0 10px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.preview :deep(h3) {
  color: var(--text-primary);
  font-size: 16px;
  margin: 12px 0 8px;
  font-weight: 700;
}

.preview :deep(strong) {
  color: var(--accent-blue);
  font-weight: 700;
}

.preview :deep(em) {
  color: var(--accent-purple);
}

.preview :deep(code) {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 1px 6px;
  font-family: var(--font-mono);
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

/* 导出按钮 */
.action-btn.export {
  padding: 4px 10px;
  font-size: 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--accent-purple);
  border: 1px solid rgba(168, 124, 255, 0.4);
  box-shadow: 2px 2px 0 var(--shadow-purple);
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.action-btn.export:hover:not(:disabled) {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 var(--shadow-purple);
  background: var(--accent-purple-dim);
  border-color: var(--accent-purple);
}

.action-btn.export:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

/* 导出弹窗 */
.md-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.md-modal {
  width: min(560px, 100%);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 4px 4px 0 var(--border-color), 0 20px 60px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.md-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1.5px solid var(--border-color);
  background: var(--bg-tertiary);
}

.md-modal-head strong {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.md-modal-close {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  font-size: 18px;
  color: var(--text-tertiary);
  background: transparent;
  border: 1.5px solid transparent;
  transition: all 0.15s;
}

.md-modal-close:hover {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.md-modal-body {
  padding: 18px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.md-modal-tip {
  font-size: 12px;
  color: var(--text-tertiary);
}

.md-modal-error {
  font-size: 12px;
  color: #f85149;
  background: rgba(248, 81, 73, 0.08);
  border: 1.5px solid rgba(248, 81, 73, 0.3);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
}

.md-modal-ok {
  font-size: 12px;
  color: var(--accent-green);
  background: var(--accent-green-dim);
  border: 1.5px solid rgba(46, 160, 67, 0.35);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
}

.md-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.md-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.md-field.full {
  grid-column: span 2;
}

.md-field span {
  font-size: 11px;
  color: var(--text-tertiary);
  letter-spacing: 0.04em;
  font-weight: 700;
  text-transform: uppercase;
}

.md-field input,
.md-field select,
.md-field textarea {
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 7px 10px;
  font-size: 13px;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s, background 0.15s;
  font-family: inherit;
}

.md-field textarea {
  resize: vertical;
  min-height: 56px;
}

.md-field input:focus,
.md-field select:focus,
.md-field textarea:focus {
  border-color: var(--accent-blue);
  background: var(--bg-tertiary);
}

.md-modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1.5px solid var(--border-color);
  background: var(--bg-tertiary);
}

.md-btn {
  padding: 7px 16px;
  font-size: 13px;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border-color);
  font-weight: 600;
  transition: all 0.15s;
}

.md-btn.ghost {
  background: var(--bg-card);
  color: var(--text-secondary);
}

.md-btn.ghost:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.md-btn.primary {
  background: var(--accent-blue);
  color: #fff;
  border-color: rgba(77, 158, 255, 0.6);
  box-shadow: 2px 2px 0 var(--shadow-blue);
}

.md-btn.primary:hover:not(:disabled) {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 var(--shadow-blue);
}

.md-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
