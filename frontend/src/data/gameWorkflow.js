// 四阶段只描述职责和界面文案；状态、产物与测试结论全部来自后端。
export const workflowSteps = [
  { id: 'prototype', name: '原型定义', owner: '策划 Agent', desc: '结合项目需求与品类知识，明确核心循环、玩法规则和验收范围。', outputs: ['项目简报与参考依据', '玩法规则与内容配置', '原型验证与验收标准'] },
  { id: 'art', name: '美术资源', owner: '美术 Agent', desc: '依据原型定义制作真实资源，检查规格、风格和工程引用。', outputs: ['视觉规范', '可用资源与资源清单', '资源检查结果'] },
  { id: 'code', name: '代码与集成', owner: '研发 Agent', desc: '依据项目技术方案实现玩法、集成已验收资源并执行真实构建。', outputs: ['可构建游戏工程', '可运行构建', '集成与构建记录'] },
  { id: 'test', name: '测试验收', owner: '测试 Agent', desc: '运行规则、构建和游戏验证，记录实际结果、缺陷及回归结论。', outputs: ['真实测试报告', '问题与回归记录', '可试玩游戏'] },
]
export const stagePromptSuggestions = [
  ['明确核心循环、输入方式、首版范围和验收标准', '检查胜负条件、内容组织、失败重试与进度规则'],
  ['按照原型与技术方案准备可集成资源并核对规格', '检查交互对象和界面的辨识度，列出实际资源与使用位置'],
  ['按照项目技术方案实现核心玩法，完成资源集成和真实构建', '检查状态切换、重复输入、异常处理和进度恢复'],
  ['执行真实测试并记录命令、结果和可复现问题', '验证完整核心循环、目标平台布局和异常恢复'],
]
export const statusLabels = {
  pending: '待执行', locked: '待上游确认', queued: '排队中', running: '执行中',
  awaiting_confirmation: '待评审确认', completed: '已完成', failed: '执行失败',
  cancelled: '已取消', interrupted: '已中断', stale: '上游已更新',
}
export const createBrief = () => ({
  name: '', genre: '', platform: 'Web / H5',
  engine: '', audience: '休闲游戏玩家',
  cycle: '首版可玩验证', idea: '', scope: '完整核心循环、基础引导、必要的进度保存、真实构建与测试',
})
// 这里只预填可编辑的项目输入，不生成任何阶段产物。
export const ballSortBrief = () => ({
  ...createBrief(), name: '彩球融境 · Ball Sort Fusion', genre: '益智 / Ball Sort',
  idea: '融合 Guru Ball Sort Puzzle、HM Ball Sort 和 Infinite Joy Ball Sort Puzzle 的整理爽感、渐进关卡和操作反馈，制作原创 Cocos 彩球分类游戏。参考项目内三款竞品工程拆解及融合设计报告，以真实构建和测试结果验收。',
  scope: '渐进教学关卡、6 / 8 容量高管挑战、隐藏球与难度分组、撤销与提示、主题与音效、本地进度存档、Web / H5 可玩构建和真实测试',
})
export const ballSortReferences = [
  'BallSort工程拆解_2026-10-01/guru',
  'BallSort工程拆解_2026-10-01/hm',
  'BallSort工程拆解_2026-10-01/infinite',
  'BallSort竞品拆解_2026-10-01/彩球分类头部产品拆解与融合设计报告.md',
]

// 只使用项目已保存的方案快照；旧项目没有方案时继续提供通用建议。
export function projectStageSuggestions(profile, index) {
  const stage = workflowSteps[index].id
  const guidance = profile?.genre?.stage_guidance?.[stage]
  const framework = profile?.framework?.label
  const suggestions = [...stagePromptSuggestions[index]]
  if (guidance) suggestions[0] = guidance
  if (framework && index === 2) suggestions[1] = `依据「${framework}」完成真实构建、测试与资源集成，记录命令和结果`
  return suggestions
}
