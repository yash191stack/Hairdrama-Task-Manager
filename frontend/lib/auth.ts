import { User } from '@/types'

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