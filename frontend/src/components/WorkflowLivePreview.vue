<script setup>
import { apiFetch } from '../api/http.js'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import StudioIcon from './StudioIcon.vue'

const props = defineProps({
  preview: Object,
  name: String,
  publication: Object,
})
const automatic = ref(true)
const device = ref('desktop')
const frameSrc = ref('')
const loadedRevision = ref('')
const loading = ref(false)
const error = ref('')
const surface = ref(null)
let controller,
  timeout,
  requestVersion = 0

const candidate = computed(() => {
  if (props.preview?.status !== 'ready' || !props.preview.url) return null
  const url = new URL(props.preview.url, window.location.origin)
  // 预览入口只接受本工作台的后端构建地址。
  if (
    url.origin !== window.location.origin ||
    !url.pathname.startsWith('/api/workflow/projects/')
  )
    return null
  return { url, revision: props.preview.revision || props.preview.url }
})
const hasUpdate = computed(
  () => candidate.value && candidate.value.revision !== loadedRevision.value,
)
const publishedUrl = computed(() => {
  try {
    const url = new URL(props.publication?.url)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : ''
  } catch {
    return ''
  }
})

async function loadPreview(force = false) {
  if (!candidate.value || (!force && !hasUpdate.value)) return
  const version = ++requestVersion,
    next = candidate.value
  controller?.abort()
  clearTimeout(timeout)
  controller = new AbortController()
  loading.value = true
  error.value = ''
  const url = new URL(next.url)
  url.searchParams.set('v', next.revision)
  if (force) url.searchParams.set('reload', String(Date.now()))
  try {
    // iframe 的 load 也可能是错误页，先核对入口确实能以 HTML 返回。
    const response = await apiFetch(url, {
      method: 'GET',
      cache: 'no-store',
      signal: controller.signal,
    })
    if (
      !response.ok ||
      !response.headers.get('content-type')?.includes('text/html')
    )
      throw new Error('游戏入口暂时不可用，等待构建完成后重试。')
    await response.body?.cancel()
    if (version !== requestVersion) return
    loadedRevision.value = next.revision
    frameSrc.value = url.href
    timeout = setTimeout(() => {
      loading.value = false
      error.value = '加载耗时较长，可重新加载或在独立窗口检查。'
    }, 20000)
  } catch (cause) {
    if (version !== requestVersion || cause.name === 'AbortError') return
    loading.value = false
    error.value = cause.message
  }
}
function loaded() {
  clearTimeout(timeout)
  loading.value = false
}
function failed() {
  loaded()
  error.value = '游戏加载失败，请重试或查看左侧执行记录。'
}
async function fullscreen() {
  try {
    await surface.value?.requestFullscreen()
  } catch {
    error.value = '当前浏览器不支持全屏，请使用独立窗口试玩。'
  }
}
// 只有真实构建版本变化才刷新；日志、设备尺寸或普通状态同步都不改变 iframe。
watch(
  () => [candidate.value?.revision, automatic.value],
  () => {
    if (automatic.value && hasUpdate.value) loadPreview()
  },
  { immediate: true },
)
onBeforeUnmount(() => {
  requestVersion++
  controller?.abort()
  clearTimeout(timeout)
})
</script>

<template>
  <section class="live-preview" aria-label="实时游戏预览">
    <header class="preview-toolbar">
      <div class="preview-title">
        <StudioIcon name="game" :size="17" />
        <strong>游戏预览</strong>
        <span v-if="frameSrc" class="preview-live-dot">开发版本</span>
      </div>
      <div class="preview-tools">
        <div class="device-switch" aria-label="预览尺寸">
          <button
            :class="{ selected: device === 'desktop' }"
            :aria-pressed="device === 'desktop'"
            aria-label="桌面预览"
            title="桌面预览"
            @click="device = 'desktop'"
          >
            <StudioIcon name="desktop" :size="17" />
          </button>
          <button
            :class="{ selected: device === 'phone' }"
            :aria-pressed="device === 'phone'"
            aria-label="手机预览"
            title="手机预览"
            @click="device = 'phone'"
          >
            <StudioIcon name="phone" :size="16" />
          </button>
        </div>
        <button
          :disabled="!candidate"
          aria-label="重新加载游戏"
          title="重新加载游戏"
          @click="loadPreview(true)"
        >
          <StudioIcon name="refresh" :size="17" />
        </button>
        <button
          :disabled="!frameSrc"
          aria-label="全屏试玩"
          title="全屏试玩"
          @click="fullscreen"
        >
          <StudioIcon name="expand" :size="17" />
        </button>
        <a
          v-if="frameSrc"
          :href="frameSrc"
          target="_blank"
          rel="noopener"
          aria-label="独立窗口试玩"
          title="独立窗口试玩"
        >
          <StudioIcon name="diagonal" :size="17" />
        </a>
      </div>
    </header>
    <div v-if="hasUpdate && !automatic" class="preview-update">
      <span>新的游戏版本已准备好</span>
      <button @click="loadPreview()">
        加载新版本
        <StudioIcon name="refresh" :size="13" />
      </button>
    </div>
    <p v-if="error" class="preview-error" role="alert">
      {{ error }}
      <button :disabled="!candidate" @click="loadPreview(true)">重试</button>
    </p>
    <div
      ref="surface"
      class="preview-surface"
      :class="{ 'phone-mode': device === 'phone', 'has-game': !!frameSrc }"
    >
      <div v-if="loading" class="preview-loading" role="status">
        <span />
        正在加载新构建…
      </div>
      <iframe
        v-if="frameSrc"
        :src="frameSrc"
        :title="`${name} · 实时游戏预览`"
        sandbox="allow-scripts allow-same-origin allow-pointer-lock"
        allow="fullscreen; autoplay; gamepad"
        allowfullscreen
        @load="loaded"
        @error="failed"
      />
      <div v-else class="live-preview-empty">
        <div class="preview-placeholder">
          <div class="placeholder-bar">
            <i />
            <i />
            <i />
          </div>
          <div class="placeholder-game">
            <StudioIcon name="game" :size="64" />
            <span>YOUR NEXT GAME</span>
          </div>
          <span class="placeholder-spark">
            <StudioIcon name="spark" :size="25" />
          </span>
        </div>
        <span class="preview-eyebrow">从想法，到可以玩的世界</span>
        <h2>你的游戏，正在这里诞生。</h2>
        <p>
          {{
            preview?.reason || 'Agent 生成可加载的游戏构建后，这里会自动打开。'
          }}
          <br />
          你可以先在左侧跟随制作进展。
        </p>
        <span class="preview-waiting">
          <i />
          等待首个游戏构建
        </span>
      </div>
    </div>
    <footer class="preview-footer">
      <label>
        <input v-model="automatic" type="checkbox" />
        自动加载新版本
      </label>
      <span class="preview-footnote">
        {{ frameSrc ? '开发预览 · 验收结果见制作记录' : '构建就绪后自动显示' }}
      </span>
      <a
        v-if="publishedUrl"
        :href="publishedUrl"
        target="_blank"
        rel="noopener"
      >
        已发布试玩
        <StudioIcon name="diagonal" :size="13" />
      </a>
    </footer>
  </section>
</template>

<style scoped>
.live-preview {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #10161b;
}
.preview-toolbar {
  flex-shrink: 0;
  height: 61px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 22px;
  background: #171c21;
  border-bottom: 1px solid #ffffff0c;
}
.preview-title,
.preview-tools,
.device-switch {
  display: flex;
  align-items: center;
  gap: 10px;
}
.preview-title {
  font-size: 12px;
  color: #8f9b9f;
}
.preview-title strong {
  color: #c9d4d7;
  font-weight: 500;
}
.preview-live-dot {
  color: #77bda9;
  font-size: 10px;
  margin-left: 5px;
}
.preview-tools {
  gap: 5px;
}
.preview-tools button,
.preview-tools a {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #98a5ad;
  border-radius: 6px;
  padding: 8px;
}
.preview-tools :is(button, a):hover {
  color: #bdeadd;
  background: #ffffff06;
}
.device-switch {
  gap: 2px;
  border: 1px solid #ffffff0a;
  border-radius: 7px;
  padding: 2px;
  margin-right: 8px;
}
.device-switch button {
  padding: 5px 8px;
}
.device-switch button.selected {
  color: #a0d9cb;
  background: #ffffff0a;
}
.preview-surface {
  min-height: 0;
  flex: 1;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  background:
    radial-gradient(ellipse at 55% 45%, #24373155, transparent 70%), #0e1519;
  overflow: hidden;
}
.preview-surface:fullscreen {
  height: 100vh;
  background: #10161b;
}
.preview-surface iframe {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
  background: #10161b;
}
.preview-surface.phone-mode {
  padding: 20px;
  background: #0c1116;
}
.preview-surface.phone-mode iframe {
  width: 390px;
  max-width: 100%;
  border-radius: 22px;
  border: 6px solid #28333a;
  box-shadow: 0 20px 70px #0007;
}
.preview-loading {
  position: absolute;
  z-index: 2;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 14px;
  border: 1px solid #70bfa333;
  border-radius: 20px;
  background: #182b26ed;
  color: #b0dacb;
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 11px;
  white-space: nowrap;
}
.preview-loading span {
  width: 10px;
  height: 10px;
  border: 1px solid #789c8b;
  border-top-color: transparent;
  border-radius: 50%;
  animation: preview-spin 1s linear infinite;
}
.live-preview-empty {
  text-align: center;
  padding: 25px;
}
.preview-placeholder {
  position: relative;
  width: 214px;
  height: 156px;
  border: 1px solid #6184773a;
  border-radius: 12px;
  background: linear-gradient(140deg, #22332b66, #19232933);
  margin: 0 auto 39px;
  transform: rotate(-6deg);
  box-shadow:
    14px 16px 0 -1px #111e1b,
    14px 16px 0 0 #8bb5a212;
}
.placeholder-bar {
  display: flex;
  gap: 5px;
  padding: 11px;
  border-bottom: 1px solid #66857225;
}
.placeholder-bar i {
  width: 4px;
  height: 4px;
  background: #6f9c8b66;
  border-radius: 50%;
}
.placeholder-game {
  height: 116px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #6b9b8c;
  gap: 9px;
}
.placeholder-game span {
  font-size: 7px;
  letter-spacing: 3px;
  color: #78998c;
}
.placeholder-spark {
  position: absolute;
  right: -14px;
  top: -12px;
  color: #7bb9a3;
}
.preview-eyebrow {
  font-size: 10px;
  letter-spacing: 2px;
  color: #6f9e8c;
}
.live-preview-empty h2 {
  color: #dbe6e3;
  font-size: clamp(20px, 2vw, 27px);
  font-weight: 500;
  margin-top: 13px;
  letter-spacing: -0.5px;
}
.live-preview-empty p {
  font-size: 12px;
  color: #80938e;
  line-height: 2;
  margin: 17px 0 23px;
}
.preview-waiting {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #ffffff0a;
  padding: 6px 12px;
  color: #92b3a6;
  font-size: 10px;
  border-radius: 6px;
}
.preview-waiting i {
  width: 5px;
  height: 5px;
  background: #78b39c;
  border-radius: 50%;
}
.preview-footer {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 13px 20px;
  border-top: 1px solid #ffffff08;
  color: #79908a;
  font-size: 10px;
  background: #131a1e;
}
.preview-footer label,
.preview-footer a {
  display: flex;
  gap: 6px;
  align-items: center;
}
.preview-footer input {
  accent-color: #66ceb1;
}
.preview-footer a {
  color: #87d0b9;
}
.preview-update {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 20px;
  background: #1c332c;
  color: #9bd1bd;
  font-size: 12px;
}
.preview-update button {
  display: flex;
  gap: 7px;
  align-items: center;
  color: #c9ebdb;
}
.preview-error {
  color: #e3b2a2;
  background: #3b2927;
  padding: 12px 20px;
  font-size: 12px;
}
.preview-error button {
  color: #f2caba;
  text-decoration: underline;
  margin-left: 12px;
}
@keyframes preview-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (max-width: 1100px) {
  .preview-toolbar {
    padding-inline: 14px;
  }
  .preview-live-dot {
    display: none;
  }
  .preview-footnote {
    display: none;
  }
}
@media (max-width: 700px) {
  .preview-toolbar {
    height: 51px;
  }
  .preview-surface.phone-mode {
    padding: 8px;
  }
  .preview-surface.phone-mode iframe {
    border-radius: 12px;
    border-width: 3px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .preview-loading span {
    animation: none;
  }
}
</style>
