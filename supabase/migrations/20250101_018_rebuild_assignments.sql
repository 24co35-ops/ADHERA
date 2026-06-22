-- Alter assignments table for rebuild
ALTER TABLE public.assignments ADD COLUMN IF NOT EXISTS initiated_by text DEFAULT 'patient' CHECK (initiated_by IN ('patient', 'provider', 'admin'));
ALTER TABLE public.assignments ADD COLUMN IF NOT EXISTS assignment_id uuid DEFAULT gen_random_uuid();

-- Alter status check constraint to support pending, declined, removed, cancelled
ALTER TABLE public.assignments DROP CONSTRAINT IF EXISTS assignments_status_check;
ALTER TABLE public.assignments ADD CONSTRAINT assignments_status_check CHECK (status IN ('active', 'inactive', 'pending', 'declined', 'removed', 'cancelled'));
ALTER TABLE public.assignments ALTER COLUMN status SET DEFAULT 'pending';

-- Create policies
CREATE POLICY "providers_can_insert_assignments" ON public.assignments FOR INSERT WITH CHECK (auth.uid() = provider_id);
CREATE POLICY "patients_can_update_provider_invitations" ON public.assignments FOR UPDATE USING (auth.uid() = patient_id);
