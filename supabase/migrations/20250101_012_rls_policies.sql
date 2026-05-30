alter table public.profiles enable row level security;

create policy "patients_own_profile"
  on public.profiles for all
  using (auth.uid() = id);

create policy "providers_see_assigned_profiles"
  on public.profiles for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = profiles.id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

alter table public.adherence enable row level security;

create policy "patients_own_adherence"
  on public.adherence for select
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
