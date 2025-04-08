import request from './config'

export interface AppSettings {
    id: number
    pomodoro_duration: number
    short_break_duration: number
    long_break_duration: number
    long_break_interval: number
    created_at: string
    updated_at: string
}

export interface TaskCategory {
    id: number
    name: string
    created_at: string
    updated_at: string
}

export const getAppSettings = () => {
    return request.get<AppSettings[]>('/settings/')
}

export const updateAppSettings = (id: number, data: Partial<AppSettings>) => {
    return request.patch<AppSettings>(`/settings/${id}/`, data)
}

export const getTaskCategories = () => {
    return request.get<TaskCategory[]>('/categories/')
}

export const createTaskCategory = (data: { name: string }) => {
    return request.post<TaskCategory>('/categories/', data)
}

export const updateTaskCategory = (id: number, data: { name: string }) => {
    return request.patch<TaskCategory>(`/categories/${id}/`, data)
}

export const deleteTaskCategory = (id: number) => {
    return request.delete(`/categories/${id}/`)
} 