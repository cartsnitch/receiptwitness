import { useParams, Link } from 'react-router-dom'
import { useProduct } from '../hooks/useApi.ts'
import { StoreIcon } from '../components/StoreIcon.tsx'

export function StoreComparison() {
  const { productId } = useParams<{ productId: string }>()
  const { data: product, isLoading } = useProduct(productId ?? '')

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 w-20 rounded bg-gray-200" />
        <div className="mt-4 h-8 w-48 rounded bg-gray-200" />
        <div className="mt-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl bg-gray-200" />
          ))}
        </div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-gray-500">Product not found.</p>
        <Link to="/products" className="mt-4 inline-block text-sm text-brand-blue">
          Back to products
        </Link>
      </div>
    )
  }

  const sorted = product.prices.slice().sort((a, b) => a.price - b.price)
  const lowestPrice = sorted[0]?.price ?? 0
  const savings = sorted.length > 1 ? sorted[sorted.length - 1].price - sorted[0].price : 0

  return (
    <div>
      {/* Back link */}
      <Link to={`/products/${product.id}`} className="inline-flex items-center gap-1 text-sm text-brand-blue">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        {product.name}
      </Link>

      <h1 className="mt-4 text-2xl font-bold text-gray-900">Store Comparison</h1>
      <p className="mt-1 text-sm text-gray-500">{product.name} &middot; {product.brand}</p>

      {/* Savings banner */}
      {savings > 0 && (
        <div className="mt-4 rounded-xl bg-green-50 p-4">
          <p className="text-sm font-semibold text-green-800">
            Save ${savings.toFixed(2)} by shopping at {sorted[0].storeName}
          </p>
        </div>
      )}

      {/* Store comparison cards */}
      <div className="mt-4 space-y-3">
        {sorted.map((pp, idx) => (
          <div
            key={pp.storeId}
            className={`rounded-xl p-4 shadow-sm ${
              idx === 0 ? 'border-2 border-green-400 bg-white' : 'bg-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <StoreIcon storeId={pp.storeId} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900">{pp.storeName}</p>
                <p className="text-xs text-gray-500">
                  Updated{' '}
                  {new Date(pp.lastUpdated).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })}
                </p>
              </div>
              <div className="text-right">
                <p
                  className={`text-lg font-bold ${
                    pp.price === lowestPrice ? 'text-green-700' : 'text-gray-900'
                  }`}
                >
                  ${pp.price.toFixed(2)}
                </p>
                {pp.price === lowestPrice ? (
                  <span className="text-xs font-medium text-green-600">Best price</span>
                ) : (
                  <span className="text-xs text-gray-400">
                    +${(pp.price - lowestPrice).toFixed(2)}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <p className="mt-6 text-center text-xs text-gray-400">
        Prices last verified from store loyalty card data. Map view coming soon.
      </p>
    </div>
  )
}
