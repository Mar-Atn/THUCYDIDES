/**
 * Registration page — display name, email, password, role selection.
 * Data consent is collected during sign-up.
 */

import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { DataConsentModal } from '@/components/DataConsentModal'

export function Register() {
  const { signUp, signInWithGoogle } = useAuth()
  const navigate = useNavigate()

  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [systemRole, setSystemRole] = useState<'moderator' | 'participant'>(
    'participant'
  )
  const [showConsent, setShowConsent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    // Show consent modal before proceeding
    setShowConsent(true)
  }

  const handleConsentAccepted = async () => {
    setShowConsent(false)
    setLoading(true)

    const { error: signUpError } = await signUp(
      email,
      password,
      displayName,
      systemRole
    )

    if (signUpError) {
      setError(signUpError.message)
      setLoading(false)
    } else {
      setSuccess(true)
      setTimeout(() => {
        navigate('/dashboard')
      }, 1500)
    }
  }

  if (showConsent) {
    return (
      <DataConsentModal
        onAccept={handleConsentAccepted}
        onCancel={() => setShowConsent(false)}
      />
    )
  }

  if (success) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center px-4">
        <div className="bg-card border border-border rounded-lg p-8 max-w-sm w-full text-center">
          <div className="text-success text-h1 mb-4">&#10003;</div>
          <h2 className="font-heading text-h2 text-text-primary mb-2">
            Account Created
          </h2>
          <p className="font-body text-body-sm text-text-secondary">
            {systemRole === 'moderator'
              ? 'Your moderator account is being set up...'
              : 'Redirecting to your dashboard...'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <img src="/logo-96.png" alt="TTT" className="w-16 h-16 mx-auto mb-3" />
          <h1 className="font-heading text-h1 text-text-primary">
            Thucydides Trap
          </h1>
          <p className="font-body text-body-sm text-text-secondary mt-2">
            Create your account
          </p>
        </div>

        {/* Card */}
        <div className="bg-card border border-border rounded-lg p-6">
          {/* Google */}
          <button
            onClick={() => signInWithGoogle()}
            className="w-full flex items-center justify-center gap-2 bg-base border border-border text-text-primary font-body text-body-sm font-medium py-2.5 px-4 rounded hover:bg-border/30 transition-colors mb-4"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Sign up with Google
          </button>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-border" />
            <span className="font-body text-caption text-text-secondary">
              or
            </span>
            <div className="flex-1 h-px bg-border" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Display Name */}
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action transition-colors"
                placeholder="How you'll appear in the simulation"
              />
            </div>

            {/* Email */}
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action transition-colors"
                placeholder="you@example.com"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">
                Password
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

            {/* Confirm Password */}
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action transition-colors"
                placeholder="••••••••"
              />
            </div>

            {/* Role Selection */}
            <div>
              <label className="block font-body text-caption text-text-secondary mb-2">
                I am a...
              </label>
              <div className="flex gap-3">
                <label
                  className={`flex-1 flex items-center justify-center gap-2 border rounded px-3 py-2.5 cursor-pointer transition-colors ${
                    systemRole === 'participant'
                      ? 'border-action bg-action/5 text-action'
                      : 'border-border text-text-secondary hover:border-text-secondary/50'
                  }`}
                >
                  <input
                    type="radio"
                    name="role"
                    value="participant"
                    checked={systemRole === 'participant'}
                    onChange={() => setSystemRole('participant')}
                    className="sr-only"
                  />
                  <span className="font-body text-body-sm font-medium">
                    Participant
                  </span>
                </label>
                <label
                  className={`flex-1 flex items-center justify-center gap-2 border rounded px-3 py-2.5 cursor-pointer transition-colors ${
                    systemRole === 'moderator'
                      ? 'border-action bg-action/5 text-action'
                      : 'border-border text-text-secondary hover:border-text-secondary/50'
                  }`}
                >
                  <input
                    type="radio"
                    name="role"
                    value="moderator"
                    checked={systemRole === 'moderator'}
                    onChange={() => setSystemRole('moderator')}
                    className="sr-only"
                  />
                  <span className="font-body text-body-sm font-medium">
                    Moderator
                  </span>
                </label>
              </div>
              {systemRole === 'moderator' && (
                <p className="font-body text-caption text-warning mt-2">
                  Moderator accounts require approval from an existing moderator.
                </p>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="bg-danger/10 border border-danger/20 rounded px-3 py-2">
                <p className="font-body text-caption text-danger">{error}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 px-4 rounded hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          {/* Link to login */}
          <div className="mt-4 text-center">
            <Link
              to="/login"
              className="font-body text-caption text-action hover:underline"
            >
              Already have an account? Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
