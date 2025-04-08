<template>
  <div class="reminder-management">
    <div class="header">
      <el-button type="primary" @click="showCreateReminderDialog">
        创建提醒
      </el-button>
      <el-input
        v-model="searchQuery"
        placeholder="搜索提醒"
        style="width: 200px"
        class="ml-4"
      />
    </div>

    <el-card class="mt-4">
      <template #header>
        <div class="card-header">
          <span>提醒列表</span>
          <div class="filters">
            <el-select v-model="typeFilter" placeholder="提醒类型" clearable>
              <el-option
                v-for="item in typeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-select v-model="methodFilter" placeholder="提醒方式" clearable>
              <el-option
                v-for="item in methodOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="filteredReminders" style="width: 100%">
        <el-table-column prop="title" label="提醒标题" />
        <el-table-column prop="content" label="提醒内容" />
        <el-table-column prop="reminder_type" label="提醒类型" width="120">
          <template #default="scope">
            {{ getTypeLabel(scope.row.reminder_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="reminder_method" label="提醒方式" width="120">
          <template #default="scope">
            {{ getMethodLabel(scope.row.reminder_method) }}
          </template>
        </el-table-column>
        <el-table-column prop="reminder_time" label="提醒时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.reminder_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              @change="toggleReminderStatus(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button-group>
              <el-button
                size="small"
                type="danger"
                @click="deleteReminder(scope.row)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建提醒对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建提醒"
      width="50%"
    >
      <el-form
        ref="reminderForm"
        :model="reminderForm"
        :rules="reminderRules"
        label-width="100px"
      >
        <el-form-item label="提醒标题" prop="title">
          <el-input v-model="reminderForm.title" />
        </el-form-item>
        <el-form-item label="提醒内容" prop="content">
          <el-input
            v-model="reminderForm.content"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="提醒类型" prop="reminder_type">
          <el-select v-model="reminderForm.reminder_type">
            <el-option
              v-for="item in typeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="提醒方式" prop="reminder_method">
          <el-select v-model="reminderForm.reminder_method">
            <el-option
              v-for="item in methodOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="提醒时间" prop="reminder_time">
          <el-date-picker
            v-model="reminderForm.reminder_time"
            type="datetime"
            placeholder="选择提醒时间"
          />
        </el-form-item>
        <el-form-item label="周期性提醒" prop="is_periodic">
          <el-switch v-model="reminderForm.is_periodic" />
        </el-form-item>
        <template v-if="reminderForm.is_periodic">
          <el-form-item label="周期类型" prop="periodic_type">
            <el-select v-model="reminderForm.periodic_type">
              <el-option
                v-for="item in periodicTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="周期间隔" prop="periodic_interval">
            <el-input-number v-model="reminderForm.periodic_interval" :min="1" />
          </el-form-item>
          <el-form-item label="结束时间" prop="periodic_end_date">
            <el-date-picker
              v-model="reminderForm.periodic_end_date"
              type="datetime"
              placeholder="选择结束时间"
            />
          </el-form-item>
        </template>
        <el-form-item label="重复提醒" prop="repeat_reminder">
          <el-switch v-model="reminderForm.repeat_reminder" />
        </el-form-item>
        <template v-if="reminderForm.repeat_reminder">
          <el-form-item label="重复间隔" prop="repeat_interval">
            <el-input-number v-model="reminderForm.repeat_interval" :min="1" />
            <span class="ml-2">分钟</span>
          </el-form-item>
          <el-form-item label="最大重复次数" prop="max_repeats">
            <el-input-number v-model="reminderForm.max_repeats" :min="1" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitReminder">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Reminder } from '@/types'

// 数据定义
const reminders = ref<Reminder[]>([])
const searchQuery = ref('')
const typeFilter = ref('')
const methodFilter = ref('')
const dialogVisible = ref(false)
const reminderForm = ref({
  title: '',
  content: '',
  reminder_type: '',
  reminder_method: '',
  reminder_time: '',
  is_periodic: false,
  periodic_type: '',
  periodic_interval: 1,
  periodic_end_date: '',
  repeat_reminder: false,
  repeat_interval: 30,
  max_repeats: 3
})

// 选项定义
const typeOptions = [
  { value: 'TASK_DUE', label: '任务截止' },
  { value: 'ACTIVITY_START', label: '活动开始' },
  { value: 'CUSTOM', label: '自定义' },
  { value: 'PERIODIC', label: '周期性' }
]

const methodOptions = [
  { value: 'EMAIL', label: '邮件提醒' },
  { value: 'BROWSER', label: '浏览器通知' }
]

const periodicTypeOptions = [
  { value: 'DAILY', label: '每日' },
  { value: 'WEEKLY', label: '每周' },
  { value: 'MONTHLY', label: '每月' }
]

// 表单验证规则
const reminderRules = {
  title: [{ required: true, message: '请输入提醒标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入提醒内容', trigger: 'blur' }],
  reminder_type: [{ required: true, message: '请选择提醒类型', trigger: 'change' }],
  reminder_method: [{ required: true, message: '请选择提醒方式', trigger: 'change' }],
  reminder_time: [{ required: true, message: '请选择提醒时间', trigger: 'change' }]
}

// 计算属性
const filteredReminders = computed(() => {
  return reminders.value.filter(reminder => {
    const matchesSearch = reminder.title.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesType = !typeFilter.value || reminder.reminder_type === typeFilter.value
    const matchesMethod = !methodFilter.value || reminder.reminder_method === methodFilter.value
    return matchesSearch && matchesType && matchesMethod
  })
})

// 方法定义
const showCreateReminderDialog = () => {
  reminderForm.value = {
    title: '',
    content: '',
    reminder_type: '',
    reminder_method: '',
    reminder_time: '',
    is_periodic: false,
    periodic_type: '',
    periodic_interval: 1,
    periodic_end_date: '',
    repeat_reminder: false,
    repeat_interval: 30,
    max_repeats: 3
  }
  dialogVisible.value = true
}

const toggleReminderStatus = async (reminder: Reminder) => {
  try {
    // 调用更新状态API
    // await axios.put(`/api/reminders/${reminder.id}`, { is_active: reminder.is_active })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
  }
}

const deleteReminder = async (reminder: Reminder) => {
  try {
    await ElMessageBox.confirm('确定要删除这个提醒吗？', '警告', {
      type: 'warning'
    })
    // 调用删除API
    // await axios.delete(`/api/reminders/${reminder.id}`)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const submitReminder = async () => {
  try {
    // 调用创建API
    // await axios.post('/api/reminders', reminderForm.value)
    ElMessage.success('创建成功')
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

// 工具函数
const getTypeLabel = (type: string) => {
  const option = typeOptions.find(opt => opt.value === type)
  return option ? option.label : type
}

const getMethodLabel = (method: string) => {
  const option = methodOptions.find(opt => opt.value === method)
  return option ? option.label : method
}

const formatDateTime = (date: string) => {
  return new Date(date).toLocaleString()
}
</script>

<style scoped>
.reminder-management {
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
