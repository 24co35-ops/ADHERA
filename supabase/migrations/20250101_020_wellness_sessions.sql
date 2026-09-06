-- Migration 020: Wellness sessions for breathing and mental wellness tracking
CREATE TABLE IF NOT EXISTS public.wellness_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    pattern_name TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_wellness_sessions_user_completed 
ON public.wellness_sessions (user_id, completed_at DESC);

-- Enable RLS
ALTER TABLE public.wellness_sessions ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view their own wellness sessions"
ON public.wellness_sessions
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own wellness sessions"
ON public.wellness_sessions
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Service role full access
CREATE POLICY "Service role full access on wellness_sessions"
ON public.wellness_sessions
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
