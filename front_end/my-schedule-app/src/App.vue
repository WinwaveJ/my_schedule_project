<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed } from 'vue'
import GlobalTimer from '@/components/GlobalTimer.vue'

const route = useRoute()
const showLayout = computed(() => route.path !== '/login')
</script>

<template>
  <div class="app-container">
    <router-view></router-view>
    <GlobalTimer />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>
