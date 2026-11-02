<script setup>
import { computed, ref, watch } from 'vue'
const props = defineProps({ url: { type: String, default: '' }, name: { type: String, default: '游戏预览' } })
const frameVersion = ref(0)
const loading = ref(true)
const failed = ref(false)
// 只接收 HTTP 地址；预览内容由后端校验实际构建后提供。
const previewUrl = computed(() => {
  if (!props.url) return ''
  try { const url = new URL(props.url, window.location.origin); return ['http:', 'https:'].includes(url.protocol) ? url.href : '' } catch { return '' }
})
watch(() => props.url, () => { loading.value = true; failed.value = false })
function reload() { loading.value = true; failed.value = false; frameVersion.value++ }
</script>
<template>
  <section class="prototype-game" aria-label="真实游戏预览">
    <header><div><small>真实游戏构建</small><h3>{{ name }}</h3></div><div v-if="previewUrl" class="preview-actions"><button @click="reload">重新加载</button><a :href="previewUrl" target="_blank" rel="noopener">独立窗口 ↗</a></div></header>
    <template v-if="previewUrl">
      <p v-if="loading" role="status">正在加载游戏构建…</p>
      <p v-if="failed" role="alert">游戏构建加载失败，请检查运行记录或在独立窗口查看。</p>
      <iframe :key="`${previewUrl}-${frameVersion}`" :src="previewUrl" :title="`${name} · 游戏预览`" allow="fullscreen; autoplay" allowfullscreen @load="loading = false" @error="failed = true; loading = false"></iframe>
    </template>
    <div v-else class="preview-empty"><strong>尚无可运行构建</strong><p>完成代码与集成阶段后，这里会加载后端提供的真实游戏。构建失败会保留在运行记录中。</p></div>
  </section>
</template>
<style scoped>
.prototype-game { background: #f5f8f2; border: 1px solid #d3dfca; border-radius: 10px; padding: 22px; margin-bottom: 20px; }
header,.preview-actions { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
small { color: #859578; font-size: 10px; letter-spacing: 2px; } h3 { font-size: 18px; margin: 6px 0; } a,button { color: #416bb0; font-size: 12px; }
iframe { width: 100%; height: 720px; max-height: 85vh; border: 0; border-radius: 8px; margin-top: 16px; background: #e8eee4; }
p { font-size: 12px; color: #78876c; line-height: 1.8; } .preview-empty { padding: 40px 12px; text-align: center; } .preview-empty strong { font-size: 15px; }
@media(max-width: 550px) { .prototype-game { padding: 16px; } iframe { height: 670px; } }
</style>
