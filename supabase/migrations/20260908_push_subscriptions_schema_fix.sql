-- Fix and align push_subscriptions table schema and force schema cache reload
CREATE TABLE IF NOT EXISTS public.push_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  endpoint text NOT NULL,
  auth text NOT NULL,
  p256dh text NOT NULL,
  subscription jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(user_id)
);

-- Ensure all columns exist and are nullable for seamless backward/forward compatibility
ALTER TABLE public.push_subscriptions ADD COLUMN IF NOT EXISTS subscription jsonb;
ALTER TABLE public.push_subscriptions ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'push_subscriptions' AND column_name = 'subscription'
  ) THEN
    ALTER TABLE public.push_subscriptions ALTER COLUMN subscription DROP NOT NULL;
  END IF;
END $$;

-- Enable RLS
ALTER TABLE public.push_subscriptions ENABLE ROW LEVEL SECURITY;

-- Ensure policy exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'push_subscriptions' AND policyname = 'Users manage own push subscriptions'
  ) THEN
    CREATE POLICY "Users manage own push subscriptions"
      ON public.push_subscriptions FOR ALL
      USING (auth.uid() = user_id);
  END IF;
END $$;

-- Force PostgREST schema cache reload
NOTIFY pgrst, 'reload schema';
