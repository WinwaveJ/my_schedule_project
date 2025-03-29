<template>
  <div class="user-info">
    <el-dropdown trigger="hover" @command="handleCommand">
      <span class="user-name">
        {{ username }}
        <el-icon class="el-icon--right"><arrow-down /></el-icon>
      </span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="logout">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')

const handleCommand = (command: string) => {
  if (command === 'logout') {
    // 清除本地存储的token
    localStorage.removeItem('token')
    // 清除用户信息
    localStorage.removeItem('user')
    ElMessage.success('退出成功')
    // 跳转到登录页
    router.push('/login')
  }
}

onMounted(() => {
  // 从localStorage获取用户信息
  const userStr = localStorage.getItem('user')
  if (userStr) {
    const user = JSON.parse(userStr)
    username.value = user.username
  }
})
</script>

<style scoped>
.user-info {
  display: flex;
  align-items: center;
}

.user-name {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #409EFF;
  font-size: 14px;
}

.user-name:hover {
  color: #66b1ff;
}
</style> 