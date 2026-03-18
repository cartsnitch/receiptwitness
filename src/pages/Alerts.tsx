import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePriceAlerts } from '../hooks/useApi.ts'
import type { PriceAlert } from '../types/api.ts'

export function Alerts() {
  const { data: fetchedAlerts = [], isLoading, error } = usePriceAlerts()
  const [localAlerts, setLocalAlerts] = useState<PriceAlert[]>([])
  const [deletedIds, setDeletedIds] = useState<Set<string>>(new Set())
  const [showCreate, setShowCreate] = useState(false)

  // Merge fetched + locally created, minus deleted
  const alerts = [
    ...localAlerts,
    ...fetchedAlerts.filter((a) => !deletedIds.has(a.id)),
  ]

  const triggered = alerts.filter((a) => a.triggered)
  const watching = alerts.filter((a) => !a.triggered)

  function handleDelete(id: string) {
    setLocalAlerts((prev) => prev.filter((a) => a.id !== id))
    setDeletedIds((prev) => new Set(prev).add(id))
  }

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-32 rounded bg-gray-200" />
        <div className="mt-6 space-y-3">
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
        <p className="text-sm text-red-600">Failed to load price alerts.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Price Alerts</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="min-h-12 rounded-full bg-brand-blue px-4 text-sm font-medium text-white active:bg-brand-blue/90"
        >
          + New Alert
        </button>
      </div>

      {/* Create alert form */}
      {showCreate && <CreateAlertForm onClose={() => setShowCreate(false)} onCreated={(a) => {
        setLocalAlerts((prev) => [a, ...prev])
        setShowCreate(false)
      }} />}

      {/* Triggered alerts */}
      {triggered.length > 0 && (
        <section className="mt-6">
          <h2 className="mb-3 text-sm font-semibold text-green-700">
            Triggered ({triggered.length})
          </h2>
          <div className="space-y-3">
            {triggered.map((alert) => (
              <AlertCard key={alert.id} alert={alert} onDelete={handleDelete} />
            ))}
          </div>
        </section>
      )}

      {/* Watching alerts */}
      <section className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-gray-500">
          Watching ({watching.length})
        </h2>
        {watching.length === 0 ? (
          <div className="rounded-xl bg-white p-6 text-center shadow-sm">
            <p className="text-sm text-gray-500">
              No active alerts.{' '}
              <Link to="/products" className="text-brand-blue">
                Search products
              </Link>{' '}
              to set one up.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {watching.map((alert) => (
              <AlertCard key={alert.id} alert={alert} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function AlertCard({
  alert,
  onDelete,
}: {
  alert: PriceAlert
  onDelete: (id: string) => void
}) {
  const priceDiff = alert.currentPrice - alert.targetPrice
  const isBelow = priceDiff <= 0

  return (
    <div
      className={`rounded-xl p-4 shadow-sm ${
        alert.triggered ? 'border border-green-200 bg-green-50' : 'bg-white'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <Link to={`/products/${alert.productId}`} className="text-sm font-medium text-gray-900">
            {alert.productName}
          </Link>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-xs text-gray-500">Target: ${alert.targetPrice.toFixed(2)}</span>
            <span className="text-xs text-gray-400">&middot;</span>
            <span className={`text-xs font-medium ${isBelow ? 'text-green-700' : 'text-gray-500'}`}>
              Now: ${alert.currentPrice.toFixed(2)}
            </span>
          </div>
          {alert.triggered && (
            <p className="mt-1 text-xs font-medium text-green-700">
              Price dropped ${Math.abs(priceDiff).toFixed(2)} below target
            </p>
          )}
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-2">
          {alert.triggered && (
            <span className="flex h-3 w-3 rounded-full bg-green-500" />
          )}
          <button
            onClick={() => onDelete(alert.id)}
            className="min-h-12 min-w-12 rounded-lg p-2 text-gray-400 active:bg-gray-100"
            aria-label="Delete alert"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
            </svg>
          </button>
        </div>
      </div>

      {/* Progress bar toward target */}
      {!alert.triggered && (
        <div className="mt-3">
          <div className="h-1.5 rounded-full bg-gray-100">
            <div
              className="h-1.5 rounded-full bg-brand-blue-light"
              style={{
                width: `${Math.min(100, Math.max(5, (1 - priceDiff / alert.currentPrice) * 100))}%`,
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function CreateAlertForm({
  onClose,
  onCreated,
}: {
  onClose: () => void
  onCreated: (alert: PriceAlert) => void
}) {
  const [productName, setProductName] = useState('')
  const [targetPrice, setTargetPrice] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!productName || !targetPrice) return

    onCreated({
      id: `a-${Date.now()}`,
      productId: `prod-${Date.now()}`,
      productName,
      targetPrice: parseFloat(targetPrice),
      currentPrice: parseFloat(targetPrice) + 0.50,
      triggered: false,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 space-y-3 rounded-xl bg-white p-4 shadow-sm">
      <input
        type="text"
        placeholder="Product name"
        value={productName}
        onChange={(e) => setProductName(e.target.value)}
        className="min-h-12 w-full rounded-xl border border-gray-200 px-4 text-base focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
      />
      <input
        type="number"
        step="0.01"
        placeholder="Target price"
        value={targetPrice}
        onChange={(e) => setTargetPrice(e.target.value)}
        className="min-h-12 w-full rounded-xl border border-gray-200 px-4 text-base focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
      />
      <div className="flex gap-3">
        <button
          type="submit"
          className="min-h-12 flex-1 rounded-xl bg-brand-blue px-4 py-3 text-base font-medium text-white active:bg-brand-blue/90"
        >
          Create Alert
        </button>
        <button
          type="button"
          onClick={onClose}
          className="min-h-12 rounded-xl border border-gray-200 px-4 py-3 text-base font-medium text-gray-700 active:bg-gray-50"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
