<template>
  <div class="activity-management">
    <div class="header">
      <el-button type="primary" @click="showCreateActivityDialog">
        创建活动
      </el-button>
      <el-input
        v-model="searchQuery"
        placeholder="搜索活动"
        style="width: 200px"
        class="ml-4"
      />
    </div>

    <el-card class="mt-4">
      <template #header>
        <div class="card-header">
          <span>活动列表</span>
          <div class="filters">
            <el-select v-model="statusFilter" placeholder="状态" clearable>
              <el-option
                v-for="item in statusOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-select v-model="timerTypeFilter" placeholder="计时类型" clearable>
              <el-option
                v-for="item in timerTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="filteredActivities" style="width: 100%">
        <el-table-column prop="task.title" label="所属任务" min-width="180" />
        <el-table-column prop="description" label="活动描述" min-width="250" show-overflow-tooltip>
          <template #default="scope">
            {{ scope.row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="timer_type" label="计时类型" width="100" align="center">
          <template #default="scope">
            {{ getTimerTypeLabel(scope.row.timer_type) }}
          </template>
        </el-table-column>
        <el-table-column label="计时器" min-width="280" align="center">
          <template #default="scope">
            <div v-if="scope.row.timer_type === 'POMODORO'">
              <div>已完成番茄钟: {{ scope.row.pomodoro_count }}</div>
              <div v-if="scope.row.status === 'IN_PROGRESS'">
                <div>剩余时间: {{ formatDuration(remainingTimes[scope.row.id]) }}</div>
                <el-button-group>
                  <el-button
                    size="small"
                    type="primary"
                    @click="startPomodoro(scope.row)"
                  >
                    开始番茄钟
                  </el-button>
                  <el-button
                    size="small"
                    type="success"
                    @click="startBreak(scope.row)"
                  >
                    开始休息
                  </el-button>
                </el-button-group>
              </div>
            </div>
            <div v-else>
              <div v-if="scope.row.status === 'IN_PROGRESS'">
                已用时间: {{ formatDuration(elapsedTimes[scope.row.id]) }}
              </div>
              <el-button-group>
                <el-button
                  size="small"
                  type="primary"
                  @click="toggleStopwatch(scope.row)"
                >
                  {{ scope.row.status === 'IN_PROGRESS' ? '停止' : '开始' }}
                </el-button>
              </el-button-group>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="scope">
            <el-button-group>
              <el-button
                size="small"
                type="danger"
                @click="deleteActivity(scope.row)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建活动对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建活动"
      width="50%"
    >
      <el-form
        ref="activityForm"
        :model="activityForm"
        :rules="activityRules"
        label-width="100px"
      >
        <el-form-item label="所属任务" prop="task">
          <el-select v-model="activityForm.task">
            <el-option
              v-for="task in tasks"
              :key="task.id"
              :label="task.title"
              :value="task.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="活动描述" prop="description">
          <el-input
            v-model="activityForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入活动描述"
          />
        </el-form-item>
        <el-form-item label="计时类型" prop="timer_type">
          <el-select v-model="activityForm.timer_type">
            <el-option
              v-for="item in timerTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitActivity">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Activity, Task } from '@/types'

// 数据定义
const activities = ref<Activity[]>([])
const tasks = ref<Task[]>([])
const searchQuery = ref('')
const statusFilter = ref('')
const timerTypeFilter = ref('')
const dialogVisible = ref(false)
const activityForm = ref({
  task: '',
  description: '',
  timer_type: 'POMODORO'
})

// 添加计时器相关的状态
const activeTimers = ref<Record<number, NodeJS.Timer>>({})
const remainingTimes = ref<Record<number, number>>({})
const elapsedTimes = ref<Record<number, number>>({})

// 选项定义
const statusOptions = [
  { value: 'PENDING', label: '未开始' },
  { value: 'IN_PROGRESS', label: '进行中' },
  { value: 'COMPLETED', label: '已完成' },
  { value: 'PAUSED', label: '已暂停' },
  { value: 'CANCELLED', label: '已取消' }
]

const timerTypeOptions = [
  { value: 'POMODORO', label: '番茄钟' },
  { value: 'STOPWATCH', label: '正计时' }
]

// 表单验证规则
const activityRules = {
  task: [{ required: true, message: '请选择所属任务', trigger: 'change' }],
  timer_type: [{ required: true, message: '请选择计时类型', trigger: 'change' }]
}

// 计算属性
const filteredActivities = computed(() => {
  return activities.value.filter(activity => {
    const matchesSearch = activity.task.title.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesStatus = !statusFilter.value || activity.status === statusFilter.value
    const matchesTimerType = !timerTypeFilter.value || activity.timer_type === timerTypeFilter.value
    return matchesSearch && matchesStatus && matchesTimerType
  })
})

// 方法定义
const showCreateActivityDialog = () => {
  activityForm.value = {
    task: '',
    description: '',
    timer_type: 'POMODORO'
  }
  dialogVisible.value = true
}

const fetchActivities = async () => {
  try {
    const response = await activityApi.getActivities()
    activities.value = response
    // 初始化计时器状态
    activities.value.forEach(activity => {
      if (activity.status === 'IN_PROGRESS') {
        startTimer(activity)
      }
    })
  } catch (error) {
    ElMessage.error('获取活动列表失败')
  }
}

const startTimer = (activity: Activity) => {
  if (activeTimers.value[activity.id]) {
    clearInterval(activeTimers.value[activity.id])
  }

  const timer = setInterval(() => {
    if (activity.timer_type === 'POMODORO') {
      const remaining = activity.get_remaining_time()
      if (remaining) {
        remainingTimes.value[activity.id] = remaining.total_seconds()
      }
    } else {
      const elapsed = activity.get_elapsed_time()
      if (elapsed) {
        elapsedTimes.value[activity.id] = elapsed.total_seconds()
      }
    }
  }, 1000)

  activeTimers.value[activity.id] = timer
}

const stopTimer = (activityId: number) => {
  if (activeTimers.value[activityId]) {
    clearInterval(activeTimers.value[activityId])
    delete activeTimers.value[activityId]
    delete remainingTimes.value[activityId]
    delete elapsedTimes.value[activityId]
  }
}

const startPomodoro = async (activity: Activity) => {
  try {
    await activityApi.startPomodoro(activity.id)
    startTimer(activity)
    ElMessage.success('番茄钟已开始')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const startBreak = async (activity: Activity) => {
  try {
    await activityApi.startBreak(activity.id)
    startTimer(activity)
    ElMessage.success('休息已开始')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const toggleStopwatch = async (activity: Activity) => {
  try {
    if (activity.status === 'IN_PROGRESS') {
      await activityApi.stopStopwatch(activity.id)
      stopTimer(activity.id)
      ElMessage.success('计时已停止')
    } else {
      await activityApi.startStopwatch(activity.id)
      startTimer(activity)
      ElMessage.success('计时已开始')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteActivity = async (activity: Activity) => {
  try {
    await ElMessageBox.confirm('确定要删除这个活动吗？', '警告', {
      type: 'warning'
    })
    await activityApi.deleteActivity(activity.id)
    stopTimer(activity.id)
    ElMessage.success('删除成功')
    fetchActivities()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const submitActivity = async () => {
  try {
    // 调用创建API
    // await axios.post('/api/activities', activityForm.value)
    ElMessage.success('创建成功')
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

// 工具函数
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    'PENDING': 'info',
    'IN_PROGRESS': 'primary',
    'COMPLETED': 'success',
    'PAUSED': 'warning',
    'CANCELLED': 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const option = statusOptions.find(opt => opt.value === status)
  return option ? option.label : status
}

const getTimerTypeLabel = (type: string) => {
  const option = timerTypeOptions.find(opt => opt.value === type)
  return option ? option.label : type
}

const formatDuration = (duration: number | undefined) => {
  if (!duration) return '00:00:00'
  const hours = Math.floor(duration / 3600)
  const minutes = Math.floor((duration % 3600) / 60)
  const seconds = Math.floor(duration % 60)
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

// 添加组件卸载时的清理
onUnmounted(() => {
  // 清理所有计时器
  Object.values(activeTimers.value).forEach(timer => {
    clearInterval(timer)
  })
})
</script>

<style scoped>
.activity-management {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.mt-4 {
  margin-top: 20px;
}
.ml-4 {
  margin-left: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filters {
  display: flex;
  gap: 16px;
}
</style>
