/**
 * TabOrganizations — organization data viewer for the template.
 * Loads organizations and memberships from Supabase reference sim_run.
 * Read-only for now (view mode). Save functionality is a stretch goal.
 */

import { useEffect, useState } from 'react'
import {
  getTemplateOrganizations,
  getTemplateOrgMemberships,
  type Organization,
  type OrgMembership,
} from '@/lib/queries'

/** Capitalize first letter of a country id for display. */
function cap(id: string): string {
  return id.charAt(0).toUpperCase() + id.slice(1)
}

interface TabOrganizationsProps {
  templateId: string
}

export function TabOrganizations({ templateId: _templateId }: TabOrganizationsProps) {
  const [orgs, setOrgs] = useState<Organization[]>([])
  const [memberships, setMemberships] = useState<OrgMembership[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedOrg, setExpandedOrg] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [orgData, memData] = await Promise.all([
          getTemplateOrganizations(),
          getTemplateOrgMemberships(),
        ])
        setOrgs(orgData)
        setMemberships(memData)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load organizations')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  /** Get memberships for a specific org. */
  function getMembersForOrg(orgId: string): OrgMembership[] {
    return memberships.filter((m) => m.org_id === orgId)
  }

  /** Toggle expanded state of an org card. */
  function toggleExpand(orgId: string) {
    setExpandedOrg((prev) => (prev === orgId ? null : orgId))
  }

  if (loading) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">Organizations</h3>
        <p className="font-body text-body-sm text-text-secondary">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">Organizations</h3>
        <p className="font-body text-body-sm text-danger">{error}</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading text-h3 text-text-primary">Organizations</h3>
        <span className="font-body text-caption text-text-secondary bg-base px-2 py-0.5 rounded">
          View mode
        </span>
      </div>

      {orgs.length === 0 ? (
        <p className="font-body text-body-sm text-text-secondary">
          No organizations found.
        </p>
      ) : (
        <div className="space-y-3">
          {orgs.map((org) => {
            const members = getMembersForOrg(org.id)
            const isExpanded = expandedOrg === org.id

            return (
              <div
                key={org.id}
                className="border border-border rounded-lg overflow-hidden"
              >
                {/* Card header */}
                <button
                  onClick={() => toggleExpand(org.id)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-card hover:bg-base/50 transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-heading text-h3 text-text-primary">
                      {org.sim_name}
                    </span>
                    <span className="font-body text-caption text-text-secondary">
                      ({org.parallel})
                    </span>
                    <span className="font-data text-caption bg-action/10 text-action px-2 py-0.5 rounded">
                      {members.length} members
                    </span>
                    {org.chair_role_id && (
                      <span className="font-body text-caption text-accent">
                        Chair: {cap(org.chair_role_id.replace('_role', ''))}
                      </span>
                    )}
                  </div>
                  <span className="font-body text-body text-text-secondary">
                    {isExpanded ? '\u25B2' : '\u25BC'}
                  </span>
                </button>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="px-4 py-4 border-t border-border bg-base/30 space-y-4">
                    {/* Description */}
                    <div>
                      <label className="block font-body text-caption text-text-secondary mb-1">
                        Description
                      </label>
                      <textarea
                        readOnly
                        value={org.description ?? ''}
                        rows={3}
                        className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary resize-y cursor-default"
                      />
                    </div>

                    {/* Configuration fields */}
                    <div className="grid grid-cols-2 gap-4">
                      {/* Decision rule */}
                      <div>
                        <label className="block font-body text-caption text-text-secondary mb-1">
                          Decision Rule
                        </label>
                        <select
                          disabled
                          value={org.decision_rule ?? ''}
                          className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary cursor-default"
                        >
                          <option value="">--</option>
                          <option value="consensus">Consensus</option>
                          <option value="majority">Majority</option>
                          <option value="veto">Veto</option>
                          <option value="p5_veto">P5 Veto</option>
                          <option value="loose_consensus">Loose Consensus</option>
                          <option value="independent_production">Independent Production</option>
                          <option value="non_binding">Non-binding</option>
                        </select>
                      </div>

                      {/* Voting threshold */}
                      <div>
                        <label className="block font-body text-caption text-text-secondary mb-1">
                          Voting Threshold
                        </label>
                        <input
                          readOnly
                          type="text"
                          value={org.voting_threshold ?? ''}
                          className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary cursor-default"
                        />
                      </div>

                      {/* Chair role ID */}
                      <div>
                        <label className="block font-body text-caption text-text-secondary mb-1">
                          Chair Role ID
                        </label>
                        <input
                          readOnly
                          type="text"
                          value={org.chair_role_id ?? ''}
                          placeholder="(none)"
                          className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary cursor-default"
                        />
                      </div>

                      {/* Meeting frequency */}
                      <div>
                        <label className="block font-body text-caption text-text-secondary mb-1">
                          Meeting Frequency
                        </label>
                        <input
                          readOnly
                          type="text"
                          value={org.meeting_frequency ?? ''}
                          className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary cursor-default"
                        />
                      </div>
                    </div>

                    {/* Can be created at runtime */}
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        disabled
                        checked={org.can_be_created ?? false}
                        className="cursor-default"
                      />
                      <label className="font-body text-body-sm text-text-secondary">
                        Can be created at runtime
                      </label>
                    </div>

                    {/* Members table */}
                    <div>
                      <label className="block font-body text-caption text-text-secondary mb-2">
                        Members
                      </label>
                      {members.length === 0 ? (
                        <p className="font-body text-caption text-text-secondary">
                          No members.
                        </p>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full border-collapse">
                            <thead>
                              <tr className="border-b border-border">
                                <th className="text-left font-body text-caption text-text-secondary px-3 py-2">
                                  Country
                                </th>
                                <th className="text-left font-body text-caption text-text-secondary px-3 py-2">
                                  Role
                                </th>
                                <th className="text-left font-body text-caption text-text-secondary px-3 py-2">
                                  Seat
                                </th>
                                <th className="text-left font-body text-caption text-text-secondary px-3 py-2">
                                  Role in Org
                                </th>
                                <th className="text-center font-body text-caption text-text-secondary px-3 py-2">
                                  Veto
                                </th>
                              </tr>
                            </thead>
                            <tbody>
                              {members.map((m) => (
                                <tr
                                  key={m.id}
                                  className="border-b border-border/50 hover:bg-card/50"
                                >
                                  <td className="font-body text-body-sm text-text-primary px-3 py-2">
                                    {cap(m.country_code)}
                                  </td>
                                  <td className="font-body text-body-sm text-text-primary px-3 py-2">
                                    {m.role_id ? cap(m.role_id) : '—'}
                                  </td>
                                  <td className="px-3 py-2">
                                    <span className={`font-body text-caption px-1.5 py-0.5 rounded ${
                                      m.seat_type === 'individual_seat'
                                        ? 'bg-action/10 text-action'
                                        : 'bg-base text-text-secondary'
                                    }`}>
                                      {m.seat_type === 'individual_seat' ? 'Individual' : 'Country'}
                                    </span>
                                  </td>
                                  <td className="font-body text-body-sm px-3 py-2">
                                    {m.role_id === org.chair_role_id ? (
                                      <span className="font-medium text-accent">Chair</span>
                                    ) : (
                                      <span className="text-text-primary">
                                        {m.role_in_org === 'member_reelection' ? 'Member (up for re-election)' : 'Member'}
                                      </span>
                                    )}
                                  </td>
                                  <td className="text-center px-3 py-2">
                                    {m.has_veto ? (
                                      <span className="font-body text-caption text-danger font-medium">Yes</span>
                                    ) : (
                                      <span className="font-body text-caption text-text-secondary">—</span>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
