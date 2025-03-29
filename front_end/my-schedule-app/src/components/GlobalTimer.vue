<template>
  <div v-if="shouldShowTimer" class="global-timer">
    <el-button-group>
      <el-button type="primary" @click="showStopwatchDialog">
        <el-icon><Timer /></el-icon>
        正计时
      </el-button>
      <el-button type="success" @click="showPomodoroDialog">
        <el-icon><Timer /></el-icon>
        番茄钟
      </el-button>
    </el-button-group>

    <!-- 正计时全屏对话框 -->
    <el-dialog
      v-model="stopwatchVisible"
      fullscreen
      :show-close="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="stopwatch-container">
        <div class="task-title">正在专注于：{{ selectedTask?.title }}</div>
        <div class="timer-display">{{ formatTime(stopwatchTime) }}</div>
        <div class="timer-controls">
          <el-button type="danger" @click="stopStopwatch">结束计时</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 番茄钟全屏对话框 -->
    <el-dialog
      v-model="pomodoroVisible"
      fullscreen
      :show-close="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="pomodoro-container">
        <div class="task-title">正在专注于：{{ selectedTask?.title }}</div>
        <div class="tomatoes">
          <div v-for="i in 4" :key="i" class="tomato">
            <div class="tomato-fill" :style="{ height: `${(i - 1) * 25 + (currentPomodoroTime / 25) * 25}%` }"></div>
          </div>
        </div>
        <div class="timer-display">{{ formatTime(pomodoroTime) }}</div>
        <div class="timer-controls">
          <el-button type="danger" @click="stopPomodoro">结束计时</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 选择任务对话框 -->
    <el-dialog
      v-model="taskSelectVisible"
      title="选择任务"
      width="500px"
    >
      <el-form :model="taskForm" label-width="80px">
        <el-form-item label="任务">
          <el-select v-model="taskForm.taskId" placeholder="请选择任务">
            <el-option
              v-for="task in availableTasks"
              :key="task.id"
              :label="task.title"
              :value="task.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="taskSelectVisible = false">取消</el-button>
          <el-button type="primary" @click="startTimer">开始</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Timer } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'
import api from '@/api/config'

const route = useRoute()

// 判断是否应该显示计时器
const shouldShowTimer = computed(() => {
  const path = route.path
  return !['/login', '/register', '/forgot-password'].includes(path)
})

// 状态变量
const stopwatchVisible = ref(false)
const pomodoroVisible = ref(false)
const taskSelectVisible = ref(false)
const selectedTask = ref<any>(null)
const availableTasks = ref<any[]>([])
const taskForm = ref({
  taskId: ''
})
const currentTimerType = ref<'stopwatch' | 'pomodoro'>('stopwatch')

// 计时器变量
const stopwatchTime = ref(0)
const pomodoroTime = ref(25 * 60) // 25分钟
const currentPomodoroTime = ref(0)
let stopwatchInterval: any = null
let pomodoroInterval: any = null

// 获取可用任务
const fetchAvailableTasks = async () => {
  try {
    const response = await api.get('/tasks/')
    availableTasks.value = response.filter((task: any) => task.status !== 'COMPLETED')
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  }
}

// 显示正计时对话框
const showStopwatchDialog = () => {
  taskForm.value.taskId = ''
  currentTimerType.value = 'stopwatch'
  taskSelectVisible.value = true
  fetchAvailableTasks()
}

// 显示番茄钟对话框
const showPomodoroDialog = () => {
  taskForm.value.taskId = ''
  currentTimerType.value = 'pomodoro'
  taskSelectVisible.value = true
  fetchAvailableTasks()
}

// 开始计时
const startTimer = async () => {
  if (!taskForm.value.taskId) {
    ElMessage.warning('请选择任务')
    return
  }

  selectedTask.value = availableTasks.value.find(t => t.id === taskForm.value.taskId)
  taskSelectVisible.value = false

  try {
    // 创建活动记录
    const activityData = {
      task_id: taskForm.value.taskId,
      status: 'IN_PROGRESS',
      start_time: new Date().toISOString()
    }
    const endpoint = currentTimerType.value === 'stopwatch' ? '/stopwatch-activities/' : '/pomodoro-activities/'
    const response = await api.post(endpoint, activityData)

    if (currentTimerType.value === 'stopwatch') {
      stopwatchVisible.value = true
      startStopwatch(response.id)
    } else {
      pomodoroVisible.value = true
      startPomodoro(response.id)
    }
  } catch (error) {
    ElMessage.error('创建活动失败')
  }
}

// 开始正计时
const startStopwatch = (activityId: number) => {
  stopwatchTime.value = 0
  stopwatchInterval = setInterval(() => {
    stopwatchTime.value++
    // 超过一小时自动停止
    if (stopwatchTime.value >= 3600) {
      stopStopwatch()
    }
  }, 1000)
}

// 开始番茄钟
const startPomodoro = (activityId: number) => {
  currentPomodoroTime.value = 0
  pomodoroInterval = setInterval(() => {
    currentPomodoroTime.value++
    pomodoroTime.value = 25 * 60 - currentPomodoroTime.value
    if (currentPomodoroTime.value >= 25 * 60) {
      stopPomodoro()
    }
  }, 1000)
}

// 停止正计时
const stopStopwatch = async () => {
  clearInterval(stopwatchInterval)
  stopwatchVisible.value = false
  try {
    await api.patch(`/stopwatch-activities/${selectedTask.value.id}/`, {
      status: 'COMPLETED',
      duration: stopwatchTime.value
    })
    ElMessage.success('计时结束')
  } catch (error) {
    ElMessage.error('更新活动状态失败')
  }
}

// 停止番茄钟
const stopPomodoro = async () => {
  clearInterval(pomodoroInterval)
  pomodoroVisible.value = false
  try {
    await api.patch(`/pomodoro-activities/${selectedTask.value.id}/`, {
      status: 'COMPLETED',
      pomodoro_count: Math.ceil(currentPomodoroTime.value / (25 * 60))
    })
    ElMessage.success('番茄钟结束')
  } catch (error) {
    ElMessage.error('更新活动状态失败')
  }
}

// 格式化时间
const formatTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

// 组件卸载时清理定时器
onUnmounted(() => {
  clearInterval(stopwatchInterval)
  clearInterval(pomodoroInterval)
})
</script>

<style scoped>
.global-timer {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.stopwatch-container,
.pomodoro-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
}

.task-title {
  font-size: 24px;
  margin-bottom: 40px;
  color: #409EFF;
}

.timer-display {
  font-size: 72px;
  font-weight: bold;
  margin: 40px 0;
  font-family: monospace;
}

.timer-controls {
  margin-top: 40px;
}

.tomatoes {
  display: flex;
  gap: 20px;
  margin: 40px 0;
}

.tomato {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #f56c6c;
  position: relative;
  overflow: hidden;
}

.tomato-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: #67c23a;
  transition: height 1s linear;
}
</style> 