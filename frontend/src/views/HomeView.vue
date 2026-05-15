<template>
  <div class="home">
    <h2>路线规划</h2>

    <SearchInput ref="fromRef" label="起点" placeholder="输入出发地点" @select="loc => fromLoc = loc" />

    <div v-for="(stop, idx) in stops" :key="idx" class="stop-row">
      <SearchInput :label="`途经点${idx + 1}`" placeholder="输入途经地点" @select="loc => stops[idx] = loc" />
      <van-button size="small" type="danger" @click="removeStop(idx)">删除</van-button>
    </div>

    <van-button size="small" type="primary" @click="addStop">+ 添加途经点</van-button>

    <SearchInput ref="toRef" label="终点" placeholder="输入目的地点" @select="loc => toLoc = loc" />

    <ModeSelector ref="modeRef" />

    <van-button type="primary" block @click="submit">规划路线</van-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SearchInput from '../components/SearchInput.vue'
import ModeSelector from '../components/ModeSelector.vue'

const fromLoc = ref(null)
const toLoc = ref(null)
const stops = ref([])
const modeRef = ref(null)

function addStop() {
  if (stops.value.length < 3) {
    stops.value.push(null)
  }
}

function removeStop(idx) {
  stops.value.splice(idx, 1)
}

const emit = defineEmits(['submit'])

function submit() {
  if (!fromLoc.value || !toLoc.value) {
    alert('请输入起点和终点')
    return
  }

  // Build segments: from -> stop1 -> stop2 -> ... -> to
  const points = [fromLoc.value, ...stops.value.filter(Boolean), toLoc.value]
  const segments = []
  for (let i = 0; i < points.length - 1; i++) {
    segments.push({
      from_loc: points[i],
      to_loc: points[i + 1],
      modes: modeRef.value.selected,
    })
  }

  emit('submit', {
    departure_time: new Date().toISOString(),
    segments,
    optimize_by: 'duration',
  })
}
</script>

<style scoped>
.stop-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
