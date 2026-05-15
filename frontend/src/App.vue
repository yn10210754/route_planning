<template>
  <HomeView v-if="page === 'home'" @submit="onSubmit" />
  <ResultView v-else :plans="plans" @back="page = 'home'" />
</template>

<script setup>
import { ref } from 'vue'
import HomeView from './views/HomeView.vue'
import ResultView from './views/ResultView.vue'
import { planRoute } from './api'

const page = ref('home')
const plans = ref([])

async function onSubmit(payload) {
  plans.value = await planRoute(payload)
  page.value = 'result'
}
</script>
