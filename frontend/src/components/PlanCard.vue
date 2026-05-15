<template>
  <div class="plan-card">
    <div class="header">
      <span class="total-time">{{ formatDuration(plan.total_duration) }}</span>
      <span class="total-cost">¥{{ plan.total_cost }}</span>
    </div>
    <RouteTimeline :segments="plan.segments" />
  </div>
</template>

<script setup>
import RouteTimeline from './RouteTimeline.vue'

const props = defineProps({ plan: Object })

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}
</script>

<style scoped>
.plan-card {
  margin: 12px;
  padding: 12px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.header {
  display: flex;
  justify-content: space-between;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
}
.total-cost { color: #ff6600; }
</style>
