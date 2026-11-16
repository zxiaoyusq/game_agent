<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import StudioIcon from './StudioIcon.vue'

defineProps({ projectName: String })
const dialog = ref(null)
const activeStep = ref(0)
const steps = ['准备游戏版本', '整理发布内容', '模拟上线']
const completed = computed(() => activeStep.value === steps.length)
let timer

function startDemo() {
  clearInterval(timer)
  activeStep.value = 0
  dialog.value.showModal()
  // 仅推进本地展示状态，不调用发布接口、不改写项目的真实发布信息。
  timer = setInterval(() => {
    activeStep.value++
    if (completed.value) clearInterval(timer)
  }, 700)
}

function closeDemo() {
  clearInterval(timer)
  dialog.value.close()
}
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <button class="publish-demo-trigger" aria-label="一键发布（前端演示）" @click="startDemo">
    <StudioIcon name="upload" :size="15" />
    <span>一键发布</span>
    <small>演示</small>
  </button>
  <dialog
    ref="dialog"
    class="publish-demo-dialog"
    aria-labelledby="publish-demo-title"
    aria-describedby="publish-demo-description"
    @cancel.prevent="closeDemo"
    @click="($event.target === dialog) && closeDemo()"
  >
    <header>
      <span><StudioIcon name="upload" :size="16" />发布工作台</span>
      <button autofocus aria-label="关闭发布演示" @click="closeDemo"><StudioIcon name="close" :size="18" /></button>
    </header>
    <div class="publish-demo-content">
      <div class="publish-demo-symbol" :class="{ completed }"><StudioIcon :name="completed ? 'check' : 'upload'" :size="28" /></div>
      <div role="status" aria-live="polite">
        <h2 id="publish-demo-title">{{ completed ? '发布演示已完成' : '正在演示发布流程' }}</h2>
        <p id="publish-demo-description">{{ completed ? '游戏尚未实际上线，也未生成公开链接。' : '本次仅模拟发布步骤，不会上传或上线游戏。' }}</p>
      </div>
      <div class="publish-demo-project"><span>当前项目</span><strong>{{ projectName }}</strong><small>前端演示</small></div>
      <ol class="publish-demo-steps" aria-label="模拟发布进度">
        <li v-for="(step, index) in steps" :key="step" :class="{ done: index < activeStep, active: index === activeStep }" :aria-current="index === activeStep ? 'step' : undefined">
          <span class="publish-step-marker"><StudioIcon v-if="index < activeStep" name="check" :size="13" /><template v-else>{{ index + 1 }}</template></span>
          <span>{{ step }}</span>
          <small>{{ index < activeStep ? '演示完成' : index === activeStep ? '模拟中…' : '待演示' }}</small>
        </li>
      </ol>
      <p class="publish-demo-note">真实发布能力接入后，可在这里一键上线和分享游戏。</p>
    </div>
    <footer><span>演示模式 · 未上线</span><button @click="closeDemo">{{ completed ? '完成' : '取消演示' }}</button></footer>
  </dialog>
</template>

<style scoped>
.publish-demo-trigger { display: flex; flex-shrink: 0; align-items: center; gap: 7px; border: 1px solid #8bdfc32b; border-radius: 7px; padding: 8px 12px; background: #70ceb4; color: #143b2f; font-size: 12px; font-weight: 600; white-space: nowrap; }
.publish-demo-trigger:hover { background: #8bddc6; }
.publish-demo-trigger small { border-left: 1px solid #244d3f36; padding-left: 7px; font-size: 9px; font-weight: 400; }
.publish-demo-dialog { margin: auto; padding: 0; width: min(460px, calc(100vw - 32px)); max-height: calc(100dvh - 32px); overflow-y: auto; color: #c9ded4; color-scheme: dark; background: #18211f; border: 1px solid #6e9c873b; border-radius: 16px; box-shadow: 0 24px 100px #0008; }
.publish-demo-dialog::backdrop { background: #060c0bbe; backdrop-filter: blur(5px); }
.publish-demo-dialog header, .publish-demo-dialog header > span, .publish-demo-dialog footer { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.publish-demo-dialog header { padding: 16px 20px; border-bottom: 1px solid #ffffff0a; font-size: 12px; color: #8bb9a4; }
.publish-demo-dialog header button { display: flex; padding: 5px; border-radius: 5px; color: #9db7ab; }
.publish-demo-content { padding: 26px 26px 22px; }
.publish-demo-symbol { display: grid; place-items: center; width: 56px; height: 56px; margin-bottom: 20px; border-radius: 15px; color: #89d5b8; background: #6ecba915; border: 1px solid #70ceb427; }
.publish-demo-symbol.completed { background: #70ceb4; color: #163b2e; }
.publish-demo-content h2 { font-size: 22px; font-weight: 600; color: #e1f0e9; margin: 0 0 9px; }
.publish-demo-content p { font-size: 12px; color: #8fa99d; line-height: 1.8; margin: 0; }
.publish-demo-project { display: flex; align-items: center; gap: 10px; padding: 14px 0; margin-top: 16px; font-size: 11px; border-bottom: 1px solid #ffffff0a; }
.publish-demo-project > span { color: #799786; flex-shrink: 0; }
.publish-demo-project strong { overflow-wrap: anywhere; font-size: 12px; font-weight: 500; }
.publish-demo-project small { margin-left: auto; white-space: nowrap; color: #9cbdaf; font-size: 10px; }
.publish-demo-steps { list-style: none; padding: 10px 0; margin: 0; }
.publish-demo-steps li { display: flex; align-items: center; gap: 12px; padding: 11px 0; font-size: 12px; color: #7d988a; }
.publish-step-marker { display: grid; place-items: center; height: 24px; width: 24px; border-radius: 50%; border: 1px solid #79928336; font-size: 10px; }
.publish-demo-steps small { margin-left: auto; font-size: 10px; }
.publish-demo-steps .active, .publish-demo-steps .done { color: #b0d8c4; }
.publish-demo-steps .active .publish-step-marker { border-color: #80cead; background: #80cead12; }
.publish-demo-steps .done .publish-step-marker { background: #70ceb424; color: #8cdbb6; border-color: transparent; }
.publish-demo-content .publish-demo-note { font-size: 11px; }
.publish-demo-dialog footer { padding: 16px 26px; border-top: 1px solid #ffffff0a; background: #ffffff02; }
.publish-demo-dialog footer > span { font-size: 11px; color: #85a391; }
.publish-demo-dialog footer button { padding: 9px 20px; border-radius: 7px; background: #70ceb4; color: #173e30; font-size: 12px; }
@media (max-width: 700px) {
  .publish-demo-trigger { padding: 7px 9px; font-size: 11px; gap: 5px; }
  .publish-demo-trigger small { display: none; }
}
</style>
