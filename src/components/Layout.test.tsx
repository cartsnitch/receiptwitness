import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import { BottomNav } from './BottomNav.tsx'

describe('BottomNav', () => {
  it('renders all navigation items', () => {
    render(
      <MemoryRouter>
        <BottomNav />
      </MemoryRouter>,
    )

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Purchases')).toBeInTheDocument()
    expect(screen.getByText('Products')).toBeInTheDocument()
    expect(screen.getByText('Coupons')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('renders navigation links with correct paths', () => {
    render(
      <MemoryRouter>
        <BottomNav />
      </MemoryRouter>,
    )

    const links = screen.getAllByRole('link')
    const hrefs = links.map((link) => link.getAttribute('href'))

    expect(hrefs).toContain('/')
    expect(hrefs).toContain('/purchases')
    expect(hrefs).toContain('/products')
    expect(hrefs).toContain('/coupons')
    expect(hrefs).toContain('/settings')
  })

  it('has touch-friendly minimum sizes (48px)', () => {
    render(
      <MemoryRouter>
        <BottomNav />
      </MemoryRouter>,
    )

    const links = screen.getAllByRole('link')
    links.forEach((link) => {
      expect(link.className).toContain('min-h-12')
      expect(link.className).toContain('min-w-12')
    })
  })
})
