import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authClient } from '../lib/auth-client.ts'
import { useAuthStore } from '../stores/auth.ts'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!email || !password) {
      setError('Please fill in all fields.')
      return
    }

    setLoading(true)
    try {
      const { error: authError } = await authClient.signIn.email({
        email,
        password,
      })

      if (authError) {
        throw new Error(authError.message ?? 'Sign in failed')
      }

      setAuthenticated(true)
      navigate('/')
    } catch {
      if (import.meta.env.VITE_MOCK_AUTH === 'true') {
        setAuthenticated(true)
        navigate('/')
      } else {
        setError('Invalid email or password. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <h1 className="mb-2 text-3xl font-bold text-gray-900">CartSnitch</h1>
      <p className="mb-8 text-sm text-gray-500">Track prices. Save money.</p>

      {error && (
        <div className="mb-4 w-full max-w-sm rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form className="w-full max-w-sm space-y-4" onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          className="min-h-12 w-full rounded-xl border border-gray-200 px-4 text-base focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          className="min-h-12 w-full rounded-xl border border-gray-200 px-4 text-base focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
        />
        <button
          type="submit"
          disabled={loading}
          className="min-h-12 w-full rounded-xl bg-brand-blue px-4 py-3 text-base font-medium text-white active:bg-brand-blue/90 disabled:opacity-60"
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>

      <Link to="/forgot-password" className="mt-4 text-sm text-brand-blue">
        Forgot password?
      </Link>

      <p className="mt-6 text-sm text-gray-500">
        Don't have an account?{' '}
        <Link to="/register" className="text-brand-blue">
          Sign up
        </Link>
      </p>
    </div>
  )
}
