/**
 * useCountryList — cached country list for action forms.
 *
 * Most action forms need the same country list (id, sim_name, color_ui)
 * for target selection dropdowns. Without caching, each form mount triggers
 * a separate REST call. This hook caches the result per simId.
 */
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { requestQueue } from '@/lib/requestQueue'

export interface CountryListItem {
  id: string
  sim_name: string
  color_ui: string
}

// Module-level cache: simId → countries
const cache = new Map<string, CountryListItem[]>()

export function useCountryList(simId: string): CountryListItem[] {
  const [countries, setCountries] = useState<CountryListItem[]>(() => cache.get(simId) ?? [])

  useEffect(() => {
    if (!simId) return
    const cached = cache.get(simId)
    if (cached && cached.length > 0) {
      setCountries(cached)
      return
    }
    requestQueue.enqueue(() =>
      supabase.from('countries')
        .select('id,sim_name,color_ui')
        .eq('sim_run_id', simId)
        .order('sim_name')
        .then(({ data }) => {
          const list = (data ?? []) as CountryListItem[]
          cache.set(simId, list)
          setCountries(list)
        })
    )
  }, [simId])

  return countries
}
