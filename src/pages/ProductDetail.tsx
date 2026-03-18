import { useParams, Link } from 'react-router-dom'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { useProduct, usePriceHistory } from '../hooks/useApi.ts'

const storeLineColors: Record<string, string> = {
  meijer: '#e31837',
  kroger: '#0068a8',
  target: '#cc0000',
}

export function ProductDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: product, isLoading: productLoading } = useProduct(id ?? '')
  const { data: history = [], isLoading: historyLoading } = usePriceHistory(id ?? '')

  if (productLoading || historyLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 w-20 rounded bg-gray-200" />
        <div className="mt-4 h-8 w-48 rounded bg-gray-200" />
        <div className="mt-6 h-52 rounded-xl bg-gray-200" />
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

  const lowestPrice = Math.min(...product.prices.map((p) => p.price))

  // Reshape history for chart: { date, meijer, kroger, target }
  const chartData: Record<string, string | number>[] = []
  const dateMap = new Map<string, Record<string, string | number>>()
  for (const h of history) {
    if (!dateMap.has(h.date)) {
      dateMap.set(h.date, { date: h.date })
    }
    dateMap.get(h.date)![h.storeId] = h.price
  }
  for (const entry of dateMap.values()) {
    chartData.push(entry)
  }

  return (
    <div>
      {/* Back link */}
      <Link to="/products" className="inline-flex items-center gap-1 text-sm text-brand-blue">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Products
      </Link>

      {/* Product header */}
      <div className="mt-4">
        <h1 className="text-2xl font-bold text-gray-900">{product.name}</h1>
        <p className="text-sm text-gray-500">
          {product.brand} &middot; {product.category}
        </p>
      </div>

      {/* Price history chart */}
      <section className="mt-6">
        <h2 className="mb-3 text-lg font-semibold text-gray-700">Price History (90 days)</h2>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10 }}
                  tickFormatter={(d: string) => {
                    const dt = new Date(d)
                    return `${dt.getMonth() + 1}/${dt.getDate()}`
                  }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 10 }}
                  domain={['auto', 'auto']}
                  tickFormatter={(v: number) => `$${v.toFixed(2)}`}
                />
                <Tooltip
                  formatter={(value) => `$${Number(value).toFixed(2)}`}
                  labelFormatter={(label) =>
                    new Date(String(label)).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })
                  }
                />
                <Legend />
                {['meijer', 'kroger', 'target'].map((store) => (
                  <Line
                    key={store}
                    type="monotone"
                    dataKey={store}
                    name={store.charAt(0).toUpperCase() + store.slice(1)}
                    stroke={storeLineColors[store]}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* Store comparison table */}
      <section className="mt-6">
        <h2 className="mb-3 text-lg font-semibold text-gray-700">Store Comparison</h2>
        <div className="rounded-xl bg-white shadow-sm">
          <div className="divide-y divide-gray-100">
            {product.prices
              .slice()
              .sort((a, b) => a.price - b.price)
              .map((pp) => (
                <div
                  key={pp.storeId}
                  className="flex items-center justify-between px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`inline-flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-white ${
                        pp.storeId === 'meijer'
                          ? 'bg-meijer-red'
                          : pp.storeId === 'kroger'
                            ? 'bg-kroger-blue'
                            : 'bg-target-red'
                      }`}
                    >
                      {pp.storeName.charAt(0)}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{pp.storeName}</p>
                      <p className="text-xs text-gray-500">
                        Updated{' '}
                        {new Date(pp.lastUpdated).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p
                      className={`text-sm font-bold ${
                        pp.price === lowestPrice ? 'text-green-700' : 'text-gray-900'
                      }`}
                    >
                      ${pp.price.toFixed(2)}
                    </p>
                    {pp.price === lowestPrice && (
                      <span className="text-xs text-green-600">Best price</span>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </div>
      </section>

      {/* Actions */}
      <div className="mt-6 space-y-3 pb-4">
        <Link
          to="/alerts"
          className="flex min-h-12 items-center justify-center rounded-xl bg-brand-blue px-4 py-3 text-base font-medium text-white active:bg-brand-blue/90"
        >
          Set Price Alert
        </Link>
        <Link
          to={`/compare/${product.id}`}
          className="flex min-h-12 items-center justify-center rounded-xl border border-gray-200 px-4 py-3 text-base font-medium text-gray-700 active:bg-gray-50"
        >
          Compare at Nearby Stores
        </Link>
      </div>
    </div>
  )
}
