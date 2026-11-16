import { request } from './http.js'

// 请求失败必须显示真实错误，不回退到本地生成。
const base = '/workflow'
const segment = (value) => encodeURIComponent(value)
export const fetchWorkflowProjects = () => request(`${base}/projects`)
export const deleteWorkflowProject = (id) => request(`${base}/projects/${segment(id)}`, { method: 'DELETE' })
export const fetchWorkflowRuntime = (provider = 'api-key', modelId = 'gpt-6.1-sol') => {
  const query = new URLSearchParams({ provider, model_id: modelId })
  return request(`${base}/runtime?${query}`)
}
export const fetchWorkflowSkills = () => request(`${base}/skills`)
export const fetchWorkflowCatalog = () => request(`${base}/catalog`)
export const fetchWorkflowTemplates = () => request(`${base}/templates`)
export const validateWorkflowTemplate = (body) => request(`${base}/templates/validate`, { method: 'POST', body })
export const startWorkflowPipeline = (id) => request(`${base}/projects/${segment(id)}/pipeline/start`, { method: 'POST' })
export const resumeWorkflowPipeline = (id) => request(`${base}/projects/${segment(id)}/pipeline/resume`, { method: 'POST' })
export const cancelWorkflowPipeline = (id) => request(`${base}/projects/${segment(id)}/pipeline/cancel`, { method: 'POST' })
export const answerWorkflowRun = (id, answers) => request(`${base}/runs/${segment(id)}/answers`, { method: 'POST', body: { answers } })
// 来源同步先展示计划，提交时携带摘要以防止把过期预览应用到新文件。
export const fetchSkillSourceSync = () => request(`${base}/skills/source-sync`)
export const syncSkillSources = (body) => request(`${base}/skills/source-sync`, { method: 'POST', body })
// 公司游戏参考保持独立只读目录，不混入知识库的文件上传、删除接口。
export const fetchReferenceGames = () => request(`${base}/reference-games`)
export const fetchReferenceGame = (id) => request(`${base}/reference-games/${segment(id)}`)
export const fetchResearchDocument = (path) => request(`${base}/reference-games/research-document?${new URLSearchParams({ path })}`)
export const createWorkflowProject = (body) => request(`${base}/projects`, { method: 'POST', body })
export const fetchWorkflowProject = (id) => request(`${base}/projects/${segment(id)}`)
export const fetchWorkflowActivity = (id) => request(`${base}/projects/${segment(id)}/activity`)
export const fetchWorkflowRuns = (id) => request(`${base}/projects/${segment(id)}/runs`)
// 只读计算下一次运行的 Skill 选择；最终启动仍由后端重新计算并冻结。
export const fetchWorkflowSkillSelection = (id, body) => request(`${base}/projects/${segment(id)}/skill-selection`, { method: 'POST', body })
export const fetchWorkflowRun = (id) => request(`${base}/runs/${segment(id)}`)
export const startWorkflowRun = (id, body) => request(`${base}/projects/${segment(id)}/runs`, { method: 'POST', body })
export const cancelWorkflowRun = (id) => request(`${base}/runs/${segment(id)}/cancel`, { method: 'POST' })
export const resumeWorkflowRun = (id) => request(`${base}/runs/${segment(id)}/resume`, { method: 'POST' })
export const confirmWorkflowStage = (id, stage, note = '') => request(`${base}/projects/${segment(id)}/stages/${segment(stage)}/confirm`, { method: 'POST', body: { note } })
export const publishWorkflowProject = (id, slug) => request(`${base}/projects/${segment(id)}/publish`, { method: 'POST', body: { slug } })
