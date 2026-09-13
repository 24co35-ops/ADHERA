-- Fix adherence_status_check constraint to include 'snoozed' status
ALTER TABLE public.adherence DROP CONSTRAINT IF EXISTS adherence_status_check;
ALTER TABLE public.adherence ADD CONSTRAINT adherence_status_check CHECK (status IN ('taken', 'missed', 'snoozed', 'superseded'));

-- Force PostgREST schema cache reload
NOTIFY pgrst, 'reload schema';
