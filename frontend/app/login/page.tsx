

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { GoogleLogin } from '@react-oauth/google'
import { GoogleOAuthProvider } from '@react-oauth/google'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { saveTokens, saveUser, isAuthenticated } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated()) {
      router.push('/dashboard')
    }
  }, [router])

const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {    
    try {
      setLoading(true)
      const response = await api.post('/users/auth/google/', {
        access_token: credentialResponse.credential,
      })

      const { user, tokens } = response.data
      saveTokens(tokens.access, tokens.refresh)
      saveUser(user)

      toast.success(`Welcome, ${user.name}!`)
      router.push('/dashboard')
    } catch {
      toast.error('Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleError = () => {
    toast.error('Google login failed. Please try again.')
  }

  return (
    <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''}>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">

          {/* Logo + Title */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span className="text-white text-2xl font-bold">H</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Hairdrama</h1>
            <p className="text-gray-500 mt-1">Task Manager</p>
          </div>

          {/* Welcome text */}
          <div className="mb-8 text-center">
            <h2 className="text-xl font-semibold text-gray-800">Welcome back!</h2>
            <p className="text-gray-500 text-sm mt-2">
              Sign in to manage your team tasks
            </p>
          </div>

          {/* Google Login Button */}
          <div className="flex flex-col items-center gap-4">
            {loading ? (
              <div className="flex items-center gap-2 text-gray-500">
                <div className="w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
                <span>Signing in...</span>
              </div>
            ) : (
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                useOneTap
                shape="rectangular"
                size="large"
                text="signin_with"
                width="300"
              />
            )}
          </div>

          {/* Footer */}
          <p className="text-center text-xs text-gray-400 mt-8">
            By signing in, you agree to our terms of service
          </p>
        </div>
      </div>
    </GoogleOAuthProvider>
  )
}