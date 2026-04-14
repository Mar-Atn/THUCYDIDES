-- ============================================================================
-- TTT Auth Module — Users Table + RLS
-- Migration: 00001_auth_users
-- Date: 2026-04-13
-- Spec: MODULES/M10_INFRASTRUCTURE/SPEC_M10.1_AUTH.md
-- ============================================================================

-- --------------------------------------------------------------------------
-- 1. Users table (extends Supabase auth.users)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email           TEXT NOT NULL UNIQUE,
    display_name    TEXT NOT NULL,
    avatar_url      TEXT,

    -- System role: moderator or participant
    system_role     TEXT NOT NULL DEFAULT 'participant'
                    CHECK (system_role IN ('moderator', 'participant')),

    -- Account status lifecycle
    status          TEXT NOT NULL DEFAULT 'registered'
                    CHECK (status IN ('registered', 'pending_approval', 'active', 'suspended')),

    -- GDPR consent
    data_consent    BOOLEAN NOT NULL DEFAULT FALSE,
    consent_given_at TIMESTAMPTZ,

    -- Metadata
    last_login_at   TIMESTAMPTZ,
    preferences     JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_system_role ON public.users(system_role);
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_status ON public.users(status);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at();

-- --------------------------------------------------------------------------
-- 2. RLS Helper Functions
-- --------------------------------------------------------------------------

-- Check if current JWT user is a moderator
CREATE OR REPLACE FUNCTION public.is_moderator()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.users
        WHERE id = auth.uid()
        AND system_role = 'moderator'
        AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check if current user has any active status (not suspended)
CREATE OR REPLACE FUNCTION public.is_active_user()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.users
        WHERE id = auth.uid()
        AND status IN ('registered', 'active')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check if this is the first moderator (for auto-approval bootstrap)
CREATE OR REPLACE FUNCTION public.is_first_moderator()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN NOT EXISTS (
        SELECT 1 FROM public.users
        WHERE system_role = 'moderator'
        AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- --------------------------------------------------------------------------
-- 3. Enable RLS
-- --------------------------------------------------------------------------
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------------------------------------
-- 4. RLS Policies
-- --------------------------------------------------------------------------

-- SELECT: Users can view their own profile
CREATE POLICY "users_select_own"
    ON public.users FOR SELECT
    TO authenticated
    USING (id = auth.uid());

-- SELECT: Moderators can view all users
CREATE POLICY "users_select_moderator"
    ON public.users FOR SELECT
    TO authenticated
    USING (public.is_moderator());

-- INSERT: Users can create their own profile row on registration
CREATE POLICY "users_insert_own"
    ON public.users FOR INSERT
    TO authenticated
    WITH CHECK (id = auth.uid());

-- INSERT: Service role can create users (backend operations)
CREATE POLICY "users_insert_service"
    ON public.users FOR INSERT
    TO service_role
    WITH CHECK (true);

-- UPDATE: Users can update their own profile (display_name, avatar, preferences, consent)
CREATE POLICY "users_update_own"
    ON public.users FOR UPDATE
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- UPDATE: Moderators can update any user (approve, suspend)
CREATE POLICY "users_update_moderator"
    ON public.users FOR UPDATE
    TO authenticated
    USING (public.is_moderator());

-- UPDATE: Service role full access
CREATE POLICY "users_update_service"
    ON public.users FOR UPDATE
    TO service_role
    USING (true);

-- DELETE: Only service role can delete users
CREATE POLICY "users_delete_service"
    ON public.users FOR DELETE
    TO service_role
    USING (true);

-- --------------------------------------------------------------------------
-- 5. Auto-approval trigger for first moderator
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.auto_approve_first_moderator()
RETURNS TRIGGER AS $$
BEGIN
    -- If registering as moderator and no active moderators exist, auto-approve
    IF NEW.system_role = 'moderator' AND NEW.status = 'pending_approval' THEN
        IF NOT EXISTS (
            SELECT 1 FROM public.users
            WHERE system_role = 'moderator'
            AND status = 'active'
            AND id != NEW.id
        ) THEN
            NEW.status := 'active';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_approve_first_moderator
    BEFORE INSERT ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.auto_approve_first_moderator();
