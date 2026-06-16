<script setup>
import { ref, computed, reactive } from 'vue'
import TaskSidebar from '../components/agent/TaskSidebar.vue'
import InputPanel from '../components/agent/InputPanel.vue'
import ChatPanel from '../components/agent/ChatPanel.vue'
import MarkdownEditor from '../components/agent/MarkdownEditor.vue'
import { streamPlanning } from '../api/planning.js'

const props = defineProps({
  moduleId: { type: String, required: true },
})

const emit = defineEmits(['navigate'])

// ---- Module metadata ----
const MODULE_META = {
  planning: {
    name: '策划 Agent',
    subtitle: 'Game Design Agent',
    color: 'var(--accent-blue)',
    accent: 'blue',
  },
  art: { name: '美术 Agent', subtitle: 'Art Production Agent', color: 'var(--accent-pink)', accent: 'pink' },
  dev: { name: '研发 Agent', subtitle: 'Development Agent', color: 'var(--accent-green)', accent: 'green' },
  ops: { name: '运营 Agent', subtitle: 'Operations Agent', color: 'var(--accent-orange)', accent: 'orange' },
}

const meta = computed(() => MODULE_META[props.moduleId] || MODULE_META.planning)
const isPlanningModule = computed(() => props.moduleId === 'planning')

// ---- Planning sub-modules (from doc: 策划 Agent 输出) ----
const SUB_MODULES = [
  { id: 'gameplay', name: '玩法策划案', icon: '🎮', desc: '核心玩法机制与体验设计', template: (t) => `# ${t} - 玩法策划案\n\n## 1. 玩法目标\n描述本次设计要解决的核心体验目标。\n\n## 2. 核心机制\n详细描述系统的玩法规则与交互方式。\n\n## 3. 玩家行为路径\n玩家从进入到离开该玩法的完整链路。\n\n## 4. 反馈与奖励\n关键节点的正反馈设计。\n` },
  { id: 'activity', name: '活动规则', icon: '🎯', desc: '限时活动与运营节点规则', template: (t) => `# ${t} - 活动规则\n\n## 1. 活动周期\n开始与结束时间。\n\n## 2. 参与条件\n等级、阵营、地区等限制。\n\n## 3. 玩法流程\n参与步骤与交互节点。\n\n## 4. 奖励发放\n奖池与发放逻辑。\n` },
  { id: 'numeric', name: '数值设计', icon: '🔢', desc: '战斗、经济、成长曲线等数值', template: (t) => `# ${t} - 数值设计\n\n## 1. 设计目标\n本次数值要达成的体验目标。\n\n## 2. 关键公式\n核心数值公式与参数。\n\n## 3. 成长曲线\n玩家成长节奏与里程碑。\n\n## 4. 经济投放\n资源产出与回收。\n` },
  { id: 'requirement', name: '需求文档', icon: '📑', desc: '面向研发的功能需求详细说明', template: (t) => `# ${t} - 需求文档\n\n## 1. 背景与目标\n\n## 2. 功能列表\n- 功能 A\n- 功能 B\n\n## 3. 交互流程\n详细的用户操作流。\n\n## 4. 边界条件\n异常处理与容错说明。\n` },
  { id: 'acceptance', name: '验收标准', icon: '✅', desc: '功能上线前的验收清单', template: (t) => `# ${t} - 验收标准\n\n## 1. 功能验收\n- [ ] 主流程跑通\n- [ ] 边界情况处理\n\n## 2. 数值验收\n- [ ] 配置数值符合策划设计\n\n## 3. 表现验收\n- [ ] 美术资源正确\n- [ ] 音效正确\n\n## 4. 性能验收\n- [ ] 内存与帧率符合标准\n` },
  { id: 'dev_brief', name: '研发需求拆解', icon: '⚙️', desc: '面向研发同学的实现拆解', template: (t) => `# ${t} - 研发需求拆解\n\n## 1. 模块划分\n客户端 / 服务端 / 配置表\n\n## 2. 接口设计\n\n## 3. 风险点\n潜在的技术风险与缓解策略。\n` },
  { id: 'art_brief', name: '美术需求初稿', icon: '🎨', desc: '面向美术的素材需求初稿', template: (t) => `# ${t} - 美术需求初稿\n\n## 1. 风格定位\n参考素材与目标氛围。\n\n## 2. 素材清单\n- 角色/道具/场景\n\n## 3. 规格要求\n尺寸、格式、命名规范。\n` },
]

// ---- Top-level state ----
const view = ref('dashboard')

const tasks = ref([
  { id: 't1', name: '春节限时活动「福气连连看」' },
  { id: 't2', name: '新玩法「欢乐麻将馆」上线' },
  { id: 't3', name: '休闲三消关卡难度重做' },
  { id: 't4', name: '新手引导优化（连连看引导）' },
])

const activeTaskId = ref('t1')
const activeSubModuleId = ref(null)

const activeTask = computed(
  () => tasks.value.find((t) => t.id === activeTaskId.value) || tasks.value[0]
)
const activeSubModule = computed(() =>
  SUB_MODULES.find((m) => m.id === activeSubModuleId.value)
)

function handleAddTask() {
  const name = prompt('请输入新任务名称（例如：连连看新主题关卡）:')
  if (name && name.trim()) {
    const id = `t${Date.now()}`
    tasks.value.push({ id, name: name.trim() })
    activeTaskId.value = id
  }
}

function selectTask(id) {
  activeTaskId.value = id
  view.value = 'dashboard'
}

function openSubModule(id) {
  activeSubModuleId.value = id
  view.value = 'editor'
}

function backToDashboard() {
  view.value = 'dashboard'
}

// ---- Editor workspace state (per task+module key) ----
const DEFAULT_INPUT = `[游戏设置]
游戏类型: 休闲 / 麻将 + 连连看
休闲向: 是
PVP: 否（弱社交，可加好友互送体力）
游玩时长: 单局 1-3 分钟，碎片时间体验
----------------
[详细设定]
这是一款轻量级休闲消除游戏，把麻将牌面与连连看玩法结合：玩家在棋盘中点选两张相同牌，
需保证连接路径折线不超过 2 次拐弯即可消除。整体节奏轻松，主打"短平快"碎片体验。`

const stateCache = reactive({})

function getKey() {
  return `${activeTaskId.value}_${activeSubModuleId.value}`
}

function ensureState() {
  const key = getKey()
  if (!stateCache[key]) {
    const initialDoc = activeSubModule.value
      ? activeSubModule.value.template(activeTask.value.name)
      : ''
    stateCache[key] = {
      input: DEFAULT_INPUT,
      inputVersions: [DEFAULT_INPUT],
      inputVerIdx: 0,
      doc: initialDoc,
      docVersions: [initialDoc],
      docVerIdx: 0,
      // 当前任务+子模块下引用的知识库条目 key 列表
      knowledgeRefs: [],
      // 当前选用的模型 id；由 ChatPanel 的下拉控件维护，初始空
      // 等模型清单加载完会被自动赋上首项
      modelId: '',
      messages: [
        {
          id: 'init-' + Date.now(),
          role: 'model',
          content: `你好！我是策划 Agent · 设计助手。我们正在编辑 「${activeTask.value.name} - ${activeSubModule.value.name}」，告诉我你的想法即可。`,
          timestamp: Date.now(),
        },
      ],
      isThinking: false,
    }
  }
  return stateCache[key]
}

const editorState = computed(() =>
  view.value === 'editor' && activeSubModule.value ? ensureState() : null
)

const isInputOpen = ref(true)

// --- Input version handlers ---
function inputSave() {
  const s = editorState.value
  s.inputVersions = [...s.inputVersions, s.input]
  s.inputVerIdx = s.inputVersions.length - 1
}
function inputDelete() {
  const s = editorState.value
  if (s.inputVerIdx === null) return
  s.inputVersions = s.inputVersions.filter((_, i) => i !== s.inputVerIdx)
  if (s.inputVersions.length === 0) {
    s.inputVerIdx = null
  } else {
    const ni = Math.max(0, s.inputVerIdx - 1)
    s.inputVerIdx = ni
    s.input = s.inputVersions[ni]
  }
}
function inputLoad(i) {
  const s = editorState.value
  s.input = s.inputVersions[i]
  s.inputVerIdx = i
}
function inputUpdate(v) {
  const s = editorState.value
  s.input = v
  if (s.inputVerIdx !== null && s.inputVersions[s.inputVerIdx] !== v) {
    s.inputVerIdx = null
  }
}

// --- Doc version handlers ---
function docSave() {
  const s = editorState.value
  s.docVersions = [...s.docVersions, s.doc]
  s.docVerIdx = s.docVersions.length - 1
}
function docDelete() {
  const s = editorState.value
  if (s.docVerIdx === null) return
  s.docVersions = s.docVersions.filter((_, i) => i !== s.docVerIdx)
  if (s.docVersions.length === 0) {
    s.docVerIdx = null
  } else {
    const ni = Math.max(0, s.docVerIdx - 1)
    s.docVerIdx = ni
    s.doc = s.docVersions[ni]
  }
}
function docLoad(i) {
  const s = editorState.value
  s.doc = s.docVersions[i]
  s.docVerIdx = i
}
function docUpdate(v) {
  const s = editorState.value
  s.doc = v
  if (s.docVerIdx !== null) s.docVerIdx = null
}

// --- Chat：调真实流式接口 ---
// 知识库内容（含图片 base64）由后端 services/kb_context 统一读取，
// 前端只需把已选条目的三段式 key 数组原样传过去。

async function sendMessage(text) {
  const s = editorState.value
  if (!s.modelId) {
    // 模型清单还没加载完成，给个温和提示，避免后端 400
    s.messages.push({
      id: 'sys-' + Date.now(),
      role: 'model',
      content: '⚠ 模型清单尚未就绪，请稍候再试。',
      timestamp: Date.now(),
    })
    return
  }

  s.messages.push({
    id: 'u-' + Date.now(),
    role: 'user',
    content: text,
    timestamp: Date.now(),
  })

  // 预先插入一条 model 消息，作为流式追加的目标
  const modelMsg = reactive({
    id: 'm-' + Date.now(),
    role: 'model',
    content: '',
    timestamp: Date.now(),
  })
  s.messages.push(modelMsg)
  s.isThinking = true // 等首字到达前展示 thinking 占位

  let firstDeltaArrived = false

  await streamPlanning(
    {
      user_input: text,
      model_id: s.modelId,
      sub_module: activeSubModuleId.value || 'gameplay',
      project_brief: s.input || '',
      kb_refs: s.knowledgeRefs || [],
    },
    {
      onDelta: (delta) => {
        if (!firstDeltaArrived) {
          firstDeltaArrived = true
          s.isThinking = false
        }
        modelMsg.content += delta
      },
      onError: (err) => {
        modelMsg.content = (modelMsg.content || '') + `\n\n⚠ 出错：${err}`
      },
      onDone: () => {
        s.isThinking = false
        // 把生成的内容也同步到右侧文档草稿，作为本次产出
        if (modelMsg.content) {
          s.doc = (s.doc ? s.doc + '\n\n' : '') + modelMsg.content
          s.docVerIdx = null
        }
      },
    }
  )
}
</script>

<template>
  <div class="agent-view">
    <!-- 顶部栏 -->
    <header class="agent-topbar">
      <button class="back-btn" @click="emit('navigate', 'home')">
        ← 主界面
      </button>
      <div class="crumbs">
        <span class="crumb">{{ meta.name }}</span>
        <span class="sep">/</span>
        <span class="crumb">{{ activeTask?.name || '—' }}</span>
        <template v-if="view === 'editor' && activeSubModule">
          <span class="sep">/</span>
          <span class="crumb current">{{ activeSubModule.name }}</span>
        </template>
      </div>
      <div class="topbar-right">
        <button class="ghost-btn">📚 知识库</button>
        <button class="ghost-btn">⏱ 历史记录</button>
        <div class="avatar-mini">U</div>
      </div>
    </header>

    <!-- Body -->
    <div v-if="!isPlanningModule" class="placeholder">
      <div class="placeholder-card">
        <div class="placeholder-icon">🚧</div>
        <div class="placeholder-title">{{ meta.name }} 工作台</div>
        <div class="placeholder-desc">该模块正在搭建中，本次 Demo 重点呈现「策划 Agent」流程。</div>
        <button class="primary-btn" @click="emit('navigate', 'agent', 'planning')">
          切换到策划 Agent →
        </button>
      </div>
    </div>

    <div v-else class="agent-body">
      <TaskSidebar
        :tasks="tasks"
        :active-task-id="activeTaskId"
        title="策划任务"
        @select="selectTask"
        @add="handleAddTask"
      />

      <!-- Dashboard -->
      <main v-if="view === 'dashboard'" class="dashboard">
        <div class="project-banner">
          <div class="banner-icon">🎮</div>
          <div class="banner-content">
            <div class="banner-title">项目：欢乐麻将连连看 · 休闲消除</div>
            <div class="banner-desc">
              麻将牌面 + 连连看消除玩法，主打碎片化时间内的"轻松通关"体验。本次任务：
              <strong>{{ activeTask?.name }}</strong>。请在下方选择要产出的成果物。
            </div>
          </div>
          <div class="banner-tags">
            <span class="b-tag">休闲</span>
            <span class="b-tag">麻将</span>
            <span class="b-tag">连连看</span>
          </div>
        </div>

        <div class="dashboard-section">
          <div class="section-title">
            <span>选择产出物</span>
            <span class="section-hint">点击进入编辑工作台</span>
          </div>
          <div class="module-grid">
            <button
              v-for="m in SUB_MODULES"
              :key="m.id"
              class="module-card"
              @click="openSubModule(m.id)"
            >
              <div class="module-icon">{{ m.icon }}</div>
              <div class="module-name">{{ m.name }}</div>
              <div class="module-desc">{{ m.desc }}</div>
              <div class="module-foot">点击编辑文档 →</div>
            </button>
          </div>
        </div>
      </main>

      <!-- Editor Workspace -->
      <main v-else class="editor-workspace">
        <InputPanel
          :is-open="isInputOpen"
          :model-value="editorState.input"
          :versions="editorState.inputVersions"
          :current-version-index="editorState.inputVerIdx"
          :knowledge-refs="editorState.knowledgeRefs"
          @toggle="isInputOpen = !isInputOpen"
          @update:model-value="inputUpdate"
          @update:knowledge-refs="(v) => (editorState.knowledgeRefs = v)"
          @save="inputSave"
          @delete="inputDelete"
          @load="inputLoad"
        />

        <div class="chat-col" :class="{ collapsed: !isInputOpen }">
          <div class="back-strip">
            <button class="back-mini" @click="backToDashboard">← 返回模块</button>
            <span class="ctx-title">{{ activeSubModule?.name }}</span>
          </div>
          <ChatPanel
            :messages="editorState.messages"
            :is-thinking="editorState.isThinking"
            :model-id="editorState.modelId"
            @update:model-id="(v) => (editorState.modelId = v)"
            @send="sendMessage"
          />
        </div>

        <div class="doc-col">
          <MarkdownEditor
            :model-value="editorState.doc"
            :versions="editorState.docVersions"
            :current-version-index="editorState.docVerIdx"
            :default-export-title="`${activeTask?.name || ''} - ${activeSubModule?.name || ''}`"
            default-export-module="planning"
            default-export-category="docs"
            @update:model-value="docUpdate"
            @save="docSave"
            @delete="docDelete"
            @load="docLoad"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.agent-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-primary);
}

/* Top bar */
.agent-topbar {
  height: 56px;
  flex-shrink: 0;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1.5px solid var(--border-color);
  background: var(--bg-secondary);
}

.back-btn {
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.back-btn:hover {
  background: var(--bg-hover);
  color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.crumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.crumb {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.crumb.current {
  color: var(--accent-blue);
  font-weight: 700;
}

.sep {
  color: var(--text-tertiary);
  font-size: 12px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ghost-btn {
  padding: 5px 10px;
  font-size: 12px;
  color: var(--text-secondary);
  background: transparent;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.ghost-btn:hover {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.avatar-mini {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-pink), var(--accent-orange));
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Body */
.agent-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* Dashboard */
.dashboard {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
}

.project-banner {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 20px 24px;
  background: linear-gradient(
    135deg,
    rgba(77, 158, 255, 0.10),
    rgba(168, 124, 255, 0.06)
  );
  border: 1.5px solid rgba(77, 158, 255, 0.4);
  border-radius: var(--radius-lg);
  margin-bottom: 28px;
}

.banner-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--accent-blue-dim);
  border: 1.5px solid rgba(77, 158, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.banner-content {
  flex: 1;
  min-width: 0;
}

.banner-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
  letter-spacing: -0.01em;
}

.banner-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.banner-desc strong {
  color: var(--accent-blue);
  font-weight: 600;
}

.banner-tags {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.b-tag {
  font-size: 10px;
  color: var(--accent-blue);
  background: var(--accent-blue-dim);
  border: 1px solid rgba(77, 158, 255, 0.3);
  padding: 2px 8px;
  border-radius: 3px;
  text-align: center;
  letter-spacing: 0.04em;
  font-weight: 600;
}

.dashboard-section {
  max-width: 1100px;
  margin: 0 auto;
}

.section-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title > span:first-child {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.section-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-weight: 500;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.module-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 22px;
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-lg);
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 160px;
}

.module-card:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.module-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  border: 1.5px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  margin-bottom: 4px;
  transition: all 0.2s;
}

.module-card:hover .module-icon {
  background: var(--accent-blue-dim);
  border-color: rgba(77, 158, 255, 0.35);
}

.module-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.module-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.module-foot {
  margin-top: auto;
  font-size: 11px;
  color: var(--text-tertiary);
  padding-top: 8px;
  width: 100%;
  border-top: 1px solid var(--border-color);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-weight: 500;
}

.module-card:hover .module-foot {
  color: var(--accent-blue);
}

/* Editor Workspace */
.editor-workspace {
  flex: 1;
  display: flex;
  min-height: 0;
  position: relative;
}

.chat-col {
  width: 400px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1.5px solid var(--border-color);
  min-height: 0;
}

.chat-col.collapsed {
  width: 440px;
}

.back-strip {
  flex-shrink: 0;
  padding: 10px 20px;
  background: var(--bg-tertiary);
  border-bottom: 1.5px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.back-mini {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  transition: all 0.15s;
}

.back-mini:hover {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.ctx-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--accent-blue);
  letter-spacing: 0.02em;
}

.doc-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* Placeholder for non-planning modules */
.placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.placeholder-card {
  max-width: 400px;
  text-align: center;
  padding: 40px;
  background: var(--bg-secondary);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.placeholder-icon {
  font-size: 56px;
  margin-bottom: 16px;
}

.placeholder-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.01em;
}

.placeholder-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 24px;
  line-height: 1.6;
}

.primary-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  color: #fff;
  border: 1.5px solid rgba(77, 158, 255, 0.5);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 700;
  box-shadow: 2px 2px 0 var(--shadow-blue);
  transition: all 0.15s;
}

.primary-btn:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 var(--shadow-blue);
}
</style>
