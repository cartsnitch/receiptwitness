import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api.ts'
import type { Purchase, Product, Coupon, PriceAlert, PriceHistory } from '../types/api.ts'

export function usePurchases() {
  return useQuery({
    queryKey: ['purchases'],
    queryFn: () => api.get<Purchase[]>('/purchases'),
  })
}

export function usePurchase(id: string) {
  return useQuery({
    queryKey: ['purchases', id],
    queryFn: () => api.get<Purchase>(`/purchases/${id}`),
    enabled: !!id,
  })
}

export function useProducts(search?: string) {
  return useQuery({
    queryKey: ['products', search],
    queryFn: () => api.get<Product[]>(`/products${search ? `?q=${encodeURIComponent(search)}` : ''}`),
  })
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: ['products', id],
    queryFn: () => api.get<Product>(`/products/${id}`),
    enabled: !!id,
  })
}

export function usePriceHistory(productId: string) {
  return useQuery({
    queryKey: ['priceHistory', productId],
    queryFn: () => api.get<PriceHistory[]>(`/products/${productId}/price-history`),
    enabled: !!productId,
  })
}

export function useCoupons() {
  return useQuery({
    queryKey: ['coupons'],
    queryFn: () => api.get<Coupon[]>('/coupons'),
  })
}

export function usePriceAlerts() {
  return useQuery({
    queryKey: ['priceAlerts'],
    queryFn: () => api.get<PriceAlert[]>('/price-alerts'),
  })
}
