-- Backfill app_metadata.role for all existing auth users from their profiles row.
-- New registrations stamp app_metadata at sign-up time; this one-time script
-- catches everyone registered before that fix was deployed.
--
-- Requires pg_net or direct auth schema access. Runs as a DO block using
-- the built-in auth.users table (available in Supabase managed Postgres).

do $$
declare
  rec record;
begin
  for rec in
    select p.id, p.role
    from public.profiles p
    join auth.users u on u.id = p.id
    where
      -- only update users whose app_metadata is missing the role key
      (u.raw_app_meta_data is null
       or u.raw_app_meta_data->>'role' is null
       or u.raw_app_meta_data->>'role' = '')
      and p.role is not null
  loop
    update auth.users
    set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb) || jsonb_build_object('role', rec.role)
    where id = rec.id;
  end loop;
end;
$$;

notify pgrst, 'reload schema';
