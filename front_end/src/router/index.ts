import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import Layout from '../components/Layout.vue'

const routes: RouteRecordRaw[] = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/',
        component: Layout,
        meta: { requiresAuth: true },
        redirect: '/dashboard',
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('../views/Dashboard.vue')
            },
            {
                path: 'tasks',
                name: 'TaskManagement',
                component: () => import('../views/TaskManagement.vue')
            },
            {
                path: 'activities',
                name: 'ActivityManagement',
                component: () => import('../views/ActivityManagement.vue')
            },
            {
                path: 'reminders',
                name: 'ReminderManagement',
                component: () => import('../views/ReminderManagement.vue')
            },
            {
                path: 'settings',
                name: 'AppSettings',
                component: () => import('../views/AppSettings.vue')
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')

    if (to.meta.requiresAuth && !token) {
        // 需要认证但未登录，重定向到登录页
        next('/login')
    } else if (to.path === '/login' && token) {
        // 已登录用户访问登录页，重定向到仪表盘
        next('/dashboard')
    } else {
        next()
    }
})

export default router 