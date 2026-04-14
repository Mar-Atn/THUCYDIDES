/**
 * Update password page — reached via reset email link.
 */

import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export function UpdatePassword() {
  const { updatePassword } = useAuth()
  const navigate = useNavigate()

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)
    const { error: updateError } = await updatePassword(password)

    if (updateError) {
      setError(updateError.message)
      setLoading(false)
    } else {
      navigate('/dashboard')
    }
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="font-heading text-h1 text-text-primary">
            New Password
          </h1>
        </div>

        <div className="bg-card border border-border rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">
                New Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action transition-colors"
                placeholder="At least 6 characters"
              />
            </div>

            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action transition-colors"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="bg-danger/10 border border-danger/20 rounded px-3 py-2">
                <p className="font-body text-caption text-danger">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 px-4 rounded hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
