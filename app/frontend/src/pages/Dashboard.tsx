/**
 * Post-login landing page — routes to the right view based on role.
 *
 * Moderator: sees moderator dashboard stub (real content comes in M9).
 * Participant: sees participant dashboard stub (real content comes in M6).
 */

import { useAuth } from '@/contexts/AuthContext'
import { ModeratorDashboard } from '@/pages/ModeratorDashboard'
import { ParticipantDashboard } from '@/pages/ParticipantDashboard'

export function Dashboard() {
  const { profile } = useAuth()

  if (!profile) return null

  if (profile.system_role === 'moderator') {
    return <ModeratorDashboard />
  }

  return <ParticipantDashboard />
}
