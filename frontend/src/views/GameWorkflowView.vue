<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import WorkflowPrototype from '../components/WorkflowPrototype.vue'
import WorkflowStageChat from '../components/WorkflowStageChat.vue'
import { renderMarkdown } from '../utils/markdown.js'
import { ballSortBrief, ballSortReferences, createBrief, projectStageSuggestions, statusLabels, workflowSteps } from '../data/gameWorkflow.js'
import { cancelWorkflowRun, confirmWorkflowStage, createWorkflowProject, fetchWorkflowCatalog, fetchWorkflowProject, fetchWorkflowProjects, fetchWorkflowRun, fetchWorkflowRuns, fetchWorkflowRuntime, fetchWorkflowSkills, resumeWorkflowRun, startWorkflowRun } from '../api/workflow.js'
import { fetchKbItems, kbRawUrl } from '../api/knowledge.js'

const emit = defineEmits(['navigate'])
const projects = ref([])
const project = ref(null)
const page = ref('projects')
const step = ref(0)
const brief = reactive(createBrief())
const workspace = ref('')
const references = ref('')
const runtime = ref(null)
const runtimeLoading = ref(true)
const runtimeError = ref('')
const skills = ref([])
const skillError = ref('')
const catalog = ref({ genres: [], frameworks: [], documents: [] })
const catalogError = ref('')
const catalogLoading = ref(true)
const genreId = ref('general')
const frameworkId = ref('cocos-web')
const extraKnowledge = ref([])
const knowledgePreview = ref(null)
const knowledgeText = ref('')
const knowledgeLoading = ref(false)
const knowledgeError = ref('')
let knowledgeController
let knowledgeRequest = 0
const selectedSkills = reactive({ prototype: [], art: [], code: [], test: [] })
const drafts = reactive({ prototype: '', art: '', code: '', test: '' })
const runs = ref([])
const run = ref(null)
const search = ref('')
const loading = ref(false)
const submitting = ref(false)
const error = ref('')
const notice = ref('')
const reviewed = ref(false)
const reviewNote = ref('')
const selectedArtifact = ref(null)
const artifactText = ref('')
const artifactLoading = ref(false)
const artifactError = ref('')
const legacyData = ref('')
let pollTimer
let toastTimer
let disposed = false
let artifactController
let requestVersion = 0

// 旧八阶段记录保持原样，仅提供导出；绝不按下标套用到新四阶段。
try { legacyData.value = localStorage.getItem('game-agent-workflow-v1') || '' } catch { /* 存储受限不影响服务端项目。 */ }
const currentStep = computed(() => workflowSteps[step.value])
const stage = computed(() => project.value?.stages?.find((item) => item.id === currentStep.value.id))
const stageRuns = computed(() => runs.value.filter((item) => item.stage === currentStep.value.id).sort((a, b) => String(b.created_at).localeCompare(String(a.created_at))))
const activeRun = computed(() => runs.value.find((item) => ['queued', 'running'].includes(item.status)))
const running = computed(() => ['queued', 'running'].includes(run.value?.status))
const confirmedCount = computed(() => project.value?.stages?.filter((item) => item.confirmed_at || item.status === 'completed').length || 0)
const available = computed(() => step.value === 0 || !!project.value?.stages?.find((item) => item.id === workflowSteps[step.value - 1].id)?.confirmed_at || project.value?.stages?.find((item) => item.id === workflowSteps[step.value - 1].id)?.status === 'completed')
const runtimeUnavailable = computed(() => !runtime.value || runtime.value.available === false || runtime.value.ready === false)
const filteredProjects = computed(() => projects.value.filter((item) => item.name?.toLowerCase().includes(search.value.toLowerCase())))
const chatMessages = computed(() => [...stageRuns.value].reverse().flatMap((item) => {
  const messages = []
  if (item.prompt) messages.push({ role: 'user', content: item.prompt, status: item.status })
  if (item.summary || item.error) messages.push({ role: item.error ? 'system' : 'assistant', content: item.error || item.summary, status: item.status })
  return messages
}))
const projectBrief = computed(() => project.value?.brief && typeof project.value.brief === 'object' ? project.value.brief : {})
const selectedGenre = computed(() => catalog.value.genres.find((item) => item.id === genreId.value))
const selectedFramework = computed(() => catalog.value.frameworks.find((item) => item.id === frameworkId.value))
const catalogReady = computed(() => !catalogLoading.value && !catalogError.value && !!selectedGenre.value && !!selectedFramework.value)
const requiredKnowledge = computed(() => [...new Set([...(selectedGenre.value?.knowledge_paths || []), ...(selectedFramework.value?.knowledge_paths || [])])])
const optionalKnowledge = computed(() => catalog.value.documents.filter((item) => !requiredKnowledge.value.includes(item.path)))
// 项目的方案是创建时的冻结快照，后续目录更新不得改写旧项目的指引。
const productionProfile = computed(() => project.value?.production_profile || null)
const stageSuggestions = computed(() => projectStageSuggestions(productionProfile.value, step.value))
const projectKnowledge = computed(() => project.value?.knowledge_paths || productionProfile.value?.knowledge_paths || [])
const runKnowledge = computed(() => run.value?.knowledge_paths || run.value?.knowledge_snapshot?.map((item) => item.path) || run.value?.production_profile?.knowledge_paths || [])
const knowledgeReads = computed(() => (run.value?.events || []).filter((item) => item.type === 'knowledge_read'))
const knowledgeHtml = computed(() => renderMarkdown(knowledgeText.value))
// 服务端项目也允许自由简报字段，完整展示中文或扩展键，避免只识别表单字段。
const briefEntries = computed(() => {
  const names = { engine: '引擎', audience: '目标玩家', idea: '核心想法', scope: '首版范围', cycle: '阶段目标' }
  return Object.entries(projectBrief.value).filter(([key]) => !['name', 'genre', 'platform'].includes(key))
    .map(([key, value]) => [names[key] || key, typeof value === 'object' ? JSON.stringify(value, null, 2) : value])
})
const runArtifacts = computed(() => run.value?.artifacts || [])
const markdownArtifact = computed(() => /\.md$/i.test(selectedArtifact.value?.path || ''))
const artifactHtml = computed(() => markdownArtifact.value ? renderMarkdown(artifactText.value, {
  internalPathPrefixes: ['/api/workflow/artifacts/'],
  // 相对链接只解析到已收集的产物快照，避免跳到前端页面或读取任意工作目录。
  resolveRelativeUrl: (relative) => {
    try {
      const currentPath = selectedArtifact.value?.path || ''
      const target = new URL(relative, `https://workflow.local/${currentPath}`)
      if (target.origin !== 'https://workflow.local') return ''
      const path = decodeURIComponent(target.pathname.slice(1))
      const candidates = [...runArtifacts.value, ...runs.value.flatMap((item) => item.artifacts || [])]
      return candidates.find((item) => item.path === path)?.url || ''
    } catch { return '' }
  },
}) : '')
const previewUrl = computed(() => project.value?.preview_url || runArtifacts.value.find((item) => item.kind === 'preview')?.url || '')
const canConfirm = computed(() => run.value?.status === 'awaiting_confirmation' && run.value?.id === stage.value?.run_id && reviewed.value && !submitting.value && !activeRun.value)

function label(status) { return statusLabels[status] || status || '待执行' }
// 区分本轮实际写入、验证输出和引用快照，避免把并行观察到的文件都归为模型生成。
function provenanceLabel(value) {
  return { agent_edit: '本轮工具写入', validation_output: '验证产生', reference_asset: '引用资源快照', workspace_observation: '工作区文件快照' }[value] || '历史文件快照'
}
function formatTime(value) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '—' }
function toast(message) { notice.value = message; clearTimeout(toastTimer); toastTimer = setTimeout(() => { notice.value = '' }, 4000) }
function resetArtifact() { artifactController?.abort(); selectedArtifact.value = null; artifactText.value = ''; artifactError.value = ''; artifactLoading.value = false }
function knowledgeTitle(path) { return catalog.value.documents.find((item) => item.path === path)?.title || path }
function projectTechnology(item) {
  const data = item.brief && typeof item.brief === 'object' ? item.brief : {}
  return [data.engine || data['引擎'], data.platform || data['平台']].filter(Boolean).join(' · ') || '技术方案未填写'
}
function chooseGenre() { if (selectedGenre.value) brief.genre = selectedGenre.value.label }
function chooseFramework() { if (selectedFramework.value) brief.engine = selectedFramework.value.label }
function toggleKnowledge(path) {
  extraKnowledge.value = extraKnowledge.value.includes(path) ? extraKnowledge.value.filter((item) => item !== path) : [...extraKnowledge.value, path]
}
function closeKnowledge() {
  knowledgeController?.abort(); knowledgeRequest++; knowledgePreview.value = null; knowledgeText.value = ''; knowledgeError.value = ''; knowledgeLoading.value = false
}
// 原文仍从现有知识库只读接口取出，路径仅用于匹配元信息，不拼任意文件下载地址。
async function viewKnowledge(path) {
  closeKnowledge()
  const version = knowledgeRequest
  knowledgePreview.value = { path, title: knowledgeTitle(path), url: '' }
  knowledgeLoading.value = true
  try {
    let url = catalog.value.documents.find((item) => item.path === path)?.url
    if (!url) {
      const [module, category, ...rest] = path.split('/')
      const response = await fetchKbItems({ module, category })
      if (version !== knowledgeRequest) return
      const relative = rest.join('/')
      const item = (response.items || []).find((value) => [value.folder, value.stored_name || value.filename].filter(Boolean).join('/') === relative)
      if (!item) throw new Error('知识库中未找到这份资料，请刷新目录或在知识库中检查文件。')
      url = kbRawUrl(module, category, item.id)
    }
    knowledgePreview.value = { path, title: knowledgeTitle(path), url }
    knowledgeController = new AbortController()
    const raw = await fetch(url, { signal: knowledgeController.signal })
    if (!raw.ok) throw new Error(`HTTP ${raw.status}`)
    const content = await raw.text()
    if (version === knowledgeRequest) knowledgeText.value = content
  } catch (cause) {
    if (version === knowledgeRequest && cause.name !== 'AbortError') knowledgeError.value = `资料读取失败：${cause.message}`
  } finally { if (version === knowledgeRequest) knowledgeLoading.value = false }
}
// 用户提交操作时使旧轮询失效，避免迟到的响应覆盖新运行或评审结果。
function stopPolling() { requestVersion++; clearTimeout(pollTimer) }

// 独立读取环境和 Skill；单个接口失败时保留可读的项目列表并明确报错。
async function loadLibrary() {
  loading.value = true
  runtimeLoading.value = true
  catalogLoading.value = true
  error.value = ''
  const results = await Promise.allSettled([
    fetchWorkflowProjects().then((value) => { if (!disposed) projects.value = value }),
    fetchWorkflowRuntime().then((value) => { if (!disposed) { runtime.value = value; runtimeError.value = '' } }),
    fetchWorkflowSkills().then((value) => { if (!disposed) { skills.value = value; skillError.value = '' } }),
    fetchWorkflowCatalog().then((value) => {
      if (disposed) return
      if (!Array.isArray(value.genres) || !Array.isArray(value.frameworks) || !Array.isArray(value.documents)) throw new Error('方案目录返回格式不完整')
      catalog.value = value; catalogError.value = ''
      if (page.value === 'create') { if (!brief.genre) chooseGenre(); if (!brief.engine) chooseFramework() }
    }),
  ])
  if (disposed) return
  if (results[0].status === 'rejected') error.value = `无法加载服务端项目：${results[0].reason.message}`
  if (results[1].status === 'rejected') { runtime.value = null; runtimeError.value = results[1].reason.message }
  if (results[2].status === 'rejected') skillError.value = results[2].reason.message
  if (results[3].status === 'rejected') { catalogError.value = results[3].reason.message; catalog.value = { genres: [], frameworks: [], documents: [] } }
  runtimeLoading.value = false
  catalogLoading.value = false
  loading.value = false
}
function resetInputs() {
  for (const definition of workflowSteps) { drafts[definition.id] = ''; selectedSkills[definition.id] = [] }
}
function newProject(example = false) {
  resetInputs()
  clearTimeout(pollTimer)
  requestVersion++
  project.value = null; run.value = null; runs.value = []; step.value = 0; page.value = 'create'; error.value = ''
  Object.assign(brief, example ? ballSortBrief() : createBrief())
  genreId.value = example ? 'sorting' : 'general'; frameworkId.value = 'cocos-web'; extraKnowledge.value = []
  if (!example) chooseGenre()
  chooseFramework()
  // 示例只填简报，新项目仍由后端分配独立目录，避免覆盖已验收成品。
  workspace.value = ''
  references.value = example ? ballSortReferences.join('\n') : ''
  resetArtifact()
}
async function createProject() {
  if (!catalogReady.value) { error.value = '请先成功加载品类与技术方案目录。'; return }
  if (!brief.name.trim() || !brief.idea.trim()) { error.value = '请填写项目名称和核心想法。'; return }
  submitting.value = true; error.value = ''
  try {
    const normalized = Object.fromEntries(Object.entries(brief).map(([key, value]) => [key, value.trim()]))
    const payload = { name: normalized.name, brief: normalized, references: references.value.split('\n').map((item) => item.trim()).filter(Boolean), genre_id: genreId.value, framework_id: frameworkId.value, knowledge_paths: extraKnowledge.value.filter((path) => !requiredKnowledge.value.includes(path)) }
    if (workspace.value.trim()) payload.workspace = workspace.value.trim()
    const created = await createWorkflowProject(payload)
    projects.value = [created, ...projects.value.filter((item) => item.id !== created.id)]
    await openProject(created)
    toast('项目已保存到服务端，可开始原型定义。')
  } catch (cause) { error.value = `创建失败：${cause.message}` } finally { submitting.value = false }
}
async function openProject(item) {
  resetInputs()
  clearTimeout(pollTimer)
  requestVersion++
  project.value = item; page.value = 'workspace'; run.value = null; runs.value = []; error.value = ''; reviewed.value = false
  const index = workflowSteps.findIndex((definition) => !item.stages?.find((value) => value.id === definition.id)?.confirmed_at && item.stages?.find((value) => value.id === definition.id)?.status !== 'completed')
  step.value = index < 0 ? 3 : index
  resetArtifact()
  await refreshProject(true)
  // 新方案默认引用通用流程与所选框架技能；已有运行优先恢复上次选择，旧项目不推断技术方案。
  const framework = project.value?.production_profile?.framework
  const defaults = project.value?.production_profile ? ['casual-game-production/SKILL.md', ...(framework?.recommended_skills || [])] : []
  for (const definition of workflowSteps) {
    const previous = [...runs.value].filter((item) => item.stage === definition.id).sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)))[0]
    selectedSkills[definition.id] = [...new Set(previous?.skill_paths || defaults)].filter((path) => skills.value.some((item) => item.path === path))
  }
}
async function refreshProject(showLoading = false) {
  if (!project.value?.id || page.value !== 'workspace') return
  const id = project.value.id
  const version = requestVersion
  if (showLoading) loading.value = true
  try {
    const [detail, history] = await Promise.all([fetchWorkflowProject(id), fetchWorkflowRuns(id)])
    if (disposed || version !== requestVersion || project.value?.id !== id) return
    project.value = detail; runs.value = history
    const selectedId = run.value?.stage === currentStep.value.id ? run.value.id : stage.value?.run_id || stageRuns.value[0]?.id
    if (selectedId) {
      const detailRun = await fetchWorkflowRun(selectedId)
      if (disposed || version !== requestVersion) return
      run.value = detailRun
    } else run.value = null
    error.value = ''
  } catch (cause) { if (version === requestVersion) error.value = `无法同步执行状态：${cause.message}。页面不会据此标记成功。` }
  finally {
    if (version === requestVersion && !disposed) {
      loading.value = false
      clearTimeout(pollTimer)
      // 仅轮询真实后端状态，页面关闭后运行仍由服务端管理。
      pollTimer = setTimeout(() => refreshProject(), 2000)
    }
  }
}
function goStep(index) {
  requestVersion++; clearTimeout(pollTimer); step.value = index; run.value = null; reviewed.value = false; reviewNote.value = ''; resetArtifact(); refreshProject(true)
}
async function selectRun(id) {
  stopPolling()
  const version = requestVersion
  try { const detail = await fetchWorkflowRun(id); if (version === requestVersion) { run.value = detail; reviewed.value = false; resetArtifact(); await refreshProject() } } catch (cause) { error.value = cause.message; refreshProject() }
}
async function execute(prompt = drafts[currentStep.value.id].trim()) {
  if (!project.value || submitting.value || activeRun.value || !available.value || runtimeUnavailable.value) return
  stopPolling()
  submitting.value = true; error.value = ''
  try {
    const created = await startWorkflowRun(project.value.id, { stage: currentStep.value.id, prompt: prompt || `请执行${currentStep.value.name}阶段，读取项目简报、品类与技术知识、上游产物和所选 Skill，完成真实文件操作与检查。`, skill_paths: selectedSkills[currentStep.value.id] })
    run.value = created; runs.value = [...runs.value.filter((item) => item.id !== created.id), created]
    drafts[currentStep.value.id] = ''; reviewed.value = false; resetArtifact()
    await refreshProject()
  } catch (cause) { error.value = `启动失败：${cause.message}`; pollTimer = setTimeout(() => refreshProject(), 4000) } finally { submitting.value = false }
}
async function cancelRun() {
  if (!run.value || submitting.value) return
  stopPolling()
  submitting.value = true; error.value = ''
  try { await cancelWorkflowRun(run.value.id); await refreshProject(); toast('取消请求已提交，最终状态以服务端记录为准。') }
  catch (cause) { error.value = `取消失败：${cause.message}`; pollTimer = setTimeout(() => refreshProject(), 4000) } finally { submitting.value = false }
}
async function resumeRun() {
  if (!run.value || activeRun.value || submitting.value) return
  stopPolling()
  submitting.value = true; error.value = ''
  try { const resumed = await resumeWorkflowRun(run.value.id); run.value = resumed; await refreshProject() }
  catch (cause) { error.value = `继续失败：${cause.message}`; pollTimer = setTimeout(() => refreshProject(), 4000) } finally { submitting.value = false }
}
async function confirmStage() {
  if (!canConfirm.value) return
  stopPolling()
  submitting.value = true; error.value = ''
  try { project.value = await confirmWorkflowStage(project.value.id, currentStep.value.id, reviewNote.value); reviewed.value = false; await refreshProject(); toast('阶段评审已确认，下游已解锁。') }
  catch (cause) { error.value = `确认失败：${cause.message}`; pollTimer = setTimeout(() => refreshProject(), 4000) } finally { submitting.value = false }
}
function toggleSkill(path) {
  const list = selectedSkills[currentStep.value.id]
  selectedSkills[currentStep.value.id] = list.includes(path) ? list.filter((value) => value !== path) : [...list, path]
}
async function viewArtifact(item) {
  resetArtifact(); selectedArtifact.value = item
  if (item.kind === 'image' || item.kind === 'preview') return
  if (item.size > 2 * 1024 * 1024) { artifactError.value = '文件较大，请下载后查看。'; return }
  const textFile = item.kind === 'text' || /\.(md|txt|json|jsonl|csv|ts|js|log|yaml|yml|html|css|xml|py)$/i.test(item.path || item.name)
  if (!textFile) return
  artifactController = new AbortController(); artifactLoading.value = true
  try {
    const response = await fetch(item.url, { signal: artifactController.signal })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const content = await response.text()
    if (selectedArtifact.value?.id === item.id) artifactText.value = content
  } catch (cause) { if (cause.name !== 'AbortError') artifactError.value = `产物读取失败：${cause.message}` }
  finally { if (selectedArtifact.value?.id === item.id) artifactLoading.value = false }
}
function downloadLegacy() {
  const url = URL.createObjectURL(new Blob([legacyData.value], { type: 'application/json;charset=utf-8' }))
  const link = document.createElement('a'); link.href = url; link.download = '八阶段本地演示记录备份.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function backToProjects() { clearTimeout(pollTimer); requestVersion++; page.value = 'projects'; resetArtifact(); loadLibrary() }
onMounted(loadLibrary)
onBeforeUnmount(() => { disposed = true; requestVersion++; clearTimeout(pollTimer); clearTimeout(toastTimer); artifactController?.abort(); closeKnowledge() })
</script>

<template>
  <div class="studio-shell">
    <header class="studio-topbar"><button class="studio-brand" @click="emit('navigate', 'home')"><span>✦</span><div>游戏研发工作台<small>GAME DEVELOPMENT WORKSPACE</small></div></button><div class="topbar-actions"><span class="runtime-chip" :class="{ unavailable: runtimeUnavailable }">{{ runtimeLoading ? '执行环境核验中' : runtimeUnavailable ? '执行环境待检查' : '真实执行已连接' }}</span><button @click="emit('navigate', 'knowledge')">知识库与 Skill ↗</button><button @click="emit('navigate', 'home')">返回首页</button></div></header>
    <main class="studio-main">
      <div v-if="legacyData" class="legacy-note">检测到旧八阶段本地演示记录，已原样保留。当前四阶段从服务端加载，不沿用旧产出和确认状态。<button @click="downloadLegacy">下载旧记录备份 ↓</button></div>
      <div v-if="error" class="error-banner" role="alert">{{ error }}<button v-if="page === 'projects'" @click="loadLibrary">重新连接</button></div>
      <template v-if="page === 'projects'">
        <section class="projects-hero"><div><div class="eyebrow">从融合创意到可玩游戏</div><h1>让每一步研发<br />都有真实产物。</h1><p>DeepAgents 执行策划、资源、工程与测试。<br />引用真实 Skill，查看过程，评审后进入下一阶段。</p><div class="hero-actions"><button class="button primary" @click="newProject()">＋ 创建新项目</button><button class="button" @click="newProject(true)">加载 Ball Sort 融合简报 ↗</button></div></div><div class="hero-map"><div v-for="(item, index) in workflowSteps" :key="item.id"><span>0{{ index + 1 }}</span><strong>{{ item.name }}</strong><small>{{ item.outputs[0] }}</small></div></div></section>
        <section class="project-library"><div class="library-heading"><div><div class="eyebrow">服务端项目</div><h2>我的游戏项目 <span>{{ projects.length }}</span></h2></div><div class="library-controls"><input v-model="search" placeholder="搜索项目名称…" aria-label="搜索项目" /><button class="text-button" :disabled="loading" @click="loadLibrary">{{ loading ? '加载中…' : '刷新' }}</button></div></div><div class="project-grid"><button class="create-card" @click="newProject()"><span>＋</span><strong>创建新项目</strong><small>填写简报，启动四阶段研发</small></button><button v-for="item in filteredProjects" :key="item.id" class="project-card" @click="openProject(item)"><div class="project-cover"><span>{{ projectTechnology(item) }}</span><b>✦</b><small>{{ item.stages?.filter(s => s.status === 'completed').length || 0 }} / 4 已确认</small></div><div class="project-card-body"><h3>{{ item.name }}</h3><p>{{ item.brief?.genre || '游戏研发项目' }}</p><div class="project-card-footer"><span>{{ formatTime(item.updated_at || item.created_at) }}</span><strong>打开工作台 →</strong></div></div></button></div><p v-if="!filteredProjects.length && !loading" class="empty-message">{{ error ? '服务端项目暂不可用，请检查后端连接。' : '还没有项目。选择适合的品类与技术方案，开始新项目。' }}</p></section>
      </template>
      <template v-else-if="page === 'create'">
        <div class="workspace-breadcrumb"><button @click="backToProjects">← 我的项目</button><span>/ 新建项目</span></div><div class="workspace-title"><div><div class="eyebrow">项目输入</div><h1>定义你的下一款游戏</h1><p>先保存真实项目，再由 Agent 执行原型定义。</p></div><button class="text-button" @click="newProject(true)">填入 Ball Sort 融合简报 ↗</button></div>
        <form class="panel brief-form" @submit.prevent="createProject">
          <div v-if="catalogLoading" class="info-banner" role="status">正在加载品类与技术方案…</div>
          <div v-else-if="catalogError" class="error-banner" role="alert">方案目录加载失败：{{ catalogError }}<button type="button" @click="loadLibrary">重新加载</button></div>
          <div class="form-row">
            <label>品类方案<select v-model="genreId" :disabled="!catalogReady" aria-label="品类方案" @change="chooseGenre"><option v-for="item in catalog.genres" :key="item.id" :value="item.id">{{ item.label }}</option></select><p class="choice-description">{{ selectedGenre?.description }}</p></label>
            <label>技术方案<select v-model="frameworkId" :disabled="!catalogReady" aria-label="技术方案" @change="chooseFramework"><option v-for="item in catalog.frameworks" :key="item.id" :value="item.id">{{ item.label }}</option></select><p class="choice-description">{{ selectedFramework?.description }}</p><p v-if="selectedFramework?.status" class="choice-status">验证程度：{{ selectedFramework.status }}</p></label>
          </div>
          <div v-if="selectedFramework" class="profile-explanation">
            <p>{{ selectedFramework.instructions }}</p>
            <p v-if="selectedFramework.required_validations?.length">项目验收命令：{{ selectedFramework.required_validations.join('；') }}</p>
            <p v-if="selectedFramework.preview_entry">预览入口：{{ selectedFramework.preview_entry }}</p>
          </div>
          <section class="knowledge-selection" aria-label="项目知识资料">
            <h3>品类与技术知识</h3><p class="muted">基础资料随方案自动加入；可补充其它资料，Agent 实际读取后会留下内容哈希。</p>
            <div v-for="path in requiredKnowledge" :key="path" class="knowledge-row"><span class="required-mark">已预选</span><span>{{ knowledgeTitle(path) }}<small>{{ path }}</small></span><button type="button" class="text-button" @click="viewKnowledge(path)">查看</button></div>
            <details v-if="optionalKnowledge.length" class="extra-knowledge"><summary>补充资料 · 已选 {{ extraKnowledge.filter(path => !requiredKnowledge.includes(path)).length }} 份</summary><div v-for="item in optionalKnowledge" :key="item.path" class="knowledge-row"><label><input type="checkbox" :checked="extraKnowledge.includes(item.path)" @change="toggleKnowledge(item.path)" /><span>{{ item.title }}<small>{{ item.summary || item.path }}</small></span></label><button type="button" class="text-button" @click="viewKnowledge(item.path)">查看</button></div></details>
          </section>
          <div class="form-row"><label>项目名称 <em>*</em><input v-model="brief.name" required maxlength="120" /></label><label>游戏类型 <small>可细化方案中的类型</small><input v-model="brief.genre" /></label></div>
          <div class="form-row"><label>目标平台<input v-model="brief.platform" /></label><label>引擎与运行方式 <small>技术方案的具体版本和要求</small><input v-model="brief.engine" /></label></div>
          <div class="form-row"><label>目标玩家<input v-model="brief.audience" /></label><label>阶段目标<input v-model="brief.cycle" /></label></div>
          <label>核心想法 <em>*</em><textarea v-model="brief.idea" rows="4" required /></label><label>首版范围<textarea v-model="brief.scope" rows="3" /></label>
          <label>参考资料路径 <small>每行一条，相对工程 ref/ 目录；交给后端读取与核验</small><textarea v-model="references" rows="4" placeholder="例如 竞品研究/报告.md" /></label>
          <label>工作目录 <small>留空时由后端分配；不同项目应使用独立目录</small><input v-model="workspace" placeholder="留空，自动分配新项目目录" /></label>
          <div class="form-foot"><span>项目简报、方案快照与所选知识保存在服务端。</span><button class="button primary" :disabled="submitting || !catalogReady">{{ submitting ? '正在创建…' : '保存项目并进入原型定义 →' }}</button></div>
        </form>
      </template>
      <template v-else-if="project">
        <div class="workspace-breadcrumb"><button @click="backToProjects">← 我的项目</button><span>/</span><strong>{{ project.name }}</strong><span class="save-state">服务端记录 · 每 2 秒同步</span></div>
        <nav class="pipeline" aria-label="游戏研发四阶段"><button v-for="(item, index) in workflowSteps" :key="item.id" :class="{ current: step === index, complete: project.stages?.find(s => s.id === item.id)?.status === 'completed' }" :aria-current="step === index ? 'step' : undefined" @click="goStep(index)"><span>{{ project.stages?.find(s => s.id === item.id)?.confirmed_at ? '✓' : `0${index + 1}` }}</span><strong>{{ item.name }}</strong><small>{{ label(project.stages?.find(s => s.id === item.id)?.status) }}</small></button></nav>
        <div class="workspace-title"><div><div class="eyebrow">阶段 0{{ step + 1 }} / 04 · {{ currentStep.owner }}</div><h1>{{ currentStep.name }}<span class="status-tag" :class="stage?.status">{{ label(stage?.status) }}</span></h1><p>{{ currentStep.desc }}</p></div><div class="completion-meter"><strong>{{ confirmedCount }}<small> / 4</small></strong><span>已评审阶段</span></div></div>
        <div class="workspace-grid"><div class="stage-main">
          <div v-if="!available" class="info-banner">请先完成并确认「{{ workflowSteps[step - 1].name }}」。可以先查看本阶段历史记录与产物。</div>
          <div v-if="runtimeUnavailable && !runtimeLoading" class="error-banner" role="alert">真实执行环境尚不可用：{{ runtimeError || runtime?.error || runtime?.message || '请检查 Codex 登录、模型和后端配置。' }}<button @click="loadLibrary">重新检查</button></div>
          <section class="panel execution-panel"><div class="panel-heading"><h2><span class="section-number">01</span> 阶段执行</h2><span class="muted">{{ runtime?.model || 'gpt-6.1-sol' }} · DeepAgents</span></div><p class="panel-description">读取项目简报、品类与技术知识、已确认的上游产物与所选 Skill，执行文件制作和检查。</p><div class="execution-actions"><button class="button primary" :disabled="!available || !!activeRun || submitting || runtimeUnavailable" @click="execute()">{{ submitting ? '正在提交…' : stage?.run_id ? '重新执行本阶段' : '运行本阶段 →' }}</button><button v-if="running" class="button" :disabled="submitting" @click="cancelRun">取消运行</button><button v-if="['failed', 'cancelled', 'interrupted'].includes(run?.status)" class="button" :disabled="!!activeRun || submitting || runtimeUnavailable" @click="resumeRun">从上次记录继续 / 重试</button></div><p v-if="stage?.run_id" class="muted">重新执行会重置本阶段及下游的确认状态，历史运行和产物仍可查阅。</p><p v-if="activeRun && activeRun.stage !== currentStep.id" class="muted">其他阶段正在运行，请等待完成或切换到对应阶段取消。</p><details class="skill-picker"><summary>引用 Skill <span>已选 {{ selectedSkills[currentStep.id].length }} 项 · 真实知识库</span></summary><p v-if="skillError" class="error-text">Skill 列表不可用：{{ skillError }}</p><p v-else-if="!skills.length" class="muted">知识库尚未提供可执行 Skill。</p><div class="skill-list"><label v-for="item in skills" :key="item.path" class="skill-option"><input type="checkbox" :checked="selectedSkills[currentStep.id].includes(item.path)" :disabled="!!activeRun || submitting" @change="toggleSkill(item.path)" /><span><strong>{{ item.name }}</strong><small :title="item.description">{{ item.description }}</small><code>{{ item.path }}</code></span></label></div></details></section>
          <section v-if="projectKnowledge.length" class="panel project-knowledge" aria-label="项目引用知识">
            <div class="panel-heading"><h2>品类与技术知识</h2><span class="muted">已选 {{ projectKnowledge.length }} 份</span></div>
            <p class="panel-description">这些资料随项目提供给各阶段。选择记录与实际读取分别保留，可在运行事件中核对读取内容和哈希。</p>
            <div v-for="path in projectKnowledge" :key="path" class="knowledge-row"><span>{{ knowledgeTitle(path) }}<small>{{ path }}</small></span><button class="text-button" @click="viewKnowledge(path)">查看资料</button></div>
          </section>
          <WorkflowStageChat :key="`${project.id}-${currentStep.id}`" :stage-name="currentStep.name" :owner="currentStep.owner" :messages="chatMessages" :draft="drafts[currentStep.id]" :suggestions="stageSuggestions" :busy="running" :disabled="!available || submitting || runtimeUnavailable || (!!activeRun && !running)" :version="stageRuns.length" @update:draft="drafts[currentStep.id] = $event" @send="execute()" @cancel="cancelRun" />
          <section class="panel run-panel"><div class="panel-heading"><h2><span class="section-number">02</span> 运行状态与事件</h2><select v-if="stageRuns.length" :value="run?.id" aria-label="选择阶段运行记录" @change="selectRun($event.target.value)"><option v-for="item in stageRuns" :key="item.id" :value="item.id">{{ formatTime(item.created_at) }} · {{ label(item.status) }}</option></select></div><template v-if="run"><div class="run-status"><span class="status-tag" :class="run.status">{{ label(run.status) }}</span><code>{{ run.id }}</code><strong>{{ run.events?.length || 0 }} 条事件</strong></div><p v-if="run.summary" class="run-summary">{{ run.summary }}</p><p v-if="run.error" class="error-banner" role="alert">{{ run.error }}</p><p class="run-meta">{{ run.model || 'gpt-6.1-sol' }} · {{ run.provider || 'Codex' }} · 更新于 {{ formatTime(run.updated_at) }}</p><details v-if="run.skill_paths?.length" class="references"><summary>本次选择 Skill · {{ run.skill_paths.length }}</summary><p v-for="path in run.skill_paths" :key="path">{{ path }}</p></details><details v-if="runKnowledge.length" class="references"><summary>本次选择知识 · {{ runKnowledge.length }} 份</summary><p v-for="path in runKnowledge" :key="path">{{ knowledgeTitle(path) }} · {{ path }}</p></details><details v-if="knowledgeReads.length" class="references"><summary>实际知识读取 · {{ knowledgeReads.length }} 条记录</summary><p v-for="event in knowledgeReads" :key="event.seq">{{ event.data?.path }}<code v-if="event.data?.sha256">SHA-256：{{ event.data.sha256 }}</code></p></details><div class="events" role="log" aria-label="真实执行事件"><article v-for="event in run.events || []" :key="event.seq"><div><time>{{ formatTime(event.time) }}</time><span>{{ event.type }}</span></div><p>{{ event.message }}</p><details v-if="event.data && Object.keys(event.data).length"><summary>查看事件数据</summary><pre>{{ JSON.stringify(event.data, null, 2) }}</pre></details></article><p v-if="!run.events?.length" class="muted">等待后端写入事件…</p></div></template><div v-else class="stage-empty">{{ loading ? '正在读取服务端执行记录…' : '本阶段还没有运行记录。点击运行，开始真实执行。' }}</div></section>
          <section class="panel artifact-panel"><div class="panel-heading"><h2><span class="section-number">03</span> 实际产物与测试记录</h2><span class="muted">{{ runArtifacts.length }} 个文件</span></div><div v-if="runArtifacts.length" class="artifact-list"><button v-for="item in runArtifacts" :key="item.id" :class="{ selected: selectedArtifact?.id === item.id }" @click="viewArtifact(item)"><span>{{ item.kind === 'image' ? '▧' : '▤' }}</span><div><strong>{{ item.name }}</strong><small>{{ item.path }}</small></div><small>{{ provenanceLabel(item.provenance) }}</small></button></div><p v-else class="stage-empty">尚未产生真实文件。测试命令、报告和问题记录将作为产物显示在这里。</p><div v-if="selectedArtifact" class="artifact-preview"><div class="artifact-preview-heading"><strong>{{ selectedArtifact.name }}</strong><a :href="selectedArtifact.url" target="_blank" rel="noopener">打开 / 下载 ↗</a></div><p v-if="artifactLoading" role="status">正在读取产物…</p><p v-if="artifactError" class="error-text">{{ artifactError }}</p><img v-if="selectedArtifact.kind === 'image'" :src="selectedArtifact.url" :alt="selectedArtifact.name" /><div v-else-if="artifactText && markdownArtifact" class="artifact-markdown" v-html="artifactHtml"></div><pre v-else-if="artifactText">{{ artifactText }}</pre><p v-else-if="!artifactLoading && !artifactError" class="muted">请打开文件查看完整内容。</p></div></section>
          <WorkflowPrototype v-if="step >= 2 || previewUrl" :url="previewUrl" :name="project.name" />
          <section class="panel review-panel"><div class="panel-heading"><h2><span class="section-number">04</span> 阶段评审</h2><span v-if="stage?.confirmed_at" class="status-tag completed">已确认</span></div><p class="panel-description">阅读真实产物、运行事件与测试结果后确认。执行完成本身不会自动通过评审。</p><label class="check-row"><input v-model="reviewed" type="checkbox" :disabled="run?.status !== 'awaiting_confirmation' || run?.id !== stage?.run_id" />我已检查本阶段产物、验证结果与已知问题，确认可交给下一阶段。</label><textarea v-model="reviewNote" rows="2" placeholder="评审意见 / 已知问题（可选）" aria-label="评审意见" /><div class="review-actions"><button class="button primary" :disabled="!canConfirm" @click="confirmStage">确认本阶段</button><button v-if="stage?.confirmed_at && step < 3" class="button" @click="goStep(step + 1)">进入{{ workflowSteps[step + 1].name }} →</button></div></section>
        </div><aside class="context-sidebar"><section class="panel context-card"><div class="eyebrow">项目简报</div><h3>{{ project.name }}</h3><p>{{ projectBrief.genre || '游戏研发项目' }} · {{ projectBrief.platform || projectBrief['平台'] }}</p><dl><template v-for="[key, value] in briefEntries" :key="key"><dt>{{ key }}</dt><dd>{{ value || '未填写' }}</dd></template></dl><p v-if="typeof project.brief === 'string'" class="brief-text">{{ project.brief }}</p><template v-if="productionProfile"><div class="context-divider"></div><h4>项目方案快照</h4><p>品类：{{ productionProfile.genre?.label || productionProfile.genre_id }}</p><p>技术：{{ productionProfile.framework?.label || productionProfile.framework_id }}</p><p v-if="productionProfile.framework?.status">验证程度：{{ productionProfile.framework.status }}</p><p v-if="productionProfile.version">版本：{{ productionProfile.version }}</p><code v-if="productionProfile.sha256">SHA-256：{{ productionProfile.sha256 }}</code></template><div class="context-divider"></div><h4>本阶段预期产出</h4><p v-for="output in currentStep.outputs" :key="output">▤ {{ output }}</p><div class="context-divider"></div><h4>工程目录</h4><code>{{ project.workspace }}</code><details v-if="project.references?.length" class="references"><summary>参考资料 · {{ project.references.length }}</summary><p v-for="item in project.references" :key="item">{{ item }}</p></details></section><section class="panel context-card"><h4>执行信息</h4><p>框架：DeepAgents</p><p>模型：{{ runtime?.model || 'gpt-6.1-sol' }}</p><p>状态：{{ runtimeUnavailable ? '环境待检查' : '已连接' }}</p><p class="muted">上游更新后，下游应重新执行并评审。工作台只显示后端记录的状态和产物。</p></section></aside></div>
      </template>
      <footer class="studio-footer"><span>游戏研发工作台</span><span>原型定义 → 美术资源 → 代码与集成 → 测试验收</span></footer>
    </main>
    <div v-if="knowledgePreview" class="knowledge-overlay" @click.self="closeKnowledge" @keydown.esc="closeKnowledge">
      <section class="knowledge-dialog" role="dialog" aria-modal="true" :aria-label="knowledgePreview.title" tabindex="-1">
        <div class="knowledge-dialog-heading"><strong>{{ knowledgePreview.title }}</strong><button class="button" @click="closeKnowledge">关闭</button></div>
        <p class="muted">{{ knowledgePreview.path }}</p><p class="muted">这里展示知识库当前原文；具体运行采用的内容与哈希请查看该次运行事件。</p>
        <a v-if="knowledgePreview.url" :href="knowledgePreview.url" target="_blank" rel="noopener" class="text-button">打开原文 ↗</a>
        <p v-if="knowledgeLoading" role="status">正在读取知识资料…</p><p v-else-if="knowledgeError" class="error-text">{{ knowledgeError }}</p><div v-else class="artifact-markdown" v-html="knowledgeHtml"></div>
      </section>
    </div>
    <div v-if="notice" class="toast" role="status">{{ notice }}</div>
  </div>
</template>

<style scoped>
.brief-form select { display: block; width: 100%; min-width: 0; padding: 12px; margin-top: 9px; border: 1px solid #dce2d3; border-radius: 5px; background: #fcfdf9; color: #5e6e52; font: inherit; font-size: 12px; }
.brief-form .knowledge-row label { display: flex; margin: 0; }.brief-form .knowledge-row label input { display: inline-block; }
.choice-description,.choice-status,.profile-explanation { font-size: 11px; font-weight: 400; line-height: 1.85; color: #788b68; margin-top: 10px; overflow-wrap: anywhere; }.choice-status { color: #8d753e; }.profile-explanation { padding: 14px; background: #f4f7ef; border-radius: 5px; margin: 0 0 22px; }.profile-explanation p + p { margin-top: 8px; }
.knowledge-selection { margin-bottom: 26px; padding-bottom: 18px; border-bottom: 1px solid #e3e9db; }.knowledge-selection h3 { font-size: 13px; margin-bottom: 10px; }.knowledge-row { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #edf0e7; font-size: 12px; min-width: 0; }.knowledge-row > span:not(.required-mark),.knowledge-row > label { flex: 1; min-width: 0; overflow-wrap: anywhere; }.knowledge-row small { display: block; font-size: 10px; line-height: 1.8; margin-top: 5px; color: #8e9c82; overflow-wrap: anywhere; }.knowledge-row .text-button { flex-shrink: 0; }.knowledge-row label { display: flex; align-items: flex-start; gap: 10px; margin: 0; font-size: 12px; font-weight: 400; }.knowledge-row label input { width: auto; margin: 3px 0 0; flex-shrink: 0; }.required-mark { flex-shrink: 0; color: #63864b; font-size: 10px; background: #edf4e5; padding: 4px 6px; border-radius: 3px; }.extra-knowledge { margin-top: 14px; }.extra-knowledge summary { cursor: pointer; font-size: 12px; color: #71855d; }
.references code { display: block; margin-top: 5px; font-size: 9px; overflow-wrap: anywhere; }.project-cover > span { overflow-wrap: anywhere; }
.knowledge-overlay { position: fixed; inset: 0; z-index: 100; background: #17202c88; display: flex; align-items: center; justify-content: center; padding: 18px; }.knowledge-dialog { width: min(850px, 100%); max-height: 90vh; overflow-y: auto; background: #fff; border-radius: 10px; padding: 25px; box-shadow: 0 16px 50px #0003; }.knowledge-dialog-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 10px; }.knowledge-dialog-heading strong { font-size: 17px; overflow-wrap: anywhere; }.knowledge-dialog > p,.knowledge-dialog > a { margin-top: 12px; }.knowledge-dialog .artifact-markdown { max-height: none; }
.studio-shell { min-height: 100vh; background: #f5f6f0; color: #3e4b39; font-family: var(--font-ui, sans-serif); }
button { cursor: pointer; } button:disabled { opacity: .46; cursor: not-allowed; } button:focus-visible,a:focus-visible { outline: 3px solid #93ace8; outline-offset: 3px; }
.studio-topbar { height: 88px; display: flex; align-items: center; justify-content: space-between; padding: 0 4.5%; border-bottom: 1px solid #e0e4d8; background: #fbfcf8; }
.studio-brand { display: flex; align-items: center; gap: 12px; font-size: 18px; font-weight: 700; text-align: left; }.studio-brand > span { color: #769264; font-size: 33px; }.studio-brand small { display: block; margin-top: 5px; letter-spacing: 2px; font-size: 7px; color: #919b87; }
.topbar-actions { display: flex; align-items: center; gap: 24px; font-size: 12px; color: #849179; }.runtime-chip { background: #e9f0e1; color: #637e4e; padding: 5px 10px; border-radius: 5px; font-size: 10px; }.runtime-chip.unavailable { color: #a17d40; background: #fff0d6; }
.studio-main { max-width: 1440px; margin: auto; padding: 0 4.5%; }.eyebrow { color: #8a9a7a; font-size: 10px; letter-spacing: 2px; }.projects-hero { display: grid; grid-template-columns: 1fr 1fr; gap: 9%; align-items: center; padding: 64px 0; }.projects-hero h1 { font-size: 44px; line-height: 1.4; letter-spacing: -1px; margin: 17px 0; font-weight: 600; }.projects-hero p { font-size: 13px; color: #8b9680; line-height: 2; }.hero-actions { display: flex; gap: 13px; margin-top: 25px; flex-wrap: wrap; }.button { display: inline-flex; align-items: center; justify-content: center; background: #fafcf7; color: #668054; border: 1px solid #d9e0d0; border-radius: 6px; font-size: 12px; padding: 11px 17px; }.button.primary { background: #3565d2; color: white; border-color: #3565d2; }.hero-map { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; background: #edf0e5; border: 1px solid #dfe5d5; padding: 26px; border-radius: 14px; transform: rotate(-2deg); }.hero-map > div { background: #fafcf6; border: 1px solid #d8e0cd; border-radius: 7px; padding: 21px 15px; }.hero-map span { font: 10px monospace; color: #98aa87; }.hero-map strong,.hero-map small { display: block; }.hero-map strong { font-size: 16px; margin: 10px 0; }.hero-map small { color: #9ba58f; font-size: 10px; }
.library-heading { display: flex; justify-content: space-between; align-items: center; gap: 15px; margin-bottom: 23px; }.library-heading h2 { font-size: 22px; margin-top: 8px; }.library-heading h2 span { font-size: 12px; color: #9aa68e; margin-left: 8px; }.library-controls { display: flex; align-items: center; gap: 15px; }.library-controls input { padding: 10px 13px; border: 1px solid #dbe2d1; background: #fafcf7; border-radius: 6px; font-size: 12px; }.text-button { font-size: 12px; color: #5278b8; }.project-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px; }.project-card,.create-card { text-align: left; overflow: hidden; border: 1px solid #dbe1d1; border-radius: 9px; background: white; }.create-card { min-height: 253px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 17px; background: #f9fbf4; border-style: dashed; }.create-card > span { font-size: 37px; color: #9aaf8b; }.create-card strong { font-size: 15px; font-weight: 500; }.create-card small { font-size: 11px; color: #99a48d; }.project-cover { height: 130px; padding: 16px; display: flex; flex-direction: column; background: #e5ecde; color: #6c825d; }.project-cover > span,.project-cover small { font-size: 9px; }.project-cover b { align-self: center; color: #83a373; font-size: 31px; letter-spacing: 10px; margin: 10px; }.project-cover small { align-self: flex-end; }.project-card-body { padding: 20px; }.project-card-body h3 { font-size: 16px; overflow-wrap: anywhere; }.project-card-body p { font-size: 11px; color: #8c9a7e; margin: 9px 0 22px; }.project-card-footer { display: flex; justify-content: space-between; gap: 10px; font-size: 9px; color: #a2aa98; }.project-card-footer strong { font-weight: 500; color: #5777ac; }.empty-message { padding: 45px 0; text-align: center; font-size: 13px; color: #8e9b81; }
.workspace-breadcrumb { padding: 24px 0; display: flex; gap: 14px; align-items: center; font-size: 11px; color: #929b89; }.workspace-breadcrumb strong { color: #5e6b53; overflow-wrap: anywhere; }.save-state { margin-left: auto; font-size: 10px; }.pipeline { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); background: #fafcf7; border: 1px solid #dce2d3; border-radius: 9px; padding: 22px; gap: 18px; }.pipeline button { display: grid; grid-template-columns: 32px 1fr; grid-template-rows: 1fr 1fr; align-items: center; text-align: left; gap: 3px 10px; color: #929f84; }.pipeline button > span { grid-row: span 2; border: 1px solid #d9e2ce; border-radius: 50%; width: 31px; height: 31px; display: grid; place-items: center; font-size: 11px; }.pipeline strong { font-size: 12px; font-weight: 500; }.pipeline small { font-size: 9px; }.pipeline .current { color: #3565d2; }.pipeline .current > span { background: #3565d2; color: white; border-color: #3565d2; }.pipeline .complete:not(.current) { color: #66894c; }.workspace-title { display: flex; justify-content: space-between; align-items: center; gap: 20px; padding: 30px 0 25px; }.workspace-title h1 { display: flex; gap: 14px; align-items: center; font-size: 28px; font-weight: 600; margin: 9px 0; }.workspace-title p { font-size: 12px; color: #909a84; line-height: 1.8; }.completion-meter { text-align: right; flex-shrink: 0; }.completion-meter strong { display: block; font-size: 30px; color: #627b9e; }.completion-meter small { font-size: 14px; }.completion-meter > span { font-size: 10px; color: #96a08c; }.workspace-grid { display: grid; grid-template-columns: minmax(0, 1fr) 275px; gap: 24px; align-items: start; }.stage-main { min-width: 0; }.panel { padding: 24px; border: 1px solid #dce2d3; border-radius: 9px; background: white; margin-bottom: 20px; }.panel-heading { display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 20px; }.panel-heading h2 { font-size: 14px; display: flex; gap: 10px; align-items: center; }.section-number { font: 10px monospace; background: #edf2fa; color: #7d96bd; padding: 4px; border-radius: 3px; }.muted { font-size: 10px; color: #929f86; line-height: 1.8; }.panel-description { font-size: 12px; line-height: 1.9; color: #8a987e; }.execution-actions { display: flex; gap: 10px; flex-wrap: wrap; margin: 20px 0; }.status-tag { font-size: 10px; padding: 4px 8px; background: #edf1e7; color: #8a9a77; border-radius: 4px; font-weight: 500; white-space: nowrap; }.status-tag.running,.status-tag.queued { background: #e8efff; color: #416eb9; }.status-tag.failed,.status-tag.interrupted { background: #fff0e9; color: #b3694b; }.status-tag.completed { background: #eaf2e0; color: #688750; }.status-tag.awaiting_confirmation { background: #fff3db; color: #aa8648; }.skill-picker { border-top: 1px solid #e7ecdf; padding-top: 16px; }.skill-picker summary { font-size: 12px; cursor: pointer; color: #6b7e5d; }.skill-picker summary > span { float: right; font-size: 10px; color: #97a48b; }.skill-option { display: flex; align-items: start; gap: 10px; padding: 14px 0; border-bottom: 1px solid #edf0e7; }.skill-option strong { font-size: 12px; }.skill-option small,.skill-option code { display: block; margin-top: 5px; font-size: 10px; color: #95a08b; overflow-wrap: anywhere; }.skill-list { max-height: 380px; overflow-y: auto; margin-top: 12px; }.skill-option small { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }.skill-option input { margin-top: 4px; accent-color: #426cc2; }
.run-panel select { min-width: 0; max-width: 57%; font-size: 10px; border: 1px solid #dce3d4; padding: 6px; color: #7b8b6d; border-radius: 4px; background: #fafcf7; }.run-status { display: flex; align-items: center; gap: 12px; font-size: 10px; }.run-status code { overflow-wrap: anywhere; color: #a0aa94; }.run-status strong { margin-left: auto; color: #6785ad; }.run-summary { font-size: 12px; line-height: 1.9; white-space: pre-wrap; overflow-wrap: anywhere; }.run-meta { color: #99a58c; font-size: 9px; margin: 12px 0 20px; }.events { max-height: 370px; overflow: auto; border-top: 1px solid #e7ecdf; }.events article { padding: 13px 0; border-bottom: 1px solid #edf1e6; }.events article > div { display: flex; gap: 12px; color: #9baa8d; font-size: 9px; }.events article > p { color: #677d56; font-size: 11px; white-space: pre-wrap; overflow-wrap: anywhere; margin-top: 7px; line-height: 1.8; }.events details { margin-top: 8px; font-size: 10px; color: #7b8e6b; }.events pre { font-size: 10px; white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.7; padding: 10px; background: #f5f8f0; margin-top: 8px; }.stage-empty { padding: 30px 8px; font-size: 12px; text-align: center; color: #a2ac98; line-height: 1.9; }.artifact-list { display: flex; flex-direction: column; gap: 8px; }.artifact-list > button { display: flex; gap: 12px; align-items: center; text-align: left; padding: 12px; border: 1px solid #e3e8da; border-radius: 5px; }.artifact-list > button.selected { border-color: #8ba7d8; background: #f4f7fd; }.artifact-list > button > span { color: #7b9a6a; font-size: 22px; }.artifact-list strong { font-size: 12px; }.artifact-list small { display: block; color: #a1ac94; font-size: 9px; overflow-wrap: anywhere; margin-top: 4px; }.artifact-list > button > small { margin-left: auto; }.artifact-list > button > div { min-width: 0; }.artifact-preview { border-top: 1px solid #e7ecdf; margin-top: 20px; padding-top: 18px; }.artifact-preview-heading { display: flex; justify-content: space-between; gap: 15px; font-size: 11px; }.artifact-preview-heading a { color: #567cbc; flex-shrink: 0; }.artifact-preview pre { background: #f7f9f3; font-size: 11px; line-height: 1.9; white-space: pre-wrap; overflow-wrap: anywhere; max-height: 520px; overflow: auto; padding: 18px; margin-top: 15px; }.artifact-markdown { font-size: 12px; line-height: 1.95; max-height: 650px; overflow: auto; overflow-wrap: anywhere; margin-top: 18px; }.artifact-markdown :deep(h1),.artifact-markdown :deep(h2),.artifact-markdown :deep(h3) { margin: 22px 0 12px; color: #546f44; }.artifact-markdown :deep(h1) { font-size: 20px; }.artifact-markdown :deep(h2) { font-size: 17px; }.artifact-markdown :deep(h3) { font-size: 14px; }.artifact-markdown :deep(p),.artifact-markdown :deep(ul),.artifact-markdown :deep(ol) { margin: 10px 0; }.artifact-markdown :deep(ul),.artifact-markdown :deep(ol) { padding-left: 22px; }.artifact-markdown :deep(a) { color: #426bb1; text-decoration: underline; }.artifact-markdown :deep(.md-table-wrap) { overflow-x: auto; }.artifact-markdown :deep(table) { border-collapse: collapse; min-width: 100%; font-size: 11px; }.artifact-markdown :deep(th),.artifact-markdown :deep(td) { border: 1px solid #dfe6d7; padding: 8px; }.artifact-markdown :deep(th) { background: #f1f5eb; }.artifact-preview img { max-width: 100%; max-height: 500px; object-fit: contain; display: block; margin: 18px auto; }.artifact-preview > p { margin-top: 15px; }
.check-row { display: flex; align-items: flex-start; gap: 10px; font-size: 12px; color: #7c8e6b; line-height: 1.9; margin: 17px 0; }.check-row input { accent-color: #416bc0; margin-top: 5px; }.review-panel textarea { width: 100%; border: 1px solid #dce3d3; background: #fcfdf9; border-radius: 5px; padding: 11px; font: 12px/1.8 inherit; resize: vertical; }.review-actions { display: flex; gap: 12px; margin-top: 18px; flex-wrap: wrap; }.context-sidebar { position: sticky; top: 24px; }.context-card h3 { font-size: 17px; margin-top: 15px; overflow-wrap: anywhere; }.context-card > p { font-size: 10px; color: #8b9a7d; line-height: 1.9; margin-top: 9px; overflow-wrap: anywhere; }.context-card dl { margin-top: 22px; }.context-card dt,.context-card h4 { font-size: 11px; color: #6d825b; font-weight: 600; }.context-card dd { font-size: 11px; color: #97a28b; line-height: 1.9; margin: 7px 0 17px; overflow-wrap: anywhere; white-space: pre-wrap; }.context-divider { height: 1px; background: #e9eddf; margin: 20px 0; }.context-card code { display: block; font-size: 10px; color: #9ca98e; margin-top: 9px; overflow-wrap: anywhere; }.references { margin-top: 20px; font-size: 11px; color: #7e916c; }.references p { overflow-wrap: anywhere; font-size: 10px; line-height: 1.8; margin-top: 10px; }.brief-text { white-space: pre-wrap; }
.brief-form { max-width: 930px; }.brief-form label { display: block; font-size: 12px; margin-bottom: 22px; font-weight: 600; }.brief-form label > small { font-size: 10px; font-weight: 400; color: #9aa78c; margin-left: 8px; }.brief-form input,.brief-form textarea { display: block; width: 100%; border: 1px solid #dce2d3; background: #fcfdf9; color: #5e6e52; font: inherit; font-size: 12px; font-weight: 400; padding: 12px; margin-top: 9px; border-radius: 5px; line-height: 1.8; }.brief-form textarea { resize: vertical; }.brief-form em { color: #c78164; }.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }.form-foot { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding-top: 20px; border-top: 1px solid #e8eddf; }.form-foot span { font-size: 11px; color: #9aa68d; }
.error-banner,.info-banner,.legacy-note { padding: 13px 16px; border-radius: 6px; font-size: 12px; line-height: 1.8; margin: 16px 0; overflow-wrap: anywhere; }.error-banner { background: #fff0e7; color: #a45f3f; border: 1px solid #f0d8ca; }.info-banner,.legacy-note { background: #fff7e4; color: #9c834a; border: 1px solid #ebdfc0; }.error-banner button,.legacy-note button { text-decoration: underline; margin-left: 15px; font-size: 11px; }.error-text { color: #af6848; font-size: 12px; line-height: 1.8; }.studio-footer { display: flex; justify-content: space-between; padding: 25px 0; border-top: 1px solid #dfe4d5; margin-top: 35px; font-size: 9px; color: #a2ad95; letter-spacing: 1px; }.toast { position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); padding: 12px 22px; max-width: 90vw; background: #2d4250; color: white; font-size: 12px; border-radius: 7px; z-index: 50; box-shadow: 0 8px 25px #0002; }
@media(max-width:1100px) { .workspace-grid { grid-template-columns: minmax(0,1fr) 240px; gap: 18px; }.panel { padding: 20px; }.projects-hero h1 { font-size: 36px; }.hero-map { padding: 16px; }.pipeline { gap: 10px; padding: 18px 14px; } }
@media(max-width:800px) { .workspace-grid { grid-template-columns: 1fr; }.context-sidebar { position: static; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }.topbar-actions { gap: 15px; font-size: 10px; }.project-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }.hero-map { gap: 9px; }.hero-map > div { padding: 14px 10px; }.hero-map strong { font-size: 13px; }.projects-hero { gap: 5%; }.projects-hero h1 { font-size: 32px; }.pipeline button { grid-template-columns: 1fr; grid-template-rows: auto; justify-items: center; text-align: center; gap: 7px; }.pipeline button > span { grid-row: auto; }.pipeline small { font-size: 8px; } }
@media(max-width:550px) { .studio-main { padding: 0 16px; }.studio-topbar { padding: 0 16px; height: 75px; }.studio-brand { font-size: 14px; gap: 8px; }.studio-brand > span { font-size: 26px; }.studio-brand small { font-size: 5px; letter-spacing: 1px; }.topbar-actions { gap: 12px; }.topbar-actions > .runtime-chip,.topbar-actions > button:first-of-type { display: none; }.projects-hero { grid-template-columns: 1fr; padding: 38px 0; }.projects-hero h1 { font-size: 34px; }.hero-map { display: none; }.project-grid { grid-template-columns: 1fr; }.library-heading { flex-wrap: wrap; }.library-controls { width: 100%; }.library-controls input { flex: 1; min-width: 0; }.workspace-breadcrumb { font-size: 10px; gap: 10px; }.save-state { display: none; }.pipeline { gap: 4px; padding: 17px 7px; }.pipeline strong { font-size: 11px; }.workspace-title { gap: 10px; }.workspace-title h1 { font-size: 24px; gap: 8px; }.workspace-title p { font-size: 11px; }.eyebrow { font-size: 9px; letter-spacing: 1px; }.completion-meter strong { font-size: 26px; }.context-sidebar { display: block; }.panel { padding: 19px 15px; }.panel-heading { gap: 7px; flex-wrap: wrap; }.panel-heading h2 { font-size: 13px; }.run-panel select { max-width: 100%; }.run-status { flex-wrap: wrap; }.run-status code { font-size: 9px; }.artifact-list > button { padding: 10px; }.skill-picker summary > span { float: none; display: block; margin-top: 8px; }.form-row { grid-template-columns: 1fr; gap: 0; }.form-foot { flex-direction: column; align-items: stretch; }.brief-form label > small { display: block; margin: 6px 0 0; }.studio-footer { font-size: 8px; letter-spacing: 0; gap: 15px; }.legacy-note,.error-banner { font-size: 11px; } }
</style>
