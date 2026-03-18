export interface Purchase {
  id: string
  storeId: string
  storeName: string
  date: string
  total: number
  items: PurchaseItem[]
}

export interface PurchaseItem {
  id: string
  productId: string
  name: string
  quantity: number
  price: number
  unitPrice: number
}

export interface Product {
  id: string
  name: string
  brand: string
  category: string
  imageUrl?: string
  prices: ProductPrice[]
}

export interface ProductPrice {
  storeId: string
  storeName: string
  price: number
  lastUpdated: string
}

export interface PriceHistory {
  date: string
  price: number
  storeId: string
}

export interface Coupon {
  id: string
  productId?: string
  storeName: string
  description: string
  discount: string
  expiresAt: string
  code?: string
}

export interface PriceAlert {
  id: string
  productId: string
  productName: string
  targetPrice: number
  currentPrice: number
  triggered: boolean
}

export interface User {
  id: string
  email: string
  name: string
  connectedStores: string[]
}
