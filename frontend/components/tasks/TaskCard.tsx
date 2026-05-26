'use client'

import { useState } from 'react'
import { Task } from '@/types'
import { updateTask, deleteTask } from '@/lib/tasks'
import toast from 'react-hot-toast'
import { Trash2, User, Calendar, Flag } from 'lucide-react'

interface TaskCardProps {
  task: Task
  onUpdate: () => void
}

const priorityColors = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-red-100 text-red-700',
}

const statusColors = {
  pending: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
}

const statusLabels = {
  pending: 'Pending',
  in_progress: 'In Progress',
  completed: 'Completed',
}

export default function TaskCard({ task, onUpdate }: TaskCardProps) {
  const [updating, setUpdating] = useState(false)

  const handleStatusChange = async (newStatus: string) => {
    try {
      setUpdating(true)
      await updateTask(task.id, { status: newStatus })
      toast.success('Task updated!')
      onUpdate()
    } catch {
      toast.error('Failed to update task')
    } finally {
      setUpdating(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Delete this task?')) return
    try {
      await deleteTask(task.id)
      toast.success('Task deleted')
      onUpdate()
    } catch {
      toast.error('Failed to delete task')
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">

        {/* Left side */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${priorityColors[task.priority]}`}>
              <Flag size={10} className="inline mr-1" />
              {task.priority}
            </span>
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColors[task.status]}`}>
              {statusLabels[task.status]}
            </span>
          </div>

          <h3 className="font-semibold text-gray-900 mb-1">{task.title}</h3>

          {task.description && (
            <p className="text-sm text-gray-500 mb-3">{task.description}</p>
          )}

          <div className="flex items-center gap-4 text-xs text-gray-400">
            {task.assigned_to && (
              <span className="flex items-center gap-1">
                <User size={12} />
                {task.assigned_to.name}
              </span>
            )}
            {task.due_date && (
              <span className="flex items-center gap-1">
                <Calendar size={12} />
                {new Date(task.due_date).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>

        {/* Right side — actions */}
        <div className="flex items-center gap-2">
          <select
            value={task.status}
            onChange={(e) => handleStatusChange(e.target.value)}
            disabled={updating}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-300"
          >
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>

          <button
            onClick={handleDelete}
            className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}