<template>
  <div class="task-management">
    <div class="header">
      <el-input
        v-model="newTaskInput"
        placeholder="在此输入任务信息，例如：今天晚上9点 完成毕业设计 学习 紧急重要 预计60分钟"
        class="task-input"
        @input="handleInputChange"
      />
      <el-input
        v-model="searchQuery"
        placeholder="搜索任务"
        style="width: 200px"
        class="ml-4"
      />
    </div>

    <!-- 实时预览区域 -->
    <el-card v-if="newTaskInput.trim()" class="preview-card">
      <template #header>
        <div class="preview-header">
          <span class="preview-title">任务预览</span>
          <el-button type="primary" size="small" @click="handleNewTaskInput">创建任务</el-button>
        </div>
      </template>
      <div class="preview-content">
        <el-form :model="previewForm" label-width="100px" size="small">
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="任务标题">
                <el-input v-model="previewForm.title" placeholder="请输入任务标题" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="任务描述">
                <el-input v-model="previewForm.description" type="textarea" :rows="1" placeholder="请输入任务描述" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="优先级">
                <el-select v-model="previewForm.priority" placeholder="请选择优先级">
                  <el-option
                    v-for="item in priorityOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="分类">
                <el-select v-model="previewForm.category" placeholder="请选择分类">
                  <el-option
                    v-for="item in categories"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="截止时间">
                <el-date-picker
                  v-model="previewForm.due_date"
                  type="datetime"
                  placeholder="选择截止时间"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="预计时长">
                <div class="duration-input-wrapper">
                  <el-input-number
                    v-model="previewForm.estimated_duration"
                    :min="0"
                    :step="30"
                    placeholder="请输入预计时长"
                  />
                  <span class="duration-unit">分钟</span>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>
    </el-card>

    <el-card class="mt-4">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>任务列表</span>
            <el-button 
              type="primary" 
              size="small" 
              class="ml-2"
              @click="filterTodayTasks"
            >
              今天
            </el-button>
          </div>
          <div class="filters">
            <el-button 
              type="danger" 
              size="small" 
              :disabled="!selectedTasks.length"
              @click="handleBatchDelete"
            >
              批量删除
            </el-button>
            <el-button 
              type="info" 
              size="small" 
              @click="resetFilters"
            >
              重置筛选
            </el-button>
            <el-select v-model="priorityFilter" placeholder="任务优先级" clearable style="width: 150px">
              <el-option
                v-for="item in priorityOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-select v-model="statusFilter" placeholder="任务状态" clearable style="width: 150px">
              <el-option
                v-for="item in statusOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-select v-model="categoryFilter" placeholder="任务分类" clearable style="width: 150px">
              <el-option
                v-for="item in categories"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </div>
        </div>
      </template>

      <el-table 
        :data="filteredTasks" 
        style="width: 100%" 
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="任务标题" min-width="150">
          <template #default="scope">
            <el-input
              v-if="scope.row.isEditing"
              v-model="scope.row.editingData.title"
              @blur="handleTaskUpdate(scope.row)"
              @keyup.enter="handleTaskUpdate(scope.row)"
            />
            <span 
              v-else 
              @click="startEditing(scope.row)" 
              :class="{
                'completed-task': scope.row.status === 'COMPLETED',
                'overdue-task': scope.row.status === 'OVERDUE'
              }"
              style="cursor: pointer"
            >
              {{ scope.row.title }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="备注" min-width="150">
          <template #default="scope">
            <el-input
              v-if="scope.row.isEditing"
              v-model="scope.row.editingData.description"
              type="textarea"
              :rows="1"
              @blur="handleTaskUpdate(scope.row)"
              @keyup.enter="handleTaskUpdate(scope.row)"
            />
            <span v-else @click="startEditing(scope.row)" style="cursor: pointer">{{ scope.row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="150">
          <template #default="scope">
            <el-select
              v-if="scope.row.isEditing"
              v-model="scope.row.editingData.priority"
              @blur="handleTaskUpdate(scope.row)"
              @keyup.enter="handleTaskUpdate(scope.row)"
              style="width: 100%"
            >
              <el-option
                v-for="item in priorityOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-tag v-else :type="getPriorityType(scope.row.priority)" @click="startEditing(scope.row)" style="cursor: pointer">
              {{ getPriorityLabel(scope.row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-select
              v-if="scope.row.isEditing"
              v-model="scope.row.editingData.status"
              @blur="handleTaskUpdate(scope.row)"
              @keyup.enter="handleTaskUpdate(scope.row)"
              style="width: 100%"
            >
              <el-option
                v-for="item in statusOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-tag v-else :type="getStatusType(scope.row.status)" @click="startEditing(scope.row)" style="cursor: pointer">
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category.name" label="分类" width="150">
          <template #default="scope">
            <el-select
              v-if="scope.row.isEditing"
              v-model="scope.row.editingData.category_id"
              @blur="handleTaskUpdate(scope.row)"
              @keyup.enter="handleTaskUpdate(scope.row)"
              style="width: 100%"
            >
              <el-option
                v-for="item in categories"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            <span v-else @click="startEditing(scope.row)" style="cursor: pointer">{{ scope.row.category?.name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="截止时间" width="200">
          <template #default="scope">
            <el-date-picker
              v-if="scope.row.isEditing"
              v-model="scope.row.editingData.due_date"
              type="datetime"
              @blur="handleTaskUpdate(scope.row)"
              @keyup.enter="handleTaskUpdate(scope.row)"
              style="width: 100%"
            />
            <span v-else @click="startEditing(scope.row)" style="cursor: pointer">{{ formatDateTime(scope.row.due_date) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="estimated_duration_display" label="预计时长" width="150">
          <template #default="scope">
            <el-input-number
              v-if="scope.row.isEditing"
              v-model="scope.row.editingData.estimated_duration"
              :min="1"
              @blur="handleTaskUpdate(scope.row)"
              @keyup.enter="handleTaskUpdate(scope.row)"
              style="width: 100%"
            />
            <span v-else @click="startEditing(scope.row)" style="cursor: pointer">{{ scope.row.estimated_duration_display }}分钟</span>
          </template>
        </el-table-column>
        <el-table-column prop="focused_duration" label="专注时长" width="120">
          <template #default="scope">
            {{ scope.row.focused_duration || 0 }}分钟
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="180">
          <template #default="scope">
            <el-progress 
              :percentage="scope.row.progress" 
              @change="(val) => updateTaskProgress(scope.row, val)"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建任务"
      width="50%"
    >
      <el-form
        ref="taskForm"
        :model="taskForm"
        :rules="taskRules"
        label-width="100px"
      >
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="taskForm.title" />
        </el-form-item>
        <el-form-item label="任务描述" prop="description">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="taskForm.priority">
            <el-option
              v-for="item in priorityOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="taskForm.category">
            <el-option
              v-for="item in categories"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="截止时间" prop="due_date">
          <el-date-picker
            v-model="taskForm.due_date"
            type="datetime"
            placeholder="选择截止时间"
          />
        </el-form-item>
        <el-form-item label="预计时长" prop="estimated_duration">
          <el-input-number
            v-model="taskForm.estimated_duration"
            :min="0"
            :step="30"
          />
          <span class="ml-2">分钟</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTask">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Task, TaskCategory } from '../types'
import { taskApi } from '../api/tasks'
import { getTaskCategories, createTaskCategory, updateTaskCategory, deleteTaskCategory } from '../api/settings'

// 数据定义
const tasks = ref<Task[]>([])
const categories = ref<TaskCategory[]>([])
const loading = ref(false)
const searchQuery = ref('')
const priorityFilter = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')
const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const taskForm = ref({
  title: '',
  description: '',
  priority: '',
  category: '',
  due_date: '',
  estimated_duration: 0,
  progress: 0
})

// 添加新的响应式变量
const newTaskInput = ref('')

// 添加预览表单数据
const previewForm = ref({
  title: '',
  description: '',
  priority: '',
  category: '',
  due_date: '',
  estimated_duration: 0
})

// 选项定义
const priorityOptions = [
  { value: 'URGENT_IMPORTANT', label: '紧急重要' },
  { value: 'NOT_URGENT_IMPORTANT', label: '重要不紧急' },
  { value: 'URGENT_NOT_IMPORTANT', label: '紧急不重要' },
  { value: 'NOT_URGENT_NOT_IMPORTANT', label: '不紧急不重要' }
]

const statusOptions = [
  { value: 'PENDING', label: '未完成' },
  { value: 'COMPLETED', label: '已完成' },
  { value: 'OVERDUE', label: '已逾期' }
]

// 表单验证规则
const taskRules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  due_date: [{ required: true, message: '请选择截止时间', trigger: 'change' }],
  estimated_duration: [{ required: true, message: '请输入预计时长', trigger: 'blur' }]
}

// 计算属性
const filteredTasks = computed(() => {
  // 先进行过滤
  const filtered = tasks.value.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesPriority = !priorityFilter.value || task.priority === priorityFilter.value
    const matchesStatus = !statusFilter.value || task.status === statusFilter.value
    const matchesCategory = !categoryFilter.value || task.category?.id === categoryFilter.value
    
    // 添加日期范围筛选
    let matchesDate = true
    if (dateRangeFilter.value) {
      const taskDate = new Date(task.due_date)
      matchesDate = taskDate >= dateRangeFilter.value[0] && taskDate < dateRangeFilter.value[1]
    }
    
    return matchesSearch && matchesPriority && matchesStatus && matchesCategory && matchesDate
  })

  // 然后进行排序
  return filtered.sort((a, b) => {
    // 1. 已完成的任务排在最下方
    if (a.status === 'COMPLETED' && b.status !== 'COMPLETED') return 1
    if (a.status !== 'COMPLETED' && b.status === 'COMPLETED') return -1
    
    // 2. 逾期任务排在最前面
    if (a.status === 'OVERDUE' && b.status !== 'OVERDUE') return -1
    if (a.status !== 'OVERDUE' && b.status === 'OVERDUE') return 1
    
    // 3. 未完成任务排在中间
    if (a.status === 'PENDING' && b.status !== 'PENDING') return -1
    if (a.status !== 'PENDING' && b.status === 'PENDING') return 1
    
    // 4. 相同状态的任务按截止时间排序
    const dateA = new Date(a.due_date).getTime()
    const dateB = new Date(b.due_date).getTime()
    return dateA - dateB
  })
})

// 添加编辑状态控制
const editingTask = ref(null)

// 开始编辑任务
const startEditing = (task) => {
  // 确保编辑时使用正确的数据
  task.isEditing = true
  task.editingData = {
    title: task.title,
    description: task.description || '',
    priority: task.priority,
    status: task.status,
    category_id: task.category?.id || '',
    due_date: task.due_date,
    estimated_duration: task.estimated_duration_display || task.estimated_duration
  }
  editingTask.value = task
}

// 结束编辑任务
const endEditing = (task) => {
  task.isEditing = false
  task.editingData = null
  editingTask.value = null
}

// 处理任务更新
const handleTaskUpdate = async (task) => {
  try {
    // 验证预计时长
    if (task.editingData.estimated_duration > 60) {
      await ElMessageBox.confirm(
        '单个任务最长为60分钟，请拆分任务！',
        '提示',
        {
          confirmButtonText: '了解',
          type: 'warning'
        }
      )
      // 重置编辑状态
      endEditing(task)
      return
    }

    await taskApi.updateTask(task.id, {
      title: task.editingData.title,
      description: task.editingData.description,
      priority: task.editingData.priority,
      status: task.editingData.status,
      category_id: task.editingData.category_id,
      due_date: task.editingData.due_date,
      estimated_duration: task.editingData.estimated_duration
    })
    
    // 更新成功后，重新获取任务列表以更新分类信息
    await fetchTasks()
    
    ElMessage.success('更新成功')
    endEditing(task)
  } catch (error) {
    console.error('更新任务失败:', error)
    ElMessage.error('更新失败')
  }
}

// 方法定义
const fetchTasks = async () => {
  try {
    loading.value = true
    const response = await taskApi.getTasks()
    tasks.value = response.map(task => ({
      ...task,
      isEditing: false
    }))
  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

const fetchCategories = async () => {
  try {
    const response = await getTaskCategories()
    categories.value = response
  } catch (error) {
    ElMessage.error('获取任务分类失败')
  }
}

const showCreateTaskDialog = () => {
  dialogType.value = 'create'
  taskForm.value = {
    title: '',
    description: '',
    priority: '',
    category: '',
    due_date: '',
    estimated_duration: 0,
    progress: 0
  }
  dialogVisible.value = true
}

const editTask = (task: Task) => {
  dialogType.value = 'edit'
  taskForm.value = { ...task }
  dialogVisible.value = true
}

const deleteTask = async (task: Task) => {
  try {
    await ElMessageBox.confirm('确定要删除这个任务吗？', '警告', {
      type: 'warning'
    })
    await taskApi.deleteTask(task.id)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 智能解析任务信息
const parseTaskInfo = (text: string) => {
  const result = {
    title: '',
    description: '',
    priority: 'NOT_URGENT_NOT_IMPORTANT', // 设置默认优先级
    category: '', // 这里将存储分类的ID
    due_date: '',
    estimated_duration: 0
  }

  // 解析优先级
  if (text.includes('紧急重要')) {
    result.priority = 'URGENT_IMPORTANT'
  } else if (text.includes('重要不紧急')) {
    result.priority = 'NOT_URGENT_IMPORTANT'
  } else if (text.includes('紧急不重要')) {
    result.priority = 'URGENT_NOT_IMPORTANT'
  } else if (text.includes('不紧急不重要')) {
    result.priority = 'NOT_URGENT_NOT_IMPORTANT'
  }

  // 解析时间
  const now = new Date()
  let targetDate = new Date()
  
  // 处理"今天晚上"或"明天晚上"的情况
  if (text.includes('晚上')) {
    const timeMatch = text.match(/(\d{1,2})[点:：](\d{1,2})?/)
    if (timeMatch) {
      const [_, hour, minute] = timeMatch
      const hourNum = parseInt(hour)
      // 确保时间是晚上（21:00）而不是早上（09:00）
      targetDate.setHours(hourNum >= 12 ? hourNum : hourNum + 12, minute ? parseInt(minute) : 0, 0, 0)
      
      // 处理"明天晚上"的情况
      if (text.includes('明天')) {
        targetDate.setDate(now.getDate() + 1)
      }
      
      // 如果时间已经过去，设置为明天
      if (targetDate < now) {
        targetDate.setDate(targetDate.getDate() + 1)
      }
      result.due_date = targetDate.toISOString()
    }
  } else {
    // 处理其他时间表达
    const timeRegex = /(今天|明天|后天|大后天)?\s*(\d{1,2})[点:：](\d{1,2})?/
    const timeMatch = text.match(timeRegex)
    if (timeMatch) {
      const [_, dayOffset, hour, minute] = timeMatch
      
      // 处理日期偏移
      if (dayOffset === '明天') {
        targetDate.setDate(now.getDate() + 1)
      } else if (dayOffset === '后天') {
        targetDate.setDate(now.getDate() + 2)
      } else if (dayOffset === '大后天') {
        targetDate.setDate(now.getDate() + 3)
      }

      // 设置时间
      const hourNum = parseInt(hour)
      targetDate.setHours(hourNum, minute ? parseInt(minute) : 0, 0, 0)

      // 如果时间已经过去，设置为明天
      if (targetDate < now) {
        targetDate.setDate(targetDate.getDate() + 1)
      }

      result.due_date = targetDate.toISOString()
    }
  }

  // 解析时长
  const durationRegex = /(\d+)\s*分钟/
  const durationMatch = text.match(durationRegex)
  if (durationMatch) {
    result.estimated_duration = parseInt(durationMatch[1])
  }

  // 提取分类（从任务内容中提取，并与后端分类对应）
  const categoryNames = categories.value.map(cat => cat.name)
  const categoryMatch = text.match(new RegExp(categoryNames.join('|')))
  if (categoryMatch) {
    const matchedCategory = categories.value.find(cat => cat.name === categoryMatch[0])
    if (matchedCategory) {
      result.category = matchedCategory.id
    }
  } else {
    // 如果没有识别到分类，使用默认分类（假设默认分类是第一个分类）
    if (categories.value.length > 0) {
      result.category = categories.value[0].id
    }
  }

  // 提取任务标题（取最后一个非时间、非优先级、非时长的内容）
  let title = text
    .replace(/(今天|明天|后天|大后天)?\s*\d{1,2}[点:：]\d{1,2}?/g, '') // 移除时间
    .replace(/(紧急重要|重要不紧急|紧急不重要|不紧急不重要)/g, '') // 移除优先级
    .replace(/\d+\s*分钟/g, '') // 移除时长
    .replace(new RegExp(categoryNames.join('|'), 'g'), '') // 移除分类
    .replace(/\s+/g, ' ') // 将多个空格替换为单个空格
    .replace(/预计/g, '') // 移除"预计"字样
    .trim()

  // 如果标题包含多个词，取最后一个作为标题
  const titleParts = title.split(' ')
  result.title = titleParts[titleParts.length - 1] || '未命名任务'

  return result
}

// 监听任务标题输入
watch(() => taskForm.value.title, (newTitle) => {
  if (newTitle && dialogType.value === 'create') {
    const parsedInfo = parseTaskInfo(newTitle)
    taskForm.value = {
      ...taskForm.value,
      ...parsedInfo
    }
  }
})

// 修改提交任务方法
const submitTask = async () => {
  try {
    // 验证表单
    if (!taskForm.value.title) {
      ElMessage.error('请输入任务标题')
      return
    }
    if (!taskForm.value.due_date) {
      ElMessage.error('请设置截止时间')
      return
    }
    if (taskForm.value.estimated_duration < 0) {
      ElMessage.error('预计时长不能为负数')
      return
    }

    const taskData = {
      ...taskForm.value,
      estimated_duration: taskForm.value.estimated_duration, // 允许为0
      category_id: taskForm.value.category || null
    }

    if (dialogType.value === 'create') {
      await taskApi.createTask(taskData)
      ElMessage.success('创建成功')
    } else {
      await taskApi.updateTask(taskForm.value.id, taskData)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    fetchTasks()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error(dialogType.value === 'create' ? '创建失败' : '更新失败')
  }
}

// 添加更新进度的方法
const updateTaskProgress = async (task: Task, progress: number) => {
  try {
    // 如果预计时长为0，则进度直接设为0
    if (task.estimated_duration === 0) {
      progress = 0
    }
    await taskApi.updateTaskProgress(task.id, progress)
    ElMessage.success('进度更新成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error('进度更新失败')
  }
}

// 工具函数
const getPriorityType = (priority: string) => {
  const types: Record<string, string> = {
    'URGENT_IMPORTANT': 'danger',      // 紧急重要 - 红色
    'URGENT_NOT_IMPORTANT': 'warning', // 紧急不重要 - 黄色
    'NOT_URGENT_IMPORTANT': 'success', // 重要不紧急 - 绿色
    'NOT_URGENT_NOT_IMPORTANT': 'info' // 不重要不紧急 - 灰色
  }
  return types[priority] || 'info'
}

const getPriorityLabel = (priority: string) => {
  const option = priorityOptions.find(opt => opt.value === priority)
  return option ? option.label : priority
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    'PENDING': 'warning',
    'COMPLETED': 'success',
    'OVERDUE': 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const option = statusOptions.find(opt => opt.value === status)
  return option ? option.label : status
}

const formatDateTime = (date: string) => {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 修改处理输入变化函数
const handleInputChange = () => {
  if (!newTaskInput.value.trim()) {
    previewForm.value = {
      title: '',
      description: '',
      priority: '',
      category: '',
      due_date: '',
      estimated_duration: 0
    }
    return
  }
  
  // 实时解析任务信息
  const parsedInfo = parseTaskInfo(newTaskInput.value)
  previewForm.value = parsedInfo
}

// 修改创建任务处理函数
const handleNewTaskInput = async () => {
  if (!newTaskInput.value.trim()) return
  
  // 检查必要字段
  if (!previewForm.value.title) {
    ElMessage.error('请输入任务标题')
    return
  }
  if (!previewForm.value.due_date) {
    ElMessage.error('请设置截止时间')
    return
  }
  
  // 检查预计时长
  if (previewForm.value.estimated_duration < 0) {
    ElMessage.error('预计时长不能为负数')
    return
  }
  
  if (previewForm.value.estimated_duration > 60) {
    await ElMessageBox.confirm(
      '单个任务不可超过60分钟，请重新拆解任务，以实现更好的时间管理',
      '提示',
      {
        confirmButtonText: '了解',
        type: 'warning'
      }
    )
    return
  }

  try {
    // 确保所有必要字段都有值，并转换数据格式
    const taskData = {
      title: previewForm.value.title,
      description: previewForm.value.description || '',
      priority: previewForm.value.priority || 'NOT_URGENT_NOT_IMPORTANT',
      category_id: previewForm.value.category || null,
      due_date: previewForm.value.due_date,
      estimated_duration: previewForm.value.estimated_duration, // 允许为0
      status: 'PENDING',
      progress: 0
    }
    
    await taskApi.createTask(taskData)
    ElMessage.success('创建成功')
    // 清空输入和预览
    newTaskInput.value = ''
    previewForm.value = {
      title: '',
      description: '',
      priority: 'NOT_URGENT_NOT_IMPORTANT',
      category: '',
      due_date: '',
      estimated_duration: 0
    }
    // 刷新任务列表
    fetchTasks()
  } catch (error) {
    console.error('创建任务失败:', error)
    ElMessage.error('创建失败')
  }
}

// 添加选中任务相关的变量和方法
const selectedTasks = ref<Task[]>([])

const handleSelectionChange = (selection: Task[]) => {
  selectedTasks.value = selection
}

const handleBatchDelete = async () => {
  if (!selectedTasks.value.length) return
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedTasks.value.length} 个任务吗？`, '警告', {
      type: 'warning'
    })
    
    // 批量删除任务
    await Promise.all(selectedTasks.value.map(task => taskApi.deleteTask(task.id)))
    
    ElMessage.success('批量删除成功')
    selectedTasks.value = []
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 添加筛选今天任务的方法
const filterTodayTasks = () => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  
  // 设置日期范围筛选
  dateRangeFilter.value = [today, tomorrow]
}

// 添加日期范围筛选变量
const dateRangeFilter = ref<[Date, Date] | null>(null)

// 添加重置筛选条件的方法
const resetFilters = () => {
  searchQuery.value = ''
  priorityFilter.value = ''
  statusFilter.value = ''
  categoryFilter.value = ''
  dateRangeFilter.value = null
}

// 生命周期钩子
onMounted(() => {
  fetchTasks()
  fetchCategories()
})
</script>

<style scoped>
.task-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.task-input {
  flex: 1;
  margin-right: 16px;
}

.mt-4 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
}

.filters {
  display: flex;
  gap: 16px;
  align-items: center;
}

.ml-4 {
  margin-left: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.el-select {
  margin-right: 16px;
}

.preview-card {
  margin-bottom: 20px;
  transition: all 0.3s ease;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px;
  border-bottom: 1px solid #ebeef5;
}

.preview-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.preview-content {
  padding: 20px;
}

.el-form-item {
  margin-bottom: 22px;
}

.el-form-item :deep(.el-form-item__content) {
  display: flex;
  align-items: center;
}

.el-input,
.el-select,
.el-date-picker,
.el-input-number {
  width: 100%;
}

.el-input-number {
  width: 100%;
}

.el-input-number .el-input__wrapper {
  width: 100%;
}

.el-date-picker {
  width: 100%;
}

.el-date-picker .el-input__wrapper {
  width: 100%;
}

.el-select {
  width: 100%;
}

.el-select .el-input__wrapper {
  width: 100%;
}

.el-textarea {
  width: 100%;
}

.el-textarea .el-textarea__inner {
  width: 100%;
  min-height: 32px;
  line-height: 1.5;
}

.duration-input-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px;
}

.duration-input-wrapper .el-input-number {
  flex: 1;
}

.duration-unit {
  color: #606266;
  font-size: 14px;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner),
:deep(.el-select__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  transition: all 0.3s;
}

:deep(.el-input__wrapper:hover),
:deep(.el-textarea__inner:hover),
:deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #409eff inset;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-textarea__inner:focus),
:deep(.el-select__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset;
}

.el-table .cell {
  cursor: pointer;
}

.el-table .cell:not(:last-child) {
  cursor: pointer;
}

.el-table .cell:last-child {
  cursor: default;
}

.completed-task {
  text-decoration: line-through;
  color: #909399;
}

.overdue-task {
  color: #f56c6c;
  font-weight: bold;
}

/* 添加编辑模式下的样式 */
.el-select,
.el-date-picker,
.el-input-number {
  width: 100%;
}

.el-input-number .el-input__wrapper {
  width: 100%;
}

.el-date-picker .el-input__wrapper {
  width: 100%;
}

.el-select .el-input__wrapper {
  width: 100%;
}

.duration-input-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
}

.duration-input-wrapper .el-input-number {
  flex: 1;
}

.duration-unit {
  margin-left: 8px;
  color: #606266;
}
</style>
