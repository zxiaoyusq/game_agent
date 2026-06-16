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
      <div class="hero-pixel-dots"></div>
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
          <h2 class="section-title"><span class="title-mark">◆</span> 选择 Agent 模块</h2>
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
          <h2 class="section-title"><span class="title-mark">◆</span> 系统级模块</h2>
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
          <h2 class="section-title"><span class="title-mark">◆</span> 典型协作流</h2>
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
  height: 76px;
  padding: 0 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1.5px solid var(--border-color);
  background: var(--bg-secondary);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(8px);
}

.topbar::after {
  content: '';
  position: absolute;
  bottom: -3px;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-blue) 20%, var(--accent-pink) 50%, var(--accent-green) 80%, transparent);
  opacity: 0.4;
  pointer-events: none;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 44px;
  height: 44px;
  background: var(--accent-blue);
  border: 1.5px solid rgba(77, 158, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 22px;
  color: #fff;
  clip-path: polygon(4px 0, calc(100% - 4px) 0, 100% 4px, 100% calc(100% - 4px), calc(100% - 4px) 100%, 4px 100%, 0 calc(100% - 4px), 0 4px);
  position: relative;
}

.brand-logo::after {
  content: '';
  position: absolute;
  inset: -4px;
  border: 1px dashed rgba(26, 111, 255, 0.3);
  clip-path: polygon(4px 0, calc(100% - 4px) 0, 100% 4px, 100% calc(100% - 4px), calc(100% - 4px) 100%, 4px 100%, 0 calc(100% - 4px), 0 4px);
  pointer-events: none;
}

.brand-name {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
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
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.ghost-btn:hover {
  background: var(--bg-hover);
  color: var(--accent-blue);
  border-color: var(--accent-blue);
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
  border-bottom: 1.5px solid var(--border-color);
  background:
    radial-gradient(ellipse at 30% 0%, rgba(26, 111, 255, 0.06), transparent 60%),
    radial-gradient(ellipse at 70% 0%, rgba(219, 39, 119, 0.05), transparent 60%),
    var(--bg-primary);
  position: relative;
  overflow: hidden;
}

/* 像素点阵装饰 */
.hero-pixel-dots {
  position: absolute;
  top: 16px;
  right: 32px;
  width: 80px;
  height: 80px;
  background-image: radial-gradient(circle, var(--border-hover) 1.5px, transparent 1.5px);
  background-size: 10px 10px;
  opacity: 0.5;
  pointer-events: none;
}

.hero-pixel-dots::after {
  content: '';
  position: absolute;
  bottom: -40px;
  left: -120px;
  width: 60px;
  height: 60px;
  background-image: radial-gradient(circle, var(--border-hover) 1.5px, transparent 1.5px);
  background-size: 10px 10px;
  opacity: 0.6;
}

.hero-tag {
  display: inline-block;
  padding: 4px 14px;
  font-size: 12px;
  color: var(--accent-blue);
  background: var(--accent-blue-dim);
  border: 1.5px solid rgba(26, 111, 255, 0.3);
  border-radius: 999px;
  margin-bottom: 24px;
  letter-spacing: 0.5px;
  font-weight: 600;
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
  color: var(--accent-red);
  background: rgba(220, 38, 38, 0.06);
  border: 2px solid rgba(220, 38, 38, 0.5);
  border-radius: var(--radius-md);
  text-align: left;
  box-shadow: 3px 3px 0 rgba(180, 20, 20, 0.25);
}

.demo-notice-tag {
  flex-shrink: 0;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #fff;
  background: var(--accent-red);
  border-radius: 3px;
}

.hero-stats {
  display: inline-flex;
  align-items: center;
  gap: 32px;
  padding: 16px 32px;
  background: var(--bg-card);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: 4px 4px 0 var(--shadow-dark);
}

.stat-num {
  font-size: 52px;
  font-weight: 900;
  color: var(--accent-blue);
  line-height: 1;
  letter-spacing: -0.04em;
}

.stat-label {
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-tertiary);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 600;
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
  font-size: 30px;
  font-weight: 900;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.025em;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-mark {
  font-size: 16px;
  color: var(--accent-blue);
  font-weight: 900;
  opacity: 0.8;
  flex-shrink: 0;
}

.section-desc {
  font-size: 15px;
  color: var(--text-tertiary);
}

/* Agent 卡片 */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.agent-card {
  position: relative;
  padding: 28px;
  background: var(--bg-card);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
}

/* 像素角标：右下角切角装饰 */
.agent-card::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 16px;
  height: 16px;
  border-top: 2px solid var(--border-color);
  border-left: 2px solid var(--border-color);
  border-radius: 0 0 0 2px;
  pointer-events: none;
  transition: border-color 0.2s;
}

/* 顶部 accent 色条 — 常驻不需 hover */
.agent-card.accent-blue  { border-top: 4px solid var(--accent-blue); }
.agent-card.accent-pink  { border-top: 4px solid var(--accent-pink); }
.agent-card.accent-green { border-top: 4px solid var(--accent-green); }
.agent-card.accent-orange { border-top: 4px solid var(--accent-orange); }

.agent-card:hover {
  transform: translate(-2px, -3px);
}

.agent-card.accent-blue:hover  { border-color: var(--accent-blue);  box-shadow: 5px 5px 0 var(--shadow-blue); }
.agent-card.accent-pink:hover  { border-color: var(--accent-pink);  box-shadow: 5px 5px 0 var(--shadow-pink); }
.agent-card.accent-green:hover { border-color: var(--accent-green); box-shadow: 5px 5px 0 var(--shadow-green); }
.agent-card.accent-orange:hover { border-color: var(--accent-orange); box-shadow: 5px 5px 0 var(--shadow-orange); }

.agent-card.accent-blue:hover::after  { border-color: var(--accent-blue); }
.agent-card.accent-pink:hover::after  { border-color: var(--accent-pink); }
.agent-card.accent-green:hover::after { border-color: var(--accent-green); }
.agent-card.accent-orange:hover::after { border-color: var(--accent-orange); }

.agent-card-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

/* icon 根据 accent 有色背景 */
.agent-icon {
  width: 58px;
  height: 58px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.agent-card.accent-blue  .agent-icon { background: var(--accent-blue-dim);   border: 2px solid rgba(26,111,255,0.35); }
.agent-card.accent-pink  .agent-icon { background: var(--accent-pink-dim);   border: 2px solid rgba(219,39,119,0.35); }
.agent-card.accent-green .agent-icon { background: var(--accent-green-dim);  border: 2px solid rgba(22,163,74,0.35); }
.agent-card.accent-orange .agent-icon { background: var(--accent-orange-dim); border: 2px solid rgba(234,88,12,0.35); }

.agent-meta {
  flex: 1;
}

.agent-name {
  font-size: 22px;
  font-weight: 900;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

.agent-sub {
  font-size: 12px;
  color: var(--text-tertiary);
  letter-spacing: 0.3px;
  margin-top: 2px;
}

.agent-arrow {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-tertiary);
  transition: transform 0.2s;
}

.agent-card:hover .agent-arrow {
  transform: translateX(4px);
  color: var(--text-primary);
}

.agent-desc {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.65;
  margin-bottom: 16px;
  min-height: 48px;
}

.agent-section {
  margin-top: 14px;
}

.agent-section-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  font-weight: 700;
}

.agent-section-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 13px;
  padding: 3px 12px;
  border-radius: 3px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  letter-spacing: 0.03em;
}

.agent-card.accent-blue   .tag { color: var(--accent-blue);   border-color: rgba(26,111,255,0.4); background: var(--accent-blue-dim); }
.agent-card.accent-pink   .tag { color: var(--accent-pink);   border-color: rgba(219,39,119,0.4); background: var(--accent-pink-dim); }
.agent-card.accent-green  .tag { color: var(--accent-green);  border-color: rgba(22,163,74,0.4); background: var(--accent-green-dim); }
.agent-card.accent-orange .tag { color: var(--accent-orange); border-color: rgba(234,88,12,0.4); background: var(--accent-orange-dim); }

.agent-card-foot {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--border-color);
}

.enter-btn {
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
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
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s;
}

.kb-card:hover {
  border-color: var(--accent-cyan);
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 var(--shadow-cyan);
}

.kb-icon {
  width: 68px;
  height: 68px;
  border-radius: var(--radius-md);
  background: rgba(8, 145, 178, 0.1);
  border: 1.5px solid rgba(8, 145, 178, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34px;
  flex-shrink: 0;
}

.kb-info {
  flex: 1;
}

.kb-name {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.kb-sub {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.kb-desc {
  font-size: 15px;
  color: var(--text-secondary);
  margin-top: 6px;
}

.kb-stats {
  display: flex;
  gap: 32px;
  padding: 0 24px;
  border-left: 1.5px solid var(--border-color);
  border-right: 1.5px solid var(--border-color);
}

.kb-stat {
  text-align: center;
}

.kb-stat-num {
  font-size: 36px;
  font-weight: 900;
  color: var(--accent-cyan);
  letter-spacing: -0.03em;
}

.kb-stat-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
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
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow-x: auto;
}

.flow-node {
  flex: 1;
  min-width: 120px;
  padding: 20px 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  text-align: center;
  transition: transform 0.2s;
}

.flow-node:hover {
  transform: translateY(-3px);
}

.flow-node.accent-blue   { border: 2px solid rgba(26,111,255,0.6); }
.flow-node.accent-pink   { border: 2px solid rgba(219,39,119,0.6); }
.flow-node.accent-green  { border: 2px solid rgba(22,163,74,0.6); }
.flow-node.accent-orange { border: 2px solid rgba(234,88,12,0.6); }
.flow-node.accent-purple { border: 2px solid rgba(124,58,237,0.6); }
.flow-node.accent-cyan   { border: 2px solid rgba(8,145,178,0.6); }

.flow-icon {
  font-size: 30px;
  margin-bottom: 10px;
  line-height: 1;
}

.flow-name {
  font-size: 16px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.flow-text {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.flow-line {
  flex: 0 0 auto;
  align-self: center;
  width: 24px;
  height: 2px;
  background: var(--border-hover);
  position: relative;
}

.flow-line::after {
  content: '';
  position: absolute;
  right: -3px;
  top: -3px;
  width: 7px;
  height: 7px;
  border-top: 2px solid var(--border-hover);
  border-right: 2px solid var(--border-hover);
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
