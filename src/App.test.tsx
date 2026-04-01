import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import App from './App.tsx'

vi.mock('./lib/auth-client.ts', () => ({
  authClient: {
    useSession: () => ({ data: null, isPending: false }),
  },
}))

describe('App', () => {
  it('redirects unauthenticated users to login', () => {
    render(<App />)
    expect(screen.getByText('CartSnitch')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })
})
