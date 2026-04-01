import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './components/Layout.tsx'
import { ProtectedRoute } from './components/ProtectedRoute.tsx'
import { Dashboard } from './pages/Dashboard.tsx'
import { Purchases } from './pages/Purchases.tsx'
import { PurchaseDetail } from './pages/PurchaseDetail.tsx'
import { Products } from './pages/Products.tsx'
import { ProductDetail } from './pages/ProductDetail.tsx'
import { StoreComparison } from './pages/StoreComparison.tsx'
import { Coupons } from './pages/Coupons.tsx'
import { Alerts } from './pages/Alerts.tsx'
import { Settings } from './pages/Settings.tsx'
import { AccountLinking } from './pages/AccountLinking.tsx'
import { Login } from './pages/Login.tsx'
import { Register } from './pages/Register.tsx'
import { ForgotPassword } from './pages/ForgotPassword.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route element={<ProtectedRoute />}>
              <Route index element={<Dashboard />} />
              <Route path="purchases" element={<Purchases />} />
              <Route path="purchases/:id" element={<PurchaseDetail />} />
              <Route path="products" element={<Products />} />
              <Route path="products/:id" element={<ProductDetail />} />
              <Route path="compare/:productId" element={<StoreComparison />} />
              <Route path="coupons" element={<Coupons />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="settings" element={<Settings />} />
              <Route path="account-linking" element={<AccountLinking />} />
            </Route>
          </Route>
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route path="forgot-password" element={<ForgotPassword />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
