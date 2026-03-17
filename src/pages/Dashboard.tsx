import React, { Suspense } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../stores/auth.ts'
import { mockPurchases, mockAlerts, getMockPriceHistory } from '../lib/mock-data.ts'
import { StoreIcon } from '../components/StoreIcon.tsx'

const LazySparklineCard = React.lazy(() =>
  import('../components/SparklineChart.tsx').then((mod) => ({ default: mod.SparklineCard }))
)

const sparklineData = getMockPriceHistory('prod10').filter((p) => p.storeId === 'meijer').slice(-8)
const milkSparkline = getMockPriceHistory('prod1').filter((p) => p.storeId === 'kroger').slice(-8)

export function Dashboard() {
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  const triggeredAlerts = mockAlerts.filter((a) => a.triggered)
  const watchingAlerts = mockAlerts.filter((a) => !a.triggered)
  const recentPurchases = mockPurchases.slice(0, 3)

  if (!isAuthenticated) {
    return (
      <div className="py-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900">CartSnitch</h1>
        <p className="mt-2 text-sm text-gray-500">Track prices. Save money.</p>
        <div className="mt-8 space-y-3">
          <Link
            to="/login"
            className="block min-h-12 rounded-xl bg-brand-blue px-4 py-3 text-center text-base font-medium text-white active:bg-brand-blue/90"
          >
            Sign In
          </Link>
          <Link
            to="/register"
            className="block min-h-12 rounded-xl border border-gray-200 px-4 py-3 text-center text-base font-medium text-gray-700 active:bg-gray-50"
          >
            Create Account
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">
        Hi, {user?.name?.split(' ')[0] ?? 'there'}
      </h1>

      {/* Triggered alerts banner */}
      {triggeredAlerts.length > 0 && (
        <Link
          to="/alerts"
          className="mt-4 flex items-center gap-3 rounded-xl bg-green-50 p-4"
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500 text-lg text-white">
            &#x2713;
          </span>
          <div>
            <p className="text-sm font-semibold text-green-800">
              {triggeredAlerts.length} price {triggeredAlerts.length === 1 ? 'alert' : 'alerts'} triggered!
            </p>
            <p className="text-xs text-green-700">
              {triggeredAlerts.map((a) => a.productName).join(', ')}
            </p>
          </div>
        </Link>
      )}

      {/* Quick stats */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500">Watching</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{watchingAlerts.length}</p>
          <p className="text-xs text-gray-400">price alerts</p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500">This Month</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            ${recentPurchases.reduce((sum, p) => sum + p.total, 0).toFixed(0)}
          </p>
          <p className="text-xs text-gray-400">grocery spend</p>
        </div>
      </div>

      {/* Price trend sparklines */}
      <section className="mt-6">
        <h2 className="mb-3 text-lg font-semibold text-gray-700">Price Trends</h2>
        <div className="space-y-3">
          <Suspense fallback={<SparklinePlaceholder />}>
            <LazySparklineCard label="Eggs (dozen)" data={sparklineData} current="$5.44" />
            <LazySparklineCard label="Whole Milk (1 gal)" data={milkSparkline} current="$3.29" />
          </Suspense>
        </div>
      </section>

      {/* Recent purchases */}
      <section className="mt-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-700">Recent Purchases</h2>
          <Link to="/purchases" className="text-sm text-brand-blue">
            View all
          </Link>
        </div>
        <div className="mt-3 space-y-3">
          {recentPurchases.map((purchase) => (
            <Link
              key={purchase.id}
              to={`/purchases/${purchase.id}`}
              className="flex items-center gap-3 rounded-xl bg-white p-4 shadow-sm active:bg-gray-50"
            >
              <StoreIcon storeId={purchase.storeId} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900">{purchase.storeName}</p>
                <p className="text-xs text-gray-500">
                  {new Date(purchase.date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })}{' '}
                  &middot; {purchase.items.length} items
                </p>
              </div>
              <span className="text-sm font-semibold text-gray-900">
                ${purchase.total.toFixed(2)}
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Quick actions */}
      <section className="mt-6 pb-4">
        <h2 className="mb-3 text-lg font-semibold text-gray-700">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-3">
          <Link
            to="/products"
            className="flex min-h-12 items-center justify-center rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-medium text-gray-700 shadow-sm active:bg-gray-50"
          >
            Compare Prices
          </Link>
          <Link
            to="/settings"
            className="flex min-h-12 items-center justify-center rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-medium text-gray-700 shadow-sm active:bg-gray-50"
          >
            Link a Store
          </Link>
        </div>
      </section>
    </div>
  )
}

function SparklinePlaceholder() {
  return (
    <div className="flex items-center gap-4 rounded-xl bg-white p-4 shadow-sm animate-pulse">
      <div className="min-w-0 flex-1">
        <div className="h-4 w-24 rounded bg-gray-200" />
        <div className="mt-2 h-6 w-16 rounded bg-gray-200" />
      </div>
      <div className="h-10 w-24 rounded bg-gray-100" />
    </div>
  )
}
