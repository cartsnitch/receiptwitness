import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import App from './App.tsx'

vi.mock('./lib/auth-client.ts', () => ({
  authClient: {
    useSession: () => ({ data: null, isPending: false }),
  },
}))

describe('App', () => {
  it('renders the dashboard on the root route', () => {
    render(<App />)
    expect(screen.getByText('CartSnitch')).toBeInTheDocument()
  })

  it('renders the bottom navigation', () => {
    render(<App />)
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Purchases')).toBeInTheDocument()
    expect(screen.getByText('Products')).toBeInTheDocument()
  })
})
