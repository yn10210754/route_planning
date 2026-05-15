<template>
  <div class="search-input">
    <van-field
      v-model="keyword"
      :label="label"
      :placeholder="placeholder"
      @update:model-value="onInput"
    />
    <van-list v-if="results.length > 0" class="results">
      <van-cell
        v-for="item in results"
        :key="item.name + item.lng"
        :title="item.name"
        :label="item.address"
        @click="select(item)"
      />
    </van-list>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchPoi } from '../api'

const props = defineProps({
  label: String,
  placeholder: String,
})

const emit = defineEmits(['select'])

const keyword = ref('')
const results = ref([])

// Debounce search: wait 300ms after user stops typing
let timer = null
function onInput() {
  clearTimeout(timer)
  timer = setTimeout(async () => {
    if (keyword.value.length < 2) {
      results.value = []
      return
    }
    results.value = await searchPoi(keyword.value)
  }, 300)
}

function select(item) {
  keyword.value = item.name
  results.value = []
  emit('select', item)
}
</script>

<style scoped>
.results {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #eee;
}
</style>
