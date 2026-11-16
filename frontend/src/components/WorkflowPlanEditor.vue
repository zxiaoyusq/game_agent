<script setup>
import { workflowSteps } from '../data/gameWorkflow.js'
const props = defineProps({
  modelValue: Object,
  skills: { type: Array, default: () => [] },
  section: { type: String, default: 'all' },
})
const emit = defineEmits(['update:modelValue'])
function change(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
function changeStage(id, key, value) {
  change('stages', {
    ...props.modelValue.stages,
    [id]: { ...props.modelValue.stages[id], [key]: value },
  })
}
</script>

<template>
  <section v-if="modelValue" class="plan-editor" aria-label="统一制作需求">
    <template v-if="section === 'all' || section === 'art'">
      <h3>让游戏有自己的样子</h3>
      <label>
        美术需求与修改范围
        <textarea
          :value="modelValue.art_requirements"
          rows="6"
          maxlength="12000"
          placeholder="参考哪款游戏、保留哪些贴图、修改哪些部分、配色与动画要求…"
          @input="change('art_requirements', $event.target.value)"
        />
      </label>
      <p>
        美术参考文件在下方「参考资料路径」或公司游戏参考中选择。以上要求会提供给全部阶段。
      </p>
    </template>
    <details
      v-if="section === 'all' || section === 'advanced'"
      class="advanced-plan"
    >
      <summary>
        高级配置：四阶段提示词与 Skill（已预填，无需逐阶段输入）
      </summary>
      <div v-for="step in workflowSteps" :key="step.id" class="stage-plan">
        <h4>{{ step.name }}</h4>
        <label>
          预置提示词
          <textarea
            :value="modelValue.stages[step.id].prompt"
            rows="4"
            maxlength="6000"
            @input="changeStage(step.id, 'prompt', $event.target.value)"
          />
        </label>
        <label>
          Skill 选择方式
          <select
            :value="modelValue.stages[step.id].skill_mode"
            @change="changeStage(step.id, 'skill_mode', $event.target.value)"
          >
            <option value="auto">自动选择，可补充指定 Skill</option>
            <option value="manual">仅使用指定 Skill</option>
          </select>
        </label>
        <details>
          <summary>
            指定 Skill · {{ modelValue.stages[step.id].skill_paths.length }} 项
          </summary>
          <label v-for="skill in skills" :key="skill.path" class="skill-option">
            <input
              type="checkbox"
              :checked="
                modelValue.stages[step.id].skill_paths.includes(skill.path)
              "
              @change="
                changeStage(
                  step.id,
                  'skill_paths',
                  $event.target.checked
                    ? [...modelValue.stages[step.id].skill_paths, skill.path]
                    : modelValue.stages[step.id].skill_paths.filter(
                        (path) => path !== skill.path,
                      ),
                )
              "
            />
            <span>
              {{ skill.name }}
              <small>{{ skill.path }}</small>
            </span>
          </label>
        </details>
      </div>
    </details>
    <template v-if="section === 'all' || section === 'delivery'">
      <h3>做好之后，分享给全世界</h3>
      <label class="publish-choice">
        <input
          type="checkbox"
          :checked="modelValue.auto_publish"
          @change="change('auto_publish', $event.target.checked)"
        />
        测试通过后自动发布独立试玩链接
      </label>
      <label v-if="modelValue.auto_publish">
        访问路径名称（留空自动生成唯一地址）
        <input
          :value="modelValue.publish_slug"
          maxlength="64"
          pattern="[a-z0-9][a-z0-9-]{1,62}[a-z0-9]"
          placeholder="例如 ludo-classic-replay-02"
          @input="change('publish_slug', $event.target.value.trim())"
        />
      </label>
    </template>
  </section>
</template>

<style scoped>
.plan-editor {
  border-top: 1px solid #e0e5dc;
  padding-top: 16px;
  margin-top: 20px;
}
.plan-editor p {
  color: #687262;
  font-size: 13px;
  line-height: 1.6;
}
.plan-editor label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 12px 0;
}
.plan-editor textarea,
.plan-editor select,
.plan-editor input:not([type='checkbox']) {
  box-sizing: border-box;
  width: 100%;
  padding: 10px;
  border: 1px solid #ccd6c5;
  border-radius: 5px;
  font: inherit;
}
.advanced-plan {
  margin: 20px 0;
}
.advanced-plan summary {
  cursor: pointer;
  line-height: 1.6;
}
.stage-plan {
  border-bottom: 1px solid #e0e5dc;
  padding: 14px 0;
}
.plan-editor .publish-choice,
.plan-editor .skill-option {
  flex-direction: row;
  align-items: flex-start;
}
.skill-option small {
  display: block;
  overflow-wrap: anywhere;
  color: #687262;
}
.skill-option input {
  flex-shrink: 0;
  margin-top: 4px;
}
</style>
