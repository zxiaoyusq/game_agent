// 工作台专用的本地知识样例，不触发现有知识库接口，也不冒充已上传的真实资料。
export const knowledgeLibraries = [
  '项目规范',
  '策划知识库',
  '美术知识库',
  '研发知识库',
  '测试知识库',
  '运营知识库',
]

export const workflowKnowledge = [
  {
    id: 'brief',
    library: '项目规范',
    title: '游戏立项与项目简报模板',
    stages: [0, 1],
    tags: ['定位', '目标玩家', '范围'],
    content:
      '项目简报应明确目标玩家、使用场景、核心体验、目标平台和首版范围。区分已知条件与待验证假设，并列出本版本不做的内容。每个里程碑应有负责人、产出和验收条件。',
  },
  {
    id: 'scope',
    library: '项目规范',
    title: '最小可玩版本范围与评审规范',
    stages: [0, 1, 7],
    tags: ['MVP', '评审', '里程碑'],
    content:
      '首版应先闭合一条完整的核心循环。将需求划分为必须实现、可延后和本轮排除三类。上游文档变更后，下游资源、代码与测试必须重新核对；评审确认后才允许进入下一阶段。',
  },
  {
    id: 'players',
    library: '策划知识库',
    title: '休闲游戏玩家需求分析方法',
    stages: [0, 1],
    tags: ['用户', '需求', '碎片时间'],
    content:
      '从玩家动机、单局时长、操作负担和失败成本描述需求。为每条需求填写使用场景、预期体验、优先级和验收方式。没有真实用户调研的数据应标注为待验证假设。',
  },
  {
    id: 'gdd',
    library: '策划知识库',
    title: '游戏策划案与核心循环检查表',
    stages: [2, 3],
    tags: ['GDD', '玩法', '胜负', '新手引导'],
    content:
      '策划案需要描述玩家输入、状态变化、反馈奖励和下一次决策。覆盖胜利、失败、暂停、重试和退出。新手引导逐步引入规则，避免首次体验同时出现多个新机制。',
  },
  {
    id: 'levels',
    library: '策划知识库',
    title: '关卡难度与奖励设计参考',
    stages: [2, 3, 6],
    tags: ['关卡', '难度', '奖励', '数值'],
    content:
      '教学关卡先验证基础操作，后续关卡逐步增加策略和组合。配置目标、步数、时间和奖励时应说明设计意图。使用完成率、失败原因和重试次数调整数值，不能以示例数值代替实测结果。',
  },
  {
    id: 'prototype',
    library: '策划知识库',
    title: '玩法原型试玩与反馈记录模板',
    stages: [3, 6],
    tags: ['原型', '试玩', '反馈', '验证'],
    content:
      '原型优先验证核心循环和首次操作。记录试玩任务、操作路径、卡点、预期反馈与实际反馈。区分规则问题、引导问题和表现问题，明确继续制作或返回策划迭代的条件。',
  },
  {
    id: 'visual',
    library: '美术知识库',
    title: '休闲游戏视觉风格与色板规范',
    stages: [4],
    tags: ['风格', '色板', '场景', '界面'],
    content:
      '场景、角色、交互对象和界面应采用一致的形状语言与色板。交互对象应与背景有足够对比度，核心操作区避免装饰遮挡。成功、失败和不可用状态不能仅依赖颜色区分。',
  },
  {
    id: 'assets',
    library: '美术知识库',
    title: '游戏资源导出与命名规范',
    stages: [4, 5],
    tags: ['尺寸', 'PNG', '透明背景', '资源'],
    content:
      '透明资源导出为带透明通道的 PNG，统一画布尺寸、锚点和缩放倍率。场景使用 bg_、交互对象使用 obj_、界面使用 ui_、特效使用 fx_ 前缀。资源清单记录格式、尺寸、用途、版本与授权来源。',
  },
  {
    id: 'state',
    library: '研发知识库',
    title: '游戏状态与重复输入保护规范',
    stages: [3, 5, 6],
    tags: ['代码', '状态', '结算', '重复点击'],
    content:
      '游戏状态至少区分加载、进行、暂停和结算。结算开始后锁定交互，奖励与跳转只执行一次。异步资源加载或动画结束时应确认当前状态，避免过期回调修改新关卡。',
  },
  {
    id: 'save',
    library: '研发知识库',
    title: '本地存档与资源加载异常处理',
    stages: [5, 6],
    tags: ['存档', '异常', '版本', '加载'],
    content:
      '存档携带结构版本号，读取时验证字段并提供迁移策略。损坏数据需提示用户并允许重新开始。资源失败使用占位反馈并提供重试，不应留下永久加载状态。',
  },
  {
    id: 'qa',
    library: '测试知识库',
    title: '游戏测试用例与缺陷分级标准',
    stages: [6],
    tags: ['测试', '边界', '回归', '缺陷'],
    content:
      '用例应包含前置条件、操作步骤、预期结果和实际结果。覆盖边界输入、重复操作、断网、存档异常和不同设备。阻断核心流程的问题优先处理，修复后回归关联功能，真实测试与模拟报告分别标记。',
  },
  {
    id: 'release',
    library: '运营知识库',
    title: '游戏版本交付与灰度发布检查表',
    stages: [6, 7],
    tags: ['交付', '发布', '回滚', '责任人'],
    content:
      '交付包含版本说明、构建包、资源清单、测试报告和已知问题。发布前核对渠道配置、授权和数据备份。明确发布责任人、灰度范围、观察窗口、停止条件与回滚步骤。',
  },
  {
    id: 'metrics',
    library: '运营知识库',
    title: '上线观察指标与反馈闭环',
    stages: [1, 7],
    tags: ['运营', '留存', '指标', '反馈'],
    content:
      '观察引导完成率、核心关卡完成率、重试次数和留存，结合反馈判断问题所在阶段。指标定义应包含统计口径和观察周期。反馈按阻断程度排序，形成下一版本需求并安排回归。',
  },
]

export function createKnowledgeSelection() {
  return {
    mode: 'recommended',
    library: '全部知识库',
    query: '',
    selectedIds: [],
  }
}

// 刷新时补全旧记录，引用 ID 只允许指向当前演示库中的真实条目。
export function normalizeKnowledgeSelection(value) {
  return {
    mode: value?.mode === 'keyword' ? 'keyword' : 'recommended',
    library: knowledgeLibraries.includes(value?.library)
      ? value.library
      : '全部知识库',
    query: typeof value?.query === 'string' ? value.query : '',
    selectedIds: Array.isArray(value?.selectedIds)
      ? [...new Set(value.selectedIds)].filter((id) =>
          workflowKnowledge.some((item) => item.id === id),
        )
      : [],
  }
}

export function resolveKnowledgeReferences(ids) {
  return ids
    .map((id) => workflowKnowledge.find((item) => item.id === id))
    .filter(Boolean)
    .map(({ id, title, library, content }) => ({ id, title, library, content }))
}

// 关键词检索匹配标题、标签和正文；阶段推荐按适用阶段筛选，不模拟向量得分。
export function searchWorkflowKnowledge(selection, stageIndex) {
  const words = selection.query
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
  return workflowKnowledge.filter((item) => {
    if (
      selection.library !== '全部知识库' &&
      item.library !== selection.library
    )
      return false
    if (selection.mode === 'recommended' && !item.stages.includes(stageIndex))
      return false
    const text =
      `${item.title} ${item.tags.join(' ')} ${item.content}`.toLowerCase()
    return words.every((word) => text.includes(word))
  })
}
