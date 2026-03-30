import { http, HttpResponse } from 'msw'
import type { Purchase, Product, Coupon, PriceAlert } from '../../types/api.ts'

const mockPurchases: Purchase[] = [
  {
    id: 'pur_1',
    storeId: 'store_1',
    storeName: 'Kroger',
    date: '2024-01-15',
    total: 42.5,
    items: [
      { id: 'item_1', productId: 'prod_1', name: 'Milk', quantity: 1, price: 3.99, unitPrice: 3.99 },
      { id: 'item_2', productId: 'prod_2', name: 'Bread', quantity: 2, price: 5.98, unitPrice: 2.99 },
    ],
  },
]

const mockProducts: Product[] = [
  {
    id: 'prod_1',
    name: 'Whole Milk',
    brand: 'Kroger',
    category: 'Dairy',
    prices: [{ storeId: 'store_1', storeName: 'Kroger', price: 3.99, lastUpdated: '2024-01-15' }],
  },
  {
    id: 'prod_2',
    name: 'Whole Wheat Bread',
    brand: 'Nature\'s Own',
    category: 'Bakery',
    prices: [{ storeId: 'store_1', storeName: 'Kroger', price: 2.99, lastUpdated: '2024-01-15' }],
  },
]

const mockCoupons: Coupon[] = [
  {
    id: 'coupon_1',
    productId: 'prod_1',
    storeName: 'Kroger',
    description: '$1 off milk',
    discount: '$1.00',
    expiresAt: '2024-12-31',
    code: 'MILK1',
  },
]

const mockAlerts: PriceAlert[] = [
  {
    id: 'alert_1',
    productId: 'prod_1',
    productName: 'Whole Milk',
    targetPrice: 2.99,
    currentPrice: 3.99,
    triggered: false,
  },
]

export const handlers = [
  http.get('/api/v1/health', () => HttpResponse.json({ status: 'ok' })),
  http.get('/api/v1/purchases', () => HttpResponse.json(mockPurchases)),
  http.get('/api/v1/products', () => HttpResponse.json(mockProducts)),
  http.get('/api/v1/products/prod_1', () => HttpResponse.json(mockProducts[0])),
  http.get('/api/v1/coupons', () => HttpResponse.json(mockCoupons)),
  http.get('/api/v1/price-alerts', () => HttpResponse.json(mockAlerts)),
]
