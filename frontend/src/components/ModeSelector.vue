<template>
  <div class="mode-selector">
    <span
      v-for="mode in modes"
      :key="mode.value"
      :class="['mode-tag', { active: selected.includes(mode.value) }]"
      @click="toggle(mode.value)"
    >
      {{ mode.icon }} {{ mode.label }}
    </span>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const modes = [
  { value: 'transit', label: '公交/地铁', icon: '🚌' },
  { value: 'driving', label: '驾车', icon: '🚗' },
  { value: 'bicycling', label: '骑行', icon: '🚴' },
  { value: 'walking', label: '步行', icon: '🚶' },
  { value: 'train', label: '火车', icon: '🚄' },
]

const selected = ref(modes.map(m => m.value))

function toggle(value) {
  if (selected.value.includes(value)) {
    selected.value = selected.value.filter(v => v !== value)
  } else {
    selected.value.push(value)
  }
}

defineExpose({ selected })
</script>

<style scoped>
.mode-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0;
}
.mode-tag {
  padding: 6px 12px;
  border-radius: 16px;
  background: #f0f0f0;
  font-size: 14px;
  cursor: pointer;
}
.mode-tag.active {
  background: #1989fa;
  color: white;
}
</style>
