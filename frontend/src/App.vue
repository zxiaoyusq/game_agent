<script setup>
import { ref } from 'vue'
import HomeView from './views/HomeView.vue'
import AgentView from './views/AgentView.vue'
import ArtAgentView from './views/ArtAgentView.vue'
import DevAgentView from './views/DevAgentView.vue'
import KnowledgeBaseView from './views/KnowledgeBaseView.vue'

const currentView = ref('home')
const currentModule = ref(null)

function navigate(view, module = null) {
  currentView.value = view
  currentModule.value = module
}
</script>

<template>
  <div class="app-container">
    <HomeView v-if="currentView === 'home'" @navigate="navigate" />
    <ArtAgentView
      v-else-if="currentView === 'agent' && currentModule === 'art'"
      @navigate="navigate"
    />
    <DevAgentView
      v-else-if="currentView === 'agent' && currentModule === 'dev'"
      @navigate="navigate"
    />
    <AgentView
      v-else-if="currentView === 'agent'"
      :module-id="currentModule"
      @navigate="navigate"
    />
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
