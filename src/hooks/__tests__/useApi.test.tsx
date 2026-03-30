import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { usePurchases } from '../useApi'
import { http, HttpResponse } from 'msw'
import { server } from '../../test/mocks/server'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useApi hooks', () => {
  describe('usePurchases', () => {
    it('fetches and returns purchases', async () => {
      const { result } = renderHook(() => usePurchases(), { wrapper: createWrapper() })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toHaveLength(1)
      expect(result.current.data![0]).toMatchObject({
        id: 'pur_1',
        storeName: 'Kroger',
        total: 42.5,
      })
    })

    it('returns an error when the endpoint fails', async () => {
      server.use(
        http.get('/api/v1/purchases', () => HttpResponse.error()),
      )

      const { result } = renderHook(() => usePurchases(), { wrapper: createWrapper() })

      await waitFor(() => expect(result.current.isError).toBe(true))
    })
  })
})
