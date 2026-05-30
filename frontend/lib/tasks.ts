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

export const assignTask = async (id: string, assignedToId: string): Promise<Task> => {
  const response = await api.post(`/tasks/${id}/assign/`, { assigned_to_id: assignedToId })
  return response.data
}

export const acceptTask = async (id: string): Promise<Task> => {
  const response = await api.put(`/tasks/${id}/accept/`)
  return response.data
}

export const requestRevision = async (id: string, feedback: string): Promise<Task> => {
  const response = await api.put(`/tasks/${id}/request-revision/`, { feedback })
  return response.data
}

export const startTask = async (id: string): Promise<Task> => {
  const response = await api.put(`/tasks/${id}/start/`)
  return response.data
}

export const submitTask = async (id: string): Promise<Task> => {
  const response = await api.post(`/tasks/${id}/submit/`)
  return response.data
}

export const triggerGeneration = async (
  id: string,
  data: { image_type: string; prompt?: string; angle?: string; theme?: string }
): Promise<{ job_id: string; status: string }> => {
  const response = await api.post(`/tasks/${id}/generate/`, data)
  return response.data
}

export const pollJobStatus = async (
  jobId: string
): Promise<{ job_id: string; status: string; image_url?: string; error?: string }> => {
  const response = await api.get(`/jobs/${jobId}/status/`)
  return response.data
}

export const fetchGenerations = async (id: string): Promise<any[]> => {
  const response = await api.get(`/tasks/${id}/generations/`)
  return response.data
}

export const deleteGeneration = async (genId: string): Promise<void> => {
  await api.delete(`/generations/${genId}/`)
}

export const fetchAuditLogs = async (): Promise<any[]> => {
  const response = await api.get('/tasks/audit-logs/')
  return response.data
}

export const fetchUsers = async (): Promise<any[]> => {
  const response = await api.get('/users/list/')
  return response.data
}