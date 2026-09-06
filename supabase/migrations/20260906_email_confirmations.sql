-- ADHERA v1.2: Email confirmations and notification retries

-- 1. Email confirmations table
CREATE TABLE IF NOT EXISTS public.email_confirmations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  email text NOT NULL,
  token text NOT NULL UNIQUE,
  expires_at timestamptz NOT NULL,
  used boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_email_confirmations_token ON public.email_confirmations(token);
CREATE INDEX IF NOT EXISTS idx_email_confirmations_user_id ON public.email_confirmations(user_id);

ALTER TABLE public.email_confirmations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own email confirmations"
  ON public.email_confirmations FOR SELECT
  USING (auth.uid() = user_id);

-- 2. Notification retries table for edge function push/email retry tracking
CREATE TABLE IF NOT EXISTS public.notification_retries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reminder_id uuid REFERENCES public.reminders(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  payload jsonb NOT NULL,
  attempt integer NOT NULL DEFAULT 1,
  status text NOT NULL DEFAULT 'pending',
  error_message text,
  next_retry_utc timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notification_retries_status_next ON public.notification_retries(status, next_retry_utc);

ALTER TABLE public.notification_retries ENABLE ROW LEVEL SECURITY;

-- 3. System events table for idempotent logging if not already present
CREATE TABLE IF NOT EXISTS public.system_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type text NOT NULL,
  target_id uuid,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_system_events_type_target ON public.system_events(event_type, target_id);

ALTER TABLE public.system_events ENABLE ROW LEVEL SECURITY;

-- Reload schema cache
NOTIFY pgrst, 'reload schema';
