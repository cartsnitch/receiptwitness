import { useState } from 'react'
import { Link } from 'react-router-dom'
import { StoreIcon } from '../components/StoreIcon.tsx'

interface StoreConfig {
  id: string
  name: string
  description: string
  fields: { key: string; label: string; type: string }[]
}

const availableStores: StoreConfig[] = [
  {
    id: 'meijer',
    name: 'Meijer',
    description: 'Connect your mPerks account to import purchase history.',
    fields: [
      { key: 'email', label: 'mPerks Email', type: 'email' },
      { key: 'password', label: 'mPerks Password', type: 'password' },
    ],
  },
  {
    id: 'kroger',
    name: 'Kroger',
    description: 'Connect your Kroger Plus account for receipts and digital coupons.',
    fields: [
      { key: 'email', label: 'Kroger Email', type: 'email' },
      { key: 'password', label: 'Kroger Password', type: 'password' },
    ],
  },
  {
    id: 'target',
    name: 'Target',
    description: 'Connect Target Circle for purchase history and deals.',
    fields: [
      { key: 'email', label: 'Target Email', type: 'email' },
      { key: 'password', label: 'Target Password', type: 'password' },
    ],
  },
]

export function AccountLinking() {
  const [linking, setLinking] = useState<string | null>(null)
  const [connected, setConnected] = useState<string[]>(['meijer', 'kroger'])
  const [status, setStatus] = useState<'idle' | 'connecting' | 'success' | 'error'>('idle')

  function handleConnect(storeId: string) {
    setStatus('connecting')
    // Simulate connection — fields will be sent to API when available
    setTimeout(() => {
      setConnected((prev) => [...prev, storeId])
      setStatus('success')
      setTimeout(() => {
        setLinking(null)
        setStatus('idle')
      }, 1500)
    }, 2000)
  }

  function handleDisconnect(storeId: string) {
    setConnected((prev) => prev.filter((s) => s !== storeId))
  }

  return (
    <div>
      <Link to="/settings" className="inline-flex items-center gap-1 text-sm text-brand-blue">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Settings
      </Link>

      <h1 className="mt-4 text-2xl font-bold text-gray-900">Connect a Store</h1>
      <p className="mt-1 text-sm text-gray-500">
        Link your store loyalty accounts to automatically import purchases and track prices.
      </p>

      <div className="mt-6 space-y-4">
        {availableStores.map((store) => {
          const isConnected = connected.includes(store.id)
          const isLinking = linking === store.id

          return (
            <div key={store.id} className="rounded-xl bg-white p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <StoreIcon storeId={store.id} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900">{store.name}</p>
                  <p className="text-xs text-gray-500">
                    {isConnected ? 'Connected' : store.description}
                  </p>
                </div>
                {isConnected ? (
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-500 text-xs text-white">
                    &#x2713;
                  </span>
                ) : null}
              </div>

              {isConnected && !isLinking && (
                <button
                  onClick={() => handleDisconnect(store.id)}
                  className="mt-3 min-h-12 w-full rounded-xl border border-red-200 px-4 py-2 text-sm font-medium text-red-600 active:bg-red-50"
                >
                  Disconnect
                </button>
              )}

              {!isConnected && !isLinking && (
                <button
                  onClick={() => setLinking(store.id)}
                  className="mt-3 min-h-12 w-full rounded-xl bg-brand-blue px-4 py-3 text-base font-medium text-white active:bg-brand-blue/90"
                >
                  Connect {store.name}
                </button>
              )}

              {isLinking && (
                <LinkForm
                  store={store}
                  status={status}
                  onSubmit={() => handleConnect(store.id)}
                  onCancel={() => {
                    setLinking(null)
                    setStatus('idle')
                  }}
                />
              )}
            </div>
          )
        })}
      </div>

      <div className="mt-6 rounded-xl bg-blue-50 p-4">
        <p className="text-xs text-blue-700">
          Your credentials are encrypted and stored securely. CartSnitch never shares your login
          information with third parties.
        </p>
      </div>
    </div>
  )
}

function LinkForm({
  store,
  status,
  onSubmit,
  onCancel,
}: {
  store: StoreConfig
  status: string
  onSubmit: () => void
  onCancel: () => void
}) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(store.fields.map((f) => [f.key, ''])),
  )

  return (
    <div className="mt-3 space-y-3">
      {store.fields.map((field) => (
        <input
          key={field.key}
          type={field.type}
          placeholder={field.label}
          value={values[field.key] ?? ''}
          onChange={(e) => setValues((prev) => ({ ...prev, [field.key]: e.target.value }))}
          autoComplete={field.type === 'password' ? 'current-password' : field.type}
          className="min-h-12 w-full rounded-xl border border-gray-200 px-4 text-base focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
        />
      ))}

      {status === 'connecting' && (
        <div className="flex items-center gap-2 rounded-xl bg-blue-50 px-4 py-3">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand-blue border-t-transparent" />
          <span className="text-sm text-blue-700">Connecting to {store.name}...</span>
        </div>
      )}

      {status === 'success' && (
        <div className="rounded-xl bg-green-50 px-4 py-3 text-sm text-green-700">
          Connected successfully!
        </div>
      )}

      {status === 'error' && (
        <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          Connection failed. Please check your credentials and try again.
        </div>
      )}

      {status === 'idle' && (
        <div className="flex gap-3">
          <button
            onClick={onSubmit}
            className="min-h-12 flex-1 rounded-xl bg-brand-blue px-4 py-3 text-base font-medium text-white active:bg-brand-blue/90"
          >
            Connect
          </button>
          <button
            onClick={onCancel}
            className="min-h-12 rounded-xl border border-gray-200 px-4 py-3 text-base font-medium text-gray-700 active:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  )
}
