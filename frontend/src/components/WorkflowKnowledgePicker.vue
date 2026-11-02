<script setup>
import { computed, ref } from 'vue'
import {
  knowledgeLibraries,
  resolveKnowledgeReferences,
  searchWorkflowKnowledge,
} from '../data/workflowKnowledge.js'

const props = defineProps({
  selection: { type: Object, required: true },
  stageIndex: { type: Number, required: true },
  disabled: Boolean,
})
const emit = defineEmits(['update:selection'])
const previewId = ref('')
const selected = computed(() =>
  resolveKnowledgeReferences(props.selection.selectedIds),
)
const results = computed(() =>
  searchWorkflowKnowledge(props.selection, props.stageIndex),
)

function update(field, value) {
  if (!props.disabled)
    emit('update:selection', { ...props.selection, [field]: value })
}

function toggle(id) {
  const ids = props.selection.selectedIds
  update(
    'selectedIds',
    ids.includes(id) ? ids.filter((value) => value !== id) : [...ids, id],
  )
}

// 检索只展示候选项；只有勾选或主动批量引用的资料会随需求发送。
function addResults() {
  update('selectedIds', [
    ...new Set([
      ...props.selection.selectedIds,
      ...results.value.map((item) => item.id),
    ]),
  ])
}
</script>

<template>
  <section class="knowledge-picker" aria-label="知识库引用与检索">
    <details>
      <summary>
        <strong>▧ 知识库引用与检索</strong
        ><span>已选 {{ selected.length }} 项 · 本地示例库</span>
      </summary>
      <div class="knowledge-controls">
        <label
          >检索方式<select
            :value="selection.mode"
            :disabled="disabled"
            @change="update('mode', $event.target.value)"
          >
            <option value="recommended">本阶段推荐</option>
            <option value="keyword">关键词检索</option>
          </select></label
        >
        <label
          >检索范围<select
            :value="selection.library"
            :disabled="disabled"
            @change="update('library', $event.target.value)"
          >
            <option>全部知识库</option>
            <option v-for="library in knowledgeLibraries" :key="library">
              {{ library }}
            </option>
          </select></label
        >
        <label class="search-label"
          >搜索知识<input
            :value="selection.query"
            :disabled="disabled"
            placeholder="搜索标题、标签或正文，如：新手引导"
            @input="update('query', $event.target.value)"
        /></label>
      </div>
      <div class="results-heading">
        <span
          >{{ results.length }} 项{{
            selection.mode === 'recommended' ? '阶段相关资料' : '检索结果'
          }}</span
        ><button :disabled="disabled || !results.length" @click="addResults">
          引用当前结果
        </button>
      </div>
      <div class="knowledge-results">
        <article
          v-for="item in results"
          :key="item.id"
          :class="{ selected: selection.selectedIds.includes(item.id) }"
        >
          <div class="knowledge-row">
            <label
              ><input
                type="checkbox"
                :checked="selection.selectedIds.includes(item.id)"
                :disabled="disabled"
                @change="toggle(item.id)"
              /><span
                ><strong>{{ item.title }}</strong
                ><small
                  >{{ item.library }} · {{ item.tags.join(' / ') }}</small
                ></span
              ></label
            ><button
              :aria-expanded="previewId === item.id"
              @click="previewId = previewId === item.id ? '' : item.id"
            >
              {{ previewId === item.id ? '收起' : '预览' }}
            </button>
          </div>
          <p v-if="previewId === item.id" class="knowledge-preview">
            {{ item.content }}
          </p>
        </article>
        <p v-if="!results.length" class="knowledge-empty">
          没有匹配资料。可以调整关键词、检索范围或切换为关键词检索。
        </p>
      </div>
      <p class="knowledge-hint">
        仅勾选的资料会用于下一轮对话，检索结果不会自动引用。
      </p>
    </details>
    <div v-if="selected.length" class="selected-references">
      <span v-for="item in selected" :key="item.id"
        >{{ item.title
        }}<button
          :disabled="disabled"
          :aria-label="`移除引用：${item.title}`"
          @click="toggle(item.id)"
        >
          ×
        </button></span
      ><button
        class="clear-references"
        :disabled="disabled"
        @click="update('selectedIds', [])"
      >
        清空引用
      </button>
    </div>
    <p v-else class="knowledge-hint">
      可展开选择参考资料；未选择时仅使用项目上下文。
    </p>
  </section>
</template>

<style scoped>
.knowledge-picker {
  margin: 0 22px 16px;
  border: 1px solid #dce5ef;
  border-radius: 7px;
  padding: 12px;
  background: #fbfcfe;
}
summary {
  cursor: pointer;
  font-size: 11px;
  color: #526987;
}
summary strong {
  font-weight: 600;
}
summary > span {
  font-size: 9px;
  color: #8090a7;
  margin-left: 14px;
}
.knowledge-controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 16px 0;
}
.knowledge-controls label {
  font-size: 10px;
  color: #708099;
}
.knowledge-controls select,
.knowledge-controls input {
  width: 100%;
  display: block;
  border: 1px solid #d5dfed;
  border-radius: 4px;
  background: white;
  padding: 8px;
  font: 11px var(--font-ui);
  color: #526987;
  margin-top: 6px;
}
.search-label {
  grid-column: 1 / -1;
}
.results-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 10px;
  color: #7c8fa5;
  margin-bottom: 8px;
}
button {
  color: #426cac;
  font-size: 10px;
}
.knowledge-results {
  max-height: 270px;
  overflow-y: auto;
}
article {
  border: 1px solid #e1e7ef;
  border-radius: 5px;
  background: white;
  padding: 10px;
  margin-bottom: 7px;
}
article.selected {
  border-color: #b3c8eb;
  background: #f2f6fd;
}
.knowledge-row,
.knowledge-row label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.knowledge-row {
  justify-content: space-between;
}
.knowledge-row label {
  flex: 1;
  cursor: pointer;
  min-width: 0;
}
.knowledge-row input {
  accent-color: #3565dc;
  margin-top: 3px;
}
.knowledge-row strong {
  font-size: 11px;
  font-weight: 500;
  color: #4a607d;
}
.knowledge-row small {
  display: block;
  font-size: 9px;
  color: #8795a9;
  margin-top: 5px;
}
.knowledge-row button {
  flex-shrink: 0;
}
.knowledge-preview {
  font-size: 11px;
  line-height: 1.9;
  color: #637791;
  margin: 12px 0 0 23px;
  border-top: 1px solid #e1e7ef;
  padding-top: 10px;
}
.knowledge-hint,
.knowledge-empty {
  font-size: 10px;
  color: #8392a7;
  margin-top: 10px;
  line-height: 1.8;
}
.knowledge-empty {
  padding: 15px;
  text-align: center;
}
.selected-references {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}
.selected-references > span {
  display: flex;
  gap: 7px;
  align-items: center;
  font-size: 9px;
  color: #607b9b;
  background: #eaf0f9;
  padding: 4px 8px;
  border-radius: 4px;
}
.selected-references > span button {
  font-size: 14px;
}
.clear-references {
  padding: 5px;
}
button:disabled,
select:disabled,
input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
:is(button, summary, input, select):focus-visible {
  outline: 2px solid #799af1;
  outline-offset: 3px;
}
@media (max-width: 550px) {
  .knowledge-picker {
    margin: 0 16px 14px;
  }
  summary > span {
    display: block;
    margin: 5px 0 0 15px;
  }
  .knowledge-controls {
    gap: 8px;
  }
}
</style>
