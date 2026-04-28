/**
 * Post-login landing page — routes to the right view based on system role.
 *
 * Moderator: ModeratorDashboard (sim run list + quick actions).
 * Participant: auto-detects assigned sim run → navigates to /play/:simId.
 *   - If assigned a role → routes to that role's sim run.
 *   - If no role → routes to latest active sim (unassigned view).
 *   - If no active sim → "No active simulation" message.
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'
import { ModeratorDashboard } from '@/pages/ModeratorDashboard'

const TEMPLATE_SIM_ID = '00000000-0000-0000-0000-000000000001'

export function Dashboard() {
  const { user, profile } = useAuth()
  const navigate = useNavigate()
  const [resolving, setResolving] = useState(true)

  useEffect(() => {
    if (!user || !profile) return
    if (profile.system_role === 'moderator') {
      setResolving(false)
      return // ModeratorDashboard rendered below
    }

    // Participant: find their sim run
    const findSim = async () => {
      try {
        // 1. Check if user has an assigned role in any non-template sim
        const { data: myRoles } = await supabase
          .from('roles')
          .select('sim_run_id')
          .eq('user_id', user.id)
          .neq('sim_run_id', TEMPLATE_SIM_ID)
          .limit(1)

        if (myRoles?.length) {
          navigate(`/play/${myRoles[0].sim_run_id}`, { replace: true })
          return
        }

        // 2. No assigned role — find latest active/pre_start/setup sim
        const { data: sims } = await supabase
          .from('sim_runs')
          .select('id')
          .in('status', ['active', 'pre_start', 'setup'])
          .neq('id', TEMPLATE_SIM_ID)
          .order('created_at', { ascending: false })
          .limit(1)

        if (sims?.length) {
          navigate(`/play/${sims[0].id}`, { replace: true })
          return
        }

        // 3. No active sim — show message
        setResolving(false)
      } catch (e) {
        console.error('Failed to find sim for participant:', e)
        setResolving(false)
      }
    }
    findSim()

    // Monitor for changes to sim_runs and roles — auto-update when moderator
    // starts a sim or assigns a role
    const simChannel = supabase.channel('dashboard-sim-monitor')
      .on('postgres_changes', {
        event: '*', schema: 'public', table: 'sim_runs',
      }, () => findSim())
      .on('postgres_changes', {
        event: '*', schema: 'public', table: 'roles',
      }, () => findSim())
      .subscribe()

    return () => { supabase.removeChannel(simChannel) }
  }, [user, profile, navigate])

  if (!profile) return null

  // Moderator sees the full dashboard
  if (profile.system_role === 'moderator') {
    return <ModeratorDashboard />
  }

  // Participant: resolving their sim
  if (resolving) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <p className="font-body text-body-sm text-text-secondary">
          Connecting to simulation...
        </p>
      </div>
    )
  }

  // No active simulation found
  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4">
      <div className="bg-card border border-border rounded-lg p-8 max-w-md text-center">
        <h2 className="font-heading text-h2 text-text-primary mb-3">
          Welcome to Thucydides Trap
        </h2>
        <p className="font-body text-body-sm text-text-secondary mb-4">
          No active simulation is running right now. The moderator will start one soon.
        </p>
        <p className="font-body text-caption text-text-secondary">
          This page will update automatically when a simulation becomes available.
        </p>
      </div>
    </div>
  )
}
