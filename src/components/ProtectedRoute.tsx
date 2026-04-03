import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { authClient } from '../lib/auth-client.ts'
import { useAuthStore } from '../stores/auth.ts'

export function ProtectedRoute() {
  const isMockAuth = import.meta.env.VITE_MOCK_AUTH === 'true'
  const { data: session, isPending } = authClient.useSession()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated)

  useEffect(() => {
    if (!isMockAuth) {
      setAuthenticated(!!session)
    }
  }, [session, setAuthenticated, isMockAuth])

  // In mock auth mode, rely on Zustand store (set by Login/Register pages)
  if (isMockAuth) {
    if (!isAuthenticated) return <Navigate to="/login" replace />
    return <Outlet />
  }

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
