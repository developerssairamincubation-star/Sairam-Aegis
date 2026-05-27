create table if not exists public.local_users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  created_at timestamptz not null default now()
);

alter table public.projects drop constraint if exists projects_user_id_fkey;
alter table public.projects
  add constraint projects_user_id_fkey
  foreign key (user_id) references public.local_users(id) on delete cascade;

alter table public.conversations drop constraint if exists conversations_user_id_fkey;
alter table public.conversations
  add constraint conversations_user_id_fkey
  foreign key (user_id) references public.local_users(id) on delete cascade;
