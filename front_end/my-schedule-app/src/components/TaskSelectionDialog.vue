<template>
  <el-dialog
    v-model="dialogVisible"
    title="选择任务"
    width="30%"
    :before-close="handleClose"
  >
    <el-form>
      <el-form-item label="选择任务">
        <el-select v-model="selectedTask" placeholder="请选择任务">
          <el-option
            label="完成毕业设计"
            value="完成毕业设计"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleConfirm">
          确认
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', task: string): void
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const selectedTask = ref('')

const handleClose = () => {
  dialogVisible.value = false
}

const handleConfirm = () => {
  if (selectedTask.value) {
    emit('confirm', selectedTask.value)
    handleClose()
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 