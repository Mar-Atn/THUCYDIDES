/**
 * Shared header bar — displayed on all authenticated pages.
 * Shows app title, user name, role badge, sign out.
 */

import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

interface HeaderProps {
  subtitle?: string
}

export function Header({ subtitle }: HeaderProps) {
  const { profile, signOut } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="bg-card border-b border-border px-6 py-4 flex items-center justify-between">
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-3 hover:opacity-80 transition-opacity"
      >
        <img
          src="/logo-96.png"
          alt="TTT"
          className="w-14 h-14"
        />
        <div className="text-left">
          <h1 className="font-heading text-h3 text-text-primary">
            Thucydides Trap
          </h1>
          {subtitle && (
            <p className="font-body text-caption text-text-secondary">
              {subtitle}
            </p>
          )}
        </div>
      </button>
      <div className="flex items-center gap-3">
        <span className="font-body text-body-sm text-text-primary">
          {profile?.display_name}
        </span>
        <span
          className={`font-body text-caption font-medium px-2 py-0.5 rounded ${
            profile?.system_role === 'moderator'
              ? 'bg-action/10 text-action'
              : 'bg-accent/10 text-accent'
          }`}
        >
          {profile?.system_role}
        </span>
        <button
          onClick={() => signOut()}
          className="font-body text-caption text-text-secondary hover:text-action transition-colors"
        >
          Sign out
        </button>
      </div>
    </header>
  )
}
