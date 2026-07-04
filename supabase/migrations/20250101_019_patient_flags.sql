create table public.patient_flags (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  flag_type text not null check (flag_type in ('dose_drift', 'weekend_pattern', 'post_side_effect_drop', 'silent_inactivity')),
  severity smallint not null check (severity between 1 and 4),
  details jsonb not null default '{}'::jsonb,
  detected_at timestamptz not null default now(),
  resolved_at timestamptz,
  related_medicine_id uuid references public.medicines(id) on delete set null,
  related_feedback_id uuid references public.feedback(id) on delete set null
);

create index idx_patient_flags_user_active on public.patient_flags (user_id) where resolved_at is null;

alter table public.patient_flags enable row level security;

create policy "patients_own_flags"
  on public.patient_flags for select
  using (user_id = auth.uid());

create policy "providers_see_assigned_flags"
  on public.patient_flags for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = patient_flags.user_id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );
