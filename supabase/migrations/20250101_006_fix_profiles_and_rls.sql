-- Migration: Fix profiles sync and RLS recursion

-- 1. Create a function to handle new user registration
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (id, full_name, role, date_of_birth, contact_number, timezone)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', ''),
    coalesce(new.raw_user_meta_data->>'role', 'patient'),
    (new.raw_user_meta_data->>'date_of_birth')::date,
    new.raw_user_meta_data->>'contact_number',
    coalesce(new.raw_user_meta_data->>'timezone', 'UTC')
  );
  return new;
end;
$$;

-- 2. Create the trigger
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 3. Fix RLS recursion for profiles
drop policy if exists "admins_all_profiles" on public.profiles;
create policy "admins_all_profiles"
  on public.profiles for all
  using (
    (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
  );

-- 4. Fix RLS for assignments (avoid recursion)
drop policy if exists "admins_all_assignments" on public.assignments;
create policy "admins_all_assignments"
  on public.assignments for all
  using (
    (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
  );

-- 5. Add correction_note to doses table
alter table public.doses add column if not exists correction_note text;

-- 6. Update sync trigger to include correction_note
create or replace function public.sync_dose_to_adherence()
returns trigger language plpgsql as $$
begin
  if (NEW.status in ('taken', 'missed')) then
    insert into public.adherence (reminder_id, user_id, scheduled_utc, status, outcome_utc, correction_note)
    values (NEW.reminder_id, NEW.user_id, NEW.scheduled_utc, NEW.status, now(), NEW.correction_note);
  end if;
  return NEW;
end;
$$;
