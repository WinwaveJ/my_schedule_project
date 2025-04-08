<template>
  <div class="stopwatch-container" @mousemove="showControls = true" @mouseleave="showControls = false">
    <div class="task-info">
      <h2>当前专注于：{{ taskName }}</h2>
    </div>
    
    <div class="timer-display">
      <div class="time-block">
        <span class="number">{{ hours }}</span>
        <span class="label">时</span>
      </div>
      <div class="time-block">
        <span class="number">{{ minutes }}</span>
        <span class="label">分</span>
      </div>
      <div class="time-block">
        <span class="number">{{ seconds }}</span>
        <span class="label">秒</span>
      </div>
    </div>

    <div v-show="showControls" class="controls">
      <el-button type="danger" @click="stopTimer">停止计时</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  taskName: string
}>()

const emit = defineEmits<{
  (e: 'stop'): void
}>()

const showControls = ref(false)
const hours = ref(0)
const minutes = ref(0)
const seconds = ref(0)
let timer: number | null = null

const updateTimer = () => {
  seconds.value++
  if (seconds.value >= 60) {
    seconds.value = 0
    minutes.value++
  }
  if (minutes.value >= 60) {
    minutes.value = 0
    hours.value++
  }
}

const startTimer = () => {
  timer = window.setInterval(updateTimer, 1000)
}

const stopTimer = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  emit('stop')
}

onMounted(() => {
  startTimer()
})

onUnmounted(() => {
  stopTimer()
})
</script>

<style scoped>
.stopwatch-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.task-info {
  margin-bottom: 2rem;
  text-align: center;
}

.timer-display {
  display: flex;
  gap: 2rem;
}

.time-block {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.number {
  font-size: 4rem;
  font-weight: bold;
  color: #409EFF;
}

.label {
  font-size: 1rem;
  color: #909399;
}

.controls {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  transition: opacity 0.3s;
}
</style> 