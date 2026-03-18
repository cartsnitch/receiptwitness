import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { usePurchases } from '../hooks/useApi.ts'
import { StoreIcon } from '../components/StoreIcon.tsx'

export function Purchases() {
  const { data: purchases = [], isLoading, error } = usePurchases()
  const [storeFilter, setStoreFilter] = useState('all')

  const stores = useMemo(
    () => ['all', ...new Set(purchases.map((p) => p.storeName))],
    [purchases],
  )

  const filtered =
    storeFilter === 'all'
      ? purchases
      : purchases.filter((p) => p.storeName === storeFilter)

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-48 rounded bg-gray-200" />
        <div className="mt-4 flex gap-2">
          <div className="h-10 w-24 rounded-full bg-gray-200" />
          <div className="h-10 w-20 rounded-full bg-gray-200" />
          <div className="h-10 w-20 rounded-full bg-gray-200" />
        </div>
        <div className="mt-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-gray-200" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-red-600">Failed to load purchases.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Purchase History</h1>

      {/* Store filter chips */}
      <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
        {stores.map((store) => (
          <button
            key={store}
            onClick={() => setStoreFilter(store)}
            className={`min-h-12 shrink-0 rounded-full px-4 text-sm font-medium ${
              storeFilter === store
                ? 'bg-brand-blue text-white'
                : 'bg-white text-gray-700 shadow-sm'
            }`}
          >
            {store === 'all' ? 'All Stores' : store}
          </button>
        ))}
      </div>

      {/* Purchase list */}
      <div className="mt-4 space-y-3">
        {filtered.length === 0 ? (
          <div className="rounded-xl bg-white p-6 text-center shadow-sm">
            <p className="text-sm text-gray-500">No purchases found for this filter.</p>
          </div>
        ) : (
          filtered.map((purchase) => (
            <Link
              key={purchase.id}
              to={`/purchases/${purchase.id}`}
              className="block rounded-xl bg-white p-4 shadow-sm active:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                <StoreIcon storeId={purchase.storeId} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900">{purchase.storeName}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(purchase.date).toLocaleDateString('en-US', {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">${purchase.total.toFixed(2)}</p>
                  <p className="text-xs text-gray-500">{purchase.items.length} items</p>
                </div>
              </div>

              {/* Item preview */}
              <p className="mt-2 truncate text-xs text-gray-400">
                {purchase.items
                  .slice(0, 3)
                  .map((i) => i.name)
                  .join(', ')}
                {purchase.items.length > 3 && ` +${purchase.items.length - 3} more`}
              </p>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
