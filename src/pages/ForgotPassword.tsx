import { useState } from 'react'
import { Link } from 'react-router-dom'

export function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (email) setSubmitted(true)
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <h1 className="mb-2 text-3xl font-bold text-gray-900">Reset Password</h1>
      <p className="mb-8 max-w-sm text-center text-sm text-gray-500">
        Enter your email and we'll send you a link to reset your password.
      </p>

      {submitted ? (
        <div className="w-full max-w-sm rounded-xl bg-green-50 px-4 py-4 text-center">
          <p className="text-sm text-green-700">
            If an account exists for <strong>{email}</strong>, you'll receive a reset link shortly.
          </p>
          <Link
            to="/login"
            className="mt-4 inline-block min-h-12 rounded-xl bg-brand-blue px-6 py-3 text-base font-medium text-white active:bg-brand-blue/90"
          >
            Back to Sign In
          </Link>
        </div>
      ) : (
        <form className="w-full max-w-sm space-y-4" onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            className="min-h-12 w-full rounded-xl border border-gray-200 px-4 text-base focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
          />
          <button
            type="submit"
            className="min-h-12 w-full rounded-xl bg-brand-blue px-4 py-3 text-base font-medium text-white active:bg-brand-blue/90"
          >
            Send Reset Link
          </button>
        </form>
      )}

      <p className="mt-6 text-sm text-gray-500">
        <Link to="/login" className="text-brand-blue">
          Back to Sign In
        </Link>
      </p>
    </div>
  )
}
