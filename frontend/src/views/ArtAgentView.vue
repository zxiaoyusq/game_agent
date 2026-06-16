<script setup>
import { ref, reactive, computed, onUnmounted } from 'vue'
import KnowledgeRefBlock from '../components/agent/KnowledgeRefBlock.vue'
import { generateImage as apiGenerateImage } from '../api/artImage.js'

const emit = defineEmits(['navigate'])

// ---- 4 个美术子模块（对应参考工程的 4 步流水线）----
const MODULES = [
  { id: 'character', index: 1, name: 'AI 图片生成', hint: '基于提示词 + 参考图生成图片（Azure gpt-image）', icon: '🎨' },
  { id: 'video', index: 2, name: 'AI 视频生成', hint: '选择图片作为参考输入', icon: '🎬' },
  { id: 'motion', index: 3, name: '动作捕捉', hint: '从视频结果提取动作数据', icon: '🕴' },
  { id: 'facial', index: 4, name: '表情捕捉', hint: '从动作产物提取表情曲线', icon: '😊' },
]

// ---- 各模块可选模型 / Provider ----
// character 走真实的 Azure gpt-image 接口；其余仍是占位
const PROVIDERS = {
  character: [
    { id: 'azure_gpt_image', label: 'Azure · gpt-image', default: true },
  ],
  video: [
    { id: 'tongyi_video', label: '通义万相 · 视频生成', default: true },
    { id: 'mock_video', label: 'Mock · 本地占位生成器' },
  ],
  motion: [
    { id: 'mediapipe_motion', label: 'MediaPipe · 本地姿态估计', default: true },
    { id: 'qianmian_motion', label: '千面云 · 高精度动捕' },
  ],
  facial: [
    { id: 'mock_facial', label: 'Mock · ARKit 52 表情曲线', default: true },
  ],
}

// ---- AI 图片生成：尺寸 / 质量配置（与后端 ALLOWED_SIZES / ALLOWED_QUALITIES 对齐）----
// mode 字段：smart / reference / keyword 是"自动判定"档位，其余直接走具体规格
const IMAGE_SIZE_OPTIONS = [
  { value: 'smart', label: '智能自动' },
  { value: 'reference', label: '跟随图1比例' },
  { value: 'keyword', label: '关键词自动' },
  { value: '1024x1024', label: '方图 1024×1024' },
  { value: '1280x720', label: '16:9 1280×720' },
  { value: '2048x1152', label: '16:9 2048×1152' },
  { value: '2560x1440', label: '16:9 2560×1440' },
  { value: '3584x2016', label: '16:9 3584×2016' },
  { value: '720x1280', label: '9:16 720×1280' },
  { value: '1152x2048', label: '9:16 1152×2048' },
  { value: '1440x2560', label: '9:16 1440×2560' },
  { value: '2016x3584', label: '9:16 2016×3584' },
  { value: '1536x1024', label: '横图 1536×1024' },
  { value: '1024x1536', label: '竖图 1024×1536' },
]

const IMAGE_QUALITY_OPTIONS = [
  { value: 'low',    label: '快速（low）' },
  { value: 'medium', label: '均衡（medium）' },
  { value: 'high',   label: '极致（high）' },
  { value: 'auto',   label: '自动（auto）' },
]

// 关键词 → 尺寸映射，与 ai_image_tool.html 的 detectSizeFromKeywords 一致
function detectSizeFromKeywords(prompt) {
  const t = (prompt || '').toLowerCase()
  if (['方图','方形','正方形','头像','图标','icon','square','1:1'].some(w => t.includes(w))) return '1024x1024'
  if (['16:9','横屏','视频封面','youtube','b站封面','bilibili','widescreen'].some(w => t.includes(w))) return '2048x1152'
  if (['9:16','竖屏','手机壁纸','抖音','快手','小红书','reels','shorts','tiktok'].some(w => t.includes(w))) return '1152x2048'
  if (['横图','横版','横向','宽图','banner','landscape','3:2'].some(w => t.includes(w))) return '1536x1024'
  if (['竖图','竖版','竖向','长图','海报','portrait','2:3'].some(w => t.includes(w))) return '1024x1536'
  return null
}

// 读图片尺寸：用于"跟随图1比例"
async function readImageDimensions(file) {
  if ('createImageBitmap' in window) {
    const bmp = await createImageBitmap(file)
    const d = { width: bmp.width, height: bmp.height }
    bmp.close()
    return d
  }
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight })
      URL.revokeObjectURL(url)
    }
    img.onerror = () => {
      reject(new Error('无法读取参考图尺寸'))
      URL.revokeObjectURL(url)
    }
    img.src = url
  })
}

// 根据图1比例挑一个最贴近的尺寸
async function detectSizeFromFirstReference(refImages) {
  if (!refImages?.length) return null
  const f = refImages[0].file
  const { width, height } = await readImageDimensions(f)
  const r = width / height
  if (r >= 1.55) return '2048x1152'
  if (r >= 1.1)  return '1536x1024'
  if (r <= 0.65) return '1152x2048'
  if (r <= 0.9)  return '1024x1536'
  return '1024x1024'
}

// 根据 sizeMode 解析最终送给后端的尺寸字符串
async function resolveSize(sizeMode, prompt, refImages) {
  if (/^\d+x\d+$/.test(sizeMode)) return sizeMode
  if (sizeMode === 'keyword' || sizeMode === 'smart') {
    const ks = detectSizeFromKeywords(prompt)
    if (ks) return ks
  }
  if (sizeMode === 'reference' || sizeMode === 'smart') {
    try {
      const rs = await detectSizeFromFirstReference(refImages)
      if (rs) return rs
    } catch (_) {
      // 读尺寸失败兜底为方图
    }
  }
  return '1024x1024'
}

// ---- SVG 占位图工具，避免 demo 引入外部图片资源 ----
function svgDataUri(content) {
  return `data:image/svg+xml;utf8,${encodeURIComponent(content)}`
}

function characterPlaceholder(label, hue) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
    <defs>
      <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="hsl(${hue}, 60%, 22%)"/>
        <stop offset="100%" stop-color="hsl(${(hue + 40) % 360}, 60%, 12%)"/>
      </linearGradient>
    </defs>
    <rect width="512" height="512" fill="url(#g)"/>
    <circle cx="256" cy="200" r="64" fill="hsl(${hue}, 60%, 70%)" opacity="0.85"/>
    <rect x="180" y="270" width="152" height="180" rx="20" fill="hsl(${hue}, 60%, 55%)" opacity="0.75"/>
    <rect x="200" y="290" width="112" height="14" rx="4" fill="hsl(${(hue + 60) % 360}, 70%, 80%)" opacity="0.9"/>
    <rect x="200" y="312" width="80" height="10" rx="3" fill="hsl(${(hue + 60) % 360}, 70%, 80%)" opacity="0.7"/>
    <text x="256" y="490" text-anchor="middle" fill="rgba(255,255,255,0.85)" font-family="sans-serif" font-size="20" font-weight="600">${label}</text>
  </svg>`
  return svgDataUri(svg)
}

function previewBoxPlaceholder(label, color, subtitle = '') {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 288">
    <rect width="512" height="288" fill="${color}" fill-opacity="0.12"/>
    <rect x="12" y="12" width="488" height="264" rx="8" fill="none" stroke="${color}" stroke-width="2" stroke-dasharray="8 6"/>
    <text x="256" y="140" text-anchor="middle" fill="${color}" font-family="sans-serif" font-size="22" font-weight="600">${label}</text>
    <text x="256" y="170" text-anchor="middle" fill="${color}" fill-opacity="0.7" font-family="sans-serif" font-size="13">${subtitle}</text>
  </svg>`
  return svgDataUri(svg)
}

// ---- 预设示例任务（jobsHistory）：展示完整流水线时直接看到产物 ----
const SAMPLE_JOBS = {
  character: [
    {
      id: 'char_demo_001',
      status: 'succeeded',
      created_at: '2026-06-04T10:32:15Z',
      providerLabel: '通义万相 · 角色生成',
      prompt: 'Q 版麻将精灵，圆润可爱，手持「发」字麻将牌，糖果色搭配',
      outputs: [
        {
          id: 'asset_char_1',
          name: 'character_image_1.png',
          type: 'image',
          format: 'png',
          src: characterPlaceholder('character_image_1.png', 200),
        },
        {
          id: 'asset_char_1_json',
          name: 'character_image_1.json',
          type: 'meta',
          format: 'json',
          jsonContent: {
            id: 'character_image_1',
            prompt: 'Q 版麻将精灵，圆润可爱，手持「发」字麻将牌，糖果色搭配',
            negative_prompt: '低分辨率，低画质，肢体畸形',
            resolution: '512x512',
            seed: 1024,
            provider: 'tongyi_wanxiang',
            generated_at: '2026-06-04T10:32:15Z',
          },
        },
      ],
    },
  ],
  video: [
    {
      id: 'video_demo_001',
      status: 'succeeded',
      created_at: '2026-06-04T11:08:42Z',
      providerLabel: '通义万相 · 视频生成',
      prompt: '麻将精灵原地待机，轻微鞠躬挥手，麻将牌轻轻晃动，5 秒短片',
      outputs: [
        {
          id: 'asset_video_1',
          name: 'output_video.mp4',
          type: 'video',
          format: 'mp4',
          src: previewBoxPlaceholder('output_video.mp4', '#f778ba', '720P · 5s · 24fps · 占位预览'),
        },
        {
          id: 'asset_video_1_json',
          name: 'video_config.json',
          type: 'meta',
          format: 'json',
          jsonContent: {
            duration_seconds: 5,
            fps: 24,
            resolution: '720P',
            character_asset_ids: ['asset_char_1'],
            provider: 'tongyi_video',
            generated_at: '2026-06-04T11:08:42Z',
          },
        },
      ],
    },
  ],
  motion: [
    {
      id: 'motion_demo_001',
      status: 'succeeded',
      created_at: '2026-06-04T11:24:09Z',
      providerLabel: 'MediaPipe · 本地姿态估计',
      prompt: '',
      outputs: [
        {
          id: 'asset_motion_1',
          name: 'motion_overlay.mp4',
          type: 'video',
          format: 'mp4',
          src: previewBoxPlaceholder('motion_overlay.mp4', '#39c5cf', '骨骼叠加预览（占位）'),
        },
        {
          id: 'asset_motion_1_json',
          name: 'motion_keypoints.json',
          type: 'motion',
          format: 'json',
          jsonContent: {
            target_skeleton: 'humanoid',
            num_frames: 120,
            fps: 24,
            keypoints: [
              { frame: 0, joints: { hip: [0, 0, 0], spine: [0, 0.3, 0], head: [0, 1.6, 0] } },
              { frame: 1, joints: { hip: [0, 0.01, 0], spine: [0, 0.31, 0], head: [0, 1.61, 0] } },
              { frame: 2, joints: { hip: [0, 0.02, 0], spine: [0, 0.32, 0], head: [0, 1.62, 0] } },
            ],
            provider: 'mediapipe_motion',
          },
        },
      ],
    },
  ],
  facial: [
    {
      id: 'facial_demo_001',
      status: 'succeeded',
      created_at: '2026-06-04T11:36:51Z',
      providerLabel: 'Mock · ARKit 52 表情曲线',
      prompt: '',
      outputs: [
        {
          id: 'asset_facial_1',
          name: 'facial_curves.json',
          type: 'facial',
          format: 'json',
          jsonContent: {
            output_standard: 'arkit_52',
            include_head_pose: true,
            fps: 30,
            curves: {
              browInnerUp: [0.0, 0.05, 0.12, 0.18, 0.22, 0.18],
              eyeBlinkLeft: [0.0, 0.0, 0.32, 0.85, 0.32, 0.0],
              eyeBlinkRight: [0.0, 0.0, 0.30, 0.82, 0.30, 0.0],
              jawOpen: [0.0, 0.08, 0.18, 0.32, 0.40, 0.22],
              mouthSmileLeft: [0.05, 0.15, 0.25, 0.32, 0.38, 0.30],
              mouthSmileRight: [0.05, 0.16, 0.26, 0.33, 0.39, 0.31],
            },
          },
        },
      ],
    },
  ],
}

// ---- 状态 ----
const activeModule = ref('character')
const isRunning = ref(false)
const errorMsg = ref('')

const forms = reactive({
  character: {
    prompt: 'Q 版麻将精灵，圆润可爱，手持「发」字麻将牌，糖果色搭配，适合休闲游戏 UI 表现',
    model: PROVIDERS.character.find((p) => p.default).id,
    // AI 图片生成参数
    sizeMode: 'smart',                  // 见 IMAGE_SIZE_OPTIONS
    quality: 'medium',                  // low / medium / high / auto
    refImages: [],                      // [{ file: File, url: ObjectURL }]
    knowledgeRefs: [],
  },
  video: {
    prompt: '麻将精灵原地待机，轻微鞠躬挥手，麻将牌轻轻晃动，镜头稳定，5 秒短片',
    selectedAssetId: 'asset_char_1',
    model: PROVIDERS.video.find((p) => p.default).id,
    knowledgeRefs: [],
  },
  motion: {
    selectedAssetId: 'asset_video_1',
    model: PROVIDERS.motion.find((p) => p.default).id,
    knowledgeRefs: [],
  },
  facial: {
    selectedAssetId: 'asset_motion_1',
    model: PROVIDERS.facial.find((p) => p.default).id,
    knowledgeRefs: [],
  },
})

// 历史任务（克隆预设示例）
const jobsHistory = reactive({
  character: [...SAMPLE_JOBS.character],
  video: [...SAMPLE_JOBS.video],
  motion: [...SAMPLE_JOBS.motion],
  facial: [...SAMPLE_JOBS.facial],
})

// 当前会话生成的任务（可能 running / failed / succeeded）
const sessionJobs = reactive({
  character: null,
  video: null,
  motion: null,
  facial: null,
})

// 用户在历史下拉中选中的任务 id；空串表示自动展示最近一次
const selectedJobIds = reactive({
  character: '',
  video: '',
  motion: '',
  facial: '',
})

// ---- 计算属性 ----
const currentModule = computed(() => MODULES.find((m) => m.id === activeModule.value))

const currentJobHistory = computed(() =>
  (jobsHistory[activeModule.value] || []).filter((j) => j.status === 'succeeded')
)

const currentJob = computed(() => {
  const sid = selectedJobIds[activeModule.value]
  if (sid) return currentJobHistory.value.find((j) => j.id === sid) || null
  // 优先显示本会话刚跑过的任务（含 running/failed），其次回退到历史最新
  const sessionJob = sessionJobs[activeModule.value]
  if (sessionJob) return sessionJob
  return currentJobHistory.value[0] || null
})

const currentOutputs = computed(() => currentJob.value?.outputs || [])

// 上游资产列表（用于下游模块的下拉选择）
function flatAssetsOf(moduleId, kindFilter = null) {
  const out = []
  for (const job of jobsHistory[moduleId] || []) {
    if (job.status !== 'succeeded') continue
    for (const a of job.outputs) {
      if (kindFilter && !kindFilter(a)) continue
      out.push(a)
    }
  }
  return out
}

const characterAssets = computed(() =>
  flatAssetsOf('character', (a) => a.type === 'image')
)
const videoAssets = computed(() =>
  flatAssetsOf('video', (a) => a.type === 'video')
)
const motionAssets = computed(() =>
  flatAssetsOf('motion', (a) => a.type === 'video' || a.type === 'motion')
)

const selectedCharacterAsset = computed(() =>
  characterAssets.value.find((a) => a.id === forms.video.selectedAssetId) || null
)

// 文件名去扩展名，用来配对图片+JSON
function stemOf(name) {
  const dot = name.lastIndexOf('.')
  return dot === -1 ? name : name.slice(0, dot)
}

// 把 outputs 拼成"主资源+JSON 配对 / 单资源"列表
const previewItems = computed(() => {
  const outputs = currentOutputs.value
  const jsonByStem = new Map()
  const jsonList = []
  for (const a of outputs) {
    if (a.format === 'json') {
      jsonByStem.set(stemOf(a.name), a)
      jsonList.push(a)
    }
  }
  const usedJsonIds = new Set()
  const items = []
  for (const a of outputs) {
    if (a.format === 'json') continue
    const kind = previewKind(a)
    if (kind === 'image' || kind === 'video') {
      let paired = jsonByStem.get(stemOf(a.name))
      if (paired && usedJsonIds.has(paired.id)) paired = null
      if (!paired) paired = jsonList.find((j) => !usedJsonIds.has(j.id))
      if (paired) {
        usedJsonIds.add(paired.id)
        items.push({ kind: 'paired', primary: a, json: paired })
        continue
      }
    }
    items.push({ kind: 'single', asset: a })
  }
  for (const a of outputs) {
    if (a.format === 'json' && !usedJsonIds.has(a.id)) {
      items.push({ kind: 'single', asset: a })
    }
  }
  return items
})

function previewKind(asset) {
  if (asset.type === 'image' || asset.type === 'preview') return 'image'
  if (asset.type === 'video') return 'video'
  if (asset.format === 'json') return 'json'
  return 'file'
}

function formatJson(obj) {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

function formatJobLabel(job) {
  const t = job.created_at ? new Date(job.created_at) : null
  const timeText = t
    ? `${t.getFullYear()}/${String(t.getMonth() + 1).padStart(2, '0')}/${String(t.getDate()).padStart(2, '0')} ${String(t.getHours()).padStart(2, '0')}:${String(t.getMinutes()).padStart(2, '0')}`
    : '时间未知'
  const tail = job.id ? job.id.slice(-6) : ''
  return `${timeText} · ${job.outputs?.length ?? 0} 输出 · ${tail}`
}

function formatJobStatus(job) {
  if (!job) return '未创建任务'
  return { pending: '等待中', running: '执行中', succeeded: '已完成', failed: '失败' }[job.status] || job.status
}

// ---- 行为 ----
function chooseModule(id) {
  activeModule.value = id
  errorMsg.value = ''
}

// ============================================================
// AI 图片生成（character 模块）—— 真实 Azure gpt-image 接入
// ============================================================

// 当前生成中的 AbortController；用于"取消生成"按钮
const imageAbortController = ref(null)
// 上次生成的结果（PNG dataURL）+ 元信息；每个 character 任务覆盖前一次
const lastImageResult = ref(null)
// Lightbox
const showLightbox = ref(false)

// ---- 参考图管理 ----
const ALLOWED_REF_TYPES = ['image/png', 'image/jpeg']

function addRefImageFiles(fileList, sourceText = '已添加参考图') {
  const files = Array.from(fileList || [])
  let added = 0
  for (const f of files) {
    if (!f.type.startsWith('image/')) continue
    if (!ALLOWED_REF_TYPES.includes(f.type)) {
      errorMsg.value = `跳过不支持的格式：${f.name}`
      continue
    }
    if (f.size > 50 * 1024 * 1024) {
      errorMsg.value = `跳过过大图片：${f.name}（>50MB）`
      continue
    }
    forms.character.refImages.push({
      file: f,
      url: URL.createObjectURL(f),
    })
    added++
  }
  if (added) errorMsg.value = ''
  return added
}

function removeRefImage(index) {
  const list = forms.character.refImages
  const [removed] = list.splice(index, 1)
  if (removed?.url) URL.revokeObjectURL(removed.url)
}

function moveRefImage(index, delta) {
  const list = forms.character.refImages
  const next = index + delta
  if (next < 0 || next >= list.length) return
  const [it] = list.splice(index, 1)
  list.splice(next, 0, it)
}

function clearRefImages() {
  for (const r of forms.character.refImages) {
    if (r.url) URL.revokeObjectURL(r.url)
  }
  forms.character.refImages = []
}

// ---- 拖拽 / 粘贴 ----
const refDragOver = ref(false)
function onRefDragOver(e) { e.preventDefault(); refDragOver.value = true }
function onRefDragLeave() { refDragOver.value = false }
function onRefDrop(e) {
  e.preventDefault()
  refDragOver.value = false
  if (e.dataTransfer?.files?.length) {
    addRefImageFiles(e.dataTransfer.files, '已拖入参考图')
  }
}
function onRefPaste(e) {
  const items = e.clipboardData?.items
  if (!items) return
  const files = []
  for (const item of items) {
    if (item.type?.startsWith('image/')) {
      const blob = item.getAsFile()
      if (blob) {
        const ext = blob.type === 'image/jpeg' ? 'jpg' : 'png'
        const ts = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)
        files.push(new File([blob], `clipboard_${ts}.${ext}`, { type: blob.type || 'image/png' }))
      }
    }
  }
  if (files.length) {
    e.preventDefault()
    addRefImageFiles(files, '已粘贴参考图')
  }
}

// ---- 文件下载 ----
function downloadDataUrl(dataUrl, filename) {
  const a = document.createElement('a')
  a.href = dataUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// ---- 生成入口（character 专用，真实 API） ----
async function runImageGeneration() {
  if (isRunning.value) return
  errorMsg.value = ''
  const f = forms.character
  const prompt = (f.prompt || '').trim()
  if (!prompt) {
    errorMsg.value = '请先填写提示词'
    return
  }

  // 1) 计算最终尺寸
  let finalSize
  try {
    finalSize = await resolveSize(f.sizeMode, prompt, f.refImages)
  } catch (e) {
    finalSize = '1024x1024'
  }

  isRunning.value = true
  imageAbortController.value = new AbortController()

  // 占位"运行中"任务条
  const startedAt = new Date().toISOString()
  const tempJob = {
    id: `character_${Date.now()}`,
    status: 'running',
    created_at: startedAt,
    providerLabel: 'Azure · gpt-image',
    prompt,
    outputs: [],
    sizeLabel: finalSize,
    qualityLabel: f.quality,
  }
  sessionJobs.character = tempJob

  try {
    const t0 = Date.now()
    const blob = await apiGenerateImage({
      prompt,
      size: finalSize,
      quality: f.quality,
      references: f.refImages.map((r) => r.file),
      kbRefs: f.knowledgeRefs || [],
      signal: imageAbortController.value.signal,
    })
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1)

    // 转成 dataURL，便于直接 <img src> + 下载
    const dataUrl = await blobToDataUrl(blob)
    const filename = `image_${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}.png`

    lastImageResult.value = {
      dataUrl,
      filename,
      elapsed,
      size: finalSize,
      quality: f.quality,
      refCount: f.refImages.length,
      kbRefCount: (f.knowledgeRefs || []).length,
      prompt,
    }

    // 同步进 job history（让"结果预览"区也能看到）
    const finishedJob = {
      ...tempJob,
      status: 'succeeded',
      outputs: [
        {
          id: `${tempJob.id}_img`,
          name: filename,
          type: 'image',
          format: 'png',
          src: dataUrl,
        },
      ],
    }
    sessionJobs.character = finishedJob
    jobsHistory.character = [finishedJob, ...jobsHistory.character]
    selectedJobIds.character = ''

    // 与原有流水线联动
    forms.video.selectedAssetId = finishedJob.outputs[0].id
  } catch (e) {
    if (e?.name === 'AbortError') {
      errorMsg.value = '已取消生成'
      sessionJobs.character = { ...tempJob, status: 'failed' }
    } else {
      errorMsg.value = e?.message || '生成失败'
      sessionJobs.character = { ...tempJob, status: 'failed' }
    }
  } finally {
    imageAbortController.value = null
    isRunning.value = false
  }
}

function abortImageGeneration() {
  imageAbortController.value?.abort()
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error || new Error('读取失败'))
    reader.readAsDataURL(blob)
  })
}

// 离开页面 / 销毁组件时释放参考图 ObjectURL
onUnmounted(() => {
  for (const r of forms.character.refImages) {
    if (r.url) URL.revokeObjectURL(r.url)
  }
})

function onSelectHistoryJob(e) {
  selectedJobIds[activeModule.value] = e.target.value
}

// 模拟"运行任务"：1.5s 后产生一条新任务并写入历史
function runMockJob() {
  if (isRunning.value) return
  errorMsg.value = ''
  const moduleId = activeModule.value

  // 校验：下游模块需要先选择上游产物
  if (moduleId === 'motion' && !forms.motion.selectedAssetId) {
    errorMsg.value = '请先选择 AI 视频生成模块的输出作为输入。'
    return
  }
  if (moduleId === 'facial' && !forms.facial.selectedAssetId) {
    errorMsg.value = '请先选择动作捕捉模块的输出作为输入。'
    return
  }

  isRunning.value = true
  // 占位"运行中"任务
  const startedAt = new Date().toISOString()
  const tempJob = {
    id: `${moduleId}_${Date.now()}`,
    status: 'running',
    created_at: startedAt,
    providerLabel: PROVIDERS[moduleId].find((p) => p.id === forms[moduleId].model)?.label || forms[moduleId].model,
    prompt: forms[moduleId].prompt || '',
    outputs: [],
  }
  sessionJobs[moduleId] = tempJob

  // 1.5 秒后填充示例输出，状态变 succeeded
  setTimeout(() => {
    const sample = SAMPLE_JOBS[moduleId][0]
    // 把 outputs 浅克隆一份并改写 id / 名称，避免与历史任务里的资产 id 冲突
    const outs = sample.outputs.map((o, idx) => ({
      ...o,
      id: `${tempJob.id}_out_${idx}`,
      name: o.name,
    }))
    const finished = {
      ...tempJob,
      status: 'succeeded',
      outputs: outs,
    }
    sessionJobs[moduleId] = finished
    // 写入历史最前
    jobsHistory[moduleId] = [finished, ...jobsHistory[moduleId]]
    // 自动联动：把新输出关联到下游模块的"上游选择"
    if (moduleId === 'character') forms.video.selectedAssetId = outs[0].id
    if (moduleId === 'video') forms.motion.selectedAssetId = outs[0].id
    if (moduleId === 'motion') forms.facial.selectedAssetId = outs[0].id
    selectedJobIds[moduleId] = ''
    isRunning.value = false
  }, 1500)
}
</script>

<template>
  <div class="art-view">
    <!-- 顶部栏：与策划 Agent 保持一致 -->
    <header class="art-topbar">
      <button class="back-btn" @click="emit('navigate', 'home')">← 主界面</button>
      <div class="crumbs">
        <span class="crumb">美术 Agent</span>
        <span class="sep">/</span>
        <span class="crumb current">{{ currentModule.name }}</span>
      </div>
      <div class="topbar-right">
        <button class="ghost-btn">📚 资产库</button>
        <button class="ghost-btn">⏱ 历史记录</button>
        <div class="avatar-mini">U</div>
      </div>
    </header>

    <div class="art-body">
      <!-- 侧边模块导航 -->
      <aside class="art-sidebar">
        <div class="brand">
          <div class="brand-mark">AI</div>
          <div class="brand-text">
            <div class="brand-title">美术生产工具链</div>
            <div class="brand-sub">AI 图片 / 视频 / 动捕 / 表情</div>
          </div>
        </div>

        <nav class="module-nav" aria-label="模块导航">
          <button
            v-for="m in MODULES"
            :key="m.id"
            class="module-button"
            :class="{ active: m.id === activeModule }"
            type="button"
            @click="chooseModule(m.id)"
          >
            <span class="step">{{ m.index }}</span>
            <span class="module-text">
              <strong>{{ m.icon }} {{ m.name }}</strong>
              <small>{{ m.hint }}</small>
            </span>
          </button>
        </nav>

        <div class="pipeline-hint">
          <div class="hint-title">流水线提示</div>
          <p>1 → 2 → 3 → 4 顺序执行；每步会自动选中上一步的产物作为输入。</p>
        </div>
      </aside>

      <!-- 主工作区 -->
      <main class="art-workspace">
        <header class="ws-header">
          <div>
            <p class="eyebrow">模块 {{ currentModule.index }}</p>
            <h2 class="ws-title">{{ currentModule.name }}</h2>
          </div>
          <button class="ghost-btn ws-refresh">🔄 刷新资产</button>
        </header>

        <p v-if="errorMsg" class="error-message">{{ errorMsg }}</p>

        <!-- AI 图片生成 -->
        <section v-if="activeModule === 'character'" class="work-panel" @paste="onRefPaste">
          <label class="field">
            <span class="field-label">模型选择</span>
            <select v-model="forms.character.model">
              <option v-for="opt in PROVIDERS.character" :key="opt.id" :value="opt.id">
                {{ opt.label }}
              </option>
            </select>
          </label>

          <div class="field-grid-2">
            <label class="field">
              <span class="field-label">输出尺寸</span>
              <select v-model="forms.character.sizeMode">
                <option v-for="opt in IMAGE_SIZE_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </label>
            <label class="field">
              <span class="field-label">生成质量</span>
              <select v-model="forms.character.quality">
                <option v-for="opt in IMAGE_QUALITY_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </label>
          </div>

          <label class="field">
            <span class="field-label">提示词</span>
            <textarea
              v-model="forms.character.prompt"
              rows="6"
              placeholder="描述你想要的画面，可在文中用「图1」「图2」引用参考图…"
            />
          </label>

          <!-- 参考图区 -->
          <div class="field">
            <div class="field-label-row">
              <span class="field-label">参考图（可选）</span>
              <span class="field-hint">
                支持 PNG / JPEG，单张 ≤ 50MB；可拖入、Ctrl+V 粘贴或点击 + 添加。<br>
                顺序对应提示词中的「图1」「图2」…
              </span>
            </div>

            <div
              class="ref-zone"
              :class="{ 'drag-over': refDragOver }"
              @dragover="onRefDragOver"
              @dragleave="onRefDragLeave"
              @drop="onRefDrop"
            >
              <div v-if="!forms.character.refImages.length" class="ref-empty">
                拖入图片到此处 / Ctrl+V 粘贴 / 点击右侧
                <button
                  class="ghost-btn ref-add-btn"
                  type="button"
                  @click="$refs.refFileInput.click()"
                >
                  + 添加参考图
                </button>
              </div>

              <div v-else class="ref-list">
                <div
                  v-for="(r, i) in forms.character.refImages"
                  :key="i"
                  class="ref-card"
                >
                  <img :src="r.url" :alt="`图${i + 1}`" />
                  <div class="ref-card-meta">
                    <strong>图{{ i + 1 }}</strong>
                    <span>{{ r.file.name }}</span>
                  </div>
                  <div class="ref-card-actions">
                    <button
                      type="button"
                      title="上移"
                      :disabled="i === 0"
                      @click="moveRefImage(i, -1)"
                    >▲</button>
                    <button
                      type="button"
                      title="下移"
                      :disabled="i === forms.character.refImages.length - 1"
                      @click="moveRefImage(i, 1)"
                    >▼</button>
                    <button type="button" title="删除" @click="removeRefImage(i)">×</button>
                  </div>
                </div>
                <button
                  class="ghost-btn ref-add-btn-sm"
                  type="button"
                  @click="$refs.refFileInput.click()"
                >
                  + 继续添加
                </button>
                <button
                  class="ghost-btn ref-add-btn-sm"
                  type="button"
                  @click="clearRefImages"
                >
                  清空
                </button>
              </div>
            </div>

            <input
              ref="refFileInput"
              type="file"
              accept="image/png,image/jpeg"
              multiple
              hidden
              @change="(e) => { addRefImageFiles(e.target.files); e.target.value = '' }"
            />
          </div>

          <KnowledgeRefBlock
            v-model="forms.character.knowledgeRefs"
            class="kb-in-form"
          />
          <p class="note">
            知识库引用中的图片会作为额外参考图一并送入生成；仅 PNG / JPEG 会被采用。
          </p>

          <div class="action-row">
            <button
              class="primary-btn"
              :disabled="isRunning"
              @click="runImageGeneration"
            >
              {{ isRunning ? '生成中…' : '🎨 生成图片' }}
            </button>
            <button
              v-if="isRunning"
              class="ghost-btn"
              type="button"
              @click="abortImageGeneration"
            >
              取消生成
            </button>
          </div>

          <!-- 最近一次结果（dataURL 预览 + 下载 / 放大） -->
          <div v-if="lastImageResult" class="last-result">
            <header class="last-result-head">
              <strong>最近生成</strong>
              <span>
                {{ lastImageResult.size }} · {{ lastImageResult.quality }} ·
                {{ lastImageResult.elapsed }}s
                · 参考图 {{ lastImageResult.refCount + lastImageResult.kbRefCount }} 张
              </span>
            </header>
            <div class="last-result-body">
              <img
                :src="lastImageResult.dataUrl"
                :alt="lastImageResult.filename"
                @click="showLightbox = true"
              />
              <div class="last-result-actions">
                <button
                  class="ghost-btn"
                  type="button"
                  @click="showLightbox = true"
                >🔍 放大</button>
                <button
                  class="ghost-btn"
                  type="button"
                  @click="downloadDataUrl(lastImageResult.dataUrl, lastImageResult.filename)"
                >⬇ 下载 PNG</button>
              </div>
            </div>
          </div>
        </section>

        <!-- Lightbox -->
        <Teleport to="body">
          <div
            v-if="showLightbox && lastImageResult"
            class="image-lightbox"
            @click.self="showLightbox = false"
          >
            <button class="image-lightbox-close" @click="showLightbox = false">×</button>
            <img :src="lastImageResult.dataUrl" :alt="lastImageResult.filename" />
          </div>
        </Teleport>

        <!-- 视频生成 -->
        <section v-if="activeModule === 'video'" class="work-panel">
          <label class="field">
            <span class="field-label">模型选择</span>
            <select v-model="forms.video.model">
              <option v-for="opt in PROVIDERS.video" :key="opt.id" :value="opt.id">
                {{ opt.label }}
              </option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">选择 AI 角色生成输出</span>
            <select v-model="forms.video.selectedAssetId">
              <option value="">不选择上游资产</option>
              <option v-for="a in characterAssets" :key="a.id" :value="a.id">
                {{ a.name }} · {{ a.format }}
              </option>
            </select>
          </label>

          <div v-if="selectedCharacterAsset" class="selected-asset-preview">
            <img :src="selectedCharacterAsset.src" :alt="selectedCharacterAsset.name" />
            <div class="selected-asset-meta">
              <strong>{{ selectedCharacterAsset.name }}</strong>
              <span>{{ selectedCharacterAsset.type }} · {{ selectedCharacterAsset.format }}</span>
              <span class="muted-link">参考图已加载</span>
            </div>
          </div>

          <label class="field">
            <span class="field-label">提示词</span>
            <textarea v-model="forms.video.prompt" rows="5" />
          </label>
          <KnowledgeRefBlock
            v-model="forms.video.knowledgeRefs"
            class="kb-in-form"
          />
          <button class="primary-btn" :disabled="isRunning" @click="runMockJob">
            {{ isRunning ? '生成中…' : '🎬 生成视频' }}
          </button>
        </section>

        <!-- 动作捕捉 -->
        <section v-if="activeModule === 'motion'" class="work-panel">
          <label class="field">
            <span class="field-label">模型选择</span>
            <select v-model="forms.motion.model">
              <option v-for="opt in PROVIDERS.motion" :key="opt.id" :value="opt.id">
                {{ opt.label }}
              </option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">选择 AI 视频生成输出</span>
            <select v-model="forms.motion.selectedAssetId">
              <option value="">请选择视频模块输出</option>
              <option v-for="a in videoAssets" :key="a.id" :value="a.id">
                {{ a.name }} · {{ a.format }}
              </option>
            </select>
          </label>
          <p class="note">使用 humanoid 骨骼，输出 JSON 关键点 + 叠加预览视频。</p>
          <KnowledgeRefBlock
            v-model="forms.motion.knowledgeRefs"
            class="kb-in-form"
          />
          <button class="primary-btn" :disabled="isRunning" @click="runMockJob">
            {{ isRunning ? '处理中…' : '🕴 生成动作捕捉数据' }}
          </button>
        </section>

        <!-- 表情捕捉 -->
        <section v-if="activeModule === 'facial'" class="work-panel">
          <label class="field">
            <span class="field-label">模型选择</span>
            <select v-model="forms.facial.model">
              <option v-for="opt in PROVIDERS.facial" :key="opt.id" :value="opt.id">
                {{ opt.label }}
              </option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">选择动作捕捉输出</span>
            <select v-model="forms.facial.selectedAssetId">
              <option value="">请选择动作捕捉模块输出</option>
              <option v-for="a in motionAssets" :key="a.id" :value="a.id">
                {{ a.name }} · {{ a.format }}
              </option>
            </select>
          </label>
          <p class="note">输出 ARKit 52 标准曲线 + 头部姿态。</p>
          <KnowledgeRefBlock
            v-model="forms.facial.knowledgeRefs"
            class="kb-in-form"
          />
          <button class="primary-btn" :disabled="isRunning" @click="runMockJob">
            {{ isRunning ? '处理中…' : '😊 生成表情捕捉数据' }}
          </button>
        </section>

        <!-- 预览面板 -->
        <section class="preview-section">
          <div class="section-title">
            <h3>结果预览</h3>
            <div class="section-title-right">
              <label v-if="currentJobHistory.length" class="history-picker">
                <span>历史任务</span>
                <select :value="selectedJobIds[activeModule]" @change="onSelectHistoryJob">
                  <option value="">最近一次任务</option>
                  <option v-for="job in currentJobHistory" :key="job.id" :value="job.id">
                    {{ formatJobLabel(job) }}
                  </option>
                </select>
              </label>
              <span class="status-text">
                {{ formatJobStatus(currentJob) }} · {{ currentOutputs.length }} 个输出
              </span>
            </div>
          </div>

          <div v-if="currentJob" class="job-status" :class="currentJob.status">
            <strong>最近任务：{{ currentJob.id }}</strong>
            <span>{{ currentJob.providerLabel }} · {{ formatJobStatus(currentJob) }}</span>
            <p v-if="currentJob.prompt">提示词：{{ currentJob.prompt }}</p>
          </div>

          <div v-if="!currentOutputs.length" class="empty-preview">
            当前模块还没有生成结果。
          </div>

          <div v-else class="preview-grid">
            <template
              v-for="item in previewItems"
              :key="item.kind === 'paired' ? item.primary.id : item.asset.id"
            >
              <!-- 配对：图片/视频 + JSON 横向并排 -->
              <article v-if="item.kind === 'paired'" class="asset-item asset-item-paired">
                <div class="paired-body">
                  <div class="paired-image">
                    <div class="asset-preview">
                      <img
                        v-if="previewKind(item.primary) === 'image'"
                        :src="item.primary.src"
                        :alt="item.primary.name"
                      />
                      <div
                        v-else-if="previewKind(item.primary) === 'video'"
                        class="video-mock"
                      >
                        <img :src="item.primary.src" :alt="item.primary.name" />
                        <div class="video-controls">
                          <span class="play-icon">▶</span>
                          <span class="video-tag">视频占位</span>
                        </div>
                      </div>
                    </div>
                    <div class="asset-meta">
                      <strong>{{ item.primary.name }}</strong>
                      <span>{{ item.primary.type }} · {{ item.primary.format }}</span>
                      <span class="muted-link">点击下载（demo 占位）</span>
                    </div>
                  </div>
                  <div class="paired-json">
                    <header class="paired-json-header">
                      <strong>{{ item.json.name }}</strong>
                      <span class="muted-link">查看 JSON</span>
                    </header>
                    <pre class="json-preview">{{ formatJson(item.json.jsonContent) }}</pre>
                  </div>
                </div>
              </article>

              <!-- 单资源 -->
              <article
                v-else
                class="asset-item"
                :class="{ 'asset-item-json': previewKind(item.asset) === 'json' }"
              >
                <div class="asset-preview">
                  <img
                    v-if="previewKind(item.asset) === 'image'"
                    :src="item.asset.src"
                    :alt="item.asset.name"
                  />
                  <div v-else-if="previewKind(item.asset) === 'video'" class="video-mock">
                    <img :src="item.asset.src" :alt="item.asset.name" />
                    <div class="video-controls">
                      <span class="play-icon">▶</span>
                      <span class="video-tag">视频占位</span>
                    </div>
                  </div>
                  <pre v-else-if="previewKind(item.asset) === 'json'" class="json-preview">{{ formatJson(item.asset.jsonContent) }}</pre>
                  <div v-else class="file-fallback">{{ item.asset.format.toUpperCase() }}</div>
                </div>
                <div class="asset-meta">
                  <strong>{{ item.asset.name }}</strong>
                  <span>{{ item.asset.type }} · {{ item.asset.format }}</span>
                </div>
              </article>
            </template>
          </div>

          <!-- 角色模块下方的 3D 占位 -->
          <div v-if="activeModule === 'character'" class="model3d-placeholder">
            <header class="model3d-header">
              <strong>3D 资产预览</strong>
              <span>预留窗口</span>
            </header>
            <div class="model3d-body">暂未生成 3D 资产，等待后续接入。</div>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<style scoped>
.art-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-primary);
}

/* 顶部栏 */
.art-topbar {
  height: 56px;
  flex-shrink: 0;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1.5px solid var(--border-color);
  background: var(--bg-secondary);
}

.back-btn {
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}
.back-btn:hover {
  background: var(--bg-hover);
  color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.crumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.crumb {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}
.crumb.current {
  color: var(--accent-pink);
  font-weight: 700;
}
.sep {
  color: var(--text-tertiary);
  font-size: 12px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ghost-btn {
  padding: 5px 10px;
  font-size: 12px;
  color: var(--text-secondary);
  background: transparent;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}
.ghost-btn:hover {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.avatar-mini {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-pink), var(--accent-orange));
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Body */
.art-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* 侧边栏 */
.art-sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-right: 1.5px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 16px 12px;
  overflow-y: auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 22px;
  padding: 0 4px;
}

.brand-mark {
  width: 40px;
  height: 40px;
  clip-path: polygon(4px 0, calc(100% - 4px) 0, 100% 4px, 100% calc(100% - 4px), calc(100% - 4px) 100%, 4px 100%, 0 calc(100% - 4px), 0 4px);
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #fff;
  background: var(--accent-pink);
  border: 1.5px solid rgba(240, 107, 160, 0.5);
  font-size: 14px;
}

.brand-text {
  min-width: 0;
}

.brand-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.brand-sub {
  margin-top: 2px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.module-nav {
  display: grid;
  gap: 8px;
  margin-bottom: 18px;
}

.module-button {
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: 12px;
  width: 100%;
  min-height: 66px;
  padding: 12px;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  background: transparent;
  text-align: left;
  transition: all 0.15s;
}

.module-button:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.module-button.active {
  border-color: var(--accent-pink);
  background: var(--accent-pink-dim);
  box-shadow: 2px 2px 0 var(--shadow-pink);
}

.step {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 0.05em;
  border: 1px solid var(--border-color);
}

.module-button.active .step {
  background: var(--accent-pink);
  color: #fff;
  border-color: var(--accent-pink);
}

.module-text {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.module-text strong {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.module-text small {
  font-size: 11px;
  color: var(--text-tertiary);
  line-height: 1.4;
}

.pipeline-hint {
  margin-top: auto;
  padding: 12px;
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 11px;
  color: var(--text-tertiary);
  line-height: 1.5;
}

.hint-title {
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-pink);
}

/* 工作区 */
.art-workspace {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 24px 28px 32px;
}

.ws-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1.5px solid var(--border-color);
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--accent-pink);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.ws-title {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.ws-refresh {
  font-size: 12px;
}

.error-message {
  max-width: 1120px;
  margin: 0 0 16px;
  padding: 10px 12px;
  border: 1.5px solid rgba(255, 99, 71, 0.4);
  border-radius: var(--radius-md);
  background: rgba(255, 99, 71, 0.08);
  color: #ff8b75;
  font-size: 13px;
}

.work-panel,
.preview-section {
  max-width: 1120px;
  margin-bottom: 22px;
  padding: 18px;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-xl);
  background: var(--bg-secondary);
}

.field {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
}

.field-label {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

textarea,
select {
  width: 100%;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 13px;
}

textarea {
  resize: vertical;
  min-height: 110px;
  padding: 10px 12px;
  line-height: 1.55;
  font-family: inherit;
}

textarea:focus,
select:focus {
  outline: none;
  border-color: var(--accent-pink);
  box-shadow: 0 0 0 2px rgba(240, 107, 160, 0.1);
}

select {
  min-height: 38px;
  padding: 0 10px;
  appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, var(--text-tertiary) 50%),
    linear-gradient(135deg, var(--text-tertiary) 50%, transparent 50%);
  background-position: calc(100% - 18px) center, calc(100% - 13px) center;
  background-size: 5px 5px;
  background-repeat: no-repeat;
  padding-right: 32px;
}

.note {
  margin: -4px 0 12px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.kb-in-form {
  margin-bottom: 14px;
}

.selected-asset-preview {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: -4px 0 14px;
  padding: 10px;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
}

.selected-asset-preview img {
  width: 96px;
  height: 96px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  object-fit: contain;
  background: var(--bg-card);
}

.selected-asset-meta {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.selected-asset-meta strong {
  font-size: 13px;
  color: var(--text-primary);
  overflow-wrap: anywhere;
}

.selected-asset-meta span {
  color: var(--text-tertiary);
  font-size: 12px;
}

.muted-link {
  color: var(--accent-cyan);
  font-size: 12px;
}

.primary-btn {
  min-height: 38px;
  padding: 0 18px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--accent-pink), var(--accent-orange));
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  border: 1.5px solid rgba(240, 107, 160, 0.5);
  box-shadow: 2px 2px 0 var(--shadow-pink);
  transition: all 0.15s;
}

.primary-btn:hover:not(:disabled) {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 var(--shadow-pink);
}

.primary-btn:disabled {
  cursor: progress;
  opacity: 0.7;
}

/* 预览面板 */
.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-title-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.history-picker {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.history-picker select {
  min-height: 30px;
  min-width: 240px;
  padding: 0 28px 0 10px;
  font-size: 12px;
}

.status-text {
  font-size: 12px;
  color: var(--text-tertiary);
}

.job-status {
  display: grid;
  gap: 4px;
  margin-bottom: 14px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  font-size: 12px;
}

.job-status strong {
  color: var(--text-primary);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.job-status span,
.job-status p {
  margin: 0;
  color: var(--text-tertiary);
}

.job-status.failed {
  border-color: rgba(220, 38, 38, 0.4);
  background: rgba(220, 38, 38, 0.06);
}

.job-status.running {
  border-color: rgba(26, 111, 255, 0.4);
  background: rgba(26, 111, 255, 0.06);
}

.job-status.running strong {
  color: var(--accent-blue);
}

.empty-preview {
  display: grid;
  place-items: center;
  min-height: 220px;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  font-size: 13px;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.asset-item {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-card);
}

.asset-preview {
  display: grid;
  place-items: center;
  aspect-ratio: 1 / 1;
  background: var(--bg-tertiary);
  position: relative;
}

.asset-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-mock {
  position: relative;
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
}

.video-mock img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-controls {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 6px;
  background: rgba(0, 0, 0, 0.25);
}

.play-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.92);
  color: #1a1a1a;
  font-size: 14px;
}

.video-tag {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.85);
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.5);
}

.json-preview {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 12px;
  overflow: auto;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre;
  text-align: left;
}

.asset-item-json .asset-preview {
  aspect-ratio: auto;
  min-height: 240px;
  max-height: 340px;
  background: var(--bg-tertiary);
}

.asset-item-paired {
  grid-column: 1 / -1;
}

.paired-body {
  display: grid;
  grid-template-columns: minmax(260px, 360px) minmax(0, 1fr);
}

.paired-image {
  border-right: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.paired-image .asset-preview {
  aspect-ratio: 1 / 1;
}

.paired-json {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 440px;
  background: var(--bg-tertiary);
}

.paired-json-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.paired-json-header strong {
  font-size: 12px;
  overflow-wrap: anywhere;
}

.paired-json .json-preview {
  flex: 1 1 auto;
  min-height: 0;
}

.file-fallback {
  display: grid;
  place-items: center;
  width: 80px;
  height: 80px;
  border-radius: var(--radius-md);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 13px;
}

.asset-meta {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
}

.asset-meta strong {
  font-size: 13px;
  color: var(--text-primary);
  overflow-wrap: anywhere;
}

.asset-meta span {
  color: var(--text-tertiary);
  font-size: 12px;
}

/* 3D 占位 */
.model3d-placeholder {
  margin-top: 14px;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  overflow: hidden;
}

.model3d-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px dashed var(--border-color);
  background: var(--bg-card);
}

.model3d-header strong {
  font-size: 13px;
  color: var(--text-secondary);
}

.model3d-header span {
  font-size: 11px;
  color: var(--text-tertiary);
}

.model3d-body {
  display: grid;
  place-items: center;
  min-height: 180px;
  padding: 24px;
  color: var(--text-tertiary);
  font-size: 13px;
}

@media (max-width: 900px) {
  .paired-body {
    grid-template-columns: 1fr;
  }
  .paired-image {
    border-right: 0;
    border-bottom: 1px solid var(--border-color);
  }
  .paired-json {
    height: 320px;
  }
}

/* ---- AI 图片生成（character）专属 ---- */
.field-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field-label-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 6px;
}

.field-hint {
  font-size: 11px;
  color: var(--text-tertiary);
  line-height: 1.5;
}

.ref-zone {
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  padding: 10px;
  background: var(--bg-tertiary);
  transition: border-color 0.15s, background 0.15s;
}

.ref-zone.drag-over {
  border-color: var(--accent-blue);
  background: var(--accent-blue-dim);
}

.ref-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 16px 8px;
  flex-wrap: wrap;
}

.ref-add-btn,
.ref-add-btn-sm {
  font-size: 12px;
  padding: 5px 10px;
}

.ref-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ref-card {
  display: grid;
  grid-template-columns: 60px 1fr auto;
  gap: 8px;
  align-items: center;
  padding: 6px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  width: 280px;
  max-width: 100%;
}

.ref-card img {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  background: var(--bg-tertiary);
}

.ref-card-meta {
  min-width: 0;
}

.ref-card-meta strong {
  display: block;
  font-size: 12px;
  color: var(--text-primary);
}

.ref-card-meta span {
  display: block;
  font-size: 11px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ref-card-actions {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ref-card-actions button {
  width: 22px;
  height: 22px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 11px;
  border-radius: 3px;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.ref-card-actions button:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.ref-card-actions button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.action-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.last-result {
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.last-result-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--text-secondary);
}

.last-result-head strong {
  color: var(--text-primary);
  font-size: 13px;
}

.last-result-body {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.last-result-body img {
  max-width: 360px;
  max-height: 360px;
  width: auto;
  height: auto;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  cursor: zoom-in;
  background: var(--bg-card);
}

.last-result-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Lightbox：图片放大 */
.image-lightbox {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.85);
  display: grid;
  place-items: center;
  padding: 32px;
  cursor: pointer;
}

.image-lightbox img {
  max-width: 92vw;
  max-height: 92vh;
  object-fit: contain;
  border-radius: var(--radius-md);
  cursor: default;
}

.image-lightbox-close {
  position: absolute;
  top: 18px;
  right: 24px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
}

.image-lightbox-close:hover {
  background: rgba(255, 255, 255, 0.22);
}
</style>
