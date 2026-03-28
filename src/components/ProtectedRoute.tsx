import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { authClient } from '../lib/auth-client.ts'
import { useAuthStore } from '../stores/auth.ts'

export function ProtectedRoute() {
  const { data: session, isPending } = authClient.useSession()
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated)

  useEffect(() => {
    setAuthenticated(!!session)
  }, [session, setAuthenticated])

  if (isPending) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-blue border-t-transparent" />
      </div>
    )
  }

  if (!session) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
