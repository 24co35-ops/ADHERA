create table public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  full_name    text not null,
  role         text not null check (role in ('patient', 'provider', 'admin')),
  date_of_birth date,
  contact_number text,
  timezone     text not null default 'UTC',
  is_active    boolean not null default true,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
