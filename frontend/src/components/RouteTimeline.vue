<template>
  <div class="timeline">
    <div v-for="(seg, idx) in segments" :key="idx" class="segment">
      <div class="time">
        <span v-if="seg.departure">{{ seg.departure }}</span>
        <span v-else>--:--</span>
      </div>
      <div class="dot" :class="seg.mode">{{ modeIcon(seg.mode) }}</div>
      <div class="info">
        <div class="mode">{{ modeLabel(seg.mode) }}</div>
        <div class="route">{{ seg.from_name }} → {{ seg.to_name }}</div>
        <div class="meta">{{ formatDuration(seg.duration) }} · ¥{{ seg.cost }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  segments: Array,
})

function modeIcon(mode) {
  const map = { transit: '🚌', driving: '🚗', bicycling: '🚴', walking: '🚶', train: '🚄' }
  return map[mode] || '➡️'
}

function modeLabel(mode) {
  const map = { transit: '公交/地铁', driving: '驾车', bicycling: '骑行', walking: '步行', train: '火车' }
  return map[mode] || mode
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}
</script>

<style scoped>
.timeline { padding: 8px; }
.segment {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}
.time { width: 48px; font-size: 13px; color: #666; }
.dot { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #e8f4ff; }
.info { flex: 1; }
.mode { font-weight: bold; }
.meta { font-size: 13px; color: #888; margin-top: 4px; }
</style>
