create table public.feedback (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references auth.users(id),
  medicine_id     uuid not null references public.medicines(id),
  description     text not null check (char_length(description) <= 2000),
  severity        smallint not null check (severity between 1 and 4),
  occurred_at     timestamptz not null,
  references_id   uuid references public.feedback(id),  -- patient correction reference
  created_at      timestamptz not null default now()
);
