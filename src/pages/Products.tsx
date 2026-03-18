import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useProducts } from '../hooks/useApi.ts'

export function Products() {
  const [search, setSearch] = useState('')
  const { data: products = [], isLoading, error } = useProducts(search || undefined)

  const lowestPrice = (product: typeof products[0]) =>
    Math.min(...product.prices.map((p) => p.price))

  if (error) {
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-red-600">Failed to load products.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Products</h1>

      {/* Search input */}
      <div className="mt-4">
        <input
          type="search"
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-h-12 w-full rounded-xl border border-gray-200 bg-white px-4 text-base shadow-sm focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
        />
      </div>

      {/* Product list */}
      <div className="mt-4 space-y-3">
        {isLoading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-gray-200" />
          ))
        ) : products.length === 0 ? (
          <div className="rounded-xl bg-white p-6 text-center shadow-sm">
            <p className="text-sm text-gray-500">No products match &ldquo;{search}&rdquo;.</p>
          </div>
        ) : (
          products.map((product) => {
            const low = lowestPrice(product)
            const cheapest = product.prices.find((p) => p.price === low)
            return (
              <Link
                key={product.id}
                to={`/products/${product.id}`}
                className="block rounded-xl bg-white p-4 shadow-sm active:bg-gray-50"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900">{product.name}</p>
                    <p className="text-xs text-gray-500">
                      {product.brand} &middot; {product.category}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-green-700">${low.toFixed(2)}</p>
                    <p className="text-xs text-gray-500">{cheapest?.storeName}</p>
                  </div>
                </div>
                <div className="mt-2 flex gap-2">
                  {product.prices.map((pp) => (
                    <span
                      key={pp.storeId}
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        pp.price === low
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {pp.storeName} ${pp.price.toFixed(2)}
                    </span>
                  ))}
                </div>
              </Link>
            )
          })
        )}
      </div>
    </div>
  )
}
