'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { saveTokens, saveUser, isAuthenticated } from '@/lib/auth'

function LoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated()) {
      router.push('/dashboard')
      return
    }

    const code = searchParams.get('code')
    if (code) {
      const handleGithubCallback = async () => {
        try {
          setLoading(true)
          const response = await api.post('/auth/oauth/callback', {
            provider: 'github',
            code: code,
          })
          const { user, tokens } = response.data
          saveTokens(tokens.access, tokens.refresh)
          saveUser(user)
          toast.success(`Welcome back, ${user.name}!`)
          router.push('/dashboard')
        } catch {
          toast.error('GitHub login failed. Please try again.')
        } finally {
          setLoading(false)
        }
      }
      handleGithubCallback()
    }
  }, [router, searchParams])

  const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {
    try {
      setLoading(true)
      const response = await api.post('/auth/oauth/callback', {
        provider: 'google',
        credential: credentialResponse.credential,
      })
      const { user, tokens } = response.data
      saveTokens(tokens.access, tokens.refresh)
      saveUser(user)
      toast.success(`Welcome back, ${user.name}!`)
      router.push('/dashboard')
    } catch {
      toast.error('Google login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleGithubClick = () => {
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || 'Ov23ct4x5wY6z7a8b9c0'
    const redirectUri = typeof window !== 'undefined' ? `${window.location.origin}/login` : ''
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=user:email`
  }

  return (
    <div className="w-full max-w-md p-8 bg-white rounded-xl border border-gray-250 shadow-md">
      <div className="text-center mb-8">
        <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center mx-auto mb-3">
          <span className="text-white text-xl font-bold">H</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Hairdrama</h1>
        <p className="text-gray-500 text-sm mt-1">Task & AI Generation Manager</p>
      </div>

      <div className="mb-6 text-center">
        <h2 className="text-lg font-semibold text-gray-800">Sign In</h2>
        <p className="text-gray-500 text-xs mt-1">Access your dashboard using one of the providers below</p>
      </div>

      <div className="flex flex-col gap-4">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-6 gap-2">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            <span className="text-gray-500 text-sm">Please wait...</span>
          </div>
        ) : (
          <>
            <div className="flex justify-center w-full">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => toast.error('Google login failed.')}
                shape="rectangular"
                size="large"
                theme="outline"
                text="signin_with"
                width="320"
              />
            </div>

            <div className="relative flex py-2 items-center">
              <div className="flex-grow border-t border-gray-200"></div>
              <span className="flex-shrink mx-4 text-gray-400 text-xs uppercase font-medium">or</span>
              <div className="flex-grow border-t border-gray-200"></div>
            </div>

            <button
              onClick={handleGithubClick}
              className="flex items-center justify-center gap-2 w-[320px] mx-auto py-2 px-4 bg-gray-900 hover:bg-gray-800 text-white rounded text-sm font-medium transition-colors cursor-pointer border border-gray-800 shadow-sm"
            >
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
              </svg>
              Sign in with GitHub
            </button>
          </>
        )}
      </div>

      <div className="mt-8 text-center text-[11px] text-gray-400">
        By continuing, you agree to access guidelines
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''}>
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <Suspense fallback={
          <div className="flex flex-col items-center justify-center p-8 bg-white rounded-xl border border-gray-200">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-2" />
            <span className="text-gray-500 text-sm">Loading session...</span>
          </div>
        }>
          <LoginContent />
        </Suspense>
      </div>
    </GoogleOAuthProvider>
  )
}
