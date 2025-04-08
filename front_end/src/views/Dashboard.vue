<template>
    <div class="dashboard">
        <el-row :gutter="20">
            <!-- 任务统计卡片 -->
            <el-col :span="6" v-for="(stat, index) in taskStats" :key="index">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>{{ stat.title }}</span>
                        </div>
                    </template>
                    <div class="stat-value">{{ stat.value }}</div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="20" class="mt-4">
            <!-- 今日待办任务 -->
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>今日待办</span>
                        </div>
                    </template>
<div class="quadrant-container">
    <div class="quadrant">
        <div class="quadrant-title">紧急重要</div>
        <div class="task-grid" @dragover.prevent @drop="handleDrop($event, 'URGENT_IMPORTANT')">
            <div v-for="task in urgentImportantTasks" :key="task.id"
                class="task-box urgent-important"
                :class="{ 'overdue-task': task.status === 'OVERDUE' }" draggable="true"
                @dragstart="handleDragStart($event, task)" @dragend="handleDragEnd">
                {{ task.title }}
            </div>
        </div>
    </div>
    <div class="quadrant">
        <div class="quadrant-title">重要不紧急</div>
        <div class="task-grid" @dragover.prevent @drop="handleDrop($event, 'NOT_URGENT_IMPORTANT')">
            <div v-for="task in importantNotUrgentTasks" :key="task.id"
                class="task-box important-not-urgent"
                :class="{ 'overdue-task': task.status === 'OVERDUE' }" draggable="true"
                @dragstart="handleDragStart($event, task)" @dragend="handleDragEnd">
                {{ task.title }}
            </div>
        </div>
    </div>
    <div class="quadrant">
        <div class="quadrant-title">紧急不重要</div>
        <div class="task-grid" @dragover.prevent @drop="handleDrop($event, 'URGENT_NOT_IMPORTANT')">
            <div v-for="task in urgentNotImportantTasks" :key="task.id"
                class="task-box urgent-not-important"
                :class="{ 'overdue-task': task.status === 'OVERDUE' }" draggable="true"
                @dragstart="handleDragStart($event, task)" @dragend="handleDragEnd">
                {{ task.title }}
            </div>
        </div>
    </div>
    <div class="quadrant">
        <div class="quadrant-title">不紧急不重要</div>
        <div class="task-grid" @dragover.prevent
            @drop="handleDrop($event, 'NOT_URGENT_NOT_IMPORTANT')">
            <div v-for="task in notUrgentNotImportantTasks" :key="task.id"
                class="task-box not-urgent-not-important"
                :class="{ 'overdue-task': task.status === 'OVERDUE' }" draggable="true"
                @dragstart="handleDragStart($event, task)" @dragend="handleDragEnd">
                {{ task.title }}
            </div>
        </div>
    </div>
</div>
                </el-card>
            </el-col>

            <!-- 番茄钟统计 -->
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>番茄钟使用情况</span>
                        </div>
                    </template>
                    <div ref="pomodoroChart" style="height: 300px"></div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="20" class="mt-4">
            <!-- 活动趋势图 -->
            <el-col :span="24">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>活动趋势</span>
                        </div>
                    </template>
                    <div ref="activityChart" style="height: 300px"></div>
                </el-card>
            </el-col>
        </el-row>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import type { Task } from '@/types'
import api from '@/api/config'

// 数据定义
const taskStats = ref([
    { title: '已完成任务', value: 0 },
    { title: '待完成任务', value: 0 },
    { title: '已逾期任务', value: 0 },
    { title: '今日番茄钟', value: 0 }
])

const todayTasks = ref<Task[]>([])
const pomodoroChart = ref<HTMLElement>()
const activityChart = ref<HTMLElement>()

// 添加计算属性来分类任务
const urgentImportantTasks = computed(() => {
    return todayTasks.value.filter(task => task.priority === 'URGENT_IMPORTANT')
})

const importantNotUrgentTasks = computed(() => {
    return todayTasks.value.filter(task => task.priority === 'NOT_URGENT_IMPORTANT')
})

const urgentNotImportantTasks = computed(() => {
    return todayTasks.value.filter(task => task.priority === 'URGENT_NOT_IMPORTANT')
})

const notUrgentNotImportantTasks = computed(() => {
    return todayTasks.value.filter(task => task.priority === 'NOT_URGENT_NOT_IMPORTANT')
})

// 添加拖拽相关的变量和方法
const draggedTask = ref<Task | null>(null)

const handleDragStart = (event: DragEvent, task: Task) => {
    draggedTask.value = task
    if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move'
        event.dataTransfer.setData('text/plain', task.id.toString())
    }
}

const handleDragEnd = () => {
    draggedTask.value = null
}

const handleDrop = async (event: DragEvent, newPriority: string) => {
    event.preventDefault()

    if (!draggedTask.value || draggedTask.value.priority === newPriority) {
        return
    }

    try {
        // 调用API更新任务优先级
        await api.patch(`/tasks/${draggedTask.value.id}/`, {
            priority: newPriority
        })

        // 更新本地数据
        const taskIndex = todayTasks.value.findIndex(t => t.id === draggedTask.value?.id)
        if (taskIndex !== -1) {
            todayTasks.value[taskIndex] = {
                ...todayTasks.value[taskIndex],
                priority: newPriority
            }
        }

        // 重新获取仪表盘数据以更新统计信息
        await fetchDashboardData()

        ElMessage.success('任务优先级更新成功')
    } catch (error) {
        console.error('更新任务优先级失败:', error)
        ElMessage.error('更新任务优先级失败')
    } finally {
        draggedTask.value = null
    }
}

// 初始化图表
onMounted(async () => {
    await fetchDashboardData()
    initCharts()
})

// 获取仪表盘数据
const fetchDashboardData = async () => {
    try {
        const response = await api.get('/stats/summary/')
        console.log('获取到的数据:', response) // 添加日志输出

        if (!response || !response.task_stats || !response.activity_stats) {
            throw new Error('数据格式不正确')
        }

        const { task_stats, activity_stats } = response

        // 更新任务统计
        console.log('任务统计数据:', {
            total_tasks: task_stats.total_tasks,
            completed_tasks: task_stats.completed_tasks,
            overdue_tasks: task_stats.overdue_tasks,
            pending_tasks: (task_stats.total_tasks || 0) - (task_stats.completed_tasks || 0) - (task_stats.overdue_tasks || 0)
        })
        taskStats.value = [
            { title: '已完成任务', value: task_stats.completed_tasks || 0 },
            { title: '待完成任务', value: (task_stats.total_tasks || 0) - (task_stats.completed_tasks || 0) - (task_stats.overdue_tasks || 0) },
            { title: '已逾期任务', value: task_stats.overdue_tasks || 0 },
            { title: '今日番茄钟', value: Math.round((activity_stats.total_pomodoro_duration || 0) / 60) }
        ]

        // 更新今日待办任务
        const todayResponse = await api.get('/tasks/')
        console.log('获取到的任务数据:', todayResponse) // 添加日志输出

        if (Array.isArray(todayResponse)) {
            const today = new Date()
            today.setHours(0, 0, 0, 0)
            const tomorrow = new Date(today)
            tomorrow.setDate(tomorrow.getDate() + 1)

            todayTasks.value = todayResponse.filter((task: Task) => {
                const taskDate = new Date(task.due_date)
                return taskDate >= today && taskDate < tomorrow && task.status !== 'COMPLETED'
            })
        }

        // 更新图表数据
        updateCharts(response)
    } catch (error: any) {
        console.error('获取数据失败:', error)
        ElMessage.error(error.message || '获取数据失败')
    }
}

// 更新图表数据
const updateCharts = (data: any) => {
    try {
        // 番茄钟使用情况图表
        const pomodoro = echarts.init(pomodoroChart.value!)
        pomodoro.setOption({
            title: { text: '番茄钟使用情况' },
            tooltip: {
                trigger: 'axis',
                formatter: '{b}: {c} 分钟'
            },
            xAxis: {
                type: 'category',
                data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            },
            yAxis: {
                type: 'value',
                name: '分钟',
                minInterval: 1
            },
            series: [{
                name: '番茄钟时长',
                data: data.activity_stats?.daily_pomodoro_duration || [0, 0, 0, 0, 0, 0, 0],
                type: 'line',
                smooth: true,
                areaStyle: {
                    opacity: 0.3
                }
            }]
        })

        // 活动趋势图表
        const activity = echarts.init(activityChart.value!)
        activity.setOption({
            title: { text: '活动趋势' },
            tooltip: {
                trigger: 'axis',
                formatter: '{b}: {c} 分钟'
            },
            legend: {
                data: ['番茄钟', '正计时']
            },
            xAxis: {
                type: 'category',
                data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            },
            yAxis: {
                type: 'value',
                name: '分钟',
                minInterval: 1
            },
            series: [
                {
                    name: '番茄钟',
                    type: 'bar',
                    data: data.activity_stats?.daily_pomodoro_duration || [0, 0, 0, 0, 0, 0, 0],
                    itemStyle: {
                        color: '#409EFF'
                    }
                },
                {
                    name: '正计时',
                    type: 'bar',
                    data: data.activity_stats?.daily_stopwatch_duration || [0, 0, 0, 0, 0, 0, 0],
                    itemStyle: {
                        color: '#67C23A'
                    }
                }
            ]
        })
    } catch (error) {
        console.error('更新图表失败:', error)
    }
}

// 工具函数
const getPriorityType = (priority: string) => {
    const types: Record<string, string> = {
        'URGENT_IMPORTANT': 'danger',
        'NOT_URGENT_IMPORTANT': 'warning',
        'URGENT_NOT_IMPORTANT': 'info',
        'NOT_URGENT_NOT_IMPORTANT': 'success'
    }
    return types[priority] || 'info'
}

const formatDateTime = (date: string) => {
    return new Date(date).toLocaleString()
}
</script>

<style scoped>
.dashboard {
    padding: 20px;
}

.mt-4 {
    margin-top: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.stat-value {
    font-size: 24px;
    font-weight: bold;
    text-align: center;
    color: #409EFF;
}

.quadrant-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 16px;
    height: 300px;
}

.quadrant {
    display: flex;
    flex-direction: column;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    padding: 12px;
    transition: all 0.3s;
}

.quadrant-title {
    font-weight: bold;
    margin-bottom: 8px;
    color: #606266;
}

.task-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 6px;
    overflow-y: auto;
    min-height: 100px;
    padding: 6px;
    border-radius: 4px;
    transition: all 0.3s;
}

.task-box {
    padding: 6px;
    border-radius: 4px;
    font-size: 11px;
    text-align: center;
    word-break: break-all;
    cursor: move;
    transition: all 0.3s;
    user-select: none;
    line-height: 1.2;
    max-height: 40px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

.task-box:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.urgent-important {
    background-color: #fef0f0;
    color: #f56c6c;
    border: 1px solid #fde2e2;
}

.important-not-urgent {
    background-color: #f0f9eb;
    color: #67c23a;
    border: 1px solid #e1f3d8;
}

.urgent-not-important {
    background-color: #fdf6ec;
    color: #e6a23c;
    border: 1px solid #faecd8;
}

.not-urgent-not-important {
    background-color: #f4f4f5;
    color: #909399;
    border: 1px solid #e9e9eb;
}

/* 添加拖动时的样式 */
.task-box[draggable="true"]:active {
    opacity: 0.5;
    cursor: grabbing;
}

.quadrant.drag-over {
    background-color: rgba(64, 158, 255, 0.1);
    border-color: #409eff;
}

.overdue-task {
    font-weight: bold;
    color: #f56c6c !important;
    font-size: 13px !important;
}
</style>
