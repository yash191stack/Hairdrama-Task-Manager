export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  created_at: string
}


export interface Task {
  id: string
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed'
  priority: 'low' | 'medium' | 'high'
  created_by: User
  assigned_to?: User
  due_date?: string
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  user: User
  tokens: {
    access: string
    refresh: string
  }
}

export interface TaskFormData {
  title: string
  description?: string
  priority: 'low' | 'medium' | 'high'
  assigned_to_id?: string
  due_date?: string
}