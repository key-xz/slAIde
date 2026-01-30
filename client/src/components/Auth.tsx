import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

type AuthMode = 'signin' | 'signup' | 'magic-link'

export function Auth() {
  const [mode, setMode] = useState<AuthMode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null)

  const { signIn, signUp, signInWithOtp } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)

    try {
      if (mode === 'magic-link') {
        const { error } = await signInWithOtp(email)
        if (error) {
          setMessage({ type: 'error', text: error.message })
        } else {
          setMessage({
            type: 'success',
            text: 'check your email for the magic link!',
          })
          setEmail('')
        }
      } else if (mode === 'signup') {
        const { error } = await signUp(email, password)
        if (error) {
          setMessage({ type: 'error', text: error.message })
        } else {
          setMessage({
            type: 'success',
            text: 'check your email to confirm your account!',
          })
          setEmail('')
          setPassword('')
        }
      } else {
        const { error } = await signIn(email, password)
        if (error) {
          setMessage({ type: 'error', text: error.message })
        }
      }
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'an error occurred',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-center text-gray-900">slAIde</h1>
          <p className="mt-2 text-center text-sm text-gray-600">
            {mode === 'signin' && 'sign in to your account'}
            {mode === 'signup' && 'create a new account'}
            {mode === 'magic-link' && 'sign in with magic link'}
          </p>
        </div>

        <div className="flex gap-2 p-1 bg-gray-100 rounded-lg">
          <button
            type="button"
            onClick={() => setMode('signin')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded transition-colors ${
              mode === 'signin'
                ? 'bg-white text-gray-900 shadow'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            sign in
          </button>
          <button
            type="button"
            onClick={() => setMode('signup')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded transition-colors ${
              mode === 'signup'
                ? 'bg-white text-gray-900 shadow'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            sign up
          </button>
          <button
            type="button"
            onClick={() => setMode('magic-link')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded transition-colors ${
              mode === 'magic-link'
                ? 'bg-white text-gray-900 shadow'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            magic link
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                email address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="you@example.com"
              />
            </div>

            {mode !== 'magic-link' && (
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  password
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="••••••••"
                  minLength={6}
                />
                {mode === 'signup' && (
                  <p className="mt-1 text-xs text-gray-500">minimum 6 characters</p>
                )}
              </div>
            )}
          </div>

          {message && (
            <div
              className={`p-3 rounded-md text-sm ${
                message.type === 'error'
                  ? 'bg-red-50 text-red-800 border border-red-200'
                  : 'bg-green-50 text-green-800 border border-green-200'
              }`}
            >
              {message.text}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              'loading...'
            ) : (
              <>
                {mode === 'signin' && 'sign in'}
                {mode === 'signup' && 'create account'}
                {mode === 'magic-link' && 'send magic link'}
              </>
            )}
          </button>
        </form>

        <div className="text-center text-sm text-gray-600">
          {mode === 'magic-link' ? (
            <p>a magic link will be sent to your email for passwordless sign in</p>
          ) : (
            <button
              type="button"
              onClick={() => setMode('magic-link')}
              className="text-blue-600 hover:text-blue-500 underline"
            >
              prefer passwordless? try magic link
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
