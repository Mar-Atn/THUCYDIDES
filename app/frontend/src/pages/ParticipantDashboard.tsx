/**
 * Participant dashboard — stub for M10.1.
 * Real content (role view, action submission, etc.) comes in M6.
 */

import { useAuth } from '@/contexts/AuthContext'

export function ParticipantDashboard() {
  const { profile, signOut } = useAuth()

  return (
    <div className="min-h-screen bg-base">
      {/* Top bar */}
      <header className="bg-card border-b border-border px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="font-heading text-h3 text-text-primary">
            Thucydides Trap
          </h1>
          <p className="font-body text-caption text-text-secondary">
            Participant
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-body text-body-sm text-text-secondary">
            {profile?.display_name}
          </span>
          <button
            onClick={() => signOut()}
            className="font-body text-caption text-action hover:underline"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-6 py-12">
        <div className="bg-card border border-border rounded-lg p-8 text-center">
          <h2 className="font-heading text-h2 text-text-primary mb-4">
            Welcome, {profile?.display_name}
          </h2>
          <p className="font-body text-body text-text-secondary mb-2">
            You are registered as a <strong>participant</strong>.
          </p>
          <p className="font-body text-body-sm text-text-secondary">
            You will be assigned a role by the moderator before the simulation
            begins. Your country dashboard, available actions, and world view
            will appear here once the simulation starts.
          </p>
        </div>
      </main>
    </div>
  )
}
