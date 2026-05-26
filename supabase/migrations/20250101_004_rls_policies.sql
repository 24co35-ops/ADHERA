-- 4. Row Level Security Policies

-- PROFILES
alter table public.profiles enable row level security;

create policy "patients_own_profile"
  on public.profiles for all
  using (auth.uid() = id);

create policy "providers_see_assigned_profiles"
  on public.profiles for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = public.profiles.id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

create policy "admins_all_profiles"
  on public.profiles for all
  using (
    (select role from public.profiles where id = auth.uid()) = 'admin'
  );

-- MEDICINES
alter table public.medicines enable row level security;

create policy "patients_own_medicines"
  on public.medicines for all
  using (user_id = auth.uid());

create policy "providers_see_assigned_medicines"
  on public.medicines for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = medicines.user_id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

-- REMINDERS
alter table public.reminders enable row level security;

create policy "patients_own_reminders"
  on public.reminders for all
  using (user_id = auth.uid());

create policy "providers_see_assigned_reminders"
  on public.reminders for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = reminders.user_id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

-- ADHERENCE
alter table public.adherence enable row level security;

create policy "patients_own_adherence"
  on public.adherence for all
  using (user_id = auth.uid());

create policy "providers_see_assigned_adherence"
  on public.adherence for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = adherence.user_id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

-- FEEDBACK
alter table public.feedback enable row level security;

create policy "patients_own_feedback"
  on public.feedback for all
  using (user_id = auth.uid());

create policy "providers_see_assigned_feedback"
  on public.feedback for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = feedback.user_id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

-- EMERGENCY CONTACTS
alter table public.emergency_contacts enable row level security;

create policy "patients_own_emergency_contacts"
  on public.emergency_contacts for all
  using (user_id = auth.uid());

create policy "providers_see_assigned_emergency_contacts"
  on public.emergency_contacts for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = emergency_contacts.user_id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

-- ASSIGNMENTS
alter table public.assignments enable row level security;

create policy "patients_see_own_assignments"
  on public.assignments for select
  using (patient_id = auth.uid());

create policy "providers_see_own_assignments"
  on public.assignments for select
  using (provider_id = auth.uid());

create policy "admins_all_assignments"
  on public.assignments for all
  using (
    exists (
      select 1 from public.profiles
      where id = auth.uid()
        and role = 'admin'
    )
  );
