'use client'

import { useEffect, useState, useCallback, use } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getUser, isAuthenticated } from '@/lib/auth'
import { User, Task, GeneratedImage } from '@/types'
import {
  fetchTask,
  startTask,
  submitTask,
  triggerGeneration,
  pollJobStatus,
  fetchGenerations,
  deleteGeneration,
} from '@/lib/tasks'
import toast from 'react-hot-toast'
import { ArrowLeft, Sparkles, CheckCircle, Flame, Layers, Wand2, Download, Trash2, ArrowUpRight, Loader } from 'lucide-react'

export default function TaskDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter()
  const { id } = use(params)
  
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [generations, setGenerations] = useState<GeneratedImage[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [activeJobId, setActiveJobId] = useState<string | null>(null)

  const [imageType, setImageType] = useState('white_background')
  const [angle, setAngle] = useState('none')
  const [prompt, setPrompt] = useState('')
  const [theme, setTheme] = useState('')

  const loadTaskData = useCallback(async () => {
    try {
      setLoading(true)
      const taskData = await fetchTask(id)
      setTask(taskData)

      const genData = await fetchGenerations(id)
      setGenerations(genData)
    } catch {
      toast.error('Failed to load task details')
      router.push('/dashboard')
    } finally {
      setLoading(false)
    }
  }, [id, router])

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login')
      return
    }
    setCurrentUser(getUser())
    loadTaskData()
  }, [router, loadTaskData])

  const handleStartTask = async () => {
    try {
      setLoading(true)
      await startTask(id)
      toast.success('Task started successfully')
      loadTaskData()
    } catch {
      toast.error('Failed to start task')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    try {
      setGenerating(true)
      const data = await triggerGeneration(id, {
        image_type: imageType,
        prompt: prompt || undefined,
        angle: angle !== 'none' ? angle : undefined,
        theme: theme || undefined,
      })

      setActiveJobId(data.job_id)
      toast.success('AI generation job initiated')
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to trigger AI generation'
      toast.error(msg)
      setGenerating(false)
    }
  }

  const [latestImageUrl, setLatestImageUrl] = useState<string | null>(null);

  // Poll job status every 2 seconds when a job is active
  useEffect(() => {
    if (!activeJobId) return;

    const intervalId = setInterval(async () => {
      try {
        const job = await pollJobStatus(activeJobId);
        if (job.status === 'completed') {
          clearInterval(intervalId);
          setActiveJobId(null);
          setGenerating(false);
          toast.success('AI Image generated successfully!');
          setLatestImageUrl(job.image_url || null);
          const genData = await fetchGenerations(id);
          setGenerations(genData);
          const taskData = await fetchTask(id);
          setTask(taskData);
        } else if (job.status === 'failed') {
          clearInterval(intervalId);
          setActiveJobId(null);
          setGenerating(false);
          toast.error(job.error || 'AI generation failed.');
        }
      } catch {
        clearInterval(intervalId);
        setActiveJobId(null);
        setGenerating(false);
      }
    }, 2000);

    return () => clearInterval(intervalId);
  }, [activeJobId, id]);

  const handleDeleteGen = async (genId: string) => {
    if (!confirm('Are you sure you want to delete this AI generation?')) return
    try {
      await deleteGeneration(genId)
      toast.success('Generation deleted')
      const genData = await fetchGenerations(id)
      setGenerations(genData)
      
      const taskData = await fetchTask(id)
      setTask(taskData)
    } catch {
      toast.error('Failed to delete generation')
    }
  }

  const handleSubmitTask = async () => {
    try {
      setLoading(true)
      await submitTask(id)
      toast.success('Task submitted successfully for Admin review!')
      loadTaskData()
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Failed to submit task'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !task) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-2 text-gray-900">
        <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        <span className="text-gray-500 text-xs font-semibold">Synchronizing...</span>
      </div>
    )
  }

  if (!task) return null

  const isAssignedToMe = task.assigned_to?.id === currentUser?.id
  const canGenerate = isAssignedToMe && task.status === 'in_progress'

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      
      <nav className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 text-gray-600 hover:text-gray-900 transition-colors text-xs font-bold uppercase tracking-wider cursor-pointer"
          >
            <ArrowLeft size={14} /> Back to dashboard
          </Link>
          
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Status:</span>
            <span className="text-xs bg-gray-100 text-gray-700 border border-gray-200 px-2 py-0.5 rounded font-bold uppercase">
              {task.status.replace('_', ' ')}
            </span>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-8">
        
        <div className="flex flex-col lg:flex-row gap-6 mb-8">
          
          <div className="flex-1 space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6 relative overflow-hidden">
              <h1 className="text-xl font-bold text-gray-900 mb-2">{task.title}</h1>
              <p className="text-gray-600 text-sm leading-relaxed mb-4">{task.description || 'No description provided.'}</p>

              <div className="flex items-center gap-4 text-xs text-gray-500 border-t border-gray-100 pt-4">
                <div>
                  <span className="font-bold text-gray-700">Created by: </span>
                  <span>{task.created_by.name}</span>
                </div>
                <div>
                  <span className="font-bold text-gray-700">Assignee: </span>
                  <span className="text-indigo-600 font-semibold">{task.assigned_to?.name || 'Unassigned'}</span>
                </div>
              </div>
            </div>

            {isAssignedToMe && task.status === 'assigned' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <p className="text-blue-900 text-sm font-bold">Ready to start?</p>
                  <p className="text-blue-700 text-xs mt-0.5">Activate this task to begin AI background generations.</p>
                </div>
                <button
                  onClick={handleStartTask}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-4 py-2 rounded transition-colors cursor-pointer"
                >
                  Start Work
                </button>
              </div>
            )}

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-4">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">AI Studio Panel</h3>
                <span className="text-[11px] bg-gray-100 text-gray-700 border border-gray-200 px-2 py-0.5 rounded font-bold">
                  {generations.length} / 8 Generated
                </span>
              </div>

              {canGenerate ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">Background Type</label>
                      <select
                        value={imageType}
                        onChange={(e) => setImageType(e.target.value)}
                        className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-indigo-500"
                      >
                        <option value="white_background">Studio White</option>
                        <option value="theme">Theme-Based</option>
                        <option value="creative">Creative / Artistic</option>
                        <option value="model">Model Wearing Product</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">Camera Angle</label>
                      <select
                        value={angle}
                        onChange={(e) => setAngle(e.target.value)}
                        className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-indigo-500"
                      >
                        <option value="none">None</option>
                        <option value="front">Frontal</option>
                        <option value="side">Side view</option>
                        <option value="close_up">Close-up macro</option>
                      </select>
                    </div>
                  </div>

                  {imageType === 'theme' && (
                    <div>
                      <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">Theme Name</label>
                      <input
                        type="text"
                        value={theme}
                        onChange={(e) => setTheme(e.target.value)}
                        placeholder="e.g. Luxury Red Velvet, Premium White Marble"
                        className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  )}

                  <div>
                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">Prompt Description</label>
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="Add rich contextual visual prompts..."
                      rows={2.5}
                      className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-indigo-500 resize-none"
                    />
                  </div>

                  <button
                    disabled={generating || generations.length >= 8}
                    onClick={handleGenerate}
                    className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 rounded text-xs font-bold transition-all disabled:opacity-50 cursor-pointer shadow-sm"
                  >
                    {generating ? (
                      <>
                        <Loader className="w-4 h-4 animate-spin text-white" />
                        Generating with Stability AI...
                      </>
                    ) : (
                      <>
                        <Sparkles size={14} />
                        Generate AI Variation
                      </>
                    )}
                  </button>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-400 text-xs font-medium border border-gray-300 border-dashed rounded">
                  {isAssignedToMe
                    ? 'Start work on the task to unlock AI Generation panel'
                    : 'Only the assigned user can execute AI generations.'}
                </div>
              )}
            </div>
            {latestImageUrl && (
              <div className="my-4">
                <h3 className="text-sm font-bold mb-2">Latest Generated Image</h3>
                <img src={latestImageUrl} alt="Generated" className="max-w-full rounded border" />
              </div>
            )}
          </div>

          <div className="w-full lg:w-80 space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-5">
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Product Image</h3>
              {task.product_image_url ? (
                <div className="relative aspect-square rounded border border-gray-200 bg-gray-100 flex items-center justify-center overflow-hidden">
                  <img
                    src={task.product_image_url}
                    alt={task.title}
                    className="max-w-full max-h-full object-contain"
                  />
                </div>
              ) : (
                <div className="aspect-square bg-gray-150 border border-gray-200 rounded flex flex-col items-center justify-center text-gray-400 gap-1.5 p-4 text-center">
                  <Flame size={20} />
                  <p className="text-[10px] font-bold uppercase tracking-wider">No Image</p>
                  <p className="text-[9px] text-gray-500">Upload a product image before generating.</p>
                </div>
              )}
            </div>

            {isAssignedToMe && task.status === 'in_progress' && (
              <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-3.5">
                <div>
                  <h3 className="text-xs font-bold text-gray-900 uppercase tracking-wider">Submit Deliverables</h3>
                  <div className="w-full bg-gray-100 h-2 rounded-full mt-2.5 overflow-hidden border border-gray-200">
                    <div
                      className="bg-indigo-600 h-full transition-all duration-300"
                      style={{ width: `${(generations.length / 8) * 100}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-gray-500 font-bold uppercase mt-1.5">
                    <span>Progress Tracker</span>
                    <span>{generations.length} / 8</span>
                  </div>
                </div>

                <button
                  disabled={generations.length !== 8}
                  onClick={handleSubmitTask}
                  className="w-full flex items-center justify-center gap-1.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-150 disabled:text-gray-400 disabled:border-gray-200 border border-transparent text-white py-2 rounded text-xs font-bold transition-all cursor-pointer shadow-sm"
                >
                  <CheckCircle size={14} />
                  Submit to Admin
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center gap-2 pb-3 border-b border-gray-100 mb-6">
            <Layers size={16} className="text-indigo-600" />
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Variations Gallery</h3>
          </div>

          {generations.length === 0 ? (
            <div className="text-center py-20 text-gray-400 text-xs font-semibold border border-gray-200 border-dashed rounded-lg">
              No generations yet. Pick a type and run the studio.
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {generations.map((gen) => (
                <div key={gen.id} className="group relative aspect-square bg-gray-100 border border-gray-200 rounded-lg overflow-hidden hover:shadow transition-all duration-300">
                  <img
                    src={gen.image_url}
                    alt={gen.prompt_used || 'Generation'}
                    className="w-full h-full object-cover"
                  />
                  
                  <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-between p-3">
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-[9px] bg-indigo-600 text-white font-bold px-1.5 py-0.5 rounded capitalize shadow-sm">
                        {gen.image_type.replace('_', ' ')}
                      </span>
                      
                      {(currentUser?.role === 'admin' || isAssignedToMe) && (
                        <button
                          onClick={() => handleDeleteGen(gen.id)}
                          className="p-1 bg-gray-900 hover:bg-red-750 text-gray-300 hover:text-white rounded transition-colors cursor-pointer border border-gray-800"
                        >
                          <Trash2 size={11} />
                        </button>
                      )}
                    </div>

                    <div>
                      {gen.prompt_used && (
                        <p className="text-[10px] text-gray-200 line-clamp-2 leading-normal mb-2">
                          {gen.prompt_used}
                        </p>
                      )}

                      <a
                        href={gen.image_url}
                        target="_blank"
                        rel="noreferrer"
                        className="w-full flex items-center justify-center gap-1 bg-gray-900 hover:bg-gray-800 text-white py-1 rounded text-[10px] font-bold border border-gray-800 transition-colors shadow-sm"
                      >
                        <Download size={10} /> View / Download
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
