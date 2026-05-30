'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getUser, logout, isAuthenticated } from '@/lib/auth'
import { User, Task, AuditLog } from '@/types'
import { fetchTasks, fetchUsers, fetchAuditLogs } from '@/lib/tasks'
import toast from 'react-hot-toast'
import { LogOut, Plus, RefreshCw, BarChart2, ShieldAlert } from 'lucide-react'
import TaskCard from '@/components/tasks/TaskCard'
import CreateTaskModal from '@/components/tasks/CreateTaskModal'

export default function DashboardPage() {
  const router = useRouter()
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showLogs, setShowLogs] = useState(false)
  const [filterStatus, setFilterStatus] = useState<string>('all')

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true)
      const tasksData = await fetchTasks()
      setTasks(tasksData)

      const user = getUser()
      if (user?.role === 'admin') {
        const usersData = await fetchUsers()
        setUsers(usersData)

        const logsData = await fetchAuditLogs()
        setAuditLogs(logsData)
      }
    } catch {
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login')
      return
    }
    const user = getUser()
    setCurrentUser(user)
    loadDashboardData()
  }, [router, loadDashboardData])

  const pending = tasks.filter(t => t.status === 'pending').length
  const assigned = tasks.filter(t => t.status === 'assigned').length
  const inProgress = tasks.filter(t => t.status === 'in_progress').length
  const submitted = tasks.filter(t => t.status === 'submitted').length
  const accepted = tasks.filter(t => t.status === 'accepted').length
  const revisions = tasks.filter(t => t.status === 'revision_requested').length

  const filteredTasks = tasks.filter(t => {
    if (filterStatus === 'all') return true
    return t.status === filterStatus
  })

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      
      <nav className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded flex items-center justify-center">
              <span className="text-white font-bold">H</span>
            </div>
            <span className="font-bold text-gray-900 text-lg">Hairdrama Hub</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {currentUser?.avatar ? (
                <img src={currentUser.avatar} alt={currentUser.name} className="w-8 h-8 rounded-full border border-gray-200" />
              ) : (
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center border border-gray-300">
                  <span className="text-xs font-bold text-gray-600">{currentUser?.name?.[0]}</span>
                </div>
              )}
              <div className="hidden sm:block text-left">
                <p className="text-xs font-bold text-gray-900 leading-none">{currentUser?.name}</p>
                <p className="text-[10px] text-gray-500 capitalize mt-0.5 leading-none font-semibold">{currentUser?.role}</p>
              </div>
            </div>

            <button
              onClick={logout}
              className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900 transition-colors bg-white hover:bg-gray-50 border border-gray-300 px-3 py-1.5 rounded cursor-pointer font-medium shadow-sm"
            >
              <LogOut size={13} />
              Sign Out
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-8">
        
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Task Overview</h1>
            <p className="text-gray-500 text-xs mt-1">Real-time task counters and records</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadDashboardData}
              className="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors text-gray-500 cursor-pointer"
            >
              <RefreshCw size={15} />
            </button>

            {currentUser?.role === 'admin' && (
              <>
                <button
                  onClick={() => setShowLogs(!showLogs)}
                  className={`flex items-center gap-1 border px-4 py-2 rounded text-xs font-bold transition-all cursor-pointer ${
                    showLogs
                      ? 'bg-indigo-50 text-indigo-700 border-indigo-300'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <ShieldAlert size={14} />
                  {showLogs ? 'Show Tasks' : 'Audit Logs'}
                </button>

                <button
                  onClick={() => setShowCreateModal(true)}
                  className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded text-xs font-bold transition-all cursor-pointer shadow-sm"
                >
                  <Plus size={14} />
                  New Task
                </button>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-8">
          {[
            { label: 'Unassigned', count: pending, color: 'text-gray-700', bg: 'bg-white' },
            { label: 'Assigned', count: assigned, color: 'text-blue-700', bg: 'bg-white' },
            { label: 'In Progress', count: inProgress, color: 'text-sky-700', bg: 'bg-white' },
            { label: 'Submitted', count: submitted, color: 'text-yellow-700', bg: 'bg-white' },
            { label: 'Accepted', count: accepted, color: 'text-green-700', bg: 'bg-white' },
            { label: 'Revisions', count: revisions, color: 'text-red-700', bg: 'bg-white' },
          ].map((stat, i) => (
            <div key={i} className={`rounded-lg p-4 border border-gray-200 bg-white ${stat.bg}`}>
              <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">{stat.label}</p>
              <p className={`text-2xl font-black mt-1 ${stat.color}`}>{stat.count}</p>
            </div>
          ))}
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-2">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            <span className="text-gray-500 text-xs font-semibold">Synchronizing...</span>
          </div>
        ) : showLogs ? (
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
              <div>
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Audit Log Trace</h3>
                <p className="text-[10px] text-gray-500 mt-0.5">Automated signal records of write actions</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-gray-200 text-gray-500 font-bold uppercase tracking-wider">
                    <th className="py-2.5">Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Table</th>
                    <th>Record ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-150 text-gray-600 font-medium">
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center py-6 text-gray-400">No actions recorded in logs yet</td>
                    </tr>
                  ) : (
                    auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                        <td className="py-2.5 text-gray-500">{new Date(log.timestamp).toLocaleString()}</td>
                        <td className="text-gray-900 font-semibold">{log.user?.name || 'System / Signal'}</td>
                        <td>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            log.action === 'CREATE' ? 'bg-green-50 text-green-700 border border-green-200' :
                            log.action === 'UPDATE' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                            'bg-red-50 text-red-700 border border-red-200'
                          }`}>
                            {log.action}
                          </span>
                        </td>
                        <td className="font-mono text-[11px]">{log.table_name}</td>
                        <td className="font-mono text-[10px] text-gray-500">{log.row_id}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 pb-4">
              <div className="flex items-center gap-2">
                <BarChart2 size={16} className="text-indigo-600" />
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Tasks</h3>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Filter:</span>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="bg-white border border-gray-300 rounded px-2.5 py-1 text-xs text-gray-700 focus:outline-none"
                >
                  <option value="all">All statuses</option>
                  <option value="pending">Unassigned</option>
                  <option value="assigned">Assigned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="submitted">Submitted</option>
                  <option value="accepted">Accepted</option>
                  <option value="revision_requested">Revision Requested</option>
                </select>
              </div>
            </div>

            {filteredTasks.length === 0 ? (
              <div className="text-center py-20 bg-white rounded-lg border border-gray-200">
                <p className="text-gray-400 text-sm font-medium">No tasks found matching status criterion</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {filteredTasks.map(task => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    currentUser={currentUser}
                    allUsers={users}
                    onUpdate={loadDashboardData}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {showCreateModal && (
        <CreateTaskModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false)
            loadDashboardData()
          }}
        />
      )}
    </div>
  )
}
