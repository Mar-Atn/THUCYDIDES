/**
 * Password reset request page.
 */

import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export function ResetPassword() {
  const { resetPassword } = useAuth()
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const { error: resetError } = await resetPassword(email)

    if (resetError) {
      setError(resetError.message)
    } else {
      setSent(true)
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="font-heading text-h1 text-text-primary">
            Reset Password
          </h1>
        </div>

        <div className="bg-card border border-border rounded-lg p-6">
          {sent ? (
            <div className="text-center">
              <p className="font-body text-body-sm text-text-secondary mb-4">
                Check your email for a password reset link.
              </p>
              <Link
                to="/login"
                className="font-body text-caption text-action hover:underline"
              >
                Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <p className="font-body text-body-sm text-text-secondary mb-4">
                Enter your email and we'll send you a reset link.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action transition-colors"
                    placeholder="you@example.com"
                  />
                </div>

                {error && (
                  <div className="bg-danger/10 border border-danger/20 rounded px-3 py-2">
                    <p className="font-body text-caption text-danger">
                      {error}
                    </p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 px-4 rounded hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </button>
              </form>

              <div className="mt-4 text-center">
                <Link
                  to="/login"
                  className="font-body text-caption text-action hover:underline"
                >
                  Back to sign in
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
