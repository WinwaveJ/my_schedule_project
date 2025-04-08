<template>
  <div class="app-settings">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>应用设置</span>
        </div>
      </template>

      <!-- 番茄钟设置 -->
      <el-form
        ref="pomodoroForm"
        :model="pomodoroSettings"
        :rules="pomodoroRules"
        label-width="180px"
        class="settings-form"
      >
        <h3>番茄钟设置</h3>
        <el-form-item label="番茄钟时长（分钟）" prop="pomodoro_duration">
          <el-input-number
            v-model="pomodoroSettings.pomodoro_duration"
            :min="1"
            :max="60"
            @change="handlePomodoroChange"
          />
        </el-form-item>

        <el-form-item label="短休息时长（分钟）" prop="short_break_duration">
          <el-input-number
            v-model="pomodoroSettings.short_break_duration"
            :min="1"
            :max="30"
            @change="handlePomodoroChange"
          />
        </el-form-item>

        <el-form-item label="长休息时长（分钟）" prop="long_break_duration">
          <el-input-number
            v-model="pomodoroSettings.long_break_duration"
            :min="1"
            :max="60"
            @change="handlePomodoroChange"
          />
        </el-form-item>

        <el-form-item label="长休息间隔" prop="long_break_interval">
          <el-input-number
            v-model="pomodoroSettings.long_break_interval"
            :min="1"
            :max="10"
            @change="handlePomodoroChange"
          />
        </el-form-item>
      </el-form>

      <!-- 任务分类管理 -->
      <div class="task-categories">
        <h3>任务分类管理</h3>
        <div class="category-header">
          <el-input
            v-model="newCategoryName"
            placeholder="输入新分类名称"
            style="width: 200px"
            @keyup.enter="handleAddCategory"
          />
          <el-button type="primary" @click="handleAddCategory">添加分类</el-button>
        </div>

        <el-table :data="categories" style="width: 100%">
          <el-table-column prop="name" label="分类名称" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button
                type="danger"
                link
                :disabled="row.name === '默认'"
                @click="handleDeleteCategory(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 编辑分类对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑分类"
      width="30%"
    >
      <el-form :model="editingCategory" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="editingCategory.name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveCategory">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  getAppSettings,
  updateAppSettings,
  getTaskCategories,
  createTaskCategory,
  updateTaskCategory,
  deleteTaskCategory,
  type AppSettings,
  type TaskCategory
} from '@/api/settings'

const pomodoroForm = ref<FormInstance>()
const pomodoroSettings = ref<AppSettings>({
    id: 0,
    pomodoro_duration: 25,
    short_break_duration: 5,
    long_break_duration: 15,
    long_break_interval: 4,
    created_at: '',
    updated_at: ''
})
const categories = ref<TaskCategory[]>([])
const newCategoryName = ref('')
const editDialogVisible = ref(false)
const editingCategory = ref<TaskCategory | null>(null)

const pomodoroRules = {
  pomodoro_duration: [{ required: true, message: '请输入番茄钟时长', trigger: 'blur' }],
  short_break_duration: [{ required: true, message: '请输入短休息时长', trigger: 'blur' }],
  long_break_duration: [{ required: true, message: '请输入长休息时长', trigger: 'blur' }],
  long_break_interval: [{ required: true, message: '请输入长休息间隔', trigger: 'blur' }]
}

// 获取应用设置
const fetchAppSettings = async () => {
  try {
    const response = await getAppSettings()
    console.log('应用设置响应数据:', response)
    // 后端会返回一个列表，但每个用户只有一个设置
    if (response && response.length > 0) {
      // 使用解构赋值确保所有属性都被正确复制
      pomodoroSettings.value = {
        id: response[0].id,
        pomodoro_duration: response[0].pomodoro_duration,
        short_break_duration: response[0].short_break_duration,
        long_break_duration: response[0].long_break_duration,
        long_break_interval: response[0].long_break_interval,
        created_at: response[0].created_at,
        updated_at: response[0].updated_at
      }
      console.log('当前应用设置:', pomodoroSettings.value)
    }
  } catch (error) {
    console.error('获取应用设置失败:', error)
    ElMessage.error('获取应用设置失败')
  }
}

// 获取任务分类
const fetchCategories = async () => {
  try {
    const response = await getTaskCategories()
    console.log('任务分类响应数据:', response)
    if (response) {
      // 使用map确保所有属性都被正确复制
      categories.value = response.map(category => ({
        id: category.id,
        name: category.name,
        created_at: category.created_at,
        updated_at: category.updated_at
      }))
      console.log('当前任务分类列表:', categories.value)
    }
  } catch (error) {
    console.error('获取任务分类失败:', error)
    ElMessage.error('获取任务分类失败')
  }
}

// 更新番茄钟设置
const handlePomodoroChange = async () => {
  try {
    console.log('更新番茄钟设置:', pomodoroSettings.value)
    await updateAppSettings(pomodoroSettings.value.id, pomodoroSettings.value)
    ElMessage.success('番茄钟设置更新成功')
  } catch (error) {
    console.error('更新番茄钟设置失败:', error)
    ElMessage.error('更新番茄钟设置失败')
  }
}

// 添加任务分类
const handleAddCategory = async () => {
  if (!newCategoryName.value.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  try {
    const response = await createTaskCategory({ name: newCategoryName.value.trim() })
    console.log('添加分类响应数据:', response)
    ElMessage.success('添加成功')
    newCategoryName.value = ''
    fetchCategories()
  } catch (error) {
    console.error('添加分类失败:', error)
    ElMessage.error('添加分类失败')
  }
}

// 编辑任务分类
const handleEditCategory = (category: TaskCategory) => {
  editingCategory.value = { ...category }
  editDialogVisible.value = true
}

// 保存任务分类
const handleSaveCategory = async () => {
  if (!editingCategory.value) return
  try {
    const response = await updateTaskCategory(editingCategory.value.id, {
      name: editingCategory.value.name
    })
    console.log('更新分类响应数据:', response)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    fetchCategories()
  } catch (error) {
    console.error('更新分类失败:', error)
    ElMessage.error('更新分类失败')
  }
}

// 删除任务分类
const handleDeleteCategory = async (category: TaskCategory) => {
  if (category.name === '默认') {
    ElMessage.warning('默认分类不能删除')
    return
  }
  try {
    await ElMessageBox.confirm('确定要删除该分类吗？', '提示', {
      type: 'warning'
    })
    await deleteTaskCategory(category.id)
    console.log('删除分类成功:', category.id)
    ElMessage.success('删除成功')
    fetchCategories()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除分类失败:', error)
      ElMessage.error('删除分类失败')
    }
  }
}

onMounted(() => {
  fetchAppSettings()
  fetchCategories()
})
</script>

<style scoped>
.app-settings {
  padding: 20px;
}

.settings-card {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-form {
  margin-bottom: 30px;
}

.task-categories {
  margin-top: 30px;
}

.category-header {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

h3 {
  margin: 20px 0;
  color: #303133;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
