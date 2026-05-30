'use client'

import { useEffect, useState } from 'react'
import { createTask, fetchUsers } from '@/lib/tasks'
import { User } from '@/types'
import toast from 'react-hot-toast'
import { X } from 'lucide-react'

interface CreateTaskModalProps {
  onClose: () => void
  onSuccess: () => void
}

export default function CreateTaskModal({ onClose, onSuccess }: CreateTaskModalProps) {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    title: '',
    description: '',
    product_image_url: '',
    assigned_to_id: '',
  })

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const data = await fetchUsers()
        setUsers(data)
      } catch {
        toast.error('Failed to load users')
      }
    }
    loadUsers()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.title.trim()) {
      toast.error('Title is required')
      return
    }

    try {
      setLoading(true)
      await createTask({
        title: form.title,
        description: form.description || undefined,
        product_image_url: form.product_image_url || undefined,
        assigned_to_id: form.assigned_to_id || undefined,
      })
      toast.success('Task created successfully')
      onSuccess()
    } catch {
      toast.error('Failed to create task')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-md border border-gray-200 shadow-xl relative overflow-hidden">
        
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 className="text-md font-bold text-gray-900">Create New Task</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-3.5">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Title *
            </label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Task title"
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-900 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Description
            </label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Task description"
              rows={3}
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-900 focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Product Image URL
            </label>
            <input
              type="url"
              value={form.product_image_url}
              onChange={(e) => setForm({ ...form, product_image_url: e.target.value })}
              placeholder="https://example.com/image.jpg"
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-900 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Assign User
            </label>
            <select
              value={form.assigned_to_id}
              onChange={(e) => setForm({ ...form, assigned_to_id: e.target.value })}
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-900 focus:outline-none focus:border-indigo-500"
            >
              <option value="">Keep Unassigned</option>
              {users.map(u => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.email})
                </option>
              ))}
            </select>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 rounded-md border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm font-semibold cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold disabled:opacity-50 cursor-pointer"
            >
              {loading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}