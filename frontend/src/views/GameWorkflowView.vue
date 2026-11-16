<script setup>
import { apiFetch } from '../api/http.js'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import '../styles/workflow-create.css'
import StudioIcon from '../components/StudioIcon.vue'
import WorkflowCreationSidebar from '../components/WorkflowCreationSidebar.vue'
import WorkflowGameShowcase from '../components/WorkflowGameShowcase.vue'
import WorkflowRunWorkspace from '../components/WorkflowRunWorkspace.vue'
import WorkflowPrototype from '../components/WorkflowPrototype.vue'
import WorkflowStageChat from '../components/WorkflowStageChat.vue'
import WorkflowTemplatePicker from '../components/WorkflowTemplatePicker.vue'
import WorkflowPlanEditor from '../components/WorkflowPlanEditor.vue'
import WorkflowPipelinePanel from '../components/WorkflowPipelinePanel.vue'
import WorkflowHumanInput from '../components/WorkflowHumanInput.vue'
import { fetchWorkflowTemplates, startWorkflowPipeline, resumeWorkflowPipeline, cancelWorkflowPipeline, answerWorkflowRun } from '../api/workflow.js'
import ReferenceGameLibrary from '../components/ReferenceGameLibrary.vue'
import { renderMarkdown } from '../utils/markdown.js'
import { ballSortBrief, ballSortReferences, createBrief, projectStageSuggestions, statusLabels, workflowSteps } from '../data/gameWorkflow.js'
import { cancelWorkflowRun, confirmWorkflowStage, createWorkflowProject, fetchWorkflowCatalog, fetchWorkflowProject, fetchWorkflowProjects, fetchWorkflowRun, fetchWorkflowRuns, fetchWorkflowRuntime, fetchWorkflowSkills, fetchWorkflowSkillSelection, publishWorkflowProject, resumeWorkflowRun, startWorkflowRun } from '../api/workflow.js'
import { fetchKbItems, kbRawUrl } from '../api/knowledge.js'
import { fetchWorkflowActivity } from '../api/workflow.js'
import { deleteWorkflowProject } from '../api/workflow.js'
import { refreshGamesAfterDeletion } from '../data/producedGames.js'

const emit = defineEmits(['navigate'])
const projects = ref([])
const project = ref(null)
const page = ref('projects')
const workspaceMode = ref('live')
const liveWorkspace = computed(() => page.value === 'workspace' && !!project.value && workspaceMode.value === 'live')
const step = ref(0)
const brief = reactive(createBrief())
const workspace = ref('')
const templates = ref([])
const templateError = ref('')
const productionPlan = ref(null)
// 执行方式与制作计划共用一份状态；请求、导出和确认摘要始终保持一致。
const autonomous = computed({
  get: () => productionPlan.value?.autonomous === true,
  set: (value) => {
    if (productionPlan.value) productionPlan.value = { ...productionPlan.value, autonomous: value }
  },
})
const planApproved = ref(false)
const createRequestId = ref('')
const creationTab = ref('project')
const creationTabs = [
  { id: 'project', label: '项目设定', icon: 'game' },
  { id: 'art', label: '美术与参考', icon: 'image' },
  { id: 'delivery', label: '执行与交付', icon: 'settings' },
]
const automated = computed(() => !!project.value?.production_plan)
const exportTemplate = computed(() => productionPlan.value ? {
  schema_version: 1, id: productionPlan.value.template_id, name: brief.name || '自定义游戏模板',
  description: '从工作台导出的统一制作需求', brief: { ...brief }, genre_id: genreId.value,
  framework_id: frameworkId.value, ...selectedModel(), references: referencePaths.value,
  knowledge_paths: extraKnowledge.value, production_plan: productionPlan.value,
} : null)
const references = ref('')
const referencePaths = computed(() => [...new Set(references.value.split('\n').map((item) => item.trim()).filter(Boolean))])
const runtime = ref(null)
const runtimeLoading = ref(true)
const runtimeError = ref('')
const modelProvider = ref('api-key')
const modelId = ref('gpt-6.1-sol')
let runtimeRequest = 0
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
const skillModes = reactive({ prototype: 'auto', art: 'auto', code: 'auto', test: 'auto' })
const skillIncludes = reactive({ prototype: [], art: [], code: [], test: [] })
const skillExcludes = reactive({ prototype: [], art: [], code: [], test: [] })
const skillPlans = reactive({ prototype: null, art: null, code: null, test: null })
const skillPlanLoading = ref(false)
const skillPlanError = ref('')
let skillPlanRequest = 0
let skillPlanTimer
const drafts = reactive({ prototype: '', art: '', code: '', test: '' })
const runs = ref([])
const run = ref(null)
const search = ref('')
const loading = ref(false)
const deletingProjectId = ref('')
const projectDeleteError = ref('')
const failedProjectId = ref('')
let libraryVersion = 0
const submitting = ref(false)
const taskControl = ref(null)
const taskControlError = ref('')
const error = ref('')
const notice = ref('')
const reviewed = ref(false)
const reviewNote = ref('')
const selectedArtifact = ref(null)
const artifactText = ref('')
const artifactLoading = ref(false)
const artifactError = ref('')
const publishSlug = ref('')
const publishing = ref(false)
const publicationError = ref('')
let pollTimer
let toastTimer
let disposed = false
let artifactController
let requestVersion = 0

const currentStep = computed(() => workflowSteps[step.value])
const stage = computed(() => project.value?.stages?.find((item) => item.id === currentStep.value.id))
const stageRuns = computed(() => runs.value.filter((item) => item.stage === currentStep.value.id).sort((a, b) => String(b.created_at).localeCompare(String(a.created_at))))
const activeRun = computed(() => runs.value.find((item) => ['queued', 'running', 'awaiting_input'].includes(item.status)))
const running = computed(() => ['queued', 'running'].includes(run.value?.status))
const confirmedCount = computed(() => project.value?.stages?.filter((item) => item.confirmed_at || item.status === 'completed').length || 0)
const available = computed(() => step.value === 0 || !!project.value?.stages?.find((item) => item.id === workflowSteps[step.value - 1].id)?.confirmed_at || project.value?.stages?.find((item) => item.id === workflowSteps[step.value - 1].id)?.status === 'completed')
const runtimeUnavailable = computed(() => runtimeLoading.value || !runtime.value || runtime.value.available === false || runtime.value.ready === false)
const modelOptions = computed(() => {
  const options = (runtime.value?.models || []).map(item => typeof item === 'string' ? { id: item, name: item } : { id: item.id, name: item.name || item.label || item.id })
  return options.some(item => item.id === modelId.value) ? options : [{ id: modelId.value, name: modelId.value }, ...options]
})
const runtimeStatus = computed(() => {
  if (runtimeLoading.value) return '执行配置核验中'
  if (runtimeUnavailable.value) return '执行配置待完善'
  return runtime.value.connection_checked ? '模型连接已核验' : '配置就绪 · 尚未连通验证'
})
const testConfirmed = computed(() => !!project.value?.stages?.find(item => item.id === 'test')?.confirmed_at)
const validPublishSlug = computed(() => /^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$/.test(publishSlug.value))
const canPublish = computed(() => testConfirmed.value && validPublishSlug.value && !activeRun.value && !submitting.value && !publishing.value)
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
const skillReads = computed(() => (run.value?.events || []).filter((item) => item.type === 'skill_read'))
const currentSkillPlan = computed(() => skillPlans[currentStep.value.id])
// 按入口路径的顶层目录归属技能包，沿用主入口名称，新增包和子模块会自动归组。
const skillPackages = computed(() => {
  const packages = new Map()
  for (const item of skills.value) {
    const path = item.path.split('/')[0]
    if (!packages.has(path)) packages.set(path, [])
    packages.get(path).push(item)
  }
  return [...packages].map(([path, items]) => {
    const entry = items.find((item) => item.path === `${path}/SKILL.md` || item.path === 'SKILL.md')
    return {
      path,
      name: entry?.name || path,
      entryPath: entry?.path,
      items: entry ? [entry, ...items.filter((item) => item !== entry)] : items,
      selectedCount: items.filter((item) => selectedSkills[currentStep.value.id].includes(item.path)).length,
    }
  })
})
const runSkillItems = computed(() => run.value?.skill_selection?.items || (run.value?.skill_paths || []).map((path) => ({ path, name: skills.value.find((item) => item.path === path)?.name || path })))
const skillSnapshotByPath = computed(() => Object.fromEntries((run.value?.skill_snapshot || []).map((item) => [item.path, item])))
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
function providerLabel(provider) { return provider === 'api-key' ? '服务器 API Key' : provider === 'codex-login' ? 'Codex CLI（登录）' : provider || '来源未记录' }
function selectedModel() { return { model_provider: modelProvider.value, model_id: modelId.value } }
function changeModelProvider() { modelId.value = 'gpt-6.1-sol' }
// 每次只核对当前选择，旧模型的迟到响应不能让新模型显示为可执行。
async function loadRuntime() {
  const version = ++runtimeRequest
  runtimeLoading.value = true; runtimeError.value = ''; runtime.value = null
  try {
    const value = await fetchWorkflowRuntime(modelProvider.value, modelId.value)
    if (!disposed && version === runtimeRequest) runtime.value = value
  } catch (cause) {
    if (!disposed && version === runtimeRequest) runtimeError.value = cause.message || '执行配置读取失败'
  } finally {
    if (!disposed && version === runtimeRequest) runtimeLoading.value = false
  }
}
watch([modelProvider, modelId], loadRuntime)
// 区分本轮实际写入、验证输出和引用快照，避免把并行观察到的文件都归为模型生成。
function provenanceLabel(value) {
  return { agent_edit: '本轮工具写入', generated_asset: '工程图片 API 生成', processed_asset: '图片裁切与装配', validation_output: '验证产生', reference_asset: '引用资源快照', workspace_observation: '工作区文件快照' }[value] || '历史文件快照'
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
// 公司游戏选择器逐个传回信息文件和实际ZIP路径，不引用整个素材库。
function addGameReference(path) {
  references.value = [...new Set([...referencePaths.value, path])].join('\n')
}
function toggleKnowledge(path) {
  extraKnowledge.value = extraKnowledge.value.includes(path) ? extraKnowledge.value.filter((item) => item !== path) : [...extraKnowledge.value, path]
}

function skillSelectionBody(prompt = drafts[currentStep.value.id].trim()) {
  const id = currentStep.value.id
  return { stage: id, prompt, skill_mode: skillModes[id], skill_paths: [...skillIncludes[id]], excluded_skill_paths: [...skillExcludes[id]] }
}
// 预览只读取服务端规则。项目、阶段或需求变化时使旧请求失效，防止迟到的
// 推荐覆盖当前草稿；开始运行时另行复核，运行历史不反写这组输入。
async function loadSkillSelection(prompt) {
  clearTimeout(skillPlanTimer)
  if (page.value !== 'workspace' || !project.value?.id) return null
  const projectId = project.value.id
  const body = skillSelectionBody(prompt)
  const version = ++skillPlanRequest
  skillPlanLoading.value = true
  skillPlanError.value = ''
  try {
    const plan = await fetchWorkflowSkillSelection(projectId, body)
    if (disposed || version !== skillPlanRequest || project.value?.id !== projectId || currentStep.value.id !== body.stage) return null
    skillPlans[body.stage] = plan
    selectedSkills[body.stage] = [...plan.selected_paths]
    return plan
  } catch (cause) {
    if (version === skillPlanRequest) skillPlanError.value = cause.message || 'Skill 自动选择暂不可用'
    return null
  } finally {
    if (!disposed && version === skillPlanRequest) skillPlanLoading.value = false
  }
}
function scheduleSkillSelection() {
  clearTimeout(skillPlanTimer)
  skillPlanRequest++
  skillPlanError.value = ''
  if (page.value !== 'workspace' || !project.value?.id) { skillPlanLoading.value = false; return }
  skillPlanLoading.value = true
  skillPlanTimer = setTimeout(() => loadSkillSelection(), 300)
}
watch([
  () => project.value?.id, () => page.value, () => currentStep.value.id,
  () => drafts[currentStep.value.id], () => skillModes[currentStep.value.id],
  () => JSON.stringify(skillIncludes[currentStep.value.id]),
  () => JSON.stringify(skillExcludes[currentStep.value.id]),
], scheduleSkillSelection)
function changeSkillMode(mode) {
  const id = currentStep.value.id
  skillModes[id] = mode
  skillIncludes[id] = mode === 'manual' ? [...selectedSkills[id]] : []
  skillExcludes[id] = []
}
function resetSkillSelection() {
  const id = currentStep.value.id
  skillModes[id] = 'auto'; skillIncludes[id] = []; skillExcludes[id] = []
  scheduleSkillSelection()
}
function skillReason(path) {
  return currentSkillPlan.value?.items.find((item) => item.path === path)?.reason
    || currentSkillPlan.value?.recommended_items.find((item) => item.path === path)?.reason || ''
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
    const raw = await apiFetch(url, { signal: knowledgeController.signal })
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
  const version = ++libraryVersion
  loading.value = true
  runtimeLoading.value = true
  catalogLoading.value = true
  error.value = ''
  const results = await Promise.allSettled([
    fetchWorkflowProjects().then((value) => { if (!disposed && version === libraryVersion) projects.value = value }),
    loadRuntime(),
    fetchWorkflowSkills().then((value) => { if (!disposed) { skills.value = value; skillError.value = '' } }),
    fetchWorkflowCatalog().then((value) => {
      if (disposed) return
      if (!Array.isArray(value.genres) || !Array.isArray(value.frameworks) || !Array.isArray(value.documents)) throw new Error('方案目录返回格式不完整')
      catalog.value = value; catalogError.value = ''
      if (page.value === 'create') { if (!brief.genre) chooseGenre(); if (!brief.engine) chooseFramework() }
    }),
    fetchWorkflowTemplates().then((value) => {
      if (!disposed) {
        templates.value = value; templateError.value = ''
        if (page.value === 'create' && !productionPlan.value && value[0]) {
          productionPlan.value = { ...JSON.parse(JSON.stringify(value[0].production_plan)), autonomous: false }
        }
      }
    }),
  ])
  if (disposed) return
  if (version === libraryVersion && results[0].status === 'rejected') error.value = `无法加载服务端项目：${results[0].reason.message}`
  if (results[2].status === 'rejected') skillError.value = results[2].reason.message
  if (results[3].status === 'rejected') { catalogError.value = results[3].reason.message; catalog.value = { genres: [], frameworks: [], documents: [] } }
  if (results[4].status === 'rejected') templateError.value = `模板加载失败：${results[4].reason.message}`
  catalogLoading.value = false
  if (version === libraryVersion) loading.value = false
}

async function deleteProject(item) {
  if (deletingProjectId.value) return
  const confirmed = window.confirm(`确定删除项目《${item.name}》？\n\n将永久清理项目记录、生成历史、独立工程和关联发布产出。其他项目共用的工程目录会保留。此操作无法撤销。`)
  if (!confirmed) return
  deletingProjectId.value = item.id
  projectDeleteError.value = ''
  failedProjectId.value = ''
  try {
    const result = await deleteWorkflowProject(item.id)
    if (disposed) return
    // 让删除前发出的项目列表请求失效，防止迟到的响应恢复已删卡片。
    libraryVersion++
    loading.value = false
    const deletedIds = new Set([item.id, ...(result.deleted_project_ids || [])])
    projects.value = projects.value.filter(value => !deletedIds.has(value.id))
    await refreshGamesAfterDeletion(result.deleted_ids || [])
    if (!disposed) toast(result.workspace_preserved ? '项目已删除，共享工程目录已保留。' : '项目及关联产出已删除。')
  } catch (cause) {
    if (disposed) return
    projectDeleteError.value = `《${item.name}》删除失败：${cause.message || '请重试。'}`
    failedProjectId.value = item.id
  } finally {
    deletingProjectId.value = ''
  }
}
function resetInputs() {
  for (const { id } of workflowSteps) {
    drafts[id] = ''; selectedSkills[id] = []; skillModes[id] = 'auto'
    skillIncludes[id] = []; skillExcludes[id] = []; skillPlans[id] = null
  }
}
function newProject(example = false) {
  resetInputs()
  clearTimeout(pollTimer)
  requestVersion++
  project.value = null; run.value = null; runs.value = []; step.value = 0; page.value = 'create'; error.value = ''
  modelProvider.value = 'api-key'; modelId.value = 'gpt-6.1-sol'; publicationError.value = ''
  Object.assign(brief, example ? ballSortBrief() : createBrief())
  genreId.value = example ? 'sorting' : 'general'; frameworkId.value = example ? 'cocos-web' : 'canvas-web'; extraKnowledge.value = []
  if (!example) chooseGenre()
  chooseFramework()
  // 示例只填简报，新项目仍由后端分配独立目录，避免覆盖已验收成品。
  workspace.value = ''
  references.value = example ? ballSortReferences.join('\n') : ''
  productionPlan.value = templates.value[0] ? { ...JSON.parse(JSON.stringify(templates.value[0].production_plan)), autonomous: false } : null
  planApproved.value = false; createRequestId.value = crypto.randomUUID()
  creationTab.value = 'project'
  resetArtifact()
}
function focusCreationSettings(tab = 'project') {
  creationTab.value = tab
  nextTick(() => document.getElementById('creation-settings')?.scrollIntoView({
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start',
  }))
}
function navigateCreationTabs(event, current) {
  // 配置页签支持方向键切换，仅当前页签进入 Tab 顺序。
  const index = creationTabs.findIndex(item => item.id === current)
  const last = creationTabs.length - 1
  const next = { ArrowRight: (index + 1) % creationTabs.length, ArrowLeft: (index + last) % creationTabs.length, Home: 0, End: last }[event.key]
  if (next === undefined) return
  event.preventDefault()
  creationTab.value = creationTabs[next].id
  nextTick(() => document.getElementById(`creation-tab-${creationTab.value}`)?.focus())
}
function revealInvalidField(event) {
  // 折叠分区中的必填项也能被定位，避免浏览器无法聚焦隐藏字段。
  const field = event.target
  const tab = field.closest('[data-creation-tab]')?.dataset.creationTab
  const details = field.closest('details')
  const hidden = (tab && creationTab.value !== tab) || (details && !details.open)
  if (hidden) event.preventDefault()
  if (tab) creationTab.value = tab
  if (details) details.open = true
  nextTick(() => { field.focus(); if (hidden) field.reportValidity() })
}
function useIdeaPrompt(value) {
  brief.idea = brief.idea.trim() ? `${brief.idea}\n${value}` : value
}
function applyTemplate(value, { imported = false } = {}) {
  // 仅填入输入，始终为新项目分配独立目录，避免复用模板覆盖既有游戏。
  Object.assign(brief, createBrief(), value.brief)
  genreId.value = value.genre_id; frameworkId.value = value.framework_id
  modelProvider.value = value.model_provider; modelId.value = value.model_id
  extraKnowledge.value = [...value.knowledge_paths]; references.value = value.references.join('\n')
  // 点击内置模板保留用户当前的执行方式；导入文件则完整恢复其中的设置。
  const nextAutonomous = imported ? value.production_plan.autonomous === true : autonomous.value
  productionPlan.value = { ...JSON.parse(JSON.stringify(value.production_plan)), autonomous: nextAutonomous }
  workspace.value = ''; planApproved.value = false; createRequestId.value = crypto.randomUUID()
  toast('模板已填入。检查玩法、美术与发布设置后即可开始全流程。')
}
// 改变需求会撤销勾选，防止确认后又改了关键输入而误启动。
watch([brief, productionPlan, genreId, frameworkId, references, workspace, modelProvider, modelId, extraKnowledge], () => {
  planApproved.value = false
  createRequestId.value = crypto.randomUUID()
}, { deep: true })
async function createProject() {
  if (!catalogReady.value) { error.value = '请先成功加载品类与技术方案目录。'; return }
  if (!brief.name.trim() || !brief.idea.trim()) { error.value = '请填写项目名称和核心想法。'; return }
  if (!productionPlan.value || !planApproved.value) { error.value = '请检查并确认统一需求和执行设置。'; return }
  submitting.value = true; error.value = ''
  try {
    const normalized = Object.fromEntries(Object.entries(brief).map(([key, value]) => [key, value.trim()]))
    const payload = { name: normalized.name, brief: normalized, references: referencePaths.value, genre_id: genreId.value, framework_id: frameworkId.value, knowledge_paths: extraKnowledge.value.filter((path) => !requiredKnowledge.value.includes(path)), ...selectedModel(), production_plan: productionPlan.value, request_id: createRequestId.value, start_immediately: true }
    if (workspace.value.trim()) payload.workspace = workspace.value.trim()
    // 当前后端在创建请求内启动全流程，前端只接收该请求的执行结果。
    const created = await createWorkflowProject(payload)
    projects.value = [created, ...projects.value.filter((item) => item.id !== created.id)]
    await openProject(created)
    toast('已确认并开始全流程，四阶段将自动衔接。')
  } catch (cause) { error.value = `创建失败：${cause.message}` } finally { submitting.value = false }
}
async function pipelineAction(action) {
  if (submitting.value) return
  stopPolling(); submitting.value = true; error.value = ''
  try { project.value = await action(project.value.id); await refreshProject() }
  catch (cause) { error.value = cause.message; pollTimer = setTimeout(() => refreshProject(), 2000) }
  finally { submitting.value = false }
}
async function controlGeneration({ action, runId }) {
  if (submitting.value || !project.value || !['stop', 'resume'].includes(action)) return
  const projectId = project.value.id
  const request = runId
    ? (action === 'stop' ? cancelWorkflowRun : resumeWorkflowRun)
    : (action === 'stop' ? cancelWorkflowPipeline : resumeWorkflowPipeline)
  // 停止与继续复用真实任务接口；先使旧轮询失效，再等待后端确认，避免提前显示已停止。
  stopPolling()
  const version = requestVersion
  const isCurrent = () => !disposed && project.value?.id === projectId && page.value === 'workspace' && requestVersion === version
  submitting.value = true
  taskControl.value = { projectId, action }
  taskControlError.value = ''
  try {
    const result = await request(runId || projectId)
    // 请求期间可以返回项目列表；迟到的响应不能覆盖另一个项目或新的页面状态。
    if (!isCurrent()) return
    if (runId) {
      runs.value = runs.value.map(item => item.id === runId ? result : item)
      if (run.value?.id === runId) run.value = result
    } else project.value = result
    await refreshProject()
  } catch (cause) {
    if (!isCurrent()) return
    taskControlError.value = `${action === 'stop' ? '停止' : '继续'}未成功：${cause.message || '请检查连接后重试。'}`
    // 失败后重新读取实际状态，但保留操作错误，防止轮询把失败提示立即清掉。
    await refreshProject()
  } finally {
    taskControl.value = null
    submitting.value = false
  }
}
async function answerQuestions(id, answers) {
  if (submitting.value) return
  stopPolling(); submitting.value = true; error.value = ''
  try { await answerWorkflowRun(id, answers); await refreshProject(); toast('回答已保存，正在继续制作。') }
  catch (cause) { error.value = cause.message; pollTimer = setTimeout(() => refreshProject(), 2000) }
  finally { submitting.value = false }
}
async function openProject(item) {
  if (deletingProjectId.value || item.deletion_pending) return
  taskControlError.value = ''
  resetInputs()
  clearTimeout(pollTimer)
  requestVersion++
  project.value = item; page.value = 'workspace'; run.value = null; runs.value = []; error.value = ''; reviewed.value = false
  workspaceMode.value = 'live'
  modelProvider.value = item.model_provider || 'codex-login'; modelId.value = item.model_id || 'gpt-6.1-sol'
  publishSlug.value = item.publication?.slug || item.id; publicationError.value = ''
  const index = workflowSteps.findIndex((definition) => !item.stages?.find((value) => value.id === definition.id)?.confirmed_at && item.stages?.find((value) => value.id === definition.id)?.status !== 'completed')
  step.value = index < 0 ? 3 : index
  resetArtifact()
  await refreshProject(true)
  // 新执行始终按当前项目与阶段自动推荐；旧运行的实际选择在运行记录中单独展示。
}
async function refreshProject(showLoading = false) {
  if (!project.value?.id || page.value !== 'workspace') return
  const id = project.value.id
  const version = requestVersion
  if (showLoading) loading.value = true
  try {
    // 实时视图只同步轻量活动；进入详情后再读取完整证据和产物正文。
    const [detail, history] = liveWorkspace.value
      ? await fetchWorkflowActivity(id).then(value => [value.project, value.runs])
      : await Promise.all([fetchWorkflowProject(id), fetchWorkflowRuns(id)])
    if (disposed || version !== requestVersion || project.value?.id !== id) return
    project.value = detail; runs.value = history
    const selectedId = run.value?.stage === currentStep.value.id ? run.value.id : stage.value?.run_id || stageRuns.value[0]?.id
    if (selectedId && !liveWorkspace.value) {
      const detailRun = await fetchWorkflowRun(selectedId)
      if (disposed || version !== requestVersion) return
      run.value = detailRun
    } else run.value = history.find(item => item.id === selectedId) || null
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
function showWorkspaceDetails(stageId) {
  workspaceMode.value = 'details'
  const index = workflowSteps.findIndex(item => item.id === stageId)
  goStep(index >= 0 ? index : step.value)
}
function showLiveWorkspace() {
  stopPolling(); workspaceMode.value = 'live'; refreshProject()
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
    const actualPrompt = prompt || `请执行${currentStep.value.name}阶段，读取项目简报、品类与技术知识、上游产物和所选 Skill，完成真实文件操作与检查。`
    const plan = await loadSkillSelection(actualPrompt)
    if (!plan) throw new Error(skillPlanError.value || '项目或阶段已变化，请重新核对 Skill 选择')
    const created = await startWorkflowRun(project.value.id, { ...skillSelectionBody(actualPrompt), ...selectedModel() })
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
async function publishProject() {
  if (!canPublish.value) return
  const projectId = project.value.id
  // 发布使用服务端已验收的构建；导航离开后不把结果写回另一个项目。
  stopPolling(); publishing.value = true; submitting.value = true; publicationError.value = ''
  try {
    const publication = await publishWorkflowProject(projectId, publishSlug.value)
    if (disposed || project.value?.id !== projectId) return
    project.value = { ...project.value, publication }
    toast('游戏已发布到独立试玩地址。')
    await refreshProject()
  } catch (cause) {
    if (disposed || project.value?.id !== projectId) return
    publicationError.value = cause.message || '发布失败，请检查已确认的测试结果和路径。'
    await refreshProject()
  } finally { publishing.value = false; submitting.value = false }
}
function toggleSkill(path) {
  const id = currentStep.value.id
  const selected = selectedSkills[id].includes(path)
  selectedSkills[id] = selected ? selectedSkills[id].filter((value) => value !== path) : [...selectedSkills[id], path]
  if (skillModes[id] === 'manual') { skillIncludes[id] = [...selectedSkills[id]]; return }
  // 自动建议与人工选择分开提交，取消勾选会显式排除，下一次重算不会悄悄加回。
  skillIncludes[id] = skillIncludes[id].filter((value) => value !== path)
  skillExcludes[id] = skillExcludes[id].filter((value) => value !== path)
  if (selected) skillExcludes[id].push(path)
  else if (!currentSkillPlan.value?.recommended_paths.includes(path)) skillIncludes[id].push(path)
}
async function viewArtifact(item) {
  resetArtifact(); selectedArtifact.value = item
  if (item.kind === 'image' || item.kind === 'preview') return
  if (item.size > 2 * 1024 * 1024) { artifactError.value = '文件较大，请下载后查看。'; return }
  const textFile = item.kind === 'text' || /\.(md|txt|json|jsonl|csv|ts|js|log|yaml|yml|html|css|xml|py)$/i.test(item.path || item.name)
  if (!textFile) return
  artifactController = new AbortController(); artifactLoading.value = true
  try {
    const response = await apiFetch(item.url, { signal: artifactController.signal })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const content = await response.text()
    if (selectedArtifact.value?.id === item.id) artifactText.value = content
  } catch (cause) { if (cause.name !== 'AbortError') artifactError.value = `产物读取失败：${cause.message}` }
  finally { if (selectedArtifact.value?.id === item.id) artifactLoading.value = false }
}
function backToProjects() { clearTimeout(pollTimer); requestVersion++; page.value = 'projects'; resetArtifact(); loadLibrary() }
onMounted(loadLibrary)
onBeforeUnmount(() => { disposed = true; requestVersion++; runtimeRequest++; skillPlanRequest++; clearTimeout(skillPlanTimer); clearTimeout(pollTimer); clearTimeout(toastTimer); artifactController?.abort(); closeKnowledge() })
</script>

<template>
  <div class="studio-shell" :class="{ 'creation-studio': page === 'create', 'live-workspace': liveWorkspace }">
    <WorkflowCreationSidebar v-if="page === 'create'" :projects="projects" :configured="!runtimeUnavailable" @new="newProject()" @projects="backToProjects" @navigate="emit('navigate', $event)" @open="openProject" @settings="focusCreationSettings('delivery')" />
    <header v-if="page !== 'create' && !liveWorkspace" class="studio-topbar"><button class="studio-brand" @click="emit('navigate', 'home')"><span>✦</span><div>游戏研发工作台<small>GAME DEVELOPMENT WORKSPACE</small></div></button><div class="topbar-actions"><span class="runtime-chip" :class="{ unavailable: runtimeUnavailable }">{{ runtimeStatus }}</span><button @click="emit('navigate', 'knowledge')">知识库与 Skill ↗</button><button @click="emit('navigate', 'home')">返回首页</button></div></header>
    <main class="studio-main">
      <div v-if="error && !liveWorkspace" class="error-banner" role="alert">{{ error }}<button v-if="page === 'projects'" @click="loadLibrary">重新连接</button></div>
      <template v-if="page === 'projects'">
        <section class="projects-hero"><div><div class="eyebrow">从融合创意到可玩游戏</div><h1>让每一步研发<br />都有真实产物。</h1><p>DeepAgents 执行策划、资源、工程与测试。<br />一次确认玩法与美术要求，连续执行，需要补充时再提问。</p><div class="hero-actions"><button class="button primary" @click="newProject()">＋ 创建新项目</button><button class="button" @click="newProject(true)">加载 Ball Sort 融合简报 ↗</button></div></div><div class="hero-map"><div v-for="(item, index) in workflowSteps" :key="item.id"><span>0{{ index + 1 }}</span><strong>{{ item.name }}</strong><small>{{ item.outputs[0] }}</small></div></div></section>
        <section class="project-library">
          <div class="library-heading">
            <div><div class="eyebrow">服务端项目</div><h2>我的游戏项目 <span>{{ projects.length }}</span></h2></div>
            <div class="library-controls">
              <input v-model="search" placeholder="搜索项目名称…" aria-label="搜索项目" />
              <button class="text-button" :disabled="loading || !!deletingProjectId" @click="loadLibrary">{{ loading ? '加载中…' : '刷新' }}</button>
            </div>
          </div>
          <div v-if="projectDeleteError" class="error-banner" role="alert">{{ projectDeleteError }}</div>
          <div class="project-grid">
            <button class="create-card" @click="newProject()"><span>＋</span><strong>创建新项目</strong><small>选择模板，一次确认后全流程制作</small></button>
            <article v-for="item in filteredProjects" :key="item.id" class="project-card">
              <button class="project-open" :aria-label="`打开项目 ${item.name}`" :disabled="!!deletingProjectId || item.deletion_pending" @click="openProject(item)">
                <div class="project-cover"><span>{{ projectTechnology(item) }}</span><b>✦</b><small>{{ item.deletion_pending ? '待清理，请重试删除' : `${item.stages?.filter(s => s.status === 'completed').length || 0} / 4 已确认` }}</small></div>
                <div class="project-card-body"><h3>{{ item.name }}</h3><p>{{ item.brief?.genre || '游戏研发项目' }}</p></div>
              </button>
              <div class="project-card-footer">
                <span>{{ formatTime(item.updated_at || item.created_at) }}</span>
                <div class="project-card-actions">
                  <button class="project-enter" :disabled="!!deletingProjectId || item.deletion_pending" @click="openProject(item)">打开工作台 →</button>
                  <button class="project-delete" :aria-label="`删除项目 ${item.name}`" :disabled="!!deletingProjectId" @click="deleteProject(item)">
                    {{ deletingProjectId === item.id ? '删除中…' : item.deletion_pending || failedProjectId === item.id ? '重试删除' : '删除' }}
                  </button>
                </div>
              </div>
            </article>
          </div>
          <p v-if="!filteredProjects.length && !loading" class="empty-message">{{ error ? '服务端项目暂不可用，请检查后端连接。' : search ? '没有找到匹配的项目。' : '还没有项目。选择适合的品类与技术方案，开始新项目。' }}</p>
        </section>
      </template>
      <template v-else-if="page === 'create'">
        <header class="creation-topbar">
          <div>
            <span>创作空间</span>
            <i>/</i>
            <strong>新建项目</strong>
          </div>
          <span
            class="creation-runtime"
            :class="{ unavailable: runtimeUnavailable }"
            :title="runtimeStatus"
          >
            <i />
            {{
              runtimeLoading
                ? '检查执行配置…'
                : runtimeUnavailable
                  ? '执行配置待完善'
                  : '执行配置就绪'
            }}
          </span>
        </header>
        <form
          class="creation-form"
          @submit.prevent="createProject"
          @invalid.capture="revealInvalidField"
        >
          <section class="creation-hero" aria-labelledby="creation-title">
            <div class="creation-eyebrow">
              <span />
              A LITTLE IDEA. A NEW WORLD.
            </div>
            <h1 id="creation-title">
              你想做一款
              <span>怎样的游戏？</span>
            </h1>
            <p class="creation-subtitle">
              从一个灵感，到真正可以玩的作品。下一款游戏，由你定义。
            </p>
            <div class="idea-composer" :class="{ 'has-idea': brief.idea.trim() }">
              <label for="creation-idea" class="sr-only">核心想法</label>
              <textarea
                id="creation-idea"
                v-model="brief.idea"
                required
                rows="3"
                placeholder="比如，一款保留经典美术、带真实摇骰和走子动画的 LUDO…"
                @keydown.meta.enter.prevent="focusCreationSettings()"
                @keydown.ctrl.enter.prevent="focusCreationSettings()"
              />
              <div class="composer-bottom">
                <div class="composer-tools">
                  <button
                    type="button"
                    class="composer-reference"
                    aria-label="添加美术与参考资料"
                    title="添加美术与参考资料"
                    @click="focusCreationSettings('art')"
                  >
                    <StudioIcon name="plus" :size="20" />
                  </button>
                  <span class="composer-divider" />
                  <label class="composer-model">
                    <StudioIcon name="spark" :size="16" />
                    <select
                      v-model="modelProvider"
                      aria-label="项目模型来源"
                      :disabled="submitting"
                      @change="changeModelProvider"
                    >
                      <option value="api-key">服务器 API Key</option>
                      <option value="codex-login">Codex CLI（服务器登录）</option>
                    </select>
                  </label>
                  <label class="composer-model model-choice">
                    <select
                      v-model="modelId"
                      aria-label="项目模型"
                      :disabled="submitting"
                    >
                      <option
                        v-for="item in modelOptions"
                        :key="item.id"
                        :value="item.id"
                      >
                        {{ item.name }}
                      </option>
                    </select>
                  </label>
                </div>
                <button
                  type="button"
                  class="composer-next"
                  aria-label="完善项目配置"
                  @click="focusCreationSettings()"
                >
                  <span>完善配置</span>
                  <StudioIcon name="arrow" :size="20" />
                </button>
              </div>
              <label class="creation-autonomy" :class="{ enabled: autonomous }">
                <input
                  v-model="autonomous"
                  type="checkbox"
                  aria-label="AI 自主决策，全流程免提问"
                  aria-describedby="creation-autonomy-description"
                  :disabled="!productionPlan || submitting"
                />
                <span>
                  <strong>AI 自主决策，全流程免提问</strong>
                  <small id="creation-autonomy-description">
                    按已填需求自行处理取舍并记录理由，不再因补充提问暂停。未勾选时保留人工补充。
                  </small>
                </span>
                <StudioIcon :name="autonomous ? 'check' : 'spark'" :size="17" />
              </label>
            </div>
            <div class="idea-suggestions">
              <span>试试这些灵感</span>
              <button
                type="button"
                @click="
                  useIdeaPrompt(
                    '制作一款经典 LUDO，保留原版十字棋盘和贴图质感，加入真实摇骰、逐格走子和吃子动画。',
                  )
                "
              >
                <StudioIcon name="game" :size="13" />
                经典棋盘
              </button>
              <button
                type="button"
                @click="
                  useIdeaPrompt(
                    '制作一款适合手机的轻量益智游戏，规则容易理解，有循序渐进的挑战与轻快的操作反馈。',
                  )
                "
              >
                <StudioIcon name="layers" :size="13" />
                轻量益智
              </button>
              <button type="button" @click="focusCreationSettings('art')">
                <StudioIcon name="image" :size="13" />
                让美术更出彩
              </button>
            </div>
          </section>

          <WorkflowTemplatePicker
            :templates="templates"
            :current="exportTemplate"
            @apply="applyTemplate"
          />
          <p v-if="templateError" class="creation-inline-error" role="alert">
            {{ templateError }}
            <button type="button" @click="loadLibrary">重新加载模板</button>
          </p>

          <section
            id="creation-settings"
            class="creation-settings"
            aria-label="制作配置"
          >
            <div class="creation-section-heading">
              <div>
                <h2>把想法，再打磨一点</h2>
                <p>基础配置已就位，你只需要补上在意的细节。</p>
              </div>
              <span class="settings-label">
                <StudioIcon name="settings" :size="14" />
                制作配置
              </span>
            </div>
            <div class="creation-settings-card">
              <div class="creation-tabs" role="tablist" aria-label="制作配置分区">
                <button
                  v-for="item in creationTabs"
                  :id="`creation-tab-${item.id}`"
                  :key="item.id"
                  type="button"
                  role="tab"
                  :aria-selected="creationTab === item.id"
                  :tabindex="creationTab === item.id ? 0 : -1"
                  @keydown="navigateCreationTabs($event, item.id)"
                  :aria-controls="`creation-panel-${item.id}`"
                  :class="{ active: creationTab === item.id }"
                  @click="creationTab = item.id"
                >
                  <StudioIcon :name="item.icon" :size="16" />
                  {{ item.label }}
                  <span v-if="item.id === 'art' && referencePaths.length">
                    {{ referencePaths.length }}
                  </span>
                </button>
              </div>
              <div
                v-show="creationTab === 'project'"
                id="creation-panel-project"
                class="creation-tab-panel"
                role="tabpanel"
                aria-labelledby="creation-tab-project"
                data-creation-tab="project"
              >
                <div v-if="catalogLoading" class="creation-notice" role="status">
                  正在加载品类与技术方案…
                </div>
                <div
                  v-else-if="catalogError"
                  class="creation-inline-error"
                  role="alert"
                >
                  {{ catalogError }}
                  <button type="button" @click="loadLibrary">重新加载</button>
                </div>
                <label class="creation-field">
                  给项目起个名字
                  <em>必填</em>
                  <input
                    v-model="brief.name"
                    aria-label="项目名称"
                    required
                    maxlength="120"
                    placeholder="一个让人记住的名字，例如：星光棋旅"
                  />
                </label>
                <div class="creation-field-row">
                  <label class="creation-field">
                    游戏品类
                    <select
                      v-model="genreId"
                      :disabled="!catalogReady"
                      aria-label="品类方案"
                      @change="chooseGenre"
                    >
                      <option
                        v-for="item in catalog.genres"
                        :key="item.id"
                        :value="item.id"
                      >
                        {{ item.label }}
                      </option>
                    </select>
                  </label>
                  <label class="creation-field">
                    技术方案
                    <select
                      v-model="frameworkId"
                      :disabled="!catalogReady"
                      aria-label="技术方案"
                      @change="chooseFramework"
                    >
                      <option
                        v-for="item in catalog.frameworks"
                        :key="item.id"
                        :value="item.id"
                      >
                        {{ item.label }}
                      </option>
                    </select>
                  </label>
                </div>
                <label class="creation-field scope-field">
                  这次想做到什么程度？
                  <textarea
                    v-model="brief.scope"
                    aria-label="首版范围"
                    rows="2"
                    placeholder="比如，完整核心玩法、2～4 人同屏、基础音效和存档…"
                  />
                </label>
                <details class="creation-details">
                  <summary>
                    更多项目细节
                    <StudioIcon name="chevron" :size="14" />
                  </summary>
                  <div class="creation-field-row">
                    <label class="creation-field">
                      游戏类型
                      <input v-model="brief.genre" />
                    </label>
                    <label class="creation-field">
                      目标平台
                      <input v-model="brief.platform" />
                    </label>
                    <label class="creation-field">
                      目标玩家
                      <input v-model="brief.audience" />
                    </label>
                    <label class="creation-field">
                      阶段目标
                      <input v-model="brief.cycle" />
                    </label>
                  </div>
                  <label class="creation-field">
                    引擎与运行方式
                    <input v-model="brief.engine" />
                  </label>
                </details>
              </div>
              <div
                v-show="creationTab === 'art'"
                id="creation-panel-art"
                class="creation-tab-panel"
                role="tabpanel"
                aria-labelledby="creation-tab-art"
                data-creation-tab="art"
              >
                <WorkflowPlanEditor
                  v-model="productionPlan"
                  :skills="skills"
                  section="art"
                />
                <div class="creation-reference-heading">
                  <StudioIcon name="image" :size="16" />
                  <span>给创意一些视觉参考</span>
                  <small>
                    {{
                      referencePaths.length
                        ? `已选 ${referencePaths.length} 份资料`
                        : '可选'
                    }}
                  </small>
                </div>
                <details class="company-reference-picker creation-details">
                  <summary>
                    选择公司游戏参考
                    <StudioIcon name="plus" :size="15" />
                  </summary>
                  <ReferenceGameLibrary
                    compact
                    :selected-paths="referencePaths"
                    @select="addGameReference"
                  />
                </details>
                <label class="creation-field reference-paths">
                  参考资料路径（含美术参考）
                  <small>每行一条，相对工程 ref/ 目录</small>
                  <textarea
                    v-model="references"
                    rows="3"
                    placeholder="选择上方游戏后会自动填入，也可以添加已有参考文件路径。"
                  />
                </label>
                <p class="creation-service-note">
                  <i :class="{ ready: runtime?.capabilities?.image_generation }" />
                  图片生成服务{{
                    runtime?.capabilities?.image_generation ? '已配置' : '尚未配置'
                  }}
                  <span>原图参考、贴图与动画要求都可以在这里说明。</span>
                </p>
              </div>
              <div
                v-show="creationTab === 'delivery'"
                id="creation-panel-delivery"
                class="creation-tab-panel"
                role="tabpanel"
                aria-labelledby="creation-tab-delivery"
                data-creation-tab="delivery"
              >
                <WorkflowPlanEditor
                  v-model="productionPlan"
                  :skills="skills"
                  section="delivery"
                />
                <details class="creation-details">
                  <summary>
                    模型与运行配置
                    <StudioIcon name="chevron" :size="14" />
                  </summary>
                  <p class="creation-help">
                    当前使用 {{ providerLabel(modelProvider) }} ·
                    {{ modelId }}。可在上方创意输入区切换。
                  </p>
                  <p class="creation-help">
                    {{
                      modelProvider === 'api-key'
                        ? '直接使用服务器已配置的 API Key，你无需提供或配置自己的密钥。'
                        : 'Codex CLI 使用服务器登录身份执行。'
                    }}
                  </p>
                  <p class="creation-help">
                    {{ runtimeStatus }}
                    <button
                      type="button"
                      :disabled="runtimeLoading"
                      @click="loadRuntime"
                    >
                      重新检查配置
                    </button>
                  </p>
                  <p
                    v-if="runtimeError || runtime?.error"
                    class="creation-inline-error"
                  >
                    {{ runtimeError || runtime.error }}
                  </p>
                  <label class="creation-field">
                    工作目录
                    <small>留空自动分配独立目录</small>
                    <input
                      v-model="workspace"
                      placeholder="留空，自动分配新项目目录"
                    />
                  </label>
                </details>
                <details class="creation-details">
                  <summary>
                    品类与技术知识
                    <span>{{ requiredKnowledge.length }} 份已预选</span>
                    <StudioIcon name="chevron" :size="14" />
                  </summary>
                  <p class="creation-help">
                    基础资料随品类和技术方案自动加入，可继续补充。
                  </p>
                  <div
                    v-for="path in requiredKnowledge"
                    :key="path"
                    class="creation-knowledge-row"
                  >
                    <span>
                      {{ knowledgeTitle(path) }}
                      <small>{{ path }}</small>
                    </span>
                    <button type="button" @click="viewKnowledge(path)">查看</button>
                  </div>
                  <details v-if="optionalKnowledge.length" class="creation-details">
                    <summary>
                      补充资料 · 已选
                      {{
                        extraKnowledge.filter(
                          (path) => !requiredKnowledge.includes(path),
                        ).length
                      }}
                      份
                    </summary>
                    <div
                      v-for="item in optionalKnowledge"
                      :key="item.path"
                      class="creation-knowledge-row"
                    >
                      <label>
                        <input
                          type="checkbox"
                          :checked="extraKnowledge.includes(item.path)"
                          @change="toggleKnowledge(item.path)"
                        />
                        {{ item.title }}
                      </label>
                      <button type="button" @click="viewKnowledge(item.path)">
                        查看
                      </button>
                    </div>
                  </details>
                </details>
                <WorkflowPlanEditor
                  v-model="productionPlan"
                  :skills="skills"
                  section="advanced"
                />
              </div>
            </div>
          </section>

          <section class="creation-launch" aria-label="确认制作需求">
            <div class="launch-flow">
              <span v-for="(item, index) in workflowSteps" :key="item.id">
                <i>{{ String(index + 1).padStart(2, '0') }}</i>
                {{ item.name }}
                <StudioIcon
                  v-if="index < workflowSteps.length - 1"
                  name="arrow"
                  :size="12"
                />
              </span>
            </div>
            <div class="launch-action">
              <label class="launch-consent">
                <input v-model="planApproved" type="checkbox" />
                <span>
                  我已确认玩法、美术、模型和交付设置。
                  <small>{{ autonomous ? '四阶段自动衔接，AI 自主决策并记录理由，全程不因提问暂停。' : '四阶段自动衔接，需要补充时再向我提问。' }}</small>
                </span>
              </label>
              <button
                class="creation-submit"
                :disabled="
                  submitting ||
                  !catalogReady ||
                  !productionPlan ||
                  !planApproved ||
                  runtimeUnavailable
                "
              >
                {{ submitting ? '正在启动…' : '确认需求并开始全流程' }}
                <StudioIcon name="arrow" :size="18" />
              </button>
            </div>
          </section>
        </form>
        <WorkflowGameShowcase @navigate="emit('navigate', $event)" />
        <footer class="creation-footer">
          <span>
            AHA 创造
            <span>让每个想法，都有机会被玩到。</span>
          </span>
          <span>
            由 DeepAgents 驱动
            <i />
          </span>
        </footer>
      </template>
      <WorkflowRunWorkspace
        v-else-if="liveWorkspace" :key="project.id" :project="project" :runs="runs"
        :busy="submitting" :error="error" @back="backToProjects" @details="showWorkspaceDetails"
        :control-action="taskControl?.projectId === project.id ? taskControl.action : ''" :control-error="taskControlError"
        @start="pipelineAction(startWorkflowPipeline)" @task-action="controlGeneration"
        @answer="answerQuestions" @refresh="refreshProject()"
      />
      <template v-else-if="project">
        <button class="button" @click="showLiveWorkspace">← 返回实时制作台</button>
        <div class="workspace-breadcrumb"><button @click="backToProjects">← 我的项目</button><span>/</span><strong>{{ project.name }}</strong><span class="save-state">服务端记录 · 每 2 秒同步</span></div>
        <WorkflowPipelinePanel v-if="automated" :project="project" :runs="runs" :busy="submitting" @start="pipelineAction(startWorkflowPipeline)" @resume="pipelineAction(resumeWorkflowPipeline)" @cancel="pipelineAction(cancelWorkflowPipeline)" @answer="answerQuestions" @view-stage="goStep(workflowSteps.findIndex(item => item.id === $event))" />
        <nav class="pipeline" aria-label="游戏研发四阶段"><button v-for="(item, index) in workflowSteps" :key="item.id" :class="{ current: step === index, complete: project.stages?.find(s => s.id === item.id)?.status === 'completed' }" :aria-current="step === index ? 'step' : undefined" @click="goStep(index)"><span>{{ project.stages?.find(s => s.id === item.id)?.confirmed_at ? '✓' : `0${index + 1}` }}</span><strong>{{ item.name }}</strong><small>{{ label(project.stages?.find(s => s.id === item.id)?.status) }}</small></button></nav>
        <div class="workspace-title"><div><div class="eyebrow">阶段 0{{ step + 1 }} / 04 · {{ currentStep.owner }}</div><h1>{{ currentStep.name }}<span class="status-tag" :class="stage?.status">{{ label(stage?.status) }}</span></h1><p>{{ currentStep.desc }}</p></div><div class="completion-meter"><strong>{{ confirmedCount }}<small> / 4</small></strong><span>{{ automated ? '已通过阶段' : '已评审阶段' }}</span></div></div>
        <div class="workspace-grid"><div class="stage-main">
          <div v-if="!automated && !available" class="info-banner">请先完成并确认「{{ workflowSteps[step - 1].name }}」。可以先查看本阶段历史记录与产物。</div>
          <div v-if="runtimeUnavailable && !runtimeLoading" class="error-banner" role="alert">真实执行环境尚不可用：{{ runtimeError || runtime?.error || runtime?.message || '请检查所选模型来源和后端配置。' }}<button @click="loadLibrary">重新检查</button></div>
          <section v-if="!automated" class="panel execution-panel"><div class="panel-heading"><h2><span class="section-number">01</span> 阶段执行</h2><span class="muted">{{ modelId }} · {{ providerLabel(modelProvider) }} · DeepAgents</span></div><p class="panel-description">读取项目简报、品类与技术知识、已确认的上游产物与所选 Skill，执行文件制作和检查。</p>
            <section class="model-selection" aria-label="下一次执行模型">
              <div class="form-row">
                <label>模型来源<select v-model="modelProvider" aria-label="执行模型来源" :disabled="!!activeRun || submitting" @change="changeModelProvider"><option value="api-key">服务器 API Key</option><option value="codex-login">Codex CLI（服务器登录）</option></select></label>
                <label>模型<select v-model="modelId" aria-label="执行模型" :disabled="!!activeRun || submitting"><option v-for="item in modelOptions" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
              </div>
              <p class="model-status">{{ runtimeStatus }}<button type="button" class="text-button" :disabled="runtimeLoading || !!activeRun" @click="loadRuntime">重新检查配置</button></p>
              <p class="muted">{{ modelProvider === 'api-key' ? '直接使用服务器已配置的 API Key，你无需提供自己的密钥。' : '通过服务器 Codex 登录调用，不使用 API Key 网关。' }} 配置检查不代表本次请求已经连通，实际调用以运行事件为准。</p>
              <p v-if="runtime?.capabilities" class="muted">图片生成服务：{{ runtime.capabilities.image_generation ? '已配置' : '未配置' }}；参考包分析与网页验证由本次工具能力执行。</p>
              <p v-if="run && ['failed', 'cancelled', 'interrupted'].includes(run.status)" class="muted">继续旧运行仍使用 {{ providerLabel(run.provider || run.model_provider) }} / {{ run.model || run.model_id }}；如需换模型，请重新执行本阶段。</p>
            </section><div class="execution-actions"><button class="button primary" :disabled="!available || !!activeRun || submitting || runtimeUnavailable" @click="execute()">{{ submitting ? '正在提交…' : stage?.run_id ? '重新执行本阶段' : '运行本阶段 →' }}</button><button v-if="running" class="button" :disabled="submitting" @click="cancelRun">取消运行</button><button v-if="['failed', 'cancelled', 'interrupted'].includes(run?.status)" class="button" :disabled="!!activeRun || submitting" @click="resumeRun">从上次记录继续 / 重试</button></div><p v-if="stage?.run_id" class="muted">重新执行会重置本阶段及下游的确认状态，历史运行和产物仍可查阅。</p><p v-if="activeRun && activeRun.stage !== currentStep.id" class="muted">其他阶段正在运行，请等待完成或切换到对应阶段取消。</p><section class="skill-routing" aria-label="下一次执行的 Skill 选择">
            <div class="skill-routing-head"><strong>下一次执行的 Skill</strong><div><label>选择方式<select :value="skillModes[currentStep.id]" aria-label="Skill 选择方式" :disabled="!!activeRun || submitting" @change="changeSkillMode($event.target.value)"><option value="auto">自动选择</option><option value="manual">手动选择</option></select></label><button type="button" class="text-button" :disabled="!!activeRun || submitting" @click="resetSkillSelection">恢复自动推荐</button></div></div>
            <p class="muted">根据品类、技术框架、当前阶段和本阶段需求选择；可补充或排除，启动时冻结最终版本。继续旧运行使用原选择。</p>
            <p v-if="currentSkillPlan?.context" class="skill-routing-context">{{ currentSkillPlan.context.genre_label || '既有项目' }} · {{ currentSkillPlan.context.framework_label || '沿用既有技术方案' }} · {{ currentStep.name }}</p>
            <p v-if="skillPlanLoading" class="muted" role="status">正在核对合适的 Skill…</p>
            <p v-if="skillPlanError" class="error-text" role="alert">Skill 选择检查失败：{{ skillPlanError }}<button type="button" class="text-button" @click="loadSkillSelection()">重试</button></p>
            <p v-for="warning in currentSkillPlan?.warnings || []" :key="warning" class="skill-routing-warning">{{ warning }}</p>
            <div v-if="currentSkillPlan?.items.length" class="skill-recommendations">
              <article v-for="item in currentSkillPlan.items" :key="item.path"><div><strong>{{ item.name }}</strong><span>{{ item.source === 'manual' ? '人工选择' : '自动推荐' }}</span><span v-if="item.usage === 'reference'">参考规范</span></div><p>{{ item.reason }}</p><details v-if="item.resource_paths?.length"><summary>本阶段优先参考</summary><ul><li v-for="path in item.resource_paths" :key="path"><code :title="path">{{ path.split('/').pop() }}</code></li></ul></details></article>
            </div>
            <details class="skill-picker">
              <summary>调整 Skill <span>已选 {{ selectedSkills[currentStep.id].length }} 项 · {{ skillPackages.length }} 个技能包 · {{ skills.length }} 个入口</span></summary>
              <p v-if="skillError" class="error-text">Skill 列表不可用：{{ skillError }}</p>
              <p v-else-if="!skills.length" class="muted">知识库尚未提供 Skill 入口。</p>
              <p v-else class="muted skill-picker-help">按顶层技能包展开选择，主入口与子模块可分别勾选。</p>
              <div class="skill-list">
                <details v-for="pack in skillPackages" :key="pack.path" class="skill-package">
                  <summary>
                    <span class="skill-package-heading">
                      <span><strong>{{ pack.name }}</strong><code>{{ pack.path }}</code></span>
                      <small>已选 {{ pack.selectedCount }} / {{ pack.items.length }} 项</small>
                    </span>
                  </summary>
                  <div class="skill-package-items">
                    <label v-for="item in pack.items" :key="item.path" class="skill-option">
                      <input type="checkbox" :checked="selectedSkills[currentStep.id].includes(item.path)" :disabled="!!activeRun || submitting" @change="toggleSkill(item.path)" />
                      <span>
                        <strong>{{ item.name }}<span class="skill-entry-kind">{{ item.path === pack.entryPath ? '主入口' : '子模块' }}</span><em v-if="skillExcludes[currentStep.id].includes(item.path)">已排除</em></strong>
                        <small v-if="skillReason(item.path)" class="skill-choice-reason">{{ skillReason(item.path) }}</small>
                        <small v-else :title="item.description">{{ item.description }}</small>
                        <code>{{ item.path }}</code>
                      </span>
                    </label>
                  </div>
                </details>
              </div>
            </details>
          </section></section>
          <section v-if="projectKnowledge.length" class="panel project-knowledge" aria-label="项目引用知识">
            <div class="panel-heading"><h2>品类与技术知识</h2><span class="muted">已选 {{ projectKnowledge.length }} 份</span></div>
            <p class="panel-description">这些资料随项目提供给各阶段。选择记录与实际读取分别保留，可在运行事件中核对读取内容和哈希。</p>
            <div v-for="path in projectKnowledge" :key="path" class="knowledge-row"><span>{{ knowledgeTitle(path) }}<small>{{ path }}</small></span><button class="text-button" @click="viewKnowledge(path)">查看资料</button></div>
          </section>
          <WorkflowHumanInput v-if="!automated" :run="run" :busy="submitting" @answer="answerQuestions(run.id, $event)" />
          <WorkflowStageChat v-if="!automated" :key="`${project.id}-${currentStep.id}`" :stage-name="currentStep.name" :owner="currentStep.owner" :messages="chatMessages" :draft="drafts[currentStep.id]" :suggestions="stageSuggestions" :busy="running" :disabled="!available || submitting || runtimeUnavailable || (!!activeRun && !running)" :version="stageRuns.length" @update:draft="drafts[currentStep.id] = $event" @send="execute()" @cancel="cancelRun" />
          <section class="panel run-panel"><div class="panel-heading"><h2><span class="section-number">02</span> 运行状态与事件</h2><select v-if="stageRuns.length" :value="run?.id" aria-label="选择阶段运行记录" @change="selectRun($event.target.value)"><option v-for="item in stageRuns" :key="item.id" :value="item.id">{{ formatTime(item.created_at) }} · {{ label(item.status) }}</option></select></div><template v-if="run"><div class="run-status"><span class="status-tag" :class="run.status">{{ label(run.status) }}</span><code>{{ run.id }}</code><strong>{{ run.events?.length || 0 }} 条事件</strong></div><p v-if="run.summary" class="run-summary">{{ run.summary }}</p><p v-if="run.error" class="error-banner" role="alert">{{ run.error }}</p><p class="run-meta">{{ run.model || run.model_id || '模型未记录' }} · {{ providerLabel(run.provider || run.model_provider) }} · 更新于 {{ formatTime(run.updated_at) }}</p><details v-if="runSkillItems.length" class="references run-skill-selection"><summary>本次选择 Skill · {{ runSkillItems.length }}<span v-if="run.skill_selection"> · {{ run.skill_selection.mode === 'manual' ? '手动选择' : '自动选择' }}</span></summary><p v-for="item in runSkillItems" :key="item.path"><strong>{{ item.name }}</strong><span v-if="item.reason" class="skill-run-reason">{{ item.reason }}</span><code>{{ item.path }}</code><code v-if="skillSnapshotByPath[item.path]?.sha256">冻结版本 {{ skillSnapshotByPath[item.path].version || '未标记' }} · SHA-256：{{ skillSnapshotByPath[item.path].sha256 }}</code></p><p v-for="warning in run.skill_selection?.warnings || []" :key="warning" class="skill-routing-warning">{{ warning }}</p></details><details v-if="skillReads.length" class="references run-skill-reads"><summary>实际 Skill 读取 · {{ skillReads.length }} 条记录</summary><p v-for="event in skillReads" :key="event.seq">{{ event.data?.path }}<span class="skill-run-reason">{{ event.data?.frozen ? '读取本次冻结版本' : '历史读取记录' }}<template v-if="event.data?.version"> · {{ event.data.version }}</template></span><code v-if="event.data?.sha256">SHA-256：{{ event.data.sha256 }}</code></p></details><details v-if="runKnowledge.length" class="references"><summary>本次选择知识 · {{ runKnowledge.length }} 份</summary><p v-for="path in runKnowledge" :key="path">{{ knowledgeTitle(path) }} · {{ path }}</p></details><details v-if="knowledgeReads.length" class="references"><summary>实际知识读取 · {{ knowledgeReads.length }} 条记录</summary><p v-for="event in knowledgeReads" :key="event.seq">{{ event.data?.path }}<code v-if="event.data?.sha256">SHA-256：{{ event.data.sha256 }}</code></p></details><div class="events" role="log" aria-label="真实执行事件"><article v-for="event in run.events || []" :key="event.seq"><div><time>{{ formatTime(event.time) }}</time><span>{{ event.type }}</span></div><p>{{ event.message }}</p><details v-if="event.data && Object.keys(event.data).length"><summary>查看事件数据</summary><pre>{{ JSON.stringify(event.data, null, 2) }}</pre></details></article><p v-if="!run.events?.length" class="muted">等待后端写入事件…</p></div></template><div v-else class="stage-empty">{{ loading ? '正在读取服务端执行记录…' : '本阶段还没有运行记录。点击运行，开始真实执行。' }}</div></section>
          <section class="panel artifact-panel"><div class="panel-heading"><h2><span class="section-number">03</span> 实际产物与测试记录</h2><span class="muted">{{ runArtifacts.length }} 个文件</span></div><div v-if="runArtifacts.length" class="artifact-list"><button v-for="item in runArtifacts" :key="item.id" :class="{ selected: selectedArtifact?.id === item.id }" @click="viewArtifact(item)"><span>{{ item.kind === 'image' ? '▧' : '▤' }}</span><div><strong>{{ item.name }}</strong><small>{{ item.path }}</small></div><small>{{ provenanceLabel(item.provenance) }}</small></button></div><p v-else class="stage-empty">尚未产生真实文件。测试命令、报告和问题记录将作为产物显示在这里。</p><div v-if="selectedArtifact" class="artifact-preview"><div class="artifact-preview-heading"><strong>{{ selectedArtifact.name }}</strong><a :href="selectedArtifact.url" target="_blank" rel="noopener">打开 / 下载 ↗</a></div><p v-if="artifactLoading" role="status">正在读取产物…</p><p v-if="artifactError" class="error-text">{{ artifactError }}</p><img v-if="selectedArtifact.kind === 'image'" :src="selectedArtifact.url" :alt="selectedArtifact.name" /><div v-else-if="artifactText && markdownArtifact" class="artifact-markdown" v-html="artifactHtml"></div><pre v-else-if="artifactText">{{ artifactText }}</pre><p v-else-if="!artifactLoading && !artifactError" class="muted">请打开文件查看完整内容。</p></div></section>
          <WorkflowPrototype v-if="step >= 2 || previewUrl" :url="previewUrl" :name="project.name" />
          <section v-if="step === 3" class="panel publication-panel" aria-label="发布试玩">
            <div class="panel-heading"><h2>发布试玩</h2><span class="muted">独立 H5 地址</span></div>
            <p class="panel-description">确认测试验收后，把已验证的游戏构建发布到本站。手机和电脑可直接打开同一链接。</p>
            <label>访问路径名称<input v-model.trim="publishSlug" aria-label="访问路径名称" maxlength="64" :disabled="publishing || !!activeRun" placeholder="例如 amber-caravan-api" /></label>
            <p class="muted">仅使用小写字母、数字和连字符。默认使用项目编号，避免覆盖其他游戏；实际发布仍由后端检查归属与构建大小。</p>
            <p v-if="!testConfirmed" class="muted">请先检查产物并确认「测试验收」阶段，再发布。</p>
            <p v-if="publishSlug && !validPublishSlug" class="error-text">路径须为 3–64 位小写字母、数字或连字符，首尾不能是连字符。</p>
            <p v-if="publicationError" class="error-text" role="alert">{{ publicationError }}</p>
            <div class="review-actions"><button class="button primary" :disabled="!canPublish" @click="publishProject">{{ publishing ? '正在发布…' : '发布试玩版本' }}</button><a v-if="project.publication?.url" class="button" :href="project.publication.url" target="_blank" rel="noopener">打开已发布游戏 ↗</a></div>
            <div v-if="project.publication" class="publication-result"><a :href="project.publication.url" target="_blank" rel="noopener">{{ project.publication.url }}</a><p>{{ formatTime(project.publication.published_at) }} · {{ Number(project.publication.bytes || 0).toLocaleString('zh-CN') }} 字节</p><code v-if="project.publication.sha256">SHA-256：{{ project.publication.sha256 }}</code></div>
          </section>
          <section v-if="!automated" class="panel review-panel"><div class="panel-heading"><h2><span class="section-number">04</span> 阶段评审</h2><span v-if="stage?.confirmed_at" class="status-tag completed">已确认</span></div><p class="panel-description">阅读真实产物、运行事件与测试结果后确认。执行完成本身不会自动通过评审。</p><label class="check-row"><input v-model="reviewed" type="checkbox" :disabled="run?.status !== 'awaiting_confirmation' || run?.id !== stage?.run_id" />我已检查本阶段产物、验证结果与已知问题，确认可交给下一阶段。</label><textarea v-model="reviewNote" rows="2" placeholder="评审意见 / 已知问题（可选）" aria-label="评审意见" /><div class="review-actions"><button class="button primary" :disabled="!canConfirm" @click="confirmStage">确认本阶段</button><button v-if="stage?.confirmed_at && step < 3" class="button" @click="goStep(step + 1)">进入{{ workflowSteps[step + 1].name }} →</button></div></section>
        </div><aside class="context-sidebar"><section class="panel context-card"><div class="eyebrow">项目简报</div><h3>{{ project.name }}</h3><p>{{ projectBrief.genre || '游戏研发项目' }} · {{ projectBrief.platform || projectBrief['平台'] }}</p><dl><template v-for="[key, value] in briefEntries" :key="key"><dt>{{ key }}</dt><dd>{{ value || '未填写' }}</dd></template></dl><p v-if="typeof project.brief === 'string'" class="brief-text">{{ project.brief }}</p><template v-if="productionProfile"><div class="context-divider"></div><h4>项目方案快照</h4><p>品类：{{ productionProfile.genre?.label || productionProfile.genre_id }}</p><p>技术：{{ productionProfile.framework?.label || productionProfile.framework_id }}</p><p v-if="productionProfile.framework?.status">验证程度：{{ productionProfile.framework.status }}</p><p v-if="productionProfile.version">版本：{{ productionProfile.version }}</p><code v-if="productionProfile.sha256">SHA-256：{{ productionProfile.sha256 }}</code></template><div class="context-divider"></div><h4>本阶段预期产出</h4><p v-for="output in currentStep.outputs" :key="output">▤ {{ output }}</p><div class="context-divider"></div><h4>工程目录</h4><code>{{ project.workspace }}</code><details v-if="project.references?.length" class="references"><summary>参考资料 · {{ project.references.length }}</summary><p v-for="item in project.references" :key="item">{{ item }}</p></details></section><section class="panel context-card"><h4>执行信息</h4><p>框架：DeepAgents</p><p>下次执行：{{ modelId }}</p><p>来源：{{ providerLabel(modelProvider) }}</p><p>状态：{{ runtimeStatus }}</p><p class="muted">上游更新后，下游应重新执行并评审。工作台只显示后端记录的状态和产物。</p></section></aside></div>
      </template>
      <footer v-if="page !== 'create' && !liveWorkspace" class="studio-footer"><span>游戏研发工作台</span><span>原型定义 → 美术资源 → 代码与集成 → 测试验收</span></footer>
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
.project-card { display: flex; flex-direction: column; }
.project-open { display: block; width: 100%; padding: 0; text-align: left; flex: 1; }
.project-open:focus-visible, .project-card-actions button:focus-visible { outline: 2px solid #5278b8; outline-offset: -3px; }
.project-card > .project-card-footer { padding: 0 20px 18px; align-items: center; flex-wrap: wrap; }
.project-card-actions { display: flex; align-items: center; gap: 10px; margin-left: auto; }
.project-card-actions button { font-size: 10px; padding: 6px 8px; border-radius: 5px; }
.project-enter { color: #5777ac; }
.project-delete { color: #ab5b49; background: #f9eee9; }
.project-delete:hover:not(:disabled) { background: #f4ded4; }
.project-card button:disabled { cursor: not-allowed; opacity: .55; }
/* 实时制作台独占视口，左右区域分别滚动，游戏不会随日志移动。 */
.studio-shell.live-workspace { background: #121719; min-height: 100dvh; }
.studio-shell.live-workspace > .studio-main { max-width: none; width: 100%; padding: 0; margin: 0; }
.live-workspace .toast { background: #294337; border: 1px solid #7fc7a944; color: #d2e9d9; }

/* 模型来源与连通状态分开表达，密钥配置始终保留在服务器。 */
.model-selection { margin: 18px 0 24px; padding: 16px; border: 1px solid #dce3d3; border-radius: 7px; background: #fafcf7; }
.model-selection h3 { font-size: 13px; margin-bottom: 14px; }.model-selection label { display: block; font-size: 12px; color: #65785b; margin-bottom: 12px; }
.model-selection select { display: block; width: 100%; min-width: 0; margin-top: 8px; padding: 10px; border: 1px solid #dce3d3; border-radius: 5px; background: #fff; color: inherit; font: inherit; }
.model-selection .form-row { gap: 14px; }.model-selection .model-status { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 11px; color: #627d56; line-height: 1.8; }
.model-selection .muted,.model-selection .error-text { margin-top: 8px; }
.publication-panel > label { display: block; font-size: 12px; color: #65785b; margin: 18px 0 9px; }.publication-panel input { display: block; width: 100%; margin-top: 8px; padding: 11px; border: 1px solid #dce3d3; border-radius: 5px; font: inherit; }
.publication-panel > p + p { margin-top: 8px; }.publication-result { margin-top: 18px; padding: 14px; border-radius: 5px; background: #f1f6eb; font-size: 11px; overflow-wrap: anywhere; }.publication-result a { color: #426bb1; }.publication-result p,.publication-result code { display: block; margin-top: 8px; color: #7b8a6e; font-size: 10px; }
/* 推荐理由与实际读取分开显示，避免把“已选中”误认为运行已使用。 */
.skill-routing { margin-top: 22px; padding-top: 18px; border-top: 1px solid #e0e5d9; }
.skill-routing-head,.skill-routing-head > div { display: flex; gap: 14px; align-items: center; justify-content: space-between; flex-wrap: wrap; }
.skill-routing-head > strong { font-size: 12px; }.skill-routing-head label { display: flex; gap: 8px; align-items: center; font-size: 11px; color: #65785b; }.skill-routing-head select { padding: 6px 8px; border: 1px solid #dce3d3; background: #fff; color: inherit; font: inherit; border-radius: 4px; }
.skill-routing > .muted { margin-top: 12px; }.skill-routing-context { font-size: 11px; margin-top: 10px; color: #627d56; }
.skill-routing-warning { font-size: 11px; line-height: 1.8; color: #8d6934; background: #faf5e9; border-left: 3px solid #d5b879; padding: 8px 10px; margin-top: 10px; overflow-wrap: anywhere; }
.skill-recommendations { display: grid; gap: 8px; margin-top: 14px; }.skill-recommendations article { padding: 10px 12px; border: 1px solid #e2e8db; border-radius: 5px; background: #fafcf8; }.skill-recommendations article > div { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }.skill-recommendations strong { font-size: 11px; }.skill-recommendations span { font-size: 9px; border: 1px solid #dce4d3; border-radius: 3px; padding: 1px 5px; color: #6f8462; }.skill-recommendations p { font-size: 10px; line-height: 1.8; margin-top: 5px; color: #7a8b6e; overflow-wrap: anywhere; }
.skill-option em { color: #a47e4e; font-size: 9px; font-style: normal; margin-left: 8px; }.skill-option .skill-choice-reason { color: #627d56; }.skill-run-reason { display: block; margin-top: 5px; color: #809175; }
/* 技能包默认折叠，包内保留独立勾选，摘要随当前阶段的选择实时更新。 */
.skill-picker-help { margin-top: 12px; }
.skill-package { border: 1px solid #e2e8db; border-radius: 5px; margin-bottom: 8px; }
.skill-package > summary { display: flex; align-items: center; gap: 8px; padding: 12px; background: #fafcf8; border-radius: 5px; color: #6b7e5d; cursor: pointer; list-style: none; }
.skill-package > summary::-webkit-details-marker { display: none; }
.skill-package > summary::before { content: '▶'; flex-shrink: 0; font-size: 10px; }
.skill-package[open] > summary::before { content: '▼'; }
.skill-package-heading { display: flex; flex: 1; min-width: 0; gap: 12px; align-items: center; justify-content: space-between; }
.skill-package-heading > span { min-width: 0; overflow-wrap: anywhere; }
.skill-package-heading strong { font-size: 12px; }
.skill-package-heading code { display: block; margin-top: 5px; font-size: 10px; color: #95a08b; }
.skill-package-heading > small { flex-shrink: 0; font-size: 10px; color: #7a8b6e; }
.skill-package-items { padding: 0 12px; }
.skill-package-items .skill-option:last-child { border-bottom: 0; }
.skill-option > span { min-width: 0; }
.skill-option input { flex-shrink: 0; }
.skill-entry-kind { display: inline-block; margin-left: 8px; padding: 1px 5px; border: 1px solid #dce4d3; border-radius: 3px; font-size: 9px; font-weight: 400; color: #6f8462; }

.company-reference-picker { border: 1px solid #dce3d3; border-radius: 7px; padding: 15px; margin: 0 0 22px; }
.company-reference-picker > summary { font-size: 12px; color: #6b7e5d; cursor: pointer; }
.company-reference-picker[open] > summary { margin-bottom: 18px; }
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
.workspace-breadcrumb { padding: 24px 0; display: flex; gap: 14px; align-items: center; font-size: 11px; color: #929b89; }.workspace-breadcrumb strong { color: #5e6b53; overflow-wrap: anywhere; }.save-state { margin-left: auto; font-size: 10px; }.pipeline { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); background: #fafcf7; border: 1px solid #dce2d3; border-radius: 9px; padding: 22px; gap: 18px; }.pipeline button { display: grid; grid-template-columns: 32px 1fr; grid-template-rows: 1fr 1fr; align-items: center; text-align: left; gap: 3px 10px; color: #929f84; }.pipeline button > span { grid-row: span 2; border: 1px solid #d9e2ce; border-radius: 50%; width: 31px; height: 31px; display: grid; place-items: center; font-size: 11px; }.pipeline strong { font-size: 12px; font-weight: 500; }.pipeline small { font-size: 9px; }.pipeline .current { color: #3565d2; }.pipeline .current > span { background: #3565d2; color: white; border-color: #3565d2; }.pipeline .complete:not(.current) { color: #66894c; }.workspace-title { display: flex; justify-content: space-between; align-items: center; gap: 20px; padding: 30px 0 25px; }.workspace-title h1 { display: flex; gap: 14px; align-items: center; font-size: 28px; font-weight: 600; margin: 9px 0; }.workspace-title p { font-size: 12px; color: #909a84; line-height: 1.8; }.completion-meter { text-align: right; flex-shrink: 0; }.completion-meter strong { display: block; font-size: 30px; color: #627b9e; }.completion-meter small { font-size: 14px; }.completion-meter > span { font-size: 10px; color: #96a08c; }.workspace-grid { display: grid; grid-template-columns: minmax(0, 1fr) 275px; gap: 24px; align-items: start; }.stage-main { min-width: 0; }.panel { padding: 24px; border: 1px solid #dce2d3; border-radius: 9px; background: white; margin-bottom: 20px; }.panel-heading { display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 20px; }.panel-heading h2 { font-size: 14px; display: flex; gap: 10px; align-items: center; }.section-number { font: 10px monospace; background: #edf2fa; color: #7d96bd; padding: 4px; border-radius: 3px; }.muted { font-size: 10px; color: #929f86; line-height: 1.8; }.panel-description { font-size: 12px; line-height: 1.9; color: #8a987e; }.execution-actions { display: flex; gap: 10px; flex-wrap: wrap; margin: 20px 0; }.status-tag { font-size: 10px; padding: 4px 8px; background: #edf1e7; color: #8a9a77; border-radius: 4px; font-weight: 500; white-space: nowrap; }.status-tag.running,.status-tag.queued { background: #e8efff; color: #416eb9; }.status-tag.failed,.status-tag.interrupted { background: #fff0e9; color: #b3694b; }.status-tag.completed { background: #eaf2e0; color: #688750; }.status-tag.awaiting_confirmation { background: #fff3db; color: #aa8648; }.skill-picker { border-top: 1px solid #e7ecdf; padding-top: 16px; }.skill-picker > summary { font-size: 12px; cursor: pointer; color: #6b7e5d; }.skill-picker > summary > span { float: right; font-size: 10px; color: #97a48b; }.skill-option { display: flex; align-items: start; gap: 10px; padding: 14px 0; border-bottom: 1px solid #edf0e7; }.skill-option strong { font-size: 12px; }.skill-option small,.skill-option code { display: block; margin-top: 5px; font-size: 10px; color: #95a08b; overflow-wrap: anywhere; }.skill-list { max-height: 380px; overflow-y: auto; margin-top: 12px; }.skill-option small { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }.skill-option input { margin-top: 4px; accent-color: #426cc2; }
.run-panel select { min-width: 0; max-width: 57%; font-size: 10px; border: 1px solid #dce3d4; padding: 6px; color: #7b8b6d; border-radius: 4px; background: #fafcf7; }.run-status { display: flex; align-items: center; gap: 12px; font-size: 10px; }.run-status code { overflow-wrap: anywhere; color: #a0aa94; }.run-status strong { margin-left: auto; color: #6785ad; }.run-summary { font-size: 12px; line-height: 1.9; white-space: pre-wrap; overflow-wrap: anywhere; }.run-meta { color: #99a58c; font-size: 9px; margin: 12px 0 20px; }.events { max-height: 370px; overflow: auto; border-top: 1px solid #e7ecdf; }.events article { padding: 13px 0; border-bottom: 1px solid #edf1e6; }.events article > div { display: flex; gap: 12px; color: #9baa8d; font-size: 9px; }.events article > p { color: #677d56; font-size: 11px; white-space: pre-wrap; overflow-wrap: anywhere; margin-top: 7px; line-height: 1.8; }.events details { margin-top: 8px; font-size: 10px; color: #7b8e6b; }.events pre { font-size: 10px; white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.7; padding: 10px; background: #f5f8f0; margin-top: 8px; }.stage-empty { padding: 30px 8px; font-size: 12px; text-align: center; color: #a2ac98; line-height: 1.9; }.artifact-list { display: flex; flex-direction: column; gap: 8px; }.artifact-list > button { display: flex; gap: 12px; align-items: center; text-align: left; padding: 12px; border: 1px solid #e3e8da; border-radius: 5px; }.artifact-list > button.selected { border-color: #8ba7d8; background: #f4f7fd; }.artifact-list > button > span { color: #7b9a6a; font-size: 22px; }.artifact-list strong { font-size: 12px; overflow-wrap: anywhere; }.artifact-list small { display: block; color: #a1ac94; font-size: 9px; overflow-wrap: anywhere; margin-top: 4px; }.artifact-list > button > small { margin-left: auto; }.artifact-list > button > div { min-width: 0; }.artifact-preview { border-top: 1px solid #e7ecdf; margin-top: 20px; padding-top: 18px; }.artifact-preview-heading { display: flex; justify-content: space-between; gap: 15px; font-size: 11px; }.artifact-preview-heading a { color: #567cbc; flex-shrink: 0; }.artifact-preview pre { background: #f7f9f3; font-size: 11px; line-height: 1.9; white-space: pre-wrap; overflow-wrap: anywhere; max-height: 520px; overflow: auto; padding: 18px; margin-top: 15px; }.artifact-markdown { font-size: 12px; line-height: 1.95; max-height: 650px; overflow: auto; overflow-wrap: anywhere; margin-top: 18px; }.artifact-markdown :deep(h1),.artifact-markdown :deep(h2),.artifact-markdown :deep(h3) { margin: 22px 0 12px; color: #546f44; }.artifact-markdown :deep(h1) { font-size: 20px; }.artifact-markdown :deep(h2) { font-size: 17px; }.artifact-markdown :deep(h3) { font-size: 14px; }.artifact-markdown :deep(p),.artifact-markdown :deep(ul),.artifact-markdown :deep(ol) { margin: 10px 0; }.artifact-markdown :deep(ul),.artifact-markdown :deep(ol) { padding-left: 22px; }.artifact-markdown :deep(a) { color: #426bb1; text-decoration: underline; }.artifact-markdown :deep(.md-table-wrap) { overflow-x: auto; }.artifact-markdown :deep(table) { border-collapse: collapse; min-width: 100%; font-size: 11px; }.artifact-markdown :deep(th),.artifact-markdown :deep(td) { border: 1px solid #dfe6d7; padding: 8px; }.artifact-markdown :deep(th) { background: #f1f5eb; }.artifact-preview img { max-width: 100%; max-height: 500px; object-fit: contain; display: block; margin: 18px auto; }.artifact-preview > p { margin-top: 15px; }
.check-row { display: flex; align-items: flex-start; gap: 10px; font-size: 12px; color: #7c8e6b; line-height: 1.9; margin: 17px 0; }.check-row input { accent-color: #416bc0; margin-top: 5px; }.review-panel textarea { width: 100%; border: 1px solid #dce3d3; background: #fcfdf9; border-radius: 5px; padding: 11px; font: 12px/1.8 inherit; resize: vertical; }.review-actions { display: flex; gap: 12px; margin-top: 18px; flex-wrap: wrap; }.context-sidebar { position: sticky; top: 24px; }.context-card h3 { font-size: 17px; margin-top: 15px; overflow-wrap: anywhere; }.context-card > p { font-size: 10px; color: #8b9a7d; line-height: 1.9; margin-top: 9px; overflow-wrap: anywhere; }.context-card dl { margin-top: 22px; }.context-card dt,.context-card h4 { font-size: 11px; color: #6d825b; font-weight: 600; }.context-card dd { font-size: 11px; color: #97a28b; line-height: 1.9; margin: 7px 0 17px; overflow-wrap: anywhere; white-space: pre-wrap; }.context-divider { height: 1px; background: #e9eddf; margin: 20px 0; }.context-card code { display: block; font-size: 10px; color: #9ca98e; margin-top: 9px; overflow-wrap: anywhere; }.references { margin-top: 20px; font-size: 11px; color: #7e916c; }.references p { overflow-wrap: anywhere; font-size: 10px; line-height: 1.8; margin-top: 10px; }.brief-text { white-space: pre-wrap; }
.brief-form { max-width: 930px; }.brief-form label { display: block; font-size: 12px; margin-bottom: 22px; font-weight: 600; }.brief-form label > small { font-size: 10px; font-weight: 400; color: #9aa78c; margin-left: 8px; }.brief-form input,.brief-form textarea { display: block; width: 100%; border: 1px solid #dce2d3; background: #fcfdf9; color: #5e6e52; font: inherit; font-size: 12px; font-weight: 400; padding: 12px; margin-top: 9px; border-radius: 5px; line-height: 1.8; }.brief-form textarea { resize: vertical; }.brief-form em { color: #c78164; }.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }.form-foot { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding-top: 20px; border-top: 1px solid #e8eddf; }.form-foot span { font-size: 11px; color: #9aa68d; }
.error-banner,.info-banner { padding: 13px 16px; border-radius: 6px; font-size: 12px; line-height: 1.8; margin: 16px 0; overflow-wrap: anywhere; }.error-banner { background: #fff0e7; color: #a45f3f; border: 1px solid #f0d8ca; }.info-banner { background: #fff7e4; color: #9c834a; border: 1px solid #ebdfc0; }.error-banner button { text-decoration: underline; margin-left: 15px; font-size: 11px; }.error-text { color: #af6848; font-size: 12px; line-height: 1.8; }.studio-footer { display: flex; justify-content: space-between; padding: 25px 0; border-top: 1px solid #dfe4d5; margin-top: 35px; font-size: 9px; color: #a2ad95; letter-spacing: 1px; }.toast { position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); padding: 12px 22px; max-width: 90vw; background: #2d4250; color: white; font-size: 12px; border-radius: 7px; z-index: 50; box-shadow: 0 8px 25px #0002; }
@media(max-width:1100px) { .workspace-grid { grid-template-columns: minmax(0,1fr) 240px; gap: 18px; }.panel { padding: 20px; }.projects-hero h1 { font-size: 36px; }.hero-map { padding: 16px; }.pipeline { gap: 10px; padding: 18px 14px; } }
@media(max-width:800px) { .workspace-grid { grid-template-columns: 1fr; }.context-sidebar { position: static; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }.topbar-actions { gap: 15px; font-size: 10px; }.project-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }.hero-map { gap: 9px; }.hero-map > div { padding: 14px 10px; }.hero-map strong { font-size: 13px; }.projects-hero { gap: 5%; }.projects-hero h1 { font-size: 32px; }.pipeline button { grid-template-columns: 1fr; grid-template-rows: auto; justify-items: center; text-align: center; gap: 7px; }.pipeline button > span { grid-row: auto; }.pipeline small { font-size: 8px; } }
@media(max-width:550px) { .studio-main { padding: 0 16px; }.studio-topbar { padding: 0 16px; height: 75px; }.studio-brand { font-size: 14px; gap: 8px; }.studio-brand > span { font-size: 26px; }.studio-brand small { font-size: 5px; letter-spacing: 1px; }.topbar-actions { gap: 12px; }.topbar-actions > .runtime-chip,.topbar-actions > button:first-of-type { display: none; }.projects-hero { grid-template-columns: 1fr; padding: 38px 0; }.projects-hero h1 { font-size: 34px; }.hero-map { display: none; }.project-grid { grid-template-columns: 1fr; }.library-heading { flex-wrap: wrap; }.library-controls { width: 100%; }.library-controls input { flex: 1; min-width: 0; }.workspace-breadcrumb { font-size: 10px; gap: 10px; }.save-state { display: none; }.pipeline { gap: 4px; padding: 17px 7px; }.pipeline strong { font-size: 11px; }.workspace-title { gap: 10px; }.workspace-title h1 { font-size: 24px; gap: 8px; }.workspace-title p { font-size: 11px; }.eyebrow { font-size: 9px; letter-spacing: 1px; }.completion-meter strong { font-size: 26px; }.context-sidebar { display: block; }.panel { padding: 19px 15px; }.panel-heading { gap: 7px; flex-wrap: wrap; }.panel-heading h2 { font-size: 13px; }.run-panel select { max-width: 100%; }.run-status { flex-wrap: wrap; }.run-status code { font-size: 9px; }.artifact-list > button { padding: 10px; }.skill-picker > summary > span { float: none; display: block; margin-top: 8px; }.form-row { grid-template-columns: 1fr; gap: 0; }.form-foot { flex-direction: column; align-items: stretch; }.brief-form label > small { display: block; margin: 6px 0 0; }.studio-footer { font-size: 8px; letter-spacing: 0; gap: 15px; }.error-banner { font-size: 11px; } }
</style>
