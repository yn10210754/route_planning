<template>
  <div class="result">
    <van-nav-bar title="规划结果" left-text="返回" @click-left="emit('back')" />
    <van-tabs v-model:active="activeTab">
      <van-tab title="最快到达">
        <PlanCard v-for="(plan, idx) in fastestPlans" :key="idx" :plan="plan" />
      </van-tab>
      <van-tab title="最省费用">
        <PlanCard v-for="(plan, idx) in cheapestPlans" :key="idx" :plan="plan" />
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import PlanCard from '../components/PlanCard.vue'

const props = defineProps({ plans: Array })
const emit = defineEmits(['back'])

const activeTab = ref(0)
const fastestPlans = computed(() => [...props.plans].sort((a, b) => a.total_duration - b.total_duration))
const cheapestPlans = computed(() => [...props.plans].sort((a, b) => a.total_cost - b.total_cost))
</script>
