import { request } from './http.js'

// 请求失败必须显示真实错误，不回退到本地生成。
const base = '/workflow'
const segment = (value) => encodeURIComponent(value)
export const fetchWorkflowProjects = () => request(`${base}/projects`)
export const fetchWorkflowRuntime = () => request(`${base}/runtime`)
export const fetchWorkflowSkills = () => request(`${base}/skills`)
export const fetchWorkflowCatalog = () => request(`${base}/catalog`)
export const createWorkflowProject = (body) => request(`${base}/projects`, { method: 'POST', body })
export const fetchWorkflowProject = (id) => request(`${base}/projects/${segment(id)}`)
export const fetchWorkflowRuns = (id) => request(`${base}/projects/${segment(id)}/runs`)
export const fetchWorkflowRun = (id) => request(`${base}/runs/${segment(id)}`)
export const startWorkflowRun = (id, body) => request(`${base}/projects/${segment(id)}/runs`, { method: 'POST', body })
export const cancelWorkflowRun = (id) => request(`${base}/runs/${segment(id)}/cancel`, { method: 'POST' })
export const resumeWorkflowRun = (id) => request(`${base}/runs/${segment(id)}/resume`, { method: 'POST' })
export const confirmWorkflowStage = (id, stage, note = '') => request(`${base}/projects/${segment(id)}/stages/${segment(stage)}/confirm`, { method: 'POST', body: { note } })
