'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Task, User } from '@/types'
import { deleteTask, assignTask, acceptTask, requestRevision } from '@/lib/tasks'
import { sameUserId } from '@/lib/auth'
import toast from 'react-hot-toast'

function studioHref(taskId: string) {
  return `/dashboard?task=${taskId}`
}
import { Trash2, User as UserIcon, ArrowUpRight, Sparkles } from 'lucide-react'

interface TaskCardProps {
  task: Task
  currentUser: User | null
  allUsers: User[]
  onUpdate: () => void
}

const statusColors = {
  pending: 'bg-gray-100 text-gray-700 border-gray-200',
  assigned: 'bg-blue-50 text-blue-700 border-blue-200',
  in_progress: 'bg-sky-50 text-sky-700 border-sky-200',
  submitted: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  accepted: 'bg-green-50 text-green-700 border-green-200',
  revision_requested: 'bg-red-50 text-red-700 border-red-200',
}

const statusLabels = {
  pending: 'Unassigned',
  assigned: 'Assigned',
  in_progress: 'In Progress',
  submitted: 'Submitted',
  accepted: 'Accepted',
  revision_requested: 'Revision Requested',
}

export default function TaskCard({ task, currentUser, allUsers, onUpdate }: TaskCardProps) {
  const [loading, setLoading] = useState(false)
  const [showRevisionInput, setShowRevisionInput] = useState(false)
  const [feedback, setFeedback] = useState('')

  const isAdmin = currentUser?.role === 'admin'
  const isAssignedToMe = sameUserId(task.assigned_to?.id, currentUser?.id)

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this task?')) return
    try {
      setLoading(true)
      await deleteTask(task.id)
      toast.success('Task deleted')
      onUpdate()
    } catch {
      toast.error('Failed to delete task')
    } finally {
      setLoading(false)
    }
  }

  const handleAssignChange = async (userId: string) => {
    try {
      setLoading(true)
      await assignTask(task.id, userId)
      toast.success('Task assignment updated')
      onUpdate()
    } catch {
      toast.error('Failed to assign task')
    } finally {
      setLoading(false)
    }
  }

  const handleAccept = async () => {
    try {
      setLoading(true)
      await acceptTask(task.id)
      toast.success('Task accepted and completed!')
      onUpdate()
    } catch {
      toast.error('Failed to accept task')
    } finally {
      setLoading(false)
    }
  }

  const handleRequestRevision = async () => {
    if (!feedback.trim()) {
      toast.error('Feedback is required to request a revision')
      return
    }
    try {
      setLoading(true)
      await requestRevision(task.id, feedback)
      toast.success('Revision requested')
      setShowRevisionInput(false)
      setFeedback('')
      onUpdate()
    } catch {
      toast.error('Failed to request revision')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-sm transition-shadow">
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${statusColors[task.status]}`}>
              {statusLabels[task.status]}
            </span>
            
            {task.product_image_url && (
              <span className="text-[10px] bg-gray-50 text-gray-600 border border-gray-200 px-1.5 py-0.5 rounded flex items-center gap-1">
                <Sparkles size={10} /> Has Product Image
              </span>
            )}
          </div>

          <Link href={studioHref(task.id)} className="text-base font-bold text-gray-900 mb-1 hover:text-indigo-600 block">
            {task.title}
          </Link>

          {task.description && (
            <p className="text-gray-600 text-sm mb-4 line-clamp-2 leading-relaxed">
              {task.description}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 border-t border-gray-100 pt-3">
            <div>
              <span className="font-semibold text-gray-700">Created by: </span>
              <span className="text-gray-600">{task.created_by.name}</span>
            </div>

            <div className="flex items-center gap-1">
              <span className="font-semibold text-gray-700">Assignee: </span>
              {isAdmin ? (
                <select
                  disabled={loading}
                  value={task.assigned_to?.id || ''}
                  onChange={(e) => handleAssignChange(e.target.value)}
                  className="bg-white border border-gray-300 rounded px-1.5 py-0.5 text-xs text-gray-700 focus:outline-none"
                >
                  <option value="">Unassigned</option>
                  {allUsers.map(u => (
                    <option key={u.id} value={u.id}>{u.name}</option>
                  ))}
                </select>
              ) : (
                <span className="text-gray-600">{task.assigned_to?.name || 'Unassigned'}</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-row md:flex-col items-center md:items-end justify-between md:justify-start gap-3 border-t md:border-t-0 border-gray-100 pt-3 md:pt-0">
          <div className="flex items-center gap-2">
            <Link
              href={studioHref(task.id)}
              className="flex items-center gap-1 bg-indigo-600 hover:bg-indigo-700 border border-indigo-600 text-white px-3 py-1.5 rounded text-xs font-semibold shadow-sm transition-colors cursor-pointer"
            >
              Open AI Studio
              <ArrowUpRight size={13} />
            </Link>

            {isAdmin && (
              <button
                disabled={loading}
                onClick={handleDelete}
                className="p-1.5 bg-white hover:bg-gray-50 border border-gray-300 text-gray-500 hover:text-red-600 rounded shadow-sm transition-colors cursor-pointer"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>

          {isAdmin && task.status === 'submitted' && (
            <div className="flex flex-col gap-2 w-full md:w-auto">
              <div className="flex items-center gap-2">
                <button
                  disabled={loading}
                  onClick={handleAccept}
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold text-xs px-2.5 py-1 rounded cursor-pointer transition-colors shadow-sm"
                >
                  Accept Task
                </button>
                <button
                  disabled={loading}
                  onClick={() => setShowRevisionInput(!showRevisionInput)}
                  className="bg-white hover:bg-gray-50 border border-gray-300 text-gray-700 font-semibold text-xs px-2.5 py-1 rounded cursor-pointer transition-colors shadow-sm"
                >
                  Revision
                </button>
              </div>

              {showRevisionInput && (
                <div className="mt-2 flex flex-col gap-1.5 w-60">
                  <textarea
                    placeholder="Enter revision instructions..."
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    rows={2}
                    className="w-full bg-white border border-gray-300 rounded p-1.5 text-xs text-gray-900 focus:outline-none focus:border-indigo-500 resize-none"
                  />
                  <button
                    disabled={loading}
                    onClick={handleRequestRevision}
                    className="self-end bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-[10px] px-2 py-0.5 rounded cursor-pointer transition-colors"
                  >
                    Submit
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}