/**
 * User Management — admin page for viewing and managing all registered users.
 * Moderator can approve, suspend, reactivate, and delete users.
 */

import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Header } from '@/components/Header'
import { useAuth } from '@/contexts/AuthContext'
import { getAllUsers, updateUserStatus, deleteUser, type UserRecord } from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Types                                                                     */
/* -------------------------------------------------------------------------- */

type SortField = 'display_name' | 'email' | 'system_role' | 'status' | 'created_at' | 'last_login_at'
type SortDir = 'asc' | 'desc'

/* -------------------------------------------------------------------------- */
/*  Badge helpers                                                             */
/* -------------------------------------------------------------------------- */

function roleBadgeClass(role: string): string {
  switch (role) {
    case 'moderator':
      return 'bg-action/10 text-action'
    case 'participant':
      return 'bg-accent/10 text-accent'
    default:
      return 'bg-base text-text-secondary'
  }
}

function statusBadgeClass(status: string): string {
  switch (status) {
    case 'active':
      return 'bg-success/10 text-success'
    case 'registered':
      return 'bg-action/10 text-action'
    case 'pending_approval':
      return 'bg-warning/10 text-warning'
    case 'suspended':
      return 'bg-danger/10 text-danger'
    default:
      return 'bg-base text-text-secondary'
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return 'Never'
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function statusLabel(status: string): string {
  switch (status) {
    case 'pending_approval':
      return 'Pending'
    default:
      return status.charAt(0).toUpperCase() + status.slice(1)
  }
}

/* -------------------------------------------------------------------------- */
/*  Component                                                                 */
/* -------------------------------------------------------------------------- */

export function UserManagement() {
  const { profile } = useAuth()
  const [users, setUsers] = useState<UserRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [sortField, setSortField] = useState<SortField>('created_at')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  /* ---- Data fetch ---- */

  const loadUsers = async () => {
    try {
      setError(null)
      const data = await getAllUsers()
      setUsers(data)
    } catch (e) {
      setError('Failed to load users.')
      console.error('User fetch error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [])

  /* ---- Sort toggle ---- */

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir('asc')
    }
  }

  /* ---- Filtered + sorted list ---- */

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    let list = users
    if (q) {
      list = list.filter(
        (u) =>
          u.display_name.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q)
      )
    }

    const sorted = [...list].sort((a, b) => {
      let aVal: string | null = ''
      let bVal: string | null = ''

      switch (sortField) {
        case 'display_name':
          aVal = a.display_name.toLowerCase()
          bVal = b.display_name.toLowerCase()
          break
        case 'email':
          aVal = a.email.toLowerCase()
          bVal = b.email.toLowerCase()
          break
        case 'system_role':
          aVal = a.system_role
          bVal = b.system_role
          break
        case 'status':
          aVal = a.status
          bVal = b.status
          break
        case 'created_at':
          aVal = a.created_at
          bVal = b.created_at
          break
        case 'last_login_at':
          aVal = a.last_login_at ?? ''
          bVal = b.last_login_at ?? ''
          break
      }

      if (aVal === null) aVal = ''
      if (bVal === null) bVal = ''

      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1
      return 0
    })

    return sorted
  }, [users, search, sortField, sortDir])

  /* ---- Actions ---- */

  const handleApprove = async (userId: string) => {
    setActionLoading(userId)
    try {
      await updateUserStatus(userId, 'active')
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, status: 'active' } : u))
      )
    } catch (e) {
      console.error('Approve failed:', e)
    } finally {
      setActionLoading(null)
    }
  }

  const handleSuspend = async (userId: string) => {
    setActionLoading(userId)
    try {
      await updateUserStatus(userId, 'suspended')
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, status: 'suspended' } : u))
      )
    } catch (e) {
      console.error('Suspend failed:', e)
    } finally {
      setActionLoading(null)
    }
  }

  const handleReactivate = async (userId: string) => {
    setActionLoading(userId)
    try {
      await updateUserStatus(userId, 'active')
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, status: 'active' } : u))
      )
    } catch (e) {
      console.error('Reactivate failed:', e)
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async (userId: string, displayName: string) => {
    if (!confirm(`Delete user "${displayName}"? This action cannot be undone.`)) return
    setActionLoading(userId)
    try {
      await deleteUser(userId)
      setUsers((prev) => prev.filter((u) => u.id !== userId))
    } catch (e) {
      console.error('Delete failed:', e)
    } finally {
      setActionLoading(null)
    }
  }

  /* ---- Sort indicator ---- */

  const sortIcon = (field: SortField) => {
    if (sortField !== field) return ' \u2195'
    return sortDir === 'asc' ? ' \u2191' : ' \u2193'
  }

  /* ---- Render ---- */

  return (
    <div className="min-h-screen bg-base">
      <Header subtitle="User Management" />

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Back link */}
        <Link
          to="/dashboard"
          className="font-body text-caption text-text-secondary hover:text-action transition-colors mb-6 inline-block"
        >
          &larr; Back to Dashboard
        </Link>

        {/* Page heading + search */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-heading text-h2 text-text-primary">
            Registered Users
          </h2>
          <div className="relative">
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="font-body text-body-sm bg-card border border-border rounded-lg px-4 py-2 w-72 text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action/50 transition-colors"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary text-sm"
              >
                &times;
              </button>
            )}
          </div>
        </div>

        {/* Loading / Error states */}
        {loading && (
          <p className="font-body text-body-sm text-text-secondary">
            Loading users...
          </p>
        )}

        {error && (
          <div className="bg-danger/10 border border-danger/20 rounded-lg p-4 mb-4">
            <p className="font-body text-body-sm text-danger">{error}</p>
          </div>
        )}

        {/* Table */}
        {!loading && !error && (
          <>
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <SortHeader
                      label="Display Name"
                      field="display_name"
                      current={sortField}
                      dir={sortDir}
                      icon={sortIcon}
                      onClick={handleSort}
                    />
                    <SortHeader
                      label="Email"
                      field="email"
                      current={sortField}
                      dir={sortDir}
                      icon={sortIcon}
                      onClick={handleSort}
                    />
                    <SortHeader
                      label="Role"
                      field="system_role"
                      current={sortField}
                      dir={sortDir}
                      icon={sortIcon}
                      onClick={handleSort}
                    />
                    <SortHeader
                      label="Status"
                      field="status"
                      current={sortField}
                      dir={sortDir}
                      icon={sortIcon}
                      onClick={handleSort}
                    />
                    <SortHeader
                      label="Registered"
                      field="created_at"
                      current={sortField}
                      dir={sortDir}
                      icon={sortIcon}
                      onClick={handleSort}
                    />
                    <SortHeader
                      label="Last Login"
                      field="last_login_at"
                      current={sortField}
                      dir={sortDir}
                      icon={sortIcon}
                      onClick={handleSort}
                    />
                    <th className="text-left font-body text-caption font-medium text-text-secondary px-4 py-3">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td
                        colSpan={7}
                        className="text-center font-body text-body-sm text-text-secondary py-12"
                      >
                        {search
                          ? 'No users match your search.'
                          : 'No registered users.'}
                      </td>
                    </tr>
                  ) : (
                    filtered.map((user) => {
                      const isSelf = user.id === profile?.id
                      const isLoading = actionLoading === user.id

                      return (
                        <tr
                          key={user.id}
                          className="border-b border-border/50 last:border-b-0 hover:bg-base/50 transition-colors"
                        >
                          {/* Display Name */}
                          <td className="px-4 py-3">
                            <span className="font-body text-body-sm text-text-primary">
                              {user.display_name}
                            </span>
                            {isSelf && (
                              <span className="ml-2 font-body text-caption text-text-secondary">
                                (you)
                              </span>
                            )}
                          </td>

                          {/* Email */}
                          <td className="px-4 py-3">
                            <span className="font-body text-body-sm text-text-secondary">
                              {user.email}
                            </span>
                          </td>

                          {/* Role badge */}
                          <td className="px-4 py-3">
                            <span
                              className={`font-body text-caption font-medium px-2 py-0.5 rounded ${roleBadgeClass(user.system_role)}`}
                            >
                              {user.system_role}
                            </span>
                          </td>

                          {/* Status badge */}
                          <td className="px-4 py-3">
                            <span
                              className={`font-body text-caption font-medium px-2 py-0.5 rounded ${statusBadgeClass(user.status)}`}
                            >
                              {statusLabel(user.status)}
                            </span>
                          </td>

                          {/* Registered date */}
                          <td className="px-4 py-3">
                            <span className="font-body text-caption text-text-secondary">
                              {formatDate(user.created_at)}
                            </span>
                          </td>

                          {/* Last login */}
                          <td className="px-4 py-3">
                            <span className="font-body text-caption text-text-secondary">
                              {formatDate(user.last_login_at)}
                            </span>
                          </td>

                          {/* Actions */}
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              {user.status === 'pending_approval' && (
                                <ActionButton
                                  label="Approve"
                                  className="text-success hover:underline"
                                  disabled={isLoading}
                                  onClick={() => handleApprove(user.id)}
                                />
                              )}

                              {(user.status === 'active' || user.status === 'registered') &&
                                !isSelf && (
                                  <ActionButton
                                    label="Suspend"
                                    className="text-warning hover:underline"
                                    disabled={isLoading}
                                    onClick={() => handleSuspend(user.id)}
                                  />
                                )}

                              {user.status === 'suspended' && (
                                <ActionButton
                                  label="Reactivate"
                                  className="text-action hover:underline"
                                  disabled={isLoading}
                                  onClick={() => handleReactivate(user.id)}
                                />
                              )}

                              {!isSelf && (
                                <ActionButton
                                  label="Delete"
                                  className="text-danger hover:underline"
                                  disabled={isLoading}
                                  onClick={() =>
                                    handleDelete(user.id, user.display_name)
                                  }
                                />
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Summary */}
            <p className="font-body text-caption text-text-secondary mt-4">
              {filtered.length} of {users.length} user{users.length !== 1 ? 's' : ''}
              {search ? ' matching search' : ''}
            </p>
          </>
        )}
      </main>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Sub-components                                                            */
/* -------------------------------------------------------------------------- */

/** Sortable column header cell. */
function SortHeader({
  label,
  field,
  current,
  dir,
  icon,
  onClick,
}: {
  label: string
  field: SortField
  current: SortField
  dir: SortDir
  icon: (f: SortField) => string
  onClick: (f: SortField) => void
}) {
  const isActive = current === field
  return (
    <th
      className={`text-left font-body text-caption font-medium px-4 py-3 cursor-pointer select-none transition-colors ${
        isActive ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary'
      }`}
      onClick={() => onClick(field)}
    >
      {label}
      <span className="text-text-secondary/60">{icon(field)}</span>
    </th>
  )
}

/** Small inline action button for table rows. */
function ActionButton({
  label,
  className,
  disabled,
  onClick,
}: {
  label: string
  className: string
  disabled: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`font-body text-caption font-medium px-2 py-1 transition-opacity ${className} ${
        disabled ? 'opacity-40 cursor-not-allowed' : ''
      }`}
    >
      {label}
    </button>
  )
}
