import { useAuthStore } from '../stores/auth.ts'
import {
  mockPurchases,
  mockProducts,
  mockCoupons,
  mockAlerts,
  getMockPriceHistory,
} from './mock-data.ts'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1'
const USE_MOCK = import.meta.env.VITE_MOCK_API === 'true'

// Mock response lookup table
const mockRoutes: Record<string, (path: string) => unknown> = {
  '/purchases': () => mockPurchases,
  '/products': () => mockProducts,
  '/coupons': () => mockCoupons,
  '/alerts': () => mockAlerts,
}

function matchMockRoute<T>(path: string): T | null {
  // Exact match
  if (mockRoutes[path]) return mockRoutes[path](path) as T

  // /purchases/:id
  const purchaseMatch = path.match(/^\/purchases\/(.+)$/)
  if (purchaseMatch) {
    const purchase = mockPurchases.find((p) => p.id === purchaseMatch[1])
    return (purchase ?? null) as T
  }

  // /products/:id/price-history
  const priceHistoryMatch = path.match(/^\/products\/(.+)\/prices$/)
  if (priceHistoryMatch) {
    return getMockPriceHistory(priceHistoryMatch[1]) as T
  }

  // /products/:id
  const productMatch = path.match(/^\/products\/(.+)$/)
  if (productMatch) {
    const product = mockProducts.find((p) => p.id === productMatch[1])
    return (product ?? null) as T
  }

  const productsSearch = path.match(/^\/products\?q=(.+)$/)
  if (productsSearch) {
    const q = decodeURIComponent(productsSearch[1]).toLowerCase()
    return mockProducts.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.brand.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q),
    ) as T
  }

  return null
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  // Mock interceptor: return mock data without hitting the network
  if (USE_MOCK && (!options?.method || options.method === 'GET')) {
    const mockResult = matchMockRoute<T>(path)
    if (mockResult !== null) {
      // Simulate network delay for realistic loading states
      await new Promise((r) => setTimeout(r, 300))
      return mockResult
    }
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include', // Send Better-Auth session cookie
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (res.status === 401) {
    useAuthStore.getState().setAuthenticated(false)
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }

  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, body: unknown) =>
    apiFetch<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    apiFetch<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: <T>(path: string) => apiFetch<T>(path, { method: 'DELETE' }),
}
