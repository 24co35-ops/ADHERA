-- Add mfa_secret column to profiles table
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS mfa_secret text;
