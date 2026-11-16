<script setup>
import { computed, onMounted } from 'vue'
import { KB_MODULES, ensureKbLoaded, kbStore } from '../data/knowledgeBase.js'
import { loadProducedGames, producedGames } from '../data/producedGames.js'
import UserMenu from '../components/UserMenu.vue'
import { workflowSteps } from '../data/gameWorkflow.js'

const emit = defineEmits(['navigate'])

// 首页与知识库共用实际索引，来源同步后不再展示固定的示例统计。
const knowledgeCounts = computed(() => ({
  files: kbStore.items.length,
  skills: kbStore.items.filter((item) => item.moduleId === 'skill' && item.filename === 'SKILL.md').length,
  modules: Object.keys(kbStore.modulesMap).length,
}))
onMounted(ensureKbLoaded)
onMounted(loadProducedGames)

const knowledgeModule = {
  id: 'knowledge',
  name: '知识库管理',
  subtitle: 'Knowledge Base',
  desc: '统一管理项目知识、Skill 技能包、历史经验和各模块产出沉淀',
  icon: '📚',
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
        <UserMenu />
      </div>
    </header>

    <!-- Hero 区 -->
    <section class="hero">
      <div class="hero-pixel-dots"></div>
      <div class="hero-stats">
        <div class="stat">
          <div class="stat-num">{{ workflowSteps.length }}</div>
          <div class="stat-label">研发阶段</div>
        </div>
        <div class="divider"></div>
        <div class="stat">
          <div class="stat-num">{{ KB_MODULES.length }}</div>
          <div class="stat-label">知识库</div>
        </div>
        <div class="divider"></div>
        <button class="stat game-entry" aria-label="产出游戏，选择并运行游戏" @click="emit('navigate', 'produced-games')">
          <div class="stat-num">{{ producedGames.loaded ? producedGames.items.length : '—' }}</div>
          <div class="stat-label">产出游戏 <span aria-hidden="true">↗</span></div>
        </button>
      </div>
    </section>

    <!-- 项目统一从全流程工作台创建并执行。 -->
    <section class="section production-section">
      <button class="production-entry" @click="emit('navigate', 'workflow')">
        <div class="production-copy">
          <span class="production-label">GAME STUDIO / 全流程工作台</span>
          <h1>从一个想法，到一款游戏。</h1>
          <p>选择品类与技术方案，让 Agent 执行原型定义、美术、工程与真实测试。</p>
          <div class="production-stages"><span>原型定义</span><b>→</b><span>美术资源</span><b>→</b><span>代码与集成</span><b>→</b><span>测试验收</span></div>
          <span class="production-cta">进入游戏研发工作台 <span>↗</span></span>
        </div>
        <div class="production-visual" aria-hidden="true"><span class="visual-caption">YOUR NEXT GAME</span><div class="pixel-controller">✣ <i>● ●</i></div><span class="visual-caption">4 个阶段 · 真实执行与产物</span></div>
      </button>
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
            <div class="kb-stat-num">{{ kbStore.loaded ? knowledgeCounts.files : '—' }}</div>
            <div class="kb-stat-label">资料文件</div>
          </div>
          <div class="kb-stat">
            <div class="kb-stat-num">{{ kbStore.loaded ? knowledgeCounts.skills : '—' }}</div>
            <div class="kb-stat-label">Skill 入口</div>
          </div>
          <div class="kb-stat">
            <div class="kb-stat-num">{{ kbStore.loaded ? knowledgeCounts.modules : '—' }}</div>
            <div class="kb-stat-label">知识模块</div>
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
          <p class="section-desc">原型、资源、工程和测试按阶段衔接，运行记录与产物统一归档</p>
        </div>
      </div>

      <div class="workflow">
        <template v-for="(step, index) in workflowSteps" :key="step.id">
          <div v-if="index" class="flow-line"></div>
          <div class="flow-node" :class="`accent-${['blue', 'pink', 'green', 'purple'][index]}`">
            <div class="flow-icon">{{ ['📋', '🎨', '⚙️', '✅'][index] }}</div>
            <div class="flow-name">{{ step.name }}</div>
            <div class="flow-text">{{ step.outputs[0] }}</div>
          </div>
        </template>
      </div>
    </section>

    <footer class="footer">
      <span>© 2026 游戏全链路 AI Agent 产研系统</span>
    </footer>
  </div>
</template>

<style scoped>
.game-entry { background: transparent; border: 0; padding: 8px 12px; margin: -8px -12px; border-radius: var(--radius-sm); cursor: pointer; }
.game-entry:hover { background: var(--accent-blue-dim); }
.game-entry:focus-visible { outline: 3px solid var(--accent-blue); outline-offset: 4px; }
.game-entry .stat-label { color: var(--accent-blue); }
.production-section { padding-bottom: 0 !important; }
.production-entry { display: flex; align-items: center; justify-content: space-between; gap: 28px; width: 100%; padding: 36px; text-align: left; background: #e8edff; border: 2px solid #1a1816; border-radius: 12px; box-shadow: 5px 5px 0 #1a1816; }
.production-entry:hover { transform: translateY(-3px); background: #e0e7ff; }
.production-entry:focus-visible { outline: 3px solid var(--accent-blue); outline-offset: 6px; }
.production-label { color: #395aca; font-size: 11px; letter-spacing: 2px; font-weight: 800; }
.production-copy h1 { font-size: clamp(25px, 3vw, 36px); margin: 12px 0; font-weight: 900; }
.production-copy p { font-size: 14px; color: #565b70; }
.production-stages { display: flex; flex-wrap: wrap; gap: 10px; margin: 23px 0; font-size: 12px; }
.production-stages b { color: #7284ba; }
.production-cta { display: inline-flex; gap: 28px; background: #1a1816; color: white; padding: 11px 18px; border-radius: 5px; font-size: 14px; }
.production-visual { width: 240px; flex-shrink: 0; text-align: center; transform: rotate(-5deg); }
.visual-caption { font-size: 10px; letter-spacing: 2px; color: #586daa; }
.pixel-controller { margin: 18px auto; padding: 10px 18px; width: 180px; display: flex; align-items: center; justify-content: space-between; font-size: 54px; color: white; background: #5279ed; border: 3px solid #1a1816; border-radius: 22px 22px 40px 40px; box-shadow: 5px 7px 0 #233875; }
.pixel-controller i { font-size: 22px; color: #cbe58b; font-style: normal; }
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
.flow-node.accent-purple { border: 2px solid rgba(124,58,237,0.6); }

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

/* 窄屏将统计和阶段拆行，入口始终完整显示在视口内。 */
@media (max-width: 760px) {
  .topbar { height: auto; min-height: 76px; padding: 12px 16px; gap: 12px; }
  .brand { min-width: 0; flex: 1; gap: 8px; }
  .brand-logo { flex-shrink: 0; width: 32px; height: 36px; font-size: 20px; }
  .brand-name { font-size: 14px; }
  .brand-sub { font-size: 10px; }
  .topbar-right { flex-shrink: 0; }
  .hero { padding: 28px 20px; }
  .hero-stats { display: grid; grid-template-columns: minmax(0, 1fr) 1px minmax(0, 1fr) 1px minmax(0, 1fr); width: 100%; gap: 10px; padding: 16px 12px; }
  .stat { min-width: 0; }
  .game-entry { margin: 0; padding: 0; }
  .stat-num { font-size: 38px; }
  .stat-label { white-space: nowrap; letter-spacing: 0; }
  .section { padding: 32px 20px; }
  .section-title { font-size: 24px; }
  .production-entry { padding: 22px; }
  .production-visual { display: none; }
  .kb-card { display: grid; grid-template-columns: 48px minmax(0, 1fr) 20px; gap: 16px; padding: 20px; }
  .kb-icon { width: 48px; height: 48px; font-size: 28px; }
  .kb-name { font-size: 20px; }
  .kb-desc { font-size: 13px; }
  .kb-stats { grid-column: 1 / -1; grid-row: 2; justify-content: space-around; gap: 12px; padding: 16px 0 0; border: 0; border-top: 1px solid var(--border-color); }
  .kb-stat-num { font-size: 30px; }
  .kb-arrow { grid-column: 3; grid-row: 1; }
  .workflow { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 16px; }
  .flow-node { min-width: 0; padding: 18px 8px; }
  .flow-line { display: none; }
}
</style>
