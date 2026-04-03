import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authClient } from '../lib/auth-client.ts'
import { useAuthStore } from '../stores/auth.ts'
import { useThemeStore } from '../stores/theme.ts'
import { StoreIcon } from '../components/StoreIcon.tsx'

export function Settings() {
  const { data: session } = authClient.useSession()
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated)
  const navigate = useNavigate()
  const { theme, setTheme } = useThemeStore()
  const [emailInAddress, setEmailInAddress] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!session?.user) return
    fetch('/api/v1/me/email-in-address', {
      credentials: 'include',
    })
      .then((res) => res.json())
      .then((data) => setEmailInAddress(data.email_address))
      .catch(() => setEmailInAddress(null))
  }, [session])

  async function handleCopyEmail() {
    if (emailInAddress) {
      await navigator.clipboard.writeText(emailInAddress)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const user = session?.user
  const connectedStores: string[] = []

  async function handleSignOut() {
    await authClient.signOut()
    setAuthenticated(false)
    navigate('/login')
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {/* Profile section */}
      <section className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-gray-500">Profile</h2>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-blue text-lg font-bold text-white">
              {user?.name?.charAt(0) ?? '?'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-900">{user?.name ?? 'Guest'}</p>
              <p className="truncate text-xs text-gray-500">{user?.email ?? ''}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Connected stores */}
      <section className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-gray-500">Connected Stores</h2>
        <div className="rounded-xl bg-white shadow-sm">
          {connectedStores.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {connectedStores.map((storeId) => (
                <div key={storeId} className="flex items-center gap-3 px-4 py-3">
                  <StoreIcon storeId={storeId} size="sm" />
                  <span className="text-sm font-medium text-gray-900 capitalize">{storeId}</span>
                  <span className="ml-auto text-xs text-green-600">Connected</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4">
              <p className="text-sm text-gray-500">No stores connected yet.</p>
            </div>
          )}
          <div className="border-t border-gray-100 p-3">
            <Link
              to="/account-linking"
              className="flex min-h-12 items-center justify-center rounded-xl bg-brand-blue px-4 py-3 text-base font-medium text-white active:bg-brand-blue/90"
            >
              {connectedStores.length > 0 ? 'Manage Stores' : 'Connect a Store'}
            </Link>
          </div>
        </div>
      </section>

      {/* Notifications */}
      <section className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-gray-500">Notifications</h2>
        <div className="rounded-xl bg-white shadow-sm">
          <SettingsToggle label="Price alert notifications" defaultChecked />
          <SettingsToggle label="Weekly deals digest" defaultChecked />
          <SettingsToggle label="Purchase import confirmations" />
        </div>
      </section>

      {/* Appearance */}
      <section className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-gray-500">Appearance</h2>
        <div className="rounded-xl bg-white shadow-sm">
          <div className="flex gap-2 p-3">
            {(['light', 'dark', 'system'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTheme(t)}
                className={`min-h-12 flex-1 rounded-lg px-3 py-2 text-sm font-medium capitalize ${
                  theme === t
                    ? 'bg-brand-blue text-white'
                    : 'bg-gray-100 text-gray-700 active:bg-gray-200'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Account actions */}
      <section className="mt-6 pb-4">
        <h2 className="mb-3 text-sm font-semibold text-gray-500">Account</h2>
        <div className="rounded-xl bg-white shadow-sm">
          <button
            onClick={handleSignOut}
            className="min-h-12 w-full rounded-xl px-4 py-3 text-base font-medium text-red-600 active:bg-red-50"
          >
            Sign Out
          </button>
        </div>
      </section>

      {/* Receipt Email section */}
      <section className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-gray-500">Receipt Email</h2>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="mb-2 text-sm text-gray-600">
            Forward your digital receipt emails to this address:
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 rounded-lg bg-gray-100 px-3 py-2 text-sm font-mono text-gray-800 truncate">
              {emailInAddress ?? 'Loading...'}
            </code>
            <button
              onClick={handleCopyEmail}
              className="rounded-lg bg-brand-blue px-3 py-2 text-sm font-medium text-white hover:bg-brand-blue/90 transition-colors"
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-400">
            Supports Meijer, Kroger, and Target receipt emails.
          </p>
        </div>
      </section>
    </div>
  )
}

function SettingsToggle({
  label,
  defaultChecked = false,
}: {
  label: string
  defaultChecked?: boolean
}) {
  return (
    <label className="flex min-h-12 cursor-pointer items-center justify-between px-4 py-3">
      <span className="text-sm text-gray-900">{label}</span>
      <input
        type="checkbox"
        defaultChecked={defaultChecked}
        className="h-5 w-5 rounded border-gray-300 text-brand-blue focus:ring-brand-blue"
      />
    </label>
  )
}
