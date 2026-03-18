import { useParams, Link } from 'react-router-dom'
import { usePurchase } from '../hooks/useApi.ts'
import { StoreIcon } from '../components/StoreIcon.tsx'

export function PurchaseDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: purchase, isLoading, error } = usePurchase(id ?? '')

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 w-24 rounded bg-gray-200" />
        <div className="mt-4 h-20 rounded-xl bg-gray-200" />
        <div className="mt-4 space-y-1">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-12 rounded bg-gray-200" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !purchase) {
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-gray-500">Purchase not found.</p>
        <Link to="/purchases" className="mt-4 inline-block text-sm text-brand-blue">
          Back to purchases
        </Link>
      </div>
    )
  }

  return (
    <div>
      {/* Back link */}
      <Link to="/purchases" className="inline-flex items-center gap-1 text-sm text-brand-blue">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Purchases
      </Link>

      {/* Receipt header */}
      <div className="mt-4 rounded-xl bg-white p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <StoreIcon storeId={purchase.storeId} />
          <div>
            <h1 className="text-lg font-bold text-gray-900">{purchase.storeName}</h1>
            <p className="text-sm text-gray-500">
              {new Date(purchase.date).toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric',
              })}
            </p>
          </div>
        </div>
      </div>

      {/* Line items */}
      <div className="mt-4 rounded-xl bg-white shadow-sm">
        <div className="divide-y divide-gray-100">
          {purchase.items.map((item) => (
            <Link
              key={item.id}
              to={`/products/${item.productId}`}
              className="flex items-center justify-between px-4 py-3 active:bg-gray-50"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900">{item.name}</p>
                {item.quantity > 1 && (
                  <p className="text-xs text-gray-500">
                    {item.quantity} × ${item.unitPrice.toFixed(2)}
                  </p>
                )}
              </div>
              <span className="ml-4 text-sm font-medium text-gray-900">
                ${item.price.toFixed(2)}
              </span>
            </Link>
          ))}
        </div>

        {/* Total */}
        <div className="border-t-2 border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <span className="text-base font-bold text-gray-900">Total</span>
            <span className="text-base font-bold text-gray-900">
              ${purchase.total.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
