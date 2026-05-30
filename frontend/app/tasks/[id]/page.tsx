'use client'

import { useEffect, use } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import TaskStudio from '@/components/tasks/TaskStudio'

export const dynamic = 'force-dynamic'

export default function TaskDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter()
  const { id } = use(params)

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login')
    }
  }, [router])

  return <TaskStudio taskId={id} />
}
