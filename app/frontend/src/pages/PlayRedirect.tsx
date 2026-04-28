/**
 * PlayRedirect — auto-resolves participant to their active simrun.
 *
 * Route: /play (no simId)
 *
 * Queries roles table for the logged-in user's active assignment,
 * then redirects to /play/{simId}. If multiple active simruns,
 * shows a selector. If none, shows a message.
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'

interface ActiveSim {
  simId: string
  simName: string
  roleName: string
  countryCode: string
}

export function PlayRedirect() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [activeSims, setActiveSims] = useState<ActiveSim[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) return

    async function findActiveSim() {
      // Find all roles assigned to this user in active/pre_start simruns
      const { data: roles } = await supabase
        .from('roles')
        .select('id,character_name,country_code,sim_run_id')
        .eq('user_id', user!.id)
        .eq('status', 'active')

      if (!roles || roles.length === 0) {
        setLoading(false)
        return
      }

      // Get simrun info for each role
      const simIds = [...new Set(roles.map(r => r.sim_run_id as string))]
      const { data: sims } = await supabase
        .from('sim_runs')
        .select('id,name,status')
        .in('id', simIds)
        .in('status', ['active', 'pre_start', 'paused'])

      const active: ActiveSim[] = []
      for (const sim of sims || []) {
        const role = roles.find(r => r.sim_run_id === sim.id)
        if (role) {
          active.push({
            simId: sim.id as string,
            simName: (sim.name as string) || 'Unnamed Simulation',
            roleName: (role.character_name as string) || (role.id as string),
            countryCode: (role.country_code as string) || '',
          })
        }
      }

      if (active.length >= 1) {
        // Redirect to the most recent active sim (participants always have one)
        navigate(`/play/${active[0].simId}`, { replace: true })
        return
      }

      // No assigned sim — find latest active simrun and go there unassigned
      const { data: latestSims } = await supabase
        .from('sim_runs')
        .select('id,name')
        .in('status', ['active', 'pre_start'])
        .neq('id', '00000000-0000-0000-0000-000000000001')
        .order('created_at', { ascending: false })
        .limit(1)
      if (latestSims?.[0]) {
        navigate(`/play/${latestSims[0].id}`, { replace: true })
        return
      }

      setActiveSims(active)
      setLoading(false)
    }

    findActiveSim()
  }, [user, navigate])

  if (loading) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="text-text-secondary font-body">Finding your simulation...</div>
      </div>
    )
  }

  if (activeSims.length === 0) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="bg-card border border-border rounded-xl p-8 max-w-md text-center">
          <h2 className="font-heading text-h2 text-text-primary mb-3">No Active Simulation</h2>
          <p className="font-body text-body-sm text-text-secondary mb-6">
            You are not currently assigned to any active simulation. Please contact your facilitator.
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="font-body text-body-sm text-action hover:underline"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  // Multiple active sims — show selector
  return (
    <div className="min-h-screen bg-base flex items-center justify-center">
      <div className="bg-card border border-border rounded-xl p-8 max-w-md">
        <h2 className="font-heading text-h2 text-text-primary mb-4">Select Simulation</h2>
        <p className="font-body text-body-sm text-text-secondary mb-6">
          You are assigned to multiple active simulations. Choose one to enter.
        </p>
        <div className="space-y-3">
          {activeSims.map(sim => (
            <button
              key={sim.simId}
              onClick={() => navigate(`/play/${sim.simId}`, { replace: true })}
              className="w-full text-left bg-base hover:bg-action/5 border border-border hover:border-action/30 rounded-lg px-4 py-3 transition-colors"
            >
              <div className="font-body text-body font-medium text-text-primary">{sim.simName}</div>
              <div className="font-body text-caption text-text-secondary">
                Playing as <strong>{sim.roleName}</strong> — {sim.countryCode.toUpperCase()}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
