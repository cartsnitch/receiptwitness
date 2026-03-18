import type { Purchase, Product, PriceHistory, Coupon, PriceAlert, User } from '../types/api.ts'

export const mockUser: User = {
  id: 'u1',
  email: 'sam@example.com',
  name: 'Sam Johnson',
  connectedStores: ['meijer', 'kroger'],
}

export const mockPurchases: Purchase[] = [
  {
    id: 'p1',
    storeId: 'meijer',
    storeName: 'Meijer',
    date: '2026-03-15',
    total: 47.23,
    items: [
      { id: 'i1', productId: 'prod1', name: 'Whole Milk (1 gal)', quantity: 1, price: 3.49, unitPrice: 3.49 },
      { id: 'i2', productId: 'prod2', name: 'Bananas (bunch)', quantity: 1, price: 1.29, unitPrice: 1.29 },
      { id: 'i3', productId: 'prod3', name: 'Chicken Breast (2 lb)', quantity: 1, price: 9.98, unitPrice: 4.99 },
      { id: 'i4', productId: 'prod4', name: 'Cheddar Cheese (8 oz)', quantity: 2, price: 7.58, unitPrice: 3.79 },
      { id: 'i5', productId: 'prod5', name: 'Sourdough Bread', quantity: 1, price: 4.29, unitPrice: 4.29 },
      { id: 'i6', productId: 'prod6', name: 'Baby Spinach (5 oz)', quantity: 1, price: 3.99, unitPrice: 3.99 },
      { id: 'i7', productId: 'prod7', name: 'Greek Yogurt (32 oz)', quantity: 1, price: 5.49, unitPrice: 5.49 },
      { id: 'i8', productId: 'prod8', name: 'Pasta Sauce', quantity: 1, price: 3.79, unitPrice: 3.79 },
      { id: 'i9', productId: 'prod9', name: 'Spaghetti (16 oz)', quantity: 1, price: 1.89, unitPrice: 1.89 },
      { id: 'i10', productId: 'prod10', name: 'Eggs (dozen)', quantity: 1, price: 5.44, unitPrice: 5.44 },
    ],
  },
  {
    id: 'p2',
    storeId: 'kroger',
    storeName: 'Kroger',
    date: '2026-03-12',
    total: 32.87,
    items: [
      { id: 'i11', productId: 'prod1', name: 'Whole Milk (1 gal)', quantity: 1, price: 3.29, unitPrice: 3.29 },
      { id: 'i12', productId: 'prod10', name: 'Eggs (dozen)', quantity: 1, price: 5.29, unitPrice: 5.29 },
      { id: 'i13', productId: 'prod11', name: 'Orange Juice (52 oz)', quantity: 1, price: 4.49, unitPrice: 4.49 },
      { id: 'i14', productId: 'prod12', name: 'Ground Beef (1 lb)', quantity: 2, price: 11.98, unitPrice: 5.99 },
      { id: 'i15', productId: 'prod2', name: 'Bananas (bunch)', quantity: 1, price: 0.99, unitPrice: 0.99 },
      { id: 'i16', productId: 'prod13', name: 'Tortilla Chips', quantity: 1, price: 3.49, unitPrice: 3.49 },
      { id: 'i17', productId: 'prod14', name: 'Salsa (16 oz)', quantity: 1, price: 3.34, unitPrice: 3.34 },
    ],
  },
  {
    id: 'p3',
    storeId: 'meijer',
    storeName: 'Meijer',
    date: '2026-03-08',
    total: 61.45,
    items: [
      { id: 'i18', productId: 'prod3', name: 'Chicken Breast (2 lb)', quantity: 2, price: 19.96, unitPrice: 4.99 },
      { id: 'i19', productId: 'prod15', name: 'Rice (5 lb)', quantity: 1, price: 6.99, unitPrice: 6.99 },
      { id: 'i20', productId: 'prod6', name: 'Baby Spinach (5 oz)', quantity: 2, price: 7.98, unitPrice: 3.99 },
      { id: 'i21', productId: 'prod16', name: 'Olive Oil (16 oz)', quantity: 1, price: 8.99, unitPrice: 8.99 },
      { id: 'i22', productId: 'prod5', name: 'Sourdough Bread', quantity: 1, price: 4.29, unitPrice: 4.29 },
      { id: 'i23', productId: 'prod17', name: 'Butter (1 lb)', quantity: 1, price: 4.79, unitPrice: 4.79 },
      { id: 'i24', productId: 'prod18', name: 'Avocados (3 ct)', quantity: 1, price: 4.99, unitPrice: 4.99 },
      { id: 'i25', productId: 'prod19', name: 'Cereal (Family Size)', quantity: 1, price: 3.46, unitPrice: 3.46 },
    ],
  },
  {
    id: 'p4',
    storeId: 'target',
    storeName: 'Target',
    date: '2026-03-05',
    total: 28.76,
    items: [
      { id: 'i26', productId: 'prod20', name: 'Paper Towels (6 pk)', quantity: 1, price: 12.99, unitPrice: 12.99 },
      { id: 'i27', productId: 'prod21', name: 'Dish Soap', quantity: 1, price: 3.49, unitPrice: 3.49 },
      { id: 'i28', productId: 'prod22', name: 'Trash Bags (45 ct)', quantity: 1, price: 8.79, unitPrice: 8.79 },
      { id: 'i29', productId: 'prod23', name: 'Hand Soap (2 pk)', quantity: 1, price: 3.49, unitPrice: 3.49 },
    ],
  },
]

export const mockProducts: Product[] = [
  {
    id: 'prod1',
    name: 'Whole Milk (1 gal)',
    brand: 'Store Brand',
    category: 'Dairy',
    prices: [
      { storeId: 'meijer', storeName: 'Meijer', price: 3.49, lastUpdated: '2026-03-15' },
      { storeId: 'kroger', storeName: 'Kroger', price: 3.29, lastUpdated: '2026-03-14' },
      { storeId: 'target', storeName: 'Target', price: 3.59, lastUpdated: '2026-03-13' },
    ],
  },
  {
    id: 'prod10',
    name: 'Eggs (dozen)',
    brand: 'Store Brand',
    category: 'Dairy',
    prices: [
      { storeId: 'meijer', storeName: 'Meijer', price: 5.44, lastUpdated: '2026-03-15' },
      { storeId: 'kroger', storeName: 'Kroger', price: 5.29, lastUpdated: '2026-03-14' },
      { storeId: 'target', storeName: 'Target', price: 5.69, lastUpdated: '2026-03-13' },
    ],
  },
  {
    id: 'prod3',
    name: 'Chicken Breast (2 lb)',
    brand: 'Store Brand',
    category: 'Meat',
    prices: [
      { storeId: 'meijer', storeName: 'Meijer', price: 9.98, lastUpdated: '2026-03-15' },
      { storeId: 'kroger', storeName: 'Kroger', price: 10.49, lastUpdated: '2026-03-14' },
      { storeId: 'target', storeName: 'Target', price: 10.99, lastUpdated: '2026-03-13' },
    ],
  },
  {
    id: 'prod2',
    name: 'Bananas (bunch)',
    brand: 'Dole',
    category: 'Produce',
    prices: [
      { storeId: 'meijer', storeName: 'Meijer', price: 1.29, lastUpdated: '2026-03-15' },
      { storeId: 'kroger', storeName: 'Kroger', price: 0.99, lastUpdated: '2026-03-14' },
      { storeId: 'target', storeName: 'Target', price: 1.19, lastUpdated: '2026-03-13' },
    ],
  },
  {
    id: 'prod5',
    name: 'Sourdough Bread',
    brand: 'Artisan Hearth',
    category: 'Bakery',
    prices: [
      { storeId: 'meijer', storeName: 'Meijer', price: 4.29, lastUpdated: '2026-03-15' },
      { storeId: 'kroger', storeName: 'Kroger', price: 4.49, lastUpdated: '2026-03-14' },
    ],
  },
  {
    id: 'prod6',
    name: 'Baby Spinach (5 oz)',
    brand: 'Organic Girl',
    category: 'Produce',
    prices: [
      { storeId: 'meijer', storeName: 'Meijer', price: 3.99, lastUpdated: '2026-03-15' },
      { storeId: 'kroger', storeName: 'Kroger', price: 3.79, lastUpdated: '2026-03-14' },
      { storeId: 'target', storeName: 'Target', price: 4.19, lastUpdated: '2026-03-13' },
    ],
  },
]

export function getMockPriceHistory(productId: string): PriceHistory[] {
  const basePrice = productId === 'prod1' ? 3.29
    : productId === 'prod10' ? 3.49
    : productId === 'prod3' ? 8.99
    : productId === 'prod2' ? 0.89
    : 3.99

  const stores = ['meijer', 'kroger', 'target']
  const history: PriceHistory[] = []

  for (let i = 90; i >= 0; i -= 7) {
    const date = new Date(2026, 2, 17)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]

    for (const store of stores) {
      const storeOffset = store === 'meijer' ? 0.10 : store === 'target' ? 0.20 : 0
      // simulate price variation over time
      const spike = (i > 30 && i < 50) ? 0.80 : 0
      const drift = (90 - i) * 0.005
      history.push({
        date: dateStr,
        price: Math.round((basePrice + storeOffset + spike + drift) * 100) / 100,
        storeId: store,
      })
    }
  }

  return history
}

export const mockCoupons: Coupon[] = [
  { id: 'c1', productId: 'prod1', storeName: 'Kroger', description: '$0.50 off Whole Milk (1 gal)', discount: '$0.50', expiresAt: '2026-03-31', code: 'MILK50' },
  { id: 'c2', storeName: 'Meijer', description: '10% off Meat Department', discount: '10%', expiresAt: '2026-03-22' },
  { id: 'c3', productId: 'prod6', storeName: 'Kroger', description: 'Buy 2 Get 1 Free — Baby Spinach', discount: 'B2G1', expiresAt: '2026-04-05' },
  { id: 'c4', storeName: 'Target', description: '$5 off $40+ Grocery Purchase', discount: '$5.00', expiresAt: '2026-03-28', code: 'SAVE5' },
  { id: 'c5', productId: 'prod10', storeName: 'Meijer', description: '$1 off Eggs (dozen)', discount: '$1.00', expiresAt: '2026-03-25' },
]

export const mockAlerts: PriceAlert[] = [
  { id: 'a1', productId: 'prod10', productName: 'Eggs (dozen)', targetPrice: 4.99, currentPrice: 5.29, triggered: false },
  { id: 'a2', productId: 'prod2', productName: 'Bananas (bunch)', targetPrice: 1.09, currentPrice: 0.99, triggered: true },
  { id: 'a3', productId: 'prod3', productName: 'Chicken Breast (2 lb)', targetPrice: 9.50, currentPrice: 9.98, triggered: false },
  { id: 'a4', productId: 'prod1', productName: 'Whole Milk (1 gal)', targetPrice: 3.39, currentPrice: 3.29, triggered: true },
]
