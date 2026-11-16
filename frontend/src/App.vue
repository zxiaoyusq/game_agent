<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import LoginView from './views/LoginView.vue'
import { auth, expireSession, restoreSession } from './data/auth.js'
import HomeView from './views/HomeView.vue'
import KnowledgeBaseView from './views/KnowledgeBaseView.vue'
import GameWorkflowView from './views/GameWorkflowView.vue'
import ProducedGamesView from './views/ProducedGamesView.vue'

const currentView = ref('home')

function navigate(view) {
  currentView.value = view
}

function syncLogout(event) {
  if (event.key === 'game-agent-logout') expireSession()
}
onMounted(() => {
  window.addEventListener('auth-expired', expireSession)
  window.addEventListener('storage', syncLogout)
  restoreSession()
})
onBeforeUnmount(() => {
  window.removeEventListener('auth-expired', expireSession)
  window.removeEventListener('storage', syncLogout)
})
</script>

<template>
  <div class="app-container">
    <LoginView v-if="!auth.ready || !auth.user" />
    <HomeView v-else-if="currentView === 'home'" @navigate="navigate" />
    <GameWorkflowView v-else-if="currentView === 'workflow'" @navigate="navigate" />
    <ProducedGamesView v-else-if="currentView === 'produced-games'" @navigate="navigate" />
    <KnowledgeBaseView
      v-else-if="currentView === 'knowledge'"
      @navigate="navigate"
    />
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
}
</style>
