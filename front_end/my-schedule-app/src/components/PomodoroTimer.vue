<template>
  <div class="pomodoro-container" @mousemove="showControls = true" @mouseleave="showControls = false">
    <div class="task-info">
      <h2>当前专注于：{{ taskName }}</h2>
    </div>

    <div class="tomatoes-container">
      <div v-for="(tomato, index) in tomatoes" :key="index" class="tomato-wrapper">
        <div class="tomato">
          <div 
            class="tomato-fill"
            :style="{ height: `${getTomatoFillHeight(index)}%` }"
          ></div>
        </div>
      </div>
    </div>

    <div class="timer-display">
      <span class="time">{{ formatTime }}</span>
    </div>

    <div v-show="showControls" class="controls">
      <el-button type="danger" @click="stopTimer">停止计时</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  taskName: string
}>()

const emit = defineEmits<{
  (e: 'stop'): void
}>()

const showControls = ref(false)
const tomatoes = ref([1, 2, 3, 4])
const remainingTime = ref(25 * 60) // 25分钟
let timer: number | null = null

const formatTime = computed(() => {
  const minutes = Math.floor(remainingTime.value / 60)
  const seconds = remainingTime.value % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

const getTomatoFillHeight = (index: number) => {
  const totalTime = 25 * 60 // 25分钟
  const elapsedTime = totalTime - remainingTime.value
  const progress = (elapsedTime / totalTime) * 100
  const tomatoProgress = Math.max(0, Math.min(100, progress - (index * 25)))
  return tomatoProgress
}

const updateTimer = () => {
  if (remainingTime.value > 0) {
    remainingTime.value--
  } else {
    stopTimer()
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
.pomodoro-container {
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

.tomatoes-container {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
}

.tomato-wrapper {
  width: 100px;
  height: 120px;
  position: relative;
}

.tomato {
  width: 100%;
  height: 100%;
  background-color: #e0e0e0;
  border-radius: 50% 50% 45% 45%;
  position: relative;
  overflow: hidden;
}

.tomato-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: #f56c6c;
  transition: height 0.3s ease;
}

.timer-display {
  font-size: 3rem;
  font-weight: bold;
  color: #409EFF;
  margin-top: 2rem;
}

.controls {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  transition: opacity 0.3s;
}
</style> 