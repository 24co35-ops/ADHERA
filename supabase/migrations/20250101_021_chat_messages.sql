-- Migration 021: Chat messages for grounded medical RAG assistant
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,
    suggested_feedback JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_created 
ON public.chat_messages (user_id, created_at DESC);

-- Enable RLS
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view their own chat messages"
ON public.chat_messages
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own chat messages"
ON public.chat_messages
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own chat messages"
ON public.chat_messages
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Service role full access
CREATE POLICY "Service role full access on chat_messages"
ON public.chat_messages
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
