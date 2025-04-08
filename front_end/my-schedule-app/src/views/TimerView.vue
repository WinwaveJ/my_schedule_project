<template>
  <div class="timer-view">
    <div class="timer-buttons">
      <el-button type="primary" @click="showTaskSelection('stopwatch')">正计时</el-button>
      <el-button type="success" @click="showTaskSelection('pomodoro')">番茄计时</el-button>
    </div>

    <TaskSelectionDialog
      v-model="taskSelectionVisible"
      @confirm="handleTaskSelected"
    />

    <StopwatchTimer
      v-if="showStopwatch && selectedTask"
      :task-name="selectedTask"
      @stop="handleTimerStop"
    />

    <PomodoroTimer
      v-if="showPomodoro && selectedTask"
      :task-name="selectedTask"
      @stop="handleTimerStop"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import TaskSelectionDialog from '../components/TaskSelectionDialog.vue'
import StopwatchTimer from '../components/StopwatchTimer.vue'
import PomodoroTimer from '../components/PomodoroTimer.vue'

const taskSelectionVisible = ref(false)
const selectedTask = ref('')
const showStopwatch = ref(false)
const showPomodoro = ref(false)
const currentTimerType = ref<'stopwatch' | 'pomodoro' | null>(null)

const showTaskSelection = (type: 'stopwatch' | 'pomodoro') => {
  currentTimerType.value = type
  taskSelectionVisible.value = true
}

const handleTaskSelected = (task: string) => {
  selectedTask.value = task
  if (currentTimerType.value === 'stopwatch') {
    showStopwatch.value = true
    showPomodoro.value = false
  } else {
    showStopwatch.value = false
    showPomodoro.value = true
  }
}

const handleTimerStop = () => {
  showStopwatch.value = false
  showPomodoro.value = false
  selectedTask.value = ''
  currentTimerType.value = null
}
</script>

<style scoped>
.timer-view {
  position: relative;
  min-height: 100vh;
  padding: 20px;
}

.timer-buttons {
  position: fixed;
  bottom: 20px;
  right: 20px;
  display: flex;
  gap: 10px;
  z-index: 100;
}
</style> 