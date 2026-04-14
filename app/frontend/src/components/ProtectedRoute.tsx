/**
 * Protected Route — auth + consent + role gate.
 *
 * Sequence:
 *   Loading? → spinner
 *   Not authenticated? → redirect /login
 *   No consent? → consent modal
 *   Wrong role? → access denied
 *   Pending approval? → redirect /pending
 *   All clear → render children
 */

import { type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { DataConsentModal } from '@/components/DataConsentModal'

interface ProtectedRouteProps {
  children: ReactNode
  requireRole?: 'moderator' | 'participant'
}

export function ProtectedRoute({ children, requireRole }: ProtectedRouteProps) {
  const { user, profile, loading, grantConsent, signOut } = useAuth()

  // 1. Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="text-text-secondary font-body text-body-sm">
          Loading...
        </div>
      </div>
    )
  }

  // 2. Not authenticated
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // 3. No profile yet (still loading or registration incomplete)
  if (!profile) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="text-text-secondary font-body text-body-sm">
          Setting up your account...
        </div>
      </div>
    )
  }

  // 4. Consent gate
  if (!profile.data_consent) {
    return (
      <DataConsentModal
        onAccept={async () => await grantConsent()}
        onCancel={() => signOut()}
      />
    )
  }

  // 5. Pending approval (moderator waiting for confirmation)
  if (profile.status === 'pending_approval') {
    return <Navigate to="/pending" replace />
  }

  // 6. Suspended
  if (profile.status === 'suspended') {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="bg-card border border-border rounded-lg p-8 max-w-md w-full mx-4 text-center">
          <h2 className="font-heading text-h2 text-danger mb-4">
            Account Suspended
          </h2>
          <p className="font-body text-body-sm text-text-secondary mb-6">
            Your account has been suspended. Please contact the simulation
            moderator.
          </p>
          <button
            onClick={() => signOut()}
            className="bg-base text-text-secondary border border-border font-body text-body-sm font-medium py-2 px-4 rounded hover:bg-border/30 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>
    )
  }

  // 7. Role check
  if (requireRole && profile.system_role !== requireRole) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="bg-card border border-border rounded-lg p-8 max-w-md w-full mx-4 text-center">
          <h2 className="font-heading text-h2 text-text-primary mb-4">
            Access Denied
          </h2>
          <p className="font-body text-body-sm text-text-secondary">
            This page requires{' '}
            <span className="font-medium text-text-primary">{requireRole}</span>{' '}
            access.
          </p>
        </div>
      </div>
    )
  }

  // All clear
  return <>{children}</>
}
