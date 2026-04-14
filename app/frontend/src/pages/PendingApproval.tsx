/**
 * Pending approval page — shown to moderators awaiting confirmation.
 */

import { useAuth } from '@/contexts/AuthContext'

export function PendingApproval() {
  const { profile, signOut, refreshProfile } = useAuth()

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4">
      <div className="bg-card border border-border rounded-lg p-8 max-w-sm w-full text-center">
        <h2 className="font-heading text-h2 text-text-primary mb-4">
          Pending Approval
        </h2>
        <p className="font-body text-body-sm text-text-secondary mb-6">
          Your moderator account is waiting for approval from an existing
          moderator. You'll be able to access the dashboard once approved.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => refreshProfile()}
            className="bg-action text-white font-body text-body-sm font-medium py-2 px-4 rounded hover:opacity-90 transition-opacity"
          >
            Check Status
          </button>
          <button
            onClick={() => signOut()}
            className="bg-base text-text-secondary border border-border font-body text-body-sm font-medium py-2 px-4 rounded hover:bg-border/30 transition-colors"
          >
            Sign Out
          </button>
        </div>
        {profile && (
          <p className="font-body text-caption text-text-secondary mt-4">
            Signed in as {profile.email}
          </p>
        )}
      </div>
    </div>
  )
}
