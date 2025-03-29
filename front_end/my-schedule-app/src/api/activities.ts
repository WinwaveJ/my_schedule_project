import api from './config'
import type { Activity } from '@/types'

export const activityApi = {
    // 获取活动列表
    getActivities: () => {
        return api.get<Activity[]>('/activities/')
    },

    // 获取单个活动
    getActivity: (id: number) => {
        return api.get<Activity>(`/activities/${id}/`)
    },

    // 创建活动
    createActivity: (data: Partial<Activity>) => {
        return api.post<Activity>('/activities/', data)
    },

    // 更新活动
    updateActivity: (id: number, data: Partial<Activity>) => {
        return api.put<Activity>(`/activities/${id}/`, data)
    },

    // 删除活动
    deleteActivity: (id: number) => {
        return api.delete(`/activities/${id}/`)
    },

    // 开始番茄钟
    startPomodoro: (id: number) => {
        return api.post<Activity>(`/activities/${id}/start_pomodoro/`)
    },

    // 开始休息
    startBreak: (id: number) => {
        return api.post<Activity>(`/activities/${id}/start_break/`)
    },

    // 开始正计时
    startStopwatch: (id: number) => {
        return api.post<Activity>(`/activities/${id}/start_stopwatch/`)
    },

    // 停止正计时
    stopStopwatch: (id: number) => {
        return api.post<Activity>(`/activities/${id}/stop_stopwatch/`)
    }
} 