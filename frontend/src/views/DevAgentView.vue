<script setup>
// 研发 Agent 工作台
// ----------------------------------------------------------------
// 三大子模块（参考 ArtAgentView 的两层结构）：
//   1) 代码智能 review —— 本地 git 提交触发的审查
//   2) 功能开发      —— 在已有项目中迭代功能
//   3) Demo 生成     —— 新游戏 / 新玩法的快速搭建
// 用户在 Dashboard 选择模块 → 进入任务管理（左侧任务列表 + 右侧任务详情）。
// 当前阶段全部为前端 mock，无后端接口；保留与策划/美术一致的视觉与交互。

import { computed, onMounted, reactive, ref } from 'vue'
import TaskSidebar from '../components/agent/TaskSidebar.vue'
import KnowledgeRefBlock from '../components/agent/KnowledgeRefBlock.vue'
import { ensureModelsLoaded, modelStore } from '../api/models.js'
import { streamDemoGenerate, streamDemoPlan } from '../api/devDemo.js'

const emit = defineEmits(['navigate'])

// ---- 子模块定义 -----------------------------------------------------------
const SUB_MODULES = [
  {
    id: 'review',
    name: '代码智能 Review',
    subtitle: 'AI Code Review',
    desc: '本地开发分支提交时自动触发，对 diff 做静态审查与建议',
    icon: '🔍',
    accent: '#3fb950', // 绿色，对应研发模块色
    bullets: ['Pre-commit 钩子触发', '风格 / 安全 / 复杂度多维度', '改进建议可一键采纳'],
    inputs: '当前提交 diff · 仓库历史规范 · 项目知识库',
    outputs: '问题清单 · 重构建议 · 风险评估',
  },
  {
    id: 'feature',
    name: '功能开发',
    subtitle: 'Feature Development',
    desc: '基于已有项目代码完成新需求实现，自动定位相关文件并生成补丁',
    icon: '🛠️',
    accent: '#58a6ff',
    bullets: ['需求 → 涉及文件定位', '方案设计 → 代码补丁', '可对照原文件做 diff 预览'],
    inputs: '需求描述 · 项目代码库 · 历史相似实现',
    outputs: '改动方案 · 代码补丁 · 自测用例',
  },
  {
    id: 'demo',
    name: 'Demo 生成',
    subtitle: 'Demo Scaffolding',
    desc: '从一段玩法描述快速生成可运行的最小工程（脚本 + 配置 + 资源占位）',
    icon: '🚀',
    accent: '#f0883e',
    bullets: ['模板：连连看 / 三消 / 麻将 / 推箱子 / ...', '脚本逻辑 + 关卡配置同步生成', '产物可直接打包运行'],
    inputs: '玩法描述 · 引擎 / 模板选择 · 风格参考',
    outputs: '工程结构 · 主要脚本 · 资源占位',
  },
]

const subModuleMap = Object.fromEntries(SUB_MODULES.map((m) => [m.id, m]))

// ---- 顶层视图状态 ---------------------------------------------------------
// 'dashboard' = 模块卡片选择；'tasks' = 进入某子模块的任务管理
const view = ref('dashboard')
const activeSubId = ref(null)

const activeSub = computed(() => (activeSubId.value ? subModuleMap[activeSubId.value] : null))

function openSubModule(id) {
  activeSubId.value = id
  view.value = 'tasks'
}

function backToDashboard() {
  view.value = 'dashboard'
  activeSubId.value = null
}

// ---- Mock 任务数据 --------------------------------------------------------
// 三个子模块各自维护一份任务清单；任务详情字段按子模块差异化
const tasksByModule = reactive({
  review: [
    {
      id: 'r1',
      name: 'feat: 麻将连连看「双人对战」玩法',
      status: 'reviewed',
      createdAt: '2026-06-10 18:42',
      branch: 'feature/mahjong-pvp',
      author: '张小宇',
      commitHash: 'a93f01c',
      filesChanged: 7,
      additions: 312,
      deletions: 84,
      summary:
        '本次提交完成双人对战房间的服务端撮合与结算逻辑。整体结构清晰，但有 1 处可能在玩家中途掉线时引发空指针，2 处建议提取常量。',
      issues: [
        { level: 'high', file: 'server/match/mahjong_pvp.go', line: 142, msg: '`room.Players` 在玩家掉线时可能为 nil，建议加 nil-check' },
        { level: 'medium', file: 'server/match/mahjong_pvp.go', line: 87, msg: '魔法数 `120`（单局倒计时）建议提取为 `RoundTimeoutSec`' },
        { level: 'low', file: 'config/mahjong_levels.xlsx', line: null, msg: '新增牌型字段缺少注释，建议补充牌面映射说明' },
      ],
      suggestion:
        '将 `Settle()` 中的玩家遍历包成防御式拷贝，避免运行期 panic；同时把倒计时常量提取到 `match/const.go`。',
    },
    {
      id: 'r2',
      name: 'fix: 连连看路径检测「2 折」边界判定',
      status: 'pending',
      createdAt: '2026-06-10 14:08',
      branch: 'fix/path-corner',
      author: '李研',
      commitHash: '1c04e9d',
      filesChanged: 2,
      additions: 18,
      deletions: 6,
      summary: '正在审查中…',
      issues: [],
      suggestion: '',
    },
    {
      id: 'r3',
      name: 'refactor: 牌面贴图加载缓存策略',
      status: 'reviewed',
      createdAt: '2026-06-09 21:50',
      branch: 'refactor/tile-cache',
      author: '王浩',
      commitHash: '7df8a32',
      filesChanged: 4,
      additions: 96,
      deletions: 152,
      summary:
        '把原先的同步加载链路改为按帧调度的异步队列，整体收益可观。但 `LRU.Evict` 触发节奏可能在低端机偏激进，导致连续切关时贴图闪烁。',
      issues: [
        { level: 'medium', file: 'client/asset/lru.go', line: 64, msg: '`maxBytes` 默认值偏低，建议按机型分级' },
      ],
      suggestion: '低端机阈值降一档，并加一条监控埋点观察贴图淘汰频次。',
    },
  ],

  feature: [
    {
      id: 'f1',
      name: '连连看新增「复活道具」机制',
      status: 'in_progress',
      createdAt: '2026-06-09 16:20',
      summary:
        '玩家在限时关卡失败时，可消耗 1 个复活道具继续挑战 30 秒。涉及结算流程、客户端 UI 反馈与配置表。',
      requirement:
        '当玩家连连看关卡倒计时归零且尚有未消除牌面时，若背包内存在复活道具则弹出确认；确认后扣除一个并追加 30 秒倒计时。',
      relatedFiles: [
        { path: 'server/level/settle.go', score: 0.94, hint: '关卡结算入口' },
        { path: 'client/ui/level/result_panel.tsx', score: 0.83, hint: '关卡结算面板' },
        { path: 'config/level_revive.xlsx', score: 0.72, hint: '已有复活类道具配置' },
      ],
      plan: [
        '在 `Settle()` 检测到 `timedOut=true` 且仍有牌面时，尝试消耗复活道具',
        'UI 增加二次确认弹窗，文案沿用现有 toast 体系',
        '配置表新增 `revive_item_id` 字段，驱动开关',
      ],
      patchPreview:
        '--- server/level/settle.go\n+++ server/level/settle.go\n@@\n-    if timedOut {\n-        ctx.FailLevel()\n-    }\n+    if timedOut {\n+        if ok := ctx.TryConsumeReviveItem(); !ok {\n+            ctx.FailLevel()\n+        }\n+    }',
    },
    {
      id: 'f2',
      name: '新手引导「第一次连消」A/B 实验埋点',
      status: 'todo',
      createdAt: '2026-06-08 10:11',
      summary: '为新手引导「第一次成功消除」步骤加 A/B 分桶埋点，便于后续数据分析',
      requirement: '在玩家完成首次连连看消除时按 uid 哈希分桶，上报 bucket 字段；客户端与服务端均需埋点',
      relatedFiles: [],
      plan: [],
      patchPreview: '',
    },
  ],

  demo: [
    {
      // 已完成：作为「成品样例」展示完整三段流程后状态
      id: 'd1',
      name: '麻将连连看「欢乐消消」',
      status: 'generated',
      phase: 'generated', // draft | planning | plan_ready | generating | generated
      createdAt: '2026-06-09 19:55',
      template: '2D 连连看 + 限时关卡',
      engine: 'H5（HTML/JS/CSS）',
      requirement:
        '麻将牌面的连连看玩法：8x10 棋盘，玩家点选两张相同麻将牌，路径折线不超过 2 次拐弯即可消除。每关 90 秒倒计时，全部消除则通关。要求：34 种麻将牌面、3 关难度递增、单局可完整通关。',
      // 已选的知识库引用 key 数组（module:category:itemId）
      kbRefs: [],
      modelId: 'deepseek-v4-pro',
      // Plan 步骤：每步含 title / desc / status(pending|running|done)
      plan: [
        { title: '搭建工程骨架', desc: '初始化 H5 工程目录，划分 src/scenes、src/logic、assets/tiles 三层', status: 'done' },
        { title: '实现棋盘与连接判定', desc: 'BoardLogic.js：棋盘生成、点击选中、≤2 折路径搜索', status: 'done' },
        { title: '关卡与倒计时系统', desc: 'LevelSystem.js：关卡切换、90 秒倒计时、通关判定', status: 'done' },
        { title: '关卡配置表', desc: 'levels.csv：棋盘尺寸、牌型种类、初始打乱次数', status: 'done' },
        { title: '占位美术资源', desc: '34 张麻将牌面 + 通关/失败面板（Mock 风格）', status: 'done' },
      ],
      artifacts: [
        { type: 'script', path: 'src/logic/BoardLogic.js', desc: '棋盘点选与连接判定' },
        { type: 'script', path: 'src/logic/LevelSystem.js', desc: '关卡管理与倒计时' },
        { type: 'config', path: 'assets/config/levels.csv', desc: '关卡尺寸与牌型配置' },
        { type: 'asset', path: 'assets/tiles/*.png', desc: '34 张麻将牌面占位图' },
      ],
    },
    {
      // 待确认 plan 状态：刚生成完 plan，等用户点「确认并生成」
      id: 'd2',
      name: '休闲三消「水果派对」Demo',
      status: 'pending',
      phase: 'plan_ready',
      createdAt: '2026-06-08 09:30',
      template: '2D 三消 + 步数关卡',
      engine: 'H5（HTML/JS/CSS）',
      requirement:
        '可爱画风的水果三消玩法：8x8 棋盘，玩家拖拽相邻水果交换位置，三个或以上同类水果连成一线即可消除。每关限定步数，消除目标数即通关。要求：6 种水果、3 关递进，含连击特效与步数 UI。',
      kbRefs: [],
      modelId: 'deepseek-v4-pro',
      plan: [
        { title: '搭建三消主循环', desc: '棋盘初始化 + 交换/回退 + 落子补齐机制', status: 'pending' },
        { title: '匹配与连击判定', desc: '横纵 3 连扫描，连续消除累计连击倍数', status: 'pending' },
        { title: '关卡与目标系统', desc: '步数限制 + 通关目标（如：消除 30 颗草莓）', status: 'pending' },
        { title: '占位资源 + UI', desc: 'HUD 显示步数与目标，通关/失败面板', status: 'pending' },
      ],
      artifacts: [],
    },
    {
      // 草稿：还没写需求，从这里开始走完整流程演示
      id: 'd3',
      name: '新建空白 Demo',
      status: 'todo',
      phase: 'draft',
      createdAt: '2026-06-10 11:02',
      template: '未选择',
      engine: 'H5（HTML/JS/CSS）',
      requirement: '',
      kbRefs: [],
      modelId: 'deepseek-v4-pro',
      plan: [],
      artifacts: [],
    },
  ],
})

// 当前模块的任务列表
const currentTasks = computed(() => tasksByModule[activeSubId.value] || [])

// 当前选中的任务 id（每个模块各自记一份）
const activeTaskByModule = reactive({ review: 'r1', feature: 'f1', demo: 'd1' })

const activeTaskId = computed(() => activeTaskByModule[activeSubId.value] || null)
const activeTask = computed(() =>
  currentTasks.value.find((t) => t.id === activeTaskId.value) || currentTasks.value[0] || null
)

function selectTask(id) {
  if (activeSubId.value) activeTaskByModule[activeSubId.value] = id
}

function addTask() {
  // demo 阶段：纯本地添加占位任务
  const name = prompt('请输入新任务标题：')
  if (!name?.trim()) return
  const list = tasksByModule[activeSubId.value]
  const id = `${activeSubId.value[0]}-${Date.now()}`
  const base = {
    id,
    name: name.trim(),
    status: 'todo',
    createdAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
  }
  // 各模块的字段差异：先放最小集合，详情面板里 v-if 兜底
  if (activeSubId.value === 'review') {
    list.unshift({ ...base, branch: '-', author: '我', commitHash: '-', issues: [], summary: '', filesChanged: 0, additions: 0, deletions: 0 })
  } else if (activeSubId.value === 'feature') {
    list.unshift({ ...base, requirement: '', relatedFiles: [], plan: [], patchPreview: '' })
  } else {
    // demo 任务：默认 draft 阶段，待用户填写需求并选知识库
    list.unshift({
      ...base,
      phase: 'draft',
      template: '未选择',
      engine: 'H5（HTML/JS/CSS）',
      requirement: '',
      kbRefs: [],
      modelId: modelStore.list?.[0]?.id || 'deepseek-v4-pro',
      plan: [],
      artifacts: [],
    })
  }
  activeTaskByModule[activeSubId.value] = id
}

// ---- 状态徽章映射 --------------------------------------------------------
const STATUS_LABEL = {
  reviewed: { text: '已审查', tone: 'success' },
  pending: { text: '审查中', tone: 'progress' },
  in_progress: { text: '进行中', tone: 'progress' },
  todo: { text: '待开始', tone: 'idle' },
  generated: { text: '已生成', tone: 'success' },
}

function statusOf(task) {
  // demo 任务采用 phase 推动整个流程，顶部徽章按 phase 显示更直观；
  // review / feature 仍走原 STATUS_LABEL
  if (task?.phase) {
    const phaseMap = {
      draft: { text: '草稿', tone: 'idle' },
      planning: { text: '生成 Plan…', tone: 'progress' },
      plan_ready: { text: '待确认', tone: 'progress' },
      generating: { text: '生成中', tone: 'progress' },
      generated: { text: '已生成', tone: 'success' },
    }
    if (phaseMap[task.phase]) return phaseMap[task.phase]
  }
  return STATUS_LABEL[task?.status] || { text: '未知', tone: 'idle' }
}

// ---- Review 面板：issue 等级配色 -----------------------------------------
const LEVEL_LABEL = {
  high: { text: '严重', color: '#f85149' },
  medium: { text: '中', color: '#f0883e' },
  low: { text: '提示', color: '#58a6ff' },
}

// ---- Demo 面板：阶段定义 ------------------------------------------------
// 任务在 phase 上推进；UI 根据 phase 决定哪些区域可编辑、哪些按钮出现
const DEMO_PHASES = [
  { id: 'draft', name: '需求录入', desc: '填写需求并选择参考资料' },
  { id: 'planning', name: '生成 Plan', desc: 'AI 正在拆解为可执行步骤…' },
  { id: 'plan_ready', name: '等待确认', desc: '请审阅 Plan，确认后开始生成' },
  { id: 'generating', name: '按 Plan 生成', desc: '正在按确认后的步骤生成产物…' },
  { id: 'generated', name: '已完成', desc: 'Demo 已生成完毕' },
]
const DEMO_PHASE_INDEX = Object.fromEntries(DEMO_PHASES.map((p, i) => [p.id, i]))

// 可选模板（mock，仅用于下拉）
const DEMO_TEMPLATES = ['麻将连连看', '休闲三消', '推箱子解谜', '麻将（雀魂玩法）', '消除合成']
const DEMO_ENGINES = ['Unity 2022.3', 'Unreal 5.4', 'Cocos Creator 3.8', 'Godot 4.3']

// 步骤状态徽章
function planStepBadge(status) {
  if (status === 'done') return { text: '✓ 完成', tone: 'success' }
  if (status === 'running') return { text: '生成中', tone: 'progress' }
  if (status === 'error') return { text: '失败', tone: 'error' }
  return { text: '待生成', tone: 'idle' }
}

// 当前阶段对象（用于 stepper 高亮）
const demoCurrentPhase = computed(() => activeTask.value?.phase || 'draft')

// ---- Demo 面板：阶段动作（真实接后端 SSE 流）------------------------------
// 边流式生成边把 thinking 文本积累到 task.thinking 上，UI 可显示生成中文字
// 每个任务自带一个 AbortController，切换任务或重新生成时打断旧流

const _demoAborters = new Map() // taskId -> AbortController

function _abortTaskStream(taskId) {
  const ac = _demoAborters.get(taskId)
  if (ac) {
    try {
      ac.abort()
    } catch (_) {
      /* 已 abort 时再 abort 会 throw，忽略 */
    }
    _demoAborters.delete(taskId)
  }
}

function _newAborter(taskId) {
  _abortTaskStream(taskId)
  const ac = new AbortController()
  _demoAborters.set(taskId, ac)
  return ac
}

// 触发：草稿 → planning → plan_ready，调用 /api/dev/demo/plan
function generatePlan() {
  const t = activeTask.value
  if (!t) return
  if (!t.requirement?.trim()) {
    alert('请先填写需求描述')
    return
  }
  if (!t.modelId) {
    alert('请选择模型')
    return
  }
  // 状态切换：进入 planning，清掉上一次的 thinking 文本
  t.phase = 'planning'
  t.status = 'in_progress'
  t.thinking = ''
  t.errorMsg = ''
  t.plan = []

  const ac = _newAborter(t.id)
  streamDemoPlan(
    {
      task_id: t.id,
      model_id: t.modelId,
      requirement: t.requirement,
      template: t.template === '未选择' ? null : t.template,
      engine: t.engine === '未选择' ? null : t.engine,
      kb_refs: t.kbRefs || [],
    },
    {
      onEvent(payload) {
        if (payload.type === 'thinking') {
          t.thinking = (t.thinking || '') + (payload.text || '')
        } else if (payload.type === 'plan' && Array.isArray(payload.steps)) {
          // 收到结构化 plan：填充到任务并切到 plan_ready
          t.plan = payload.steps.map((s) => ({
            title: s.title || '',
            desc: s.desc || '',
            status: 'pending',
          }))
          t.phase = 'plan_ready'
          t.status = 'pending'
        }
      },
      onError(msg) {
        t.errorMsg = msg
        // 错误时回到 draft，便于用户调整
        t.phase = 'draft'
        t.status = 'todo'
      },
      onDone() {
        // 如果流结束但没拿到 plan，也兜底回到 draft
        if (t.phase === 'planning') {
          t.phase = 'draft'
          t.status = 'todo'
          if (!t.errorMsg) t.errorMsg = '未收到有效 Plan，请重试'
        }
      },
    },
    ac.signal
  )
}

// 重新生成 plan（plan_ready 阶段触发）：先 abort，再走一遍 generatePlan
function regeneratePlan() {
  const t = activeTask.value
  if (!t) return
  _abortTaskStream(t.id)
  t.plan = []
  generatePlan()
}

// 确认 plan → /api/dev/demo/generate
function confirmAndGenerate() {
  const t = activeTask.value
  if (!t || !t.plan?.length) return

  t.phase = 'generating'
  t.status = 'in_progress'
  t.artifacts = []
  t.errorMsg = ''
  // 把所有步骤重置为 pending（重新生成 Demo 时会用到）
  t.plan.forEach((s) => {
    s.status = 'pending'
    s.thinking = ''
    s.error = ''
  })

  const ac = _newAborter(t.id)
  streamDemoGenerate(
    {
      task_id: t.id,
      model_id: t.modelId,
      requirement: t.requirement,
      template: t.template === '未选择' ? null : t.template,
      engine: t.engine === '未选择' ? null : t.engine,
      kb_refs: t.kbRefs || [],
      // 后端只关心 title/desc 两个字段，前端额外的 status/thinking 会被忽略
      plan: t.plan.map((s) => ({ title: s.title, desc: s.desc })),
    },
    {
      onEvent(payload) {
        const idx = payload.index
        const step = idx != null ? t.plan[idx] : null

        if (payload.type === 'step_start' && step) {
          step.status = 'running'
        } else if (payload.type === 'step_thinking' && step) {
          step.thinking = (step.thinking || '') + (payload.text || '')
        } else if (payload.type === 'step_artifact' && payload.artifact) {
          t.artifacts.push(payload.artifact)
        } else if (payload.type === 'step_done' && step) {
          step.status = 'done'
        } else if (payload.type === 'step_error' && step) {
          step.status = 'error'
          step.error = payload.message || '步骤失败'
        }
      },
      onError(msg) {
        t.errorMsg = msg
      },
      onDone() {
        // 若有任意步骤还停留在 running，说明流被 abort，标错
        t.plan.forEach((s) => {
          if (s.status === 'running') {
            s.status = 'error'
            s.error = s.error || '生成被中断'
          }
        })
        t.phase = 'generated'
        t.status = 'generated'
      },
    },
    ac.signal
  )
}

// 切任务时打断当前任务的流（避免后台还在写文件 / 推 token）
function selectTaskWithCleanup(id) {
  if (activeSubId.value === 'demo' && activeTask.value) {
    _abortTaskStream(activeTask.value.id)
  }
  selectTask(id)
}

// 加载模型清单（顶部下拉用）
onMounted(() => {
  ensureModelsLoaded()
})
</script>

<template>
  <div class="dev-view">
    <!-- 顶部栏 -->
    <header class="topbar">
      <button class="back-btn" @click="emit('navigate', 'home')">← 主界面</button>
      <div class="crumbs">
        <span class="crumb">研发 Agent</span>
        <template v-if="view === 'tasks' && activeSub">
          <span class="sep">/</span>
          <span class="crumb current">{{ activeSub.name }}</span>
        </template>
      </div>
      <div class="topbar-right">
        <button class="ghost-btn">📚 知识库</button>
        <div class="avatar-mini">U</div>
      </div>
    </header>

    <!-- Dashboard：3 个子模块卡片 -->
    <main v-if="view === 'dashboard'" class="dashboard">
      <div class="banner">
        <div class="banner-icon">⚙️</div>
        <div class="banner-content">
          <div class="banner-title">研发 Agent 工作台</div>
          <div class="banner-desc">
            围绕「日常代码、功能迭代、玩法验证」三类研发场景，提供 AI 辅助的端到端能力。
            请选择当前任务所属的模块。
          </div>
        </div>
      </div>

      <div class="section-title">
        <span>选择研发场景</span>
        <span class="section-hint">点击进入任务管理</span>
      </div>

      <div class="module-grid">
        <button
          v-for="m in SUB_MODULES"
          :key="m.id"
          class="module-card"
          :style="{ '--card-accent': m.accent }"
          @click="openSubModule(m.id)"
        >
          <div class="card-head">
            <span class="card-icon">{{ m.icon }}</span>
            <div class="card-title">
              <div class="card-name">{{ m.name }}</div>
              <div class="card-sub">{{ m.subtitle }}</div>
            </div>
          </div>
          <div class="card-desc">{{ m.desc }}</div>
          <ul class="card-bullets">
            <li v-for="b in m.bullets" :key="b">{{ b }}</li>
          </ul>
          <div class="card-foot">
            <span class="card-tag">输入：{{ m.inputs }}</span>
            <span class="card-tag">产出：{{ m.outputs }}</span>
          </div>
          <div class="card-cta">点击进入 →</div>
        </button>
      </div>
    </main>

    <!-- 任务管理：左侧列表 + 右侧详情 -->
    <main v-else class="tasks-layout">
      <TaskSidebar
        :tasks="currentTasks"
        :active-task-id="activeTaskId"
        :title="activeSub?.name + ' 任务'"
        @select="selectTaskWithCleanup"
        @add="addTask"
      />

      <section class="task-detail">
        <div class="back-strip">
          <button class="back-mini" @click="backToDashboard">← 返回模块</button>
          <span class="ctx-title">
            <span class="ctx-icon">{{ activeSub?.icon }}</span>
            {{ activeSub?.name }}
          </span>
          <span v-if="activeTask" class="ctx-status" :class="statusOf(activeTask).tone">
            {{ statusOf(activeTask).text }}
          </span>
        </div>

        <!-- 没有任务时的占位 -->
        <div v-if="!activeTask" class="empty-detail">
          <div class="empty-icon">📭</div>
          <div class="empty-title">还没有任务</div>
          <div class="empty-desc">点击左侧「+ 新增任务」开始一项新的研发工作。</div>
        </div>

        <!-- ===== 代码 Review 面板 ===== -->
        <div v-else-if="activeSubId === 'review'" class="panel">
          <div class="panel-head">
            <h2>{{ activeTask.name }}</h2>
            <div class="meta-row">
              <span class="meta">
                <em>分支</em>
                <code>{{ activeTask.branch || '-' }}</code>
              </span>
              <span class="meta">
                <em>提交</em>
                <code>{{ activeTask.commitHash || '-' }}</code>
              </span>
              <span class="meta">
                <em>作者</em>
                <code>{{ activeTask.author || '-' }}</code>
              </span>
              <span class="meta">
                <em>提交时间</em>
                <code>{{ activeTask.createdAt }}</code>
              </span>
            </div>
            <div class="diff-stat">
              <span class="d-files">{{ activeTask.filesChanged }} 个文件</span>
              <span class="d-add">+{{ activeTask.additions }}</span>
              <span class="d-del">-{{ activeTask.deletions }}</span>
            </div>
          </div>

          <div class="panel-section">
            <h3>📋 审查总结</h3>
            <p v-if="activeTask.summary" class="summary-text">{{ activeTask.summary }}</p>
            <p v-else class="placeholder-text">审查尚未完成…</p>
          </div>

          <div class="panel-section">
            <h3>⚠ 问题清单（{{ activeTask.issues?.length || 0 }}）</h3>
            <div v-if="activeTask.issues?.length" class="issue-list">
              <div v-for="(it, i) in activeTask.issues" :key="i" class="issue-item">
                <span
                  class="issue-level"
                  :style="{ background: LEVEL_LABEL[it.level].color }"
                >
                  {{ LEVEL_LABEL[it.level].text }}
                </span>
                <div class="issue-body">
                  <div class="issue-loc">
                    <code>{{ it.file }}</code>
                    <span v-if="it.line" class="issue-line">: {{ it.line }}</span>
                  </div>
                  <div class="issue-msg">{{ it.msg }}</div>
                </div>
              </div>
            </div>
            <p v-else class="placeholder-text">暂无问题。</p>
          </div>

          <div v-if="activeTask.suggestion" class="panel-section">
            <h3>💡 建议</h3>
            <p class="summary-text">{{ activeTask.suggestion }}</p>
          </div>

          <div class="panel-actions">
            <button class="primary">重新审查</button>
            <button class="ghost">导出报告</button>
            <button class="ghost">采纳全部建议</button>
          </div>
        </div>

        <!-- ===== 功能开发 面板 ===== -->
        <div v-else-if="activeSubId === 'feature'" class="panel">
          <div class="panel-head">
            <h2>{{ activeTask.name }}</h2>
            <div class="meta-row">
              <span class="meta"><em>创建时间</em><code>{{ activeTask.createdAt }}</code></span>
            </div>
          </div>

          <div class="panel-section">
            <h3>📝 需求描述</h3>
            <p v-if="activeTask.requirement" class="summary-text">{{ activeTask.requirement }}</p>
            <p v-else class="placeholder-text">还没有填写需求，请在此输入…</p>
          </div>

          <div class="panel-section">
            <h3>📂 相关文件定位</h3>
            <div v-if="activeTask.relatedFiles?.length" class="file-list">
              <div v-for="f in activeTask.relatedFiles" :key="f.path" class="file-item">
                <code class="file-path">{{ f.path }}</code>
                <span class="file-score">相关度 {{ (f.score * 100).toFixed(0) }}%</span>
                <span class="file-hint">{{ f.hint }}</span>
              </div>
            </div>
            <p v-else class="placeholder-text">尚未生成相关文件定位。</p>
          </div>

          <div class="panel-section">
            <h3>📌 实现方案</h3>
            <ol v-if="activeTask.plan?.length" class="plan-list">
              <li v-for="(p, i) in activeTask.plan" :key="i">{{ p }}</li>
            </ol>
            <p v-else class="placeholder-text">尚未生成方案。</p>
          </div>

          <div class="panel-section">
            <h3>🧩 代码补丁预览</h3>
            <pre v-if="activeTask.patchPreview" class="diff-block">{{ activeTask.patchPreview }}</pre>
            <p v-else class="placeholder-text">尚未生成补丁。</p>
          </div>

          <div class="panel-actions">
            <button class="primary">重新生成方案</button>
            <button class="ghost">下载补丁</button>
            <button class="ghost">应用到本地分支</button>
          </div>
        </div>

        <!-- ===== Demo 生成 面板（三阶段：需求 → Plan → 生成）===== -->
        <div v-else-if="activeSubId === 'demo'" class="panel">
          <div class="panel-head">
            <h2>{{ activeTask.name }}</h2>
            <div class="meta-row">
              <span class="meta"><em>创建时间</em><code>{{ activeTask.createdAt }}</code></span>
            </div>
          </div>

          <!-- 阶段进度条：让用户清楚当前在哪一步 -->
          <div class="phase-stepper">
            <div
              v-for="(p, idx) in DEMO_PHASES"
              :key="p.id"
              class="phase-step"
              :class="{
                done: DEMO_PHASE_INDEX[demoCurrentPhase] > idx,
                active: demoCurrentPhase === p.id,
              }"
            >
              <span class="phase-dot">{{ idx + 1 }}</span>
              <div class="phase-meta">
                <div class="phase-name">{{ p.name }}</div>
                <div class="phase-desc">{{ p.desc }}</div>
              </div>
              <span v-if="idx < DEMO_PHASES.length - 1" class="phase-line"></span>
            </div>
          </div>

          <!-- 1) 需求与参考：draft / plan_ready 都允许编辑 -->
          <div class="panel-section">
            <h3>📝 需求描述</h3>
            <textarea
              v-model="activeTask.requirement"
              class="req-input"
              :disabled="activeTask.phase === 'planning' || activeTask.phase === 'generating'"
              rows="4"
              placeholder="例：麻将牌面 + 连连看玩法，8x10 棋盘，路径折线不超过 2 次拐弯即可消除…"
            ></textarea>

            <div class="opt-row">
              <label class="opt">
                <span class="opt-label">模板</span>
                <select
                  v-model="activeTask.template"
                  :disabled="activeTask.phase === 'planning' || activeTask.phase === 'generating'"
                >
                  <option value="未选择">未选择</option>
                  <option v-for="t in DEMO_TEMPLATES" :key="t" :value="t">{{ t }}</option>
                </select>
              </label>
              <label class="opt">
                <span class="opt-label">引擎</span>
                <select
                  v-model="activeTask.engine"
                  :disabled="activeTask.phase === 'planning' || activeTask.phase === 'generating'"
                >
                  <option value="未选择">未选择</option>
                  <option v-for="e in DEMO_ENGINES" :key="e" :value="e">{{ e }}</option>
                </select>
              </label>
              <label class="opt">
                <span class="opt-label">模型</span>
                <select
                  v-model="activeTask.modelId"
                  :disabled="activeTask.phase === 'planning' || activeTask.phase === 'generating' || modelStore.loading"
                >
                  <option v-if="modelStore.loading" value="">加载中…</option>
                  <option v-for="m in modelStore.list" :key="m.id" :value="m.id">
                    {{ m.label }}
                  </option>
                </select>
              </label>
            </div>

            <!-- 整体错误提示（plan / generate 公共）-->
            <p v-if="activeTask.errorMsg" class="err-banner">
              ⚠ {{ activeTask.errorMsg }}
            </p>
          </div>

          <!-- 2) 知识库参考：复用通用组件 -->
          <div class="panel-section kb-section">
            <KnowledgeRefBlock v-model="activeTask.kbRefs" :dense="false" />
          </div>

          <!-- 3) draft：仅显示「生成 Plan」按钮 -->
          <div v-if="activeTask.phase === 'draft'" class="panel-actions">
            <button
              class="primary"
              :disabled="!activeTask.requirement?.trim()"
              @click="generatePlan"
            >
              🪄 生成 Plan
            </button>
            <span class="hint-inline">
              填写需求并选好参考后，点击生成。Plan 会拆解为可逐步执行的步骤，确认后再开始生成产物。
            </span>
          </div>

          <!-- 4) planning：进度提示 + 流式 thinking -->
          <div v-else-if="activeTask.phase === 'planning'" class="panel-section">
            <div class="loading-row">
              <span class="dots">
                <i></i><i></i><i></i>
              </span>
              <span>AI 正在拆解 Plan…</span>
            </div>
            <pre v-if="activeTask.thinking" class="thinking-block">{{ activeTask.thinking }}</pre>
          </div>

          <!-- 5) plan_ready / generating / generated：展示 plan 列表 -->
          <div
            v-if="['plan_ready', 'generating', 'generated'].includes(activeTask.phase) && activeTask.plan?.length"
            class="panel-section"
          >
            <h3>📌 执行 Plan（{{ activeTask.plan.length }} 步）</h3>
            <ol class="plan-step-list">
              <li
                v-for="(step, i) in activeTask.plan"
                :key="i"
                class="plan-step"
                :class="step.status"
              >
                <span class="plan-step-num">{{ i + 1 }}</span>
                <div class="plan-step-body">
                  <div class="plan-step-title">
                    <strong>{{ step.title }}</strong>
                    <span class="plan-step-badge" :class="planStepBadge(step.status).tone">
                      {{ planStepBadge(step.status).text }}
                    </span>
                  </div>
                  <div class="plan-step-desc">{{ step.desc }}</div>
                  <!-- running 时实时展示该步的流式 thinking -->
                  <pre
                    v-if="step.status === 'running' && step.thinking"
                    class="thinking-block compact"
                  >{{ step.thinking }}</pre>
                  <!-- 失败时显示错误信息 -->
                  <p v-if="step.status === 'error' && step.error" class="step-error">
                    ⚠ {{ step.error }}
                  </p>
                </div>
              </li>
            </ol>

            <!-- plan_ready 阶段的确认 / 重新生成按钮 -->
            <div v-if="activeTask.phase === 'plan_ready'" class="panel-actions">
              <button class="primary" @click="confirmAndGenerate">✅ 确认并按 Plan 生成</button>
              <button class="ghost" @click="regeneratePlan">重新生成 Plan</button>
              <span class="hint-inline">
                可在上方修改需求 / 参考后再「重新生成 Plan」；确认后即开始按步骤产出代码与配置。
              </span>
            </div>

            <!-- generating 阶段 -->
            <div v-else-if="activeTask.phase === 'generating'" class="hint-inline">
              <span class="dots inline">
                <i></i><i></i><i></i>
              </span>
              正在按 Plan 顺序生成，每完成一步会自动推进…
            </div>
          </div>

          <!-- 6) generated：产物清单 + 操作 -->
          <div v-if="activeTask.phase === 'generated'" class="panel-section">
            <h3>📦 生成产物（{{ activeTask.artifacts?.length || 0 }}）</h3>
            <div v-if="activeTask.artifacts?.length" class="artifact-list">
              <div v-for="(a, i) in activeTask.artifacts" :key="i" class="artifact-item">
                <span class="artifact-type" :data-type="a.type">{{ a.type }}</span>
                <code class="artifact-path">{{ a.path }}</code>
                <span class="artifact-desc">{{ a.desc }}</span>
              </div>
            </div>
            <p v-else class="placeholder-text">尚未生成产物。</p>

            <div class="panel-actions">
              <button class="primary" @click="confirmAndGenerate">重新生成 Demo</button>
              <button class="ghost">下载工程压缩包</button>
              <button class="ghost">在引擎中打开</button>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.dev-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-primary);
}

/* --- 顶部栏 --- */
.topbar {
  height: 56px;
  flex-shrink: 0;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1.5px solid var(--border-color);
  background: var(--bg-secondary);
}

.back-btn,
.ghost-btn {
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.back-btn:hover,
.ghost-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-hover);
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
  color: var(--accent-green);
  font-weight: 700;
}

.sep {
  color: var(--text-tertiary);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-mini {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-green), var(--accent-blue));
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
}

/* --- Dashboard --- */
.dashboard {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 24px;
  border-radius: var(--radius-lg);
  background: linear-gradient(
    135deg,
    rgba(46, 160, 67, 0.12),
    rgba(88, 166, 255, 0.06)
  );
  border: 1.5px solid rgba(46, 160, 67, 0.5);
  box-shadow: 2px 2px 0 var(--shadow-green);
}

.banner-icon {
  font-size: 32px;
}

.banner-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.banner-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.section-title {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 600;
}

.section-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 400;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.module-card {
  --card-accent: var(--accent-blue);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background: var(--bg-secondary);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-lg);
  text-align: left;
  transition: all 0.18s;
  position: relative;
  overflow: hidden;
}

.module-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--card-accent);
  opacity: 0.6;
  transition: opacity 0.18s;
}

.module-card:hover {
  transform: translate(-2px, -3px);
  border-color: var(--card-accent);
  box-shadow: 4px 4px 0 var(--shadow-dark);
}

.module-card:hover::before {
  opacity: 1;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-icon {
  font-size: 28px;
}

.card-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  letter-spacing: -0.01em;
}

.card-sub {
  font-size: 11px;
  color: var(--text-tertiary);
  letter-spacing: 0.4px;
  margin-top: 2px;
}

.card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.55;
}

.card-bullets {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-bullets li {
  position: relative;
  padding-left: 14px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.card-bullets li::before {
  content: '·';
  color: var(--card-accent);
  position: absolute;
  left: 4px;
  font-size: 16px;
  line-height: 1;
}

.card-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: auto;
}

.card-tag {
  font-size: 10.5px;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  padding: 3px 8px;
  border-radius: 999px;
}

.card-cta {
  font-size: 12px;
  color: var(--card-accent);
  font-weight: 500;
}

/* --- 任务管理布局 --- */
.tasks-layout {
  flex: 1;
  display: flex;
  min-height: 0;
}

.task-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-primary);
}

.back-strip {
  flex-shrink: 0;
  height: 44px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.back-mini {
  font-size: 12px;
  padding: 4px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
}

.back-mini:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.ctx-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ctx-icon {
  font-size: 14px;
}

.ctx-status {
  margin-left: auto;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  letter-spacing: 0.3px;
}

.ctx-status.success {
  color: var(--accent-green);
  background: var(--accent-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.35);
}

.ctx-status.progress {
  color: var(--accent-blue);
  background: var(--accent-blue-dim);
  border: 1px solid rgba(26, 111, 255, 0.35);
}

.ctx-status.idle {
  color: var(--text-tertiary);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
}

.empty-detail {
  flex: 1;
  display: grid;
  place-items: center;
  text-align: center;
}

.empty-icon {
  font-size: 36px;
  opacity: 0.6;
}

.empty-title {
  font-size: 16px;
  color: var(--text-primary);
  font-weight: 600;
  margin-top: 8px;
}

.empty-desc {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

/* --- 任务详情面板共用 --- */
.panel {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-head h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
  font-size: 12px;
  color: var(--text-secondary);
}

.meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.meta em {
  font-style: normal;
  color: var(--text-tertiary);
}

.meta code,
code {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--text-primary);
}

.diff-stat {
  margin-top: 10px;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.d-files {
  color: var(--text-secondary);
}

.d-add {
  color: var(--accent-green);
  font-weight: 600;
}

.d-del {
  color: var(--accent-red, #f85149);
  font-weight: 600;
}

.panel-section {
  background: var(--bg-secondary);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.panel-section h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.summary-text {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0;
}

.placeholder-text {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
}

/* --- Review issue --- */
.issue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.issue-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.issue-level {
  flex-shrink: 0;
  margin-top: 2px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: #fff;
}

.issue-body {
  flex: 1;
  min-width: 0;
}

.issue-loc {
  font-size: 12px;
  color: var(--text-secondary);
}

.issue-line {
  color: var(--text-tertiary);
}

.issue-msg {
  font-size: 13px;
  color: var(--text-primary);
  margin-top: 4px;
  line-height: 1.55;
}

/* --- Feature: file list / plan / diff --- */
.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
}

.file-path {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--text-primary);
}

.file-score {
  font-size: 11px;
  color: var(--accent-green);
  background: var(--accent-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.35);
  padding: 1px 6px;
  border-radius: 999px;
}

.file-hint {
  margin-left: auto;
  color: var(--text-tertiary);
}

.plan-list {
  margin: 0;
  padding-left: 22px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.65;
}

.diff-block {
  margin: 0;
  padding: 12px 14px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  line-height: 1.55;
  color: var(--text-primary);
  overflow-x: auto;
  white-space: pre;
}

/* --- Demo: artifact list --- */
.artifact-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.artifact-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.artifact-type {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  border: 1px solid;
}

.artifact-type[data-type='script'] {
  color: var(--accent-blue);
  border-color: rgba(26, 111, 255, 0.45);
  background: var(--accent-blue-dim);
}

.artifact-type[data-type='config'] {
  color: var(--accent-orange);
  border-color: rgba(234, 88, 12, 0.45);
  background: var(--accent-orange-dim);
}

.artifact-type[data-type='asset'] {
  color: var(--accent-pink);
  border-color: rgba(219, 39, 119, 0.45);
  background: var(--accent-pink-dim);
}

.artifact-path {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--text-primary);
}

.artifact-desc {
  margin-left: auto;
  color: var(--text-tertiary);
}

/* --- 操作按钮 --- */
.panel-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.primary {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--accent-green), var(--accent-blue));
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  border: 1.5px solid rgba(46, 160, 67, 0.5);
  box-shadow: 2px 2px 0 var(--shadow-green);
  transition: all 0.15s;
}

.primary:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 var(--shadow-green);
}

.ghost {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 12px;
}

.ghost:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--accent-green);
}

/* ---- Demo 阶段进度条 ---- */
.phase-stepper {
  display: flex;
  align-items: stretch;
  gap: 0;
  padding: 14px 16px;
  background: var(--bg-secondary);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
}

.phase-step {
  position: relative;
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 0 4px;
  min-width: 0;
}

.phase-dot {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-tertiary);
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 600;
  z-index: 1;
}

.phase-step.done .phase-dot {
  background: var(--accent-green);
  border-color: var(--accent-green);
  color: #fff;
}

.phase-step.active .phase-dot {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: #fff;
  box-shadow: 0 0 12px var(--accent-blue);
}

.phase-meta {
  min-width: 0;
  flex: 1;
}

.phase-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  line-height: 1.3;
}

.phase-step.active .phase-name {
  color: var(--accent-blue);
}

.phase-step.done .phase-name {
  color: var(--accent-green);
}

.phase-desc {
  font-size: 10.5px;
  color: var(--text-tertiary);
  line-height: 1.4;
  margin-top: 2px;
}

.phase-line {
  position: absolute;
  top: 11px;
  left: calc(50% + 14px);
  right: calc(-50% + 14px);
  height: 1px;
  background: var(--border-color);
}

.phase-step.done .phase-line {
  background: var(--accent-green);
}

/* ---- 需求输入 / 模板下拉 ---- */
.req-input {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
}

.req-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.15);
}

.req-input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.opt-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.opt {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.opt-label {
  color: var(--text-tertiary);
}

.opt select {
  padding: 5px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 12px;
  outline: none;
}

.opt select:focus {
  border-color: var(--accent-blue);
}

.opt select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 让 KnowledgeRefBlock 的内边距与其它 panel-section 协调一些 */
.kb-section {
  padding: 0;
  background: transparent;
  border: none;
}

/* ---- Plan 步骤列表 ---- */
.plan-step-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plan-step {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  transition: all 0.18s;
}

.plan-step.running {
  border-color: var(--accent-blue);
  background: var(--accent-blue-dim);
  box-shadow: 2px 2px 0 var(--shadow-blue);
}

.plan-step.done {
  border-color: rgba(22, 163, 74, 0.4);
}

.plan-step-num {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 600;
}

.plan-step.running .plan-step-num {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: #fff;
}

.plan-step.done .plan-step-num {
  background: var(--accent-green);
  border-color: var(--accent-green);
  color: #fff;
}

.plan-step-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.plan-step-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.plan-step-title strong {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 600;
}

.plan-step-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  letter-spacing: 0.3px;
}

.plan-step-badge.success {
  color: var(--accent-green);
  background: var(--accent-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.35);
}

.plan-step-badge.progress {
  color: var(--accent-blue);
  background: var(--accent-blue-dim);
  border: 1px solid rgba(26, 111, 255, 0.35);
}

.plan-step-badge.idle {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
}

.plan-step-badge.error {
  color: var(--accent-red, #dc2626);
  background: rgba(220, 38, 38, 0.08);
  border: 1px solid rgba(220, 38, 38, 0.35);
}

.plan-step.error {
  border-color: rgba(220, 38, 38, 0.4);
  background: rgba(220, 38, 38, 0.04);
}

.plan-step.error .plan-step-num {
  background: var(--accent-red, #f85149);
  border-color: var(--accent-red, #f85149);
  color: #fff;
}

/* 流式 thinking 展示块 */
.thinking-block {
  margin: 0;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11.5px;
  line-height: 1.55;
  color: var(--text-secondary);
  max-height: 220px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.thinking-block.compact {
  max-height: 140px;
  font-size: 11px;
  margin-top: 6px;
}

/* 顶部错误条 */
.err-banner {
  margin: 8px 0 0;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--accent-red);
  background: rgba(220, 38, 38, 0.06);
  border: 1px solid rgba(220, 38, 38, 0.35);
  border-radius: var(--radius-sm);
}

/* 单步错误 */
.step-error {
  margin: 6px 0 0;
  font-size: 11.5px;
  color: var(--accent-red);
}

.plan-step-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.55;
}

/* ---- loading dots ---- */
.loading-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
}

.dots {
  display: inline-flex;
  gap: 4px;
}

.dots.inline {
  margin-right: 4px;
}

.dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-blue);
  animation: dot-blink 1.2s infinite ease-in-out;
}

.dots i:nth-child(2) {
  animation-delay: 0.2s;
}
.dots i:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dot-blink {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); }
  40% { opacity: 1; transform: scale(1); }
}

.hint-inline {
  font-size: 11px;
  color: var(--text-tertiary);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  align-self: center;
}

.primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}
</style>
