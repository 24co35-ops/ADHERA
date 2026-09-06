-- =============================================================================
-- ADHERA: Migrations 020 & 021 (Wellness Sessions & Chat Messages)
-- Project: https://supabase.com/dashboard/project/olsgvrmxqsftymsbeqve/sql/new
-- =============================================================================

-- ── 1. Wellness Sessions ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.wellness_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    pattern_name TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wellness_sessions_user_completed 
ON public.wellness_sessions (user_id, completed_at DESC);

ALTER TABLE public.wellness_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own wellness sessions" ON public.wellness_sessions;
CREATE POLICY "Users can view their own wellness sessions"
ON public.wellness_sessions
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own wellness sessions" ON public.wellness_sessions;
CREATE POLICY "Users can insert their own wellness sessions"
ON public.wellness_sessions
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access on wellness_sessions" ON public.wellness_sessions;
CREATE POLICY "Service role full access on wellness_sessions"
ON public.wellness_sessions
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ── 2. Chat Messages ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,
    suggested_feedback JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_user_created 
ON public.chat_messages (user_id, created_at DESC);

ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own chat messages" ON public.chat_messages;
CREATE POLICY "Users can view their own chat messages"
ON public.chat_messages
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own chat messages" ON public.chat_messages;
CREATE POLICY "Users can insert their own chat messages"
ON public.chat_messages
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own chat messages" ON public.chat_messages;
CREATE POLICY "Users can delete their own chat messages"
ON public.chat_messages
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access on chat_messages" ON public.chat_messages;
CREATE POLICY "Service role full access on chat_messages"
ON public.chat_messages
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';
