import api from './config'
import type { Task } from '@/types'

export const taskApi = {
    // 获取任务列表
    getTasks: () => {
        return api.get<Task[]>('/tasks/')
    },

    // 获取单个任务
    getTask: (id: number) => {
        return api.get<Task>(`/tasks/${id}/`)
    },

    // 创建任务
    createTask: (data: Partial<Task>) => {
        return api.post<Task>('/tasks/', data)
    },

    // 更新任务
    updateTask: (id: number, data: Partial<Task>) => {
        return api.put<Task>(`/tasks/${id}/`, data)
    },

    // 删除任务
    deleteTask: (id: number) => {
        return api.delete(`/tasks/${id}/`)
    },

    // 更新任务进度
    updateTaskProgress: (id: number, progress: number) => {
        return api.patch<Task>(`/tasks/${id}/update_progress/`, { progress })
    }
} 