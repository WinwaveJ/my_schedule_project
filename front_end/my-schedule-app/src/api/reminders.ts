import api from './config'
import type { Reminder } from '@/types'

export const reminderApi = {
    // 获取提醒列表
    getReminders: () => {
        return api.get<Reminder[]>('/reminders/')
    },

    // 获取单个提醒
    getReminder: (id: number) => {
        return api.get<Reminder>(`/reminders/${id}/`)
    },

    // 创建提醒
    createReminder: (data: Partial<Reminder>) => {
        return api.post<Reminder>('/reminders/', data)
    },

    // 更新提醒
    updateReminder: (id: number, data: Partial<Reminder>) => {
        return api.put<Reminder>(`/reminders/${id}/`, data)
    },

    // 删除提醒
    deleteReminder: (id: number) => {
        return api.delete(`/reminders/${id}/`)
    },

    // 更新提醒状态
    updateReminderStatus: (id: number, isActive: boolean) => {
        return api.patch<Reminder>(`/reminders/${id}/`, { is_active: isActive })
    }
} 