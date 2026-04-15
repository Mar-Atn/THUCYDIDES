import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { App } from '@/App'
import './index.css'

// StrictMode removed intentionally — it causes double-mounting which
// creates navigator lock contention with Supabase Auth (PKCE flow).
// Same approach as KING SIM. See: https://github.com/supabase/auth-js/issues/888
createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <AuthProvider>
      <App />
    </AuthProvider>
  </BrowserRouter>,
)
