<template>
  <div class="layout">
    <el-container>
      <el-header>
        <div class="header-content">
          <div class="logo">
            日程管理系统
          </div>
          <div class="header-right">
            <UserInfo />
          </div>
        </div>
      </el-header>
      <el-container>
        <el-aside width="200px">
          <el-menu
            :router="true"
            :default-active="activeMenu"
            class="el-menu-vertical"
          >
            <el-menu-item index="/dashboard">
              <el-icon><DataLine /></el-icon>
              <span>仪表盘</span>
            </el-menu-item>
            <el-menu-item index="/tasks">
              <el-icon><List /></el-icon>
              <span>任务管理</span>
            </el-menu-item>
            <el-menu-item index="/activities">
              <el-icon><Timer /></el-icon>
              <span>活动管理</span>
            </el-menu-item>
            <el-menu-item index="/reminders">
              <el-icon><Bell /></el-icon>
              <span>提醒管理</span>
            </el-menu-item>
            <el-menu-item index="/settings">
              <el-icon><Setting /></el-icon>
              <span>应用设置</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view></router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataLine, List, Timer, Bell, Setting } from '@element-plus/icons-vue'
import UserInfo from './UserInfo.vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.layout {
  height: 100vh;
}

.el-container {
  height: 100%;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  padding: 0 20px;
}

.header-content {
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 18px;
  font-weight: bold;
  color: #409EFF;
}

.header-right {
  display: flex;
  align-items: center;
}

.el-aside {
  background-color: #fff;
  border-right: 1px solid #dcdfe6;
}

.el-menu-vertical {
  height: 100%;
  border-right: none;
}

.el-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style> 