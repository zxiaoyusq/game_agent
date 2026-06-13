<script setup>
const emit = defineEmits(['navigate'])

const agentModules = [
  {
    id: 'planning',
    name: '策划 Agent',
    subtitle: 'Game Design Agent',
    desc: '玩法构思、活动规则、数值思路、任务系统、版本需求文档',
    color: 'blue',
    icon: '📋',
    outputs: ['玩法策划案', '活动规则', '数值设计', '需求文档', '验收标准'],
    inputs: '玩法目标 · 版本方向 · 用户反馈 · 竞品参考',
  },
  {
    id: 'art',
    name: '美术 Agent',
    subtitle: 'Art Production Agent',
    desc: '美术需求拆解、风格参考整理、原画/建模/视频素材生成',
    color: 'pink',
    icon: '🎨',
    outputs: ['素材清单', '原画初稿', '建模需求', '视频脚本', 'AIGC Prompt'],
    inputs: '策划案 · 美术风格规范 · 历史素材参考',
  },
  {
    id: 'dev',
    name: '研发 Agent',
    subtitle: 'Development Agent',
    desc: '功能模块代码生成、Demo 搭建、资源接入和接口实现',
    color: 'green',
    icon: '⚙️',
    outputs: ['客户端逻辑', '服务端接口', '配置文件', '测试样例', '玩法 Demo'],
    inputs: '需求文档 · 素材规格 · 项目代码库 · 接口规范',
  },
  {
    id: 'ops',
    name: '运营 Agent',
    subtitle: 'Operations Agent',
    desc: '活动方案、公告文案、推送内容、用户反馈分析、版本复盘',
    color: 'orange',
    icon: '📢',
    outputs: ['活动方案', '公告文案', '推送文案', '反馈分析', '复盘报告'],
    inputs: '策划案 · 版本功能 · 美术素材 · 用户数据',
  },
]

const knowledgeModule = {
  id: 'knowledge',
  name: '知识库管理',
  subtitle: 'Knowledge Base',
  desc: '统一管理项目知识、历史经验和各模块产出沉淀',
  icon: '📚',
}

function selectAgent(id) {
  emit('navigate', 'agent', id)
}

function openKnowledge() {
  emit('navigate', 'knowledge')
}
</script>

<template>
  <div class="home">
    <!-- 顶部导航栏 -->
    <header class="topbar">
      <div class="brand">
        <div class="brand-logo">G</div>
        <div class="brand-text">
          <div class="brand-name">游戏全链路 AI Agent 产研系统</div>
          <div class="brand-sub">Game Production Agent System</div>
        </div>
      </div>
      <div class="topbar-right">
        <button class="ghost-btn">项目：欢乐麻将连连看</button>
        <button class="ghost-btn">v0.1.0</button>
        <div class="avatar">U</div>
      </div>
    </header>

    <!-- Hero 区 -->
    <section class="hero">
      <div class="demo-notice">
        <span class="demo-notice-tag">PS</span>
        演示 DEMO 只完成了策划和美术的 Agent 模块，可点击交互；后端接口均未实现，主要展示整体架构与交互逻辑。
      </div>
      <div class="hero-stats">
        <div class="stat">
          <div class="stat-num">4</div>
          <div class="stat-label">岗位 Agent</div>
        </div>
        <div class="divider"></div>
        <div class="stat">
          <div class="stat-num">5</div>
          <div class="stat-label">知识库</div>
        </div>
        <div class="divider"></div>
        <div class="stat">
          <div class="stat-num">∞</div>
          <div class="stat-label">产出沉淀</div>
        </div>
      </div>
    </section>

    <!-- Agent 模块卡片 -->
    <section class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">选择 Agent 模块</h2>
          <p class="section-desc">每个 Agent 对应真实业务环节，读取对应知识库并产出可用成果物</p>
        </div>
      </div>

      <div class="agent-grid">
        <div
          v-for="m in agentModules"
          :key="m.id"
          class="agent-card"
          :class="`accent-${m.color}`"
          @click="selectAgent(m.id)"
        >
          <div class="agent-card-head">
            <div class="agent-icon">{{ m.icon }}</div>
            <div class="agent-meta">
              <div class="agent-name">{{ m.name }}</div>
              <div class="agent-sub">{{ m.subtitle }}</div>
            </div>
            <div class="agent-arrow">→</div>
          </div>
          <div class="agent-desc">{{ m.desc }}</div>
          <div class="agent-section">
            <div class="agent-section-label">输入</div>
            <div class="agent-section-text">{{ m.inputs }}</div>
          </div>
          <div class="agent-section">
            <div class="agent-section-label">产出</div>
            <div class="tag-list">
              <span v-for="t in m.outputs" :key="t" class="tag">{{ t }}</span>
            </div>
          </div>
          <div class="agent-card-foot">
            <span class="enter-btn">进入工作台</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 知识库管理入口 -->
    <section class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">系统级模块</h2>
          <p class="section-desc">底层数据资产和跨模块协作支撑</p>
        </div>
      </div>

      <div class="kb-card" @click="openKnowledge">
        <div class="kb-icon">{{ knowledgeModule.icon }}</div>
        <div class="kb-info">
          <div class="kb-name">{{ knowledgeModule.name }}</div>
          <div class="kb-sub">{{ knowledgeModule.subtitle }}</div>
          <div class="kb-desc">{{ knowledgeModule.desc }}</div>
        </div>
        <div class="kb-stats">
          <div class="kb-stat">
            <div class="kb-stat-num">128</div>
            <div class="kb-stat-label">文档</div>
          </div>
          <div class="kb-stat">
            <div class="kb-stat-num">56</div>
            <div class="kb-stat-label">素材</div>
          </div>
          <div class="kb-stat">
            <div class="kb-stat-num">23</div>
            <div class="kb-stat-label">复盘</div>
          </div>
        </div>
        <div class="kb-arrow">→</div>
      </div>
    </section>

    <!-- 工作流图示 -->
    <section class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">典型协作流</h2>
          <p class="section-desc">上游产出经确认后流转到下游，最终沉淀到知识库</p>
        </div>
      </div>

      <div class="workflow">
        <div class="flow-node accent-blue">
          <div class="flow-icon">📋</div>
          <div class="flow-name">策划</div>
          <div class="flow-text">产出策划案</div>
        </div>
        <div class="flow-line"></div>
        <div class="flow-node accent-pink">
          <div class="flow-icon">🎨</div>
          <div class="flow-name">美术</div>
          <div class="flow-text">承接素材</div>
        </div>
        <div class="flow-line"></div>
        <div class="flow-node accent-green">
          <div class="flow-icon">⚙️</div>
          <div class="flow-name">研发</div>
          <div class="flow-text">实现 Demo</div>
        </div>
        <div class="flow-line"></div>
        <div class="flow-node accent-orange">
          <div class="flow-icon">📢</div>
          <div class="flow-name">运营</div>
          <div class="flow-text">活动包装</div>
        </div>
        <div class="flow-line"></div>
        <div class="flow-node accent-purple">
          <div class="flow-icon">✅</div>
          <div class="flow-name">审核</div>
          <div class="flow-text">一致性校验</div>
        </div>
        <div class="flow-line"></div>
        <div class="flow-node accent-cyan">
          <div class="flow-icon">📚</div>
          <div class="flow-name">沉淀</div>
          <div class="flow-text">知识库归档</div>
        </div>
      </div>
    </section>

    <footer class="footer">
      <span>© 2026 游戏全链路 AI Agent 产研系统 · Demo</span>
    </footer>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 顶部导航 */
.topbar {
  height: 64px;
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(8px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  color: #fff;
}

.brand-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.brand-sub {
  font-size: 12px;
  color: var(--text-tertiary);
  letter-spacing: 0.5px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ghost-btn {
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.ghost-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-pink), var(--accent-orange));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  color: #fff;
}

/* Hero */
.hero {
  padding: 48px 32px 40px;
  text-align: center;
  border-bottom: 1px solid var(--border-color);
  background:
    radial-gradient(ellipse at 30% 0%, rgba(88, 166, 255, 0.08), transparent 60%),
    radial-gradient(ellipse at 70% 0%, rgba(247, 120, 186, 0.06), transparent 60%);
}

.hero-tag {
  display: inline-block;
  padding: 4px 14px;
  font-size: 12px;
  color: var(--accent-blue);
  background: rgba(88, 166, 255, 0.1);
  border: 1px solid rgba(88, 166, 255, 0.2);
  border-radius: 999px;
  margin-bottom: 24px;
  letter-spacing: 0.5px;
}

.demo-notice {
  display: flex;
  align-items: center;
  gap: 10px;
  width: fit-content;
  max-width: 760px;
  margin: 0 auto 22px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  color: #ff6b6b;
  background: rgba(255, 80, 80, 0.08);
  border: 1px solid rgba(255, 80, 80, 0.45);
  border-radius: var(--radius-md);
  text-align: left;
  box-shadow: 0 0 0 1px rgba(255, 80, 80, 0.08), 0 4px 18px rgba(255, 80, 80, 0.12);
}

.demo-notice-tag {
  flex-shrink: 0;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #fff;
  background: #ff5f5f;
  border-radius: 999px;
}

.hero-stats {
  display: inline-flex;
  align-items: center;
  gap: 32px;
  padding: 16px 32px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.divider {
  width: 1px;
  height: 32px;
  background: var(--border-color);
}

/* Section */
.section {
  padding: 56px 32px;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
}

.section-head {
  margin-bottom: 28px;
}

.section-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.section-desc {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* Agent 卡片 */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.agent-card {
  position: relative;
  padding: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.25s ease;
  overflow: hidden;
}

.agent-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(135deg, transparent, transparent);
  opacity: 0;
  transition: opacity 0.25s;
  pointer-events: none;
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}

.agent-card:hover {
  transform: translateY(-3px);
  border-color: var(--border-hover);
  box-shadow: var(--shadow-lg);
}

.agent-card.accent-blue:hover { border-color: var(--accent-blue); }
.agent-card.accent-pink:hover { border-color: var(--accent-pink); }
.agent-card.accent-green:hover { border-color: var(--accent-green); }
.agent-card.accent-orange:hover { border-color: var(--accent-orange); }

.agent-card-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.agent-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  border: 1px solid var(--border-color);
}

.agent-meta {
  flex: 1;
}

.agent-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.agent-sub {
  font-size: 12px;
  color: var(--text-tertiary);
  letter-spacing: 0.3px;
}

.agent-arrow {
  font-size: 20px;
  color: var(--text-tertiary);
  transition: transform 0.2s;
}

.agent-card:hover .agent-arrow {
  transform: translateX(4px);
  color: var(--text-primary);
}

.agent-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
  min-height: 42px;
}

.agent-section {
  margin-top: 12px;
}

.agent-section-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.agent-section-text {
  font-size: 12px;
  color: var(--text-secondary);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.agent-card.accent-blue .tag { color: var(--accent-blue); border-color: rgba(88,166,255,0.25); }
.agent-card.accent-pink .tag { color: var(--accent-pink); border-color: rgba(247,120,186,0.25); }
.agent-card.accent-green .tag { color: var(--accent-green); border-color: rgba(63,185,80,0.25); }
.agent-card.accent-orange .tag { color: var(--accent-orange); border-color: rgba(240,136,62,0.25); }

.agent-card-foot {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px dashed var(--border-color);
}

.enter-btn {
  font-size: 12px;
  color: var(--text-tertiary);
}

.agent-card:hover .enter-btn {
  color: var(--text-primary);
}

/* Knowledge Base 卡片 */
.kb-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px;
  background: linear-gradient(135deg, var(--bg-card), var(--bg-tertiary));
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.25s;
}

.kb-card:hover {
  border-color: var(--accent-cyan);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.kb-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  background: rgba(57, 197, 207, 0.1);
  border: 1px solid rgba(57, 197, 207, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.kb-info {
  flex: 1;
}

.kb-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.kb-sub {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.kb-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 6px;
}

.kb-stats {
  display: flex;
  gap: 32px;
  padding: 0 24px;
  border-left: 1px solid var(--border-color);
  border-right: 1px solid var(--border-color);
}

.kb-stat {
  text-align: center;
}

.kb-stat-num {
  font-size: 22px;
  font-weight: 700;
  color: var(--accent-cyan);
}

.kb-stat-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.kb-arrow {
  font-size: 22px;
  color: var(--text-tertiary);
  transition: all 0.2s;
}

.kb-card:hover .kb-arrow {
  transform: translateX(4px);
  color: var(--accent-cyan);
}

/* Workflow */
.workflow {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 8px;
  padding: 28px 24px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow-x: auto;
}

.flow-node {
  flex: 1;
  min-width: 110px;
  padding: 16px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  text-align: center;
  transition: transform 0.2s;
}

.flow-node:hover {
  transform: translateY(-3px);
}

.flow-node.accent-blue { border-color: rgba(88,166,255,0.4); }
.flow-node.accent-pink { border-color: rgba(247,120,186,0.4); }
.flow-node.accent-green { border-color: rgba(63,185,80,0.4); }
.flow-node.accent-orange { border-color: rgba(240,136,62,0.4); }
.flow-node.accent-purple { border-color: rgba(188,140,255,0.4); }
.flow-node.accent-cyan { border-color: rgba(57,197,207,0.4); }

.flow-icon {
  font-size: 24px;
  margin-bottom: 6px;
}

.flow-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.flow-text {
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.flow-line {
  flex: 0 0 auto;
  align-self: center;
  width: 24px;
  height: 1px;
  background: var(--border-color);
  position: relative;
}

.flow-line::after {
  content: '';
  position: absolute;
  right: -3px;
  top: -3px;
  width: 7px;
  height: 7px;
  border-top: 1px solid var(--border-color);
  border-right: 1px solid var(--border-color);
  transform: rotate(45deg);
}

.footer {
  margin-top: auto;
  padding: 24px 32px;
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  border-top: 1px solid var(--border-color);
}
</style>
