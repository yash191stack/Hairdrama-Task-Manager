export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role?: 'admin' | 'user'
  created_at: string
}

export interface GeneratedImage {
  id: string
  task: string
  image_type: 'white_background' | 'theme' | 'creative' | 'model'
  image_url: string
  prompt_used?: string
  metadata?: Record<string, any>
  angle?: 'front' | 'side' | 'close_up' | 'none'
  created_at: string
}

export interface Task {
  id: string
  title: string
  description?: string
  status: 'pending' | 'assigned' | 'in_progress' | 'submitted' | 'accepted' | 'revision_requested'
  product_image_url?: string
  created_by: User
  assigned_to?: User
  generations?: GeneratedImage[]
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
  product_image_url?: string
  assigned_to_id?: string
}

export interface AuditLog {
  id: string
  user?: User
  action: string
  table_name: string
  row_id: string
  changes?: Record<string, any>
  timestamp: string
}