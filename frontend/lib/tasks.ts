import api from './api'
import { Task, TaskFormData } from '@/types'

export const fetchTasks = async (): Promise<Task[]> => {
  const response = await api.get('/tasks/')
  return response.data
}

export const fetchTask = async (id: string): Promise<Task> => {
  const response = await api.get(`/tasks/${id}/`)
  return response.data
}

export const createTask = async (data: TaskFormData): Promise<Task> => {
  const response = await api.post('/tasks/', data)
  return response.data
}

export const updateTask = async (id: string, data: Partial<TaskFormData> & { status?: string }): Promise<Task> => {
  const response = await api.put(`/tasks/${id}/`, data)
  return response.data
}

export const deleteTask = async (id: string): Promise<void> => {
  await api.delete(`/tasks/${id}/`)
}

export const fetchUsers = async () => {
  const response = await api.get('/users/list/')
  return response.data
}