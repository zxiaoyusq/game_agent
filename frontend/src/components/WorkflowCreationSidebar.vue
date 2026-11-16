<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import StudioIcon from './StudioIcon.vue'
defineProps({
  projects: { type: Array, default: () => [] },
  configured: Boolean,
})
const emit = defineEmits(['new', 'projects', 'navigate', 'open', 'settings'])
const expanded = ref(false)
const isMobile = ref(window.matchMedia('(max-width: 760px)').matches)
const sidebar = ref(null)
const menuToggle = ref(null)
const mobileQuery = window.matchMedia('(max-width: 760px)')
const originalOverflow = document.body.style.overflow

function closeMenu() {
  expanded.value = false
  menuToggle.value?.focus()
}
function go(action, value) {
  closeMenu()
  emit(action, value)
}
function updateLayout(event) {
  isMobile.value = event.matches
  expanded.value = false
}
function handleMenuKey(event) {
  if (!isMobile.value || !expanded.value) return
  if (event.key === 'Escape') {
    event.preventDefault()
    closeMenu()
    return
  }
  if (event.key !== 'Tab') return
  // 抽屉打开时焦点留在导航内，关闭后回到触发按钮。
  const buttons = [...sidebar.value.querySelectorAll('button:not(:disabled)')]
  const first = buttons[0],
    last = buttons.at(-1)
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last?.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first?.focus()
  }
}
watch(expanded, async (open) => {
  document.body.style.overflow =
    open && isMobile.value ? 'hidden' : originalOverflow
  if (open) {
    await nextTick()
    sidebar.value?.querySelector('button')?.focus()
  }
})
onMounted(() => mobileQuery.addEventListener('change', updateLayout))
onBeforeUnmount(() => {
  mobileQuery.removeEventListener('change', updateLayout)
  document.body.style.overflow = originalOverflow
})
</script>

<template>
  <div class="creation-mobile-bar">
    <button class="creation-wordmark" @click="go('navigate', 'home')">
      <StudioIcon name="spark" :size="25" />
      <b>
        AHA
        <span>创造</span>
      </b>
    </button>
    <button
      ref="menuToggle"
      class="mobile-menu-toggle"
      :aria-expanded="expanded"
      aria-controls="creation-sidebar"
      :aria-label="expanded ? '关闭导航' : '打开导航'"
      @click="expanded = !expanded"
    >
      <StudioIcon :name="expanded ? 'close' : 'menu'" />
    </button>
  </div>
  <button
    v-if="expanded"
    class="creation-sidebar-scrim"
    aria-label="关闭导航遮罩"
    tabindex="-1"
    @click="closeMenu"
  />
  <aside
    id="creation-sidebar"
    ref="sidebar"
    class="creation-sidebar"
    :class="{ expanded }"
    :inert="isMobile && !expanded"
    :role="isMobile ? 'dialog' : undefined"
    :aria-modal="isMobile && expanded ? true : undefined"
    aria-label="创作空间导航"
    @keydown="handleMenuKey"
  >
    <button
      class="creation-wordmark"
      aria-label="AHA 创造，返回首页"
      @click="go('navigate', 'home')"
    >
      <span class="brand-symbol"><StudioIcon name="spark" :size="29" /></span>
      <b>
        AHA
        <span>创造</span>
        <small>GAME CREATION STUDIO</small>
      </b>
    </button>
    <button
      class="sidebar-create active"
      aria-current="page"
      @click="go('new')"
    >
      <StudioIcon name="plus" />
      <span>新建项目</span>
      <kbd>＋</kbd>
    </button>
    <nav class="creation-nav">
      <button @click="go('projects')">
        <StudioIcon name="grid" />
        <span>我的项目</span>
        <small>{{ projects.length }}</small>
      </button>
      <button @click="go('navigate', 'produced-games')">
        <StudioIcon name="game" />
        <span>游戏作品库</span>
        <StudioIcon name="diagonal" :size="14" />
      </button>
      <button @click="go('navigate', 'knowledge')">
        <StudioIcon name="layers" />
        <span>知识库与 Skills</span>
      </button>
    </nav>
    <div class="sidebar-rule" />
    <section class="recent-projects">
      <div class="sidebar-caption">
        最近的创作
        <StudioIcon name="clock" :size="13" />
      </div>
      <button
        v-for="item in projects.slice(0, 5)"
        :key="item.id"
        :title="item.name"
        @click="go('open', item)"
      >
        <span
          class="project-indicator"
          :class="{
            completed: item.stages?.every(
              (stage) => stage.status === 'completed',
            ),
          }"
        />
        <span>{{ item.name }}</span>
      </button>
      <p v-if="!projects.length">你的第一个游戏，从这里开始。</p>
    </section>
    <div class="sidebar-bottom">
      <div class="sidebar-note">
        <span class="mini-spark">✦</span>
        <p>
          把好想法，
          <br />
          <strong>做成好玩的游戏。</strong>
        </p>
      </div>
      <button class="sidebar-connection" @click="go('settings')">
        <span class="connection-symbol">
          <StudioIcon name="settings" :size="18" />
        </span>
        <span>
          执行配置
          <small>
            <i :class="{ ready: configured }" />
            {{ configured ? '配置就绪' : '待检查配置' }}
          </small>
        </span>
        <StudioIcon name="chevron" :size="16" />
      </button>
      <button class="sidebar-home" @click="go('navigate', 'home')">
        <StudioIcon name="back" :size="15" />
        返回首页
      </button>
    </div>
  </aside>
</template>

<style scoped>
.creation-sidebar {
  width: 236px;
  padding: 32px 18px 18px;
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 30;
  display: flex;
  flex-direction: column;
  background: #18191d;
  border-right: 1px solid #ffffff09;
  color: #a5a6b0;
  font-size: 13px;
}
.creation-wordmark {
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  color: #43dfc9;
  padding: 0 10px;
  margin: 0 0 42px;
}
.creation-wordmark b {
  font-size: 25px;
  line-height: 1.1;
  letter-spacing: -0.8px;
  font-weight: 800;
}
.creation-wordmark b > span {
  font-size: 18px;
  font-weight: 600;
  color: #e4e5eb;
  margin-left: 8px;
  letter-spacing: 1px;
}
.creation-wordmark small {
  font-size: 8px;
  font-weight: 400;
  letter-spacing: 1.4px;
  white-space: nowrap;
  color: #858690;
  display: block;
  margin-top: 9px;
}
.brand-symbol {
  display: flex;
}
.sidebar-create {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 13px 15px;
  border: 1px solid #40d7c42a;
  border-radius: 10px;
  background: #2bd4bb12;
  color: #6ee4d2;
  font-weight: 550;
  font-size: 14px;
}
.sidebar-create kbd {
  margin-left: auto;
  font: 13px inherit;
  opacity: 0.55;
}
.creation-nav {
  display: grid;
  gap: 5px;
  margin: 17px 0 21px;
}
.creation-nav button {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 15px;
  border-radius: 9px;
  font-size: 13px;
  text-align: left;
}
.creation-nav button:hover,
.recent-projects button:hover {
  background: #ffffff06;
  color: #f2f3f5;
}
.creation-nav small {
  font-size: 11px;
  background: #ffffff08;
  padding: 1px 7px;
  border-radius: 5px;
}
.creation-nav span {
  flex: 1;
}
.creation-nav svg {
  color: #82848e;
}
.sidebar-rule {
  height: 1px;
  background: #ffffff09;
  margin: 0 10px;
}
.recent-projects {
  padding: 24px 7px;
  overflow: auto;
}
.sidebar-caption {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #797b87;
  padding: 0 9px;
  margin-bottom: 16px;
}
.recent-projects button {
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  width: 100%;
  padding: 10px 8px;
  border-radius: 7px;
  font-size: 12px;
}
.recent-projects button > span:last-child {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}
.project-indicator {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #727581;
  flex-shrink: 0;
}
.project-indicator.completed {
  background: #40baaa;
}
.recent-projects p {
  font-size: 11px;
  line-height: 1.8;
  padding: 0 9px;
}
.sidebar-bottom {
  margin-top: auto;
  padding-top: 22px;
}
.sidebar-note {
  display: flex;
  gap: 12px;
  padding: 18px 14px 24px;
  color: #7c808d;
}
.sidebar-note p {
  font-size: 12px;
  line-height: 1.8;
}
.sidebar-note strong {
  color: #acaebb;
  font-weight: 400;
}
.mini-spark {
  font-size: 20px;
  color: #5b6d6c;
}
.sidebar-connection {
  display: flex;
  align-items: center;
  gap: 11px;
  background: #1e2026;
  border: 1px solid #ffffff0c;
  border-radius: 11px;
  padding: 13px 12px;
  width: 100%;
  text-align: left;
  font-size: 12px;
}
.sidebar-connection > span:nth-child(2) {
  flex: 1;
  color: #c8cbd3;
}
.sidebar-connection small {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #838894;
  font-size: 10px;
  margin-top: 4px;
}
.sidebar-connection i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #d2a65b;
}
.sidebar-connection i.ready {
  background: #52c4a9;
}
.connection-symbol {
  display: flex;
  padding: 8px;
  background: #ffffff05;
  border-radius: 8px;
}
.sidebar-home {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 17px 0 0;
  color: #858893;
  font-size: 11px;
}
.creation-mobile-bar,
.creation-sidebar-scrim {
  display: none;
}
@media (max-width: 1050px) {
  .creation-sidebar {
    width: 208px;
    padding-inline: 12px;
  }
  .creation-wordmark {
    padding-inline: 8px;
  }
  .creation-wordmark small {
    font-size: 7px;
    letter-spacing: 1px;
  }
}
@media (max-width: 760px) {
  .creation-sidebar {
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    width: 250px;
    padding-top: 28px;
    z-index: 60;
  }
  .creation-sidebar.expanded {
    transform: translateX(0);
  }
  .creation-mobile-bar {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 66px;
    padding: 0 20px;
    background: #18191d;
    border-bottom: 1px solid #ffffff09;
  }
  .creation-mobile-bar .creation-wordmark {
    margin: 0;
    padding: 0;
  }
  .creation-mobile-bar .creation-wordmark b {
    font-size: 22px;
  }
  .creation-mobile-bar .creation-wordmark span {
    font-size: 16px;
  }
  .mobile-menu-toggle {
    color: #b4b9c1;
    padding: 9px;
    display: flex;
  }
  .creation-sidebar-scrim {
    display: block;
    position: fixed;
    inset: 0;
    background: #0009;
    backdrop-filter: blur(3px);
    z-index: 55;
  }
}
@media (prefers-reduced-motion: reduce) {
  .creation-sidebar {
    transition: none;
  }
}
</style>
