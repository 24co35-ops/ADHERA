-- Migration: Admin RLS Policies for Identity Directory & Administration
-- Grants admins full visibility across profiles, assignments, adherence, feedback, and medicines

-- 1. profiles: Admins can view and update all user profiles
DROP POLICY IF EXISTS "admins_manage_all_profiles" ON public.profiles;
CREATE POLICY "admins_manage_all_profiles"
  ON public.profiles FOR ALL
  USING (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
    OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- 2. assignments: Admins can view and manage all assignments
DROP POLICY IF EXISTS "admins_manage_all_assignments" ON public.assignments;
CREATE POLICY "admins_manage_all_assignments"
  ON public.assignments FOR ALL
  USING (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
    OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- 3. adherence: Admins can view all adherence records
DROP POLICY IF EXISTS "admins_view_all_adherence" ON public.adherence;
CREATE POLICY "admins_view_all_adherence"
  ON public.adherence FOR SELECT
  USING (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
    OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- 4. feedback: Admins can view all feedback records
DROP POLICY IF EXISTS "admins_view_all_feedback" ON public.feedback;
CREATE POLICY "admins_view_all_feedback"
  ON public.feedback FOR SELECT
  USING (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
    OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- 5. medicines: Admins can view all medicines
DROP POLICY IF EXISTS "admins_view_all_medicines" ON public.medicines;
CREATE POLICY "admins_view_all_medicines"
  ON public.medicines FOR SELECT
  USING (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
    OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
  );

NOTIFY pgrst, 'reload schema';
