import { User } from '@/types'
import api from './api'

export const saveTokens = (access: string, refresh: string) => {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export const removeTokens = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

export const saveUser = (user: User) => {
  localStorage.setItem('user', JSON.stringify(user))
}

export const getUser = (): User | null => {
  const user = localStorage.getItem('user')
  if (!user) return null
  try {
    return JSON.parse(user)
  } catch {
    return null
  }
}

export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('access_token')
  return !!token
}

export const logout = () => {
  removeTokens()
  window.location.href = '/login'
}

export const refreshCurrentUser = async (): Promise<User | null> => {
  try {
    const res = await api.get('/auth/me')
    saveUser(res.data)
    return res.data
  } catch {
    return getUser()
  }
}

export function sameUserId(a?: string | null, b?: string | null) {
  if (!a || !b) return false
  return String(a) === String(b)
}