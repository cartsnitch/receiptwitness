import { create } from 'zustand'

/**
 * Minimal auth state for UI reactivity.
 *
 * Session management is handled by Better-Auth via httpOnly cookies.
 * This store only tracks whether we have an active session for UI
 * gating (protected routes, nav state). No tokens in memory or localStorage.
 */
interface AuthState {
  isAuthenticated: boolean
  setAuthenticated: (value: boolean) => void
}

export const useAuthStore = create<AuthState>()((set) => ({
  isAuthenticated: false,
  setAuthenticated: (value) => set({ isAuthenticated: value }),
}))
