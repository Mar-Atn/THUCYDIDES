/**
 * Auth Context — single source of truth for authentication state.
 *
 * Provides: user session, profile, auth methods.
 * Pattern adapted from KING SIM's AuthContext.
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import type { User, Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

/* -------------------------------------------------------------------------- */
/*  Types                                                                     */
/* -------------------------------------------------------------------------- */

export interface UserProfile {
  id: string
  email: string
  display_name: string
  system_role: 'moderator' | 'participant'
  status: 'registered' | 'pending_approval' | 'active' | 'suspended'
  data_consent: boolean
  consent_given_at: string | null
  last_login_at: string | null
  preferences: Record<string, unknown>
  created_at: string
  updated_at: string
}

interface AuthContextType {
  user: User | null
  profile: UserProfile | null
  session: Session | null
  loading: boolean

  signUp: (
    email: string,
    password: string,
    displayName: string,
    systemRole: 'moderator' | 'participant'
  ) => Promise<{ error: Error | null }>

  signIn: (
    email: string,
    password: string
  ) => Promise<{ error: Error | null }>

  signInWithGoogle: () => Promise<{ error: Error | null }>

  signOut: () => Promise<void>

  resetPassword: (email: string) => Promise<{ error: Error | null }>

  updatePassword: (password: string) => Promise<{ error: Error | null }>

  grantConsent: () => Promise<{ error: Error | null }>

  refreshProfile: () => Promise<void>
}

/* -------------------------------------------------------------------------- */
/*  Context                                                                   */
/* -------------------------------------------------------------------------- */

const AuthContext = createContext<AuthContextType | undefined>(undefined)

/* -------------------------------------------------------------------------- */
/*  Provider                                                                  */
/* -------------------------------------------------------------------------- */

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  /* ---- Profile fetch (with dedup) ---- */

  let profileFetchInFlight = false

  const fetchProfile = useCallback(async (userId: string) => {
    if (profileFetchInFlight) return
    profileFetchInFlight = true

    try {
      const { data, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', userId)
        .single()

      if (error) {
        console.error('Profile fetch error:', error.message)
        setProfile(null)
      } else {
        setProfile(data as UserProfile)
      }
    } catch (e) {
      console.error('Profile fetch exception:', e)
      setProfile(null)
    } finally {
      profileFetchInFlight = false
    }
  }, [])

  /* ---- Session initialization ---- */

  useEffect(() => {
    let mounted = true

    // 1. Direct session check — fast, works even if listener misses
    const initSession = async () => {
      try {
        const { data: { session: s } } = await supabase.auth.getSession()
        if (!mounted) return
        if (s?.user) {
          setUser(s.user)
          setSession(s)
          await fetchProfile(s.user.id)
        }
      } catch (e) {
        console.warn('getSession failed:', e)
      } finally {
        if (mounted) setLoading(false)
      }
    }

    initSession()

    // 2. Listener for ongoing changes (sign in, sign out, token refresh)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, newSession) => {
      if (!mounted) return
      setSession(newSession)
      setUser(newSession?.user ?? null)

      if (event === 'SIGNED_OUT') {
        setProfile(null)
      } else if (
        newSession?.user &&
        event !== 'INITIAL_SESSION' &&
        event !== 'TOKEN_REFRESHED'
      ) {
        await fetchProfile(newSession.user.id)
      }
    })

    return () => {
      mounted = false
      subscription.unsubscribe()
    }
  }, [fetchProfile])

  /* ---- Auth methods ---- */

  const signUp = useCallback(
    async (
      email: string,
      password: string,
      displayName: string,
      systemRole: 'moderator' | 'participant'
    ) => {
      try {
        // 1. Create auth user
        const { data, error: authError } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/dashboard`,
            data: { display_name: displayName, system_role: systemRole },
          },
        })

        if (authError || !data.user) {
          return { error: authError ?? new Error('Sign-up failed') }
        }

        // 2. Profile is auto-created by DB trigger (handle_new_user)
        //    using the metadata we passed above. Wait briefly for it.
        await new Promise((r) => setTimeout(r, 500))

        // 3. Fetch the created profile (status may have changed via trigger)
        await fetchProfile(data.user.id)

        return { error: null }
      } catch (e) {
        return { error: e as Error }
      }
    },
    [fetchProfile]
  )

  const signIn = useCallback(async (email: string, password: string) => {
    try {
      // Timeout wrapper — never hang longer than 10 seconds
      const signInPromise = supabase.auth.signInWithPassword({
        email,
        password,
      })
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Sign-in timed out. Please try again.')), 10000)
      )
      const { error } = await Promise.race([signInPromise, timeoutPromise])
      if (error) return { error: new Error(error.message) }

      // Update last_login_at (non-blocking)
      supabase.auth.getUser().then(({ data: { user: currentUser } }) => {
        if (currentUser) {
          supabase
            .from('users')
            .update({ last_login_at: new Date().toISOString() })
            .eq('id', currentUser.id)
        }
      })

      return { error: null }
    } catch (e) {
      return { error: e as Error }
    }
  }, [])

  const signInWithGoogle = useCallback(async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/dashboard`,
        },
      })
      if (error) return { error: new Error(error.message) }
      return { error: null }
    } catch (e) {
      return { error: e as Error }
    }
  }, [])

  const signOut = useCallback(async () => {
    await supabase.auth.signOut()
    setUser(null)
    setProfile(null)
    setSession(null)
  }, [])

  const resetPassword = useCallback(async (email: string) => {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/update-password`,
      })
      if (error) return { error: new Error(error.message) }
      return { error: null }
    } catch (e) {
      return { error: e as Error }
    }
  }, [])

  const updatePassword = useCallback(async (password: string) => {
    try {
      const { error } = await supabase.auth.updateUser({ password })
      if (error) return { error: new Error(error.message) }
      return { error: null }
    } catch (e) {
      return { error: e as Error }
    }
  }, [])

  const grantConsent = useCallback(async () => {
    if (!user) return { error: new Error('Not authenticated') }
    try {
      const { error } = await supabase
        .from('users')
        .update({
          data_consent: true,
          consent_given_at: new Date().toISOString(),
        })
        .eq('id', user.id)

      if (error) return { error: new Error(error.message) }
      await fetchProfile(user.id)
      return { error: null }
    } catch (e) {
      return { error: e as Error }
    }
  }, [user, fetchProfile])

  const refreshProfile = useCallback(async () => {
    if (user) await fetchProfile(user.id)
  }, [user, fetchProfile])

  /* ---- Render ---- */

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        session,
        loading,
        signUp,
        signIn,
        signInWithGoogle,
        signOut,
        resetPassword,
        updatePassword,
        grantConsent,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

/* -------------------------------------------------------------------------- */
/*  Hook                                                                      */
/* -------------------------------------------------------------------------- */

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
