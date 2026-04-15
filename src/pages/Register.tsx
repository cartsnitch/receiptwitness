import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authClient } from '../lib/auth-client.ts'

export function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [registrationComplete, setRegistrationComplete] = useState(false)
  const [resendLoading, setResendLoading] = useState(false)
  const [resendMessage, setResendMessage] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!name || !email || !password) {
      setError('Please fill in all fields.')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setLoading(true)
    try {
      const { error: authError } = await authClient.signUp.email({
        name,
        email,
        password,
      })

      if (authError) {
        throw new Error(authError.message ?? 'Registration failed')
      }

      setRegistrationComplete(true)
    } catch {
      setError('Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleResendVerification() {
    setResendLoading(true)
    setResendMessage('')
    try {
      const { error } = await authClient.sendVerificationEmail({ email })
      if (error) {
        setResendMessage('Failed to resend. Please try again.')
      } else {
        setResendMessage('Verification email sent!')
      }
    } finally {
      setResendLoading(false)
    }
  }

  if (registrationComplete) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-4">
        <h1 className="mb-2 text-3xl font-bold text-gray-900">Check your email</h1>
        <p className="mb-8 text-sm text-gray-500">
          We sent a verification link to {email}. Click it to activate your account.
        </p>
        <button
          type="button"
          onClick={handleResendVerification}
          disabled={resendLoading}
          className="min-h-12 rounded-xl bg-brand-blue px-6 py-3 text-base font-medium text-white active:bg-brand-blue/90 disabled:opacity-60"
        >
          {resendLoading ? 'Sending...' : 'Resend email'}
        </button>
        {resendMessage && (
          <p className="mt-4 text-sm text-gray-500">{resendMessage}</p>
        )}
        <p className="mt-6 text-sm text-gray-500">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-blue">
            Sign in
          </Link>
        </p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <h1 className="mb-2 text-3xl font-bold text-gray-900">Create Account</h1>
      <p className="mb-8 text-sm text-gray-500">Start tracking your grocery prices.</p>

      {error && (
        <div className="mb-4 w-full max-w-sm rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form className="w-full max-w-sm space-y-4" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Full Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoComplete="name"
          className="min-h-12 w-full rounded-xl border border-gray-200 px-4 text-base focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
        />
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
          placeholder="Password (min. 8 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
          className="min-h-12 w-full rounded-xl border border-gray-200 px-4 text-base focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
        />
        <button
          type="submit"
          disabled={loading}
          className="min-h-12 w-full rounded-xl bg-brand-blue px-4 py-3 text-base font-medium text-white active:bg-brand-blue/90 disabled:opacity-60"
        >
          {loading ? 'Creating account...' : 'Create Account'}
        </button>
      </form>

      <p className="mt-6 text-sm text-gray-500">
        Already have an account?{' '}
        <Link to="/login" className="text-brand-blue">
          Sign in
        </Link>
      </p>
    </div>
  )
}
