import { useState } from 'react'
import { useCoupons } from '../hooks/useApi.ts'
import { StoreIcon } from '../components/StoreIcon.tsx'

const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000

function isExpiringSoon(expiresAt: string): boolean {
  return new Date(expiresAt).getTime() - Date.now() < SEVEN_DAYS_MS
}

export function Coupons() {
  const { data: coupons = [], isLoading, error } = useCoupons()
  const [copied, setCopied] = useState<string | null>(null)

  function handleCopy(code: string, id: string) {
    navigator.clipboard?.writeText(code)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  const storeIds: Record<string, string> = {
    Meijer: 'meijer',
    Kroger: 'kroger',
    Target: 'target',
  }

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-40 rounded bg-gray-200" />
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
        <p className="text-sm text-red-600">Failed to load coupons.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Coupons & Deals</h1>

      <div className="mt-4 space-y-3">
        {coupons.map((coupon) => {
          const expiringSoon = isExpiringSoon(coupon.expiresAt)

          return (
            <div key={coupon.id} className="rounded-xl bg-white p-4 shadow-sm">
              <div className="flex items-start gap-3">
                <StoreIcon storeId={storeIds[coupon.storeName] ?? 'unknown'} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900">{coupon.description}</p>
                  <p className="mt-0.5 text-xs text-gray-500">{coupon.storeName}</p>
                  <p
                    className={`mt-1 text-xs ${
                      expiringSoon ? 'font-medium text-orange-600' : 'text-gray-400'
                    }`}
                  >
                    Expires{' '}
                    {new Date(coupon.expiresAt).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })}
                    {expiringSoon && ' — expiring soon!'}
                  </p>
                </div>
                <span className="shrink-0 rounded-lg bg-green-100 px-2 py-1 text-sm font-bold text-green-700">
                  {coupon.discount}
                </span>
              </div>

              {coupon.code && (
                <button
                  onClick={() => handleCopy(coupon.code!, coupon.id)}
                  className="mt-3 flex min-h-12 w-full items-center justify-center gap-2 rounded-lg border border-dashed border-gray-300 px-4 py-2 text-sm font-mono active:bg-gray-50"
                >
                  <span className="text-gray-700">{coupon.code}</span>
                  <span className="text-xs text-brand-blue">
                    {copied === coupon.id ? 'Copied!' : 'Tap to copy'}
                  </span>
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
