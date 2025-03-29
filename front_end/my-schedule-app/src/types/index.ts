export interface Task {
    id: number
    title: string
    description?: string
    user: number
    priority: 'URGENT_IMPORTANT' | 'NOT_URGENT_IMPORTANT' | 'URGENT_NOT_IMPORTANT' | 'NOT_URGENT_NOT_IMPORTANT'
    status: 'PENDING' | 'COMPLETED' | 'OVERDUE'
    category?: TaskCategory
    category_id?: number
    created_at: string
    updated_at: string
    due_date: string
    estimated_duration: number
    progress: number
}

export interface Activity {
    id: number
    title: string
    description?: string
    user: number
    task: Task
    task_id: number
    status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'PAUSED' | 'CANCELLED'
    timer_type: 'POMODORO' | 'STOPWATCH'
    pomodoro_count: number
    current_pomodoro_start?: string
    current_break_start?: string
    is_break: boolean
    is_long_break: boolean
    start_time?: string
    end_time?: string
    duration?: number
    created_at: string
    updated_at: string
    remaining_time?: number
    elapsed_time?: number
}

export interface Reminder {
    id: number
    user: number
    title: string
    content: string
    reminder_type: 'TASK_DUE' | 'ACTIVITY_START' | 'CUSTOM' | 'PERIODIC'
    reminder_method: 'EMAIL' | 'BROWSER'
    related_task?: number
    related_activity?: number
    reminder_time: string
    created_at: string
    is_active: boolean
    is_periodic: boolean
    periodic_type?: 'DAILY' | 'WEEKLY' | 'MONTHLY'
    periodic_interval?: number
    periodic_end_date?: string
    repeat_reminder: boolean
    repeat_interval?: number
    max_repeats?: number
    current_repeats: number
}

export interface AppSettings {
    id: number
    user: number
    pomodoro_duration: number
    short_break_duration: number
    long_break_duration: number
    long_break_interval: number
    daily_pomodoro_goal: number
    daily_stopwatch_goal: number
    created_at: string
    updated_at: string
}

export interface TaskCategory {
    id: number
    name: string
    user: number
    created_at: string
    updated_at: string
} 