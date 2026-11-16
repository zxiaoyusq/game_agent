<script setup>
import { ref } from 'vue'
import { validateWorkflowTemplate } from '../api/workflow.js'
import StudioIcon from './StudioIcon.vue'

const props = defineProps({
  templates: { type: Array, default: () => [] },
  current: Object,
})
const emit = defineEmits(['apply'])
const error = ref('')
const busy = ref(false)
const failedImages = ref([])
const covers = {
  'ludo-classic': '/studio/ludo-board.png',
  'web-game': '/api/produced-games/ball-sort-fusion/cover',
}

async function apply(value, { imported = false } = {}) {
  busy.value = true
  error.value = ''
  try {
    emit('apply', await validateWorkflowTemplate(value), { imported })
  } catch (cause) {
    error.value = `模板校验失败：${cause.message}`
  } finally {
    busy.value = false
  }
}
async function importFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  try {
    if (file.size > 256 * 1024) throw new Error('模板文件不能超过 256KB')
    await apply(JSON.parse(await file.text()), { imported: true })
  } catch (cause) {
    error.value = `导入失败：${cause.message}`
  } finally {
    event.target.value = ''
  }
}
function exportFile() {
  // 导出的只有可复用输入；不带工作区、执行状态、密钥或固定发布地址。
  const value = JSON.parse(JSON.stringify(props.current))
  value.production_plan.publish_slug = ''
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }),
  )
  const link = document.createElement('a')
  link.href = url
  link.download = '游戏全流程模板.json'
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>

<template>
  <section class="template-picker" aria-label="导入生产模板">
    <div class="template-heading">
      <div>
        <h2>或者，从一份制作模板开始</h2>
        <p>玩法、美术与 Skills 已准备好，给创意一个起点。</p>
      </div>
      <button
        type="button"
        class="template-export"
        :disabled="!current || busy"
        @click="exportFile"
      >
        <StudioIcon name="download" :size="15" />
        导出当前配置
      </button>
    </div>
    <div class="template-cards">
      <button
        v-for="item in [...templates].reverse()"
        :key="item.id"
        type="button"
        class="template-card"
        :class="{ chosen: current?.production_plan?.template_id === item.id }"
        :disabled="busy"
        :aria-label="`使用 ${item.name} 模板`"
        @click="apply(item)"
      >
        <div class="template-art" :class="item.id">
          <img
            v-if="covers[item.id] && !failedImages.includes(item.id)"
            :src="covers[item.id]"
            alt=""
            @error="failedImages.push(item.id)"
          />
          <StudioIcon v-else name="game" :size="54" />
          <span class="template-badge">
            {{ item.id === 'ludo-classic' ? '经典焕新' : '自由创作' }}
          </span>
          <span
            v-if="current?.production_plan?.template_id === item.id"
            class="template-selected"
          >
            <StudioIcon name="check" :size="13" />
            当前模板
          </span>
        </div>
        <div class="template-copy">
          <div>
            <h3>
              {{ item.id === 'ludo-classic' ? 'LUDO · 经典新生' : item.name }}
            </h3>
            <StudioIcon name="diagonal" :size="17" />
          </div>
          <p>
            {{
              item.id === 'ludo-classic'
                ? '原版贴图的质感，真实摇骰与走子动画。'
                : item.description
            }}
          </p>
          <span>
            {{ item.id === 'ludo-classic' ? '棋盘策略' : '轻量 H5' }}
            <i />
            {{
              item.id === 'ludo-classic'
                ? '原版美术 · 完整动画'
                : '自定义玩法 · 全流程制作'
            }}
          </span>
        </div>
      </button>
      <label class="template-import-card import-label">
        <span class="import-graphic">
          <StudioIcon name="upload" :size="25" />
        </span>
        <strong>带上你的制作配方</strong>
        <span>
          导入 JSON 模板
          <br />
          让好的配置，成为下一次的起点。
        </span>
        <b>
          导入模板
          <StudioIcon name="arrow" :size="15" />
        </b>
        <input
          type="file"
          accept=".json,application/json"
          aria-label="导入 JSON 模板"
          :disabled="busy"
          @change="importFile"
        />
      </label>
    </div>
    <div v-if="!templates.length" class="template-loading">
      正在准备制作模板…
    </div>
    <p v-if="error" class="template-error" role="alert">{{ error }}</p>
    <span v-if="busy" class="template-loading" role="status">
      正在核对模板配置…
    </span>
  </section>
</template>

<style scoped>
.template-picker {
  margin-top: 38px;
  color: #e3e7ed;
}
.template-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 21px;
}
.template-heading h2 {
  font-size: 17px;
  font-weight: 550;
  letter-spacing: -0.3px;
}
.template-heading p {
  margin-top: 7px;
  font-size: 12px;
  color: #848b98;
}
.template-export {
  display: flex;
  align-items: center;
  gap: 7px;
  white-space: nowrap;
  color: #9299a5;
  font-size: 11px;
}
.template-export:hover {
  color: #69ddca;
}
.template-cards {
  display: grid;
  grid-template-columns: 1fr 1fr 0.8fr;
  gap: 16px;
}
.template-card {
  border: 1px solid #ffffff0d;
  border-radius: 14px;
  text-align: left;
  overflow: hidden;
  min-width: 0;
  background: #1b1e24;
  box-shadow: 0 7px 25px #0001;
  transition:
    border-color 0.2s,
    transform 0.2s,
    box-shadow 0.2s;
}
.template-card:hover {
  transform: translateY(-3px);
  border-color: #5fcfb969;
  box-shadow: 0 12px 30px #0003;
}
.template-card.chosen {
  border-color: #55ccb64a;
}
.template-art {
  position: relative;
  height: 112px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #263a3b;
  color: #64d2c2;
}
.template-art.ludo-classic {
  background: #312942;
}
.template-art.ludo-classic img {
  width: 100%;
  object-position: center 48%;
}
.template-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 46%;
  filter: brightness(0.8) saturate(0.85);
  transition:
    transform 0.4s ease,
    filter 0.3s;
}
.template-card:hover img {
  transform: scale(1.04);
  filter: brightness(0.95) saturate(1);
}
.template-art::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(0deg, #161b24aa, transparent 65%);
  pointer-events: none;
}
.template-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: #10131c99;
  border: 1px solid #ffffff20;
  backdrop-filter: blur(8px);
  padding: 3px 7px;
  border-radius: 5px;
  color: #f0f1f5;
  font-size: 9px;
  z-index: 1;
}
.template-selected {
  position: absolute;
  display: flex;
  gap: 4px;
  align-items: center;
  right: 11px;
  bottom: 10px;
  z-index: 1;
  color: #97eedb;
  font-size: 10px;
}
.template-copy {
  padding: 15px 16px 14px;
}
.template-copy > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.template-copy h3 {
  font-size: 14px;
  color: #e4e8ef;
  font-weight: 550;
}
.template-copy svg {
  color: #9099a5;
  flex-shrink: 0;
}
.template-copy p {
  font-size: 11px;
  color: #949ca9;
  line-height: 1.8;
  margin-top: 7px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.template-copy > span {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 9px;
  color: #757f90;
  margin-top: 12px;
}
.template-copy i {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #565d68;
}
.template-picker .template-import-card {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  text-align: center;
  background: linear-gradient(145deg, #20252a66, #171a2099);
  border: 1px dashed #ffffff24;
  border-radius: 14px;
  position: relative;
  cursor: pointer;
  margin: 0;
  padding: 22px 12px;
}
.template-import-card:hover {
  border-color: #5fd0bb88;
  background: #1e292a;
}
.import-graphic {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #ffffff04;
  color: #829a9c;
  border: 1px solid #ffffff0d;
}
.template-import-card strong {
  font-size: 13px;
  color: #bcc5cf;
  font-weight: 500;
}
.template-import-card > span:not(.import-graphic) {
  font-size: 10px;
  color: #848f9d;
  font-weight: 400;
  line-height: 1.8;
}
.template-import-card b {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #65cdbb;
  font-size: 11px;
  font-weight: 500;
  margin-top: 2px;
}
.template-picker .import-label input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}
.template-import-card:focus-within {
  outline: 2px solid #5fd5bf;
  outline-offset: 4px;
}
.template-error {
  color: #edada4;
  font-size: 12px;
  margin-top: 15px;
}
.template-loading {
  display: block;
  color: #9ba4b1;
  font-size: 12px;
  margin-top: 14px;
}
@media (max-width: 1000px) {
  .template-cards {
    gap: 12px;
    grid-template-columns: 1fr 1fr;
  }
  .template-picker .template-import-card {
    grid-column: 1 / -1;
    flex-direction: row;
    padding: 14px 18px;
    gap: 14px;
    text-align: left;
    justify-content: flex-start;
  }
  .template-import-card > span:not(.import-graphic) {
    display: none;
  }
  .template-import-card b {
    margin-left: auto;
  }
  .import-graphic {
    width: 32px;
    height: 32px;
    border-radius: 8px;
  }
  .import-graphic svg {
    width: 18px;
  }
  .template-copy {
    padding: 13px;
  }
}
@media (max-width: 500px) {
  .template-heading {
    align-items: flex-start;
  }
  .template-heading h2 {
    font-size: 15px;
  }
  .template-heading p {
    max-width: 210px;
    font-size: 11px;
  }
  .template-export {
    font-size: 0;
    padding: 5px;
  }
  .template-export svg {
    width: 18px;
    height: 18px;
  }
  .template-art {
    height: 94px;
  }
  .template-copy h3 {
    font-size: 12px;
  }
  .template-copy p {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    white-space: normal;
    min-height: 36px;
    font-size: 10px;
  }
  .template-copy > span {
    font-size: 9px;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 9px;
  }
  .template-copy > div > svg {
    width: 13px;
  }
  .template-badge {
    font-size: 8px;
    top: 8px;
    left: 8px;
  }
  .template-selected {
    font-size: 8px;
    right: 6px;
    bottom: 7px;
  }
  .template-picker {
    margin-top: 30px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .template-card,
  .template-art img {
    transition: none;
  }
  .template-card:hover {
    transform: none;
  }
}
</style>
