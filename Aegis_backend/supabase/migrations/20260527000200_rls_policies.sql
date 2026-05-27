alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.rag_ingestion_runs enable row level security;

drop policy if exists "Users can read own profile" on public.profiles;
create policy "Users can read own profile"
on public.profiles for select
to authenticated
using (id = auth.uid());

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
on public.profiles for update
to authenticated
using (id = auth.uid())
with check (id = auth.uid());

drop policy if exists "Users can read own projects" on public.projects;
create policy "Users can read own projects"
on public.projects for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "Users can create own projects" on public.projects;
create policy "Users can create own projects"
on public.projects for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "Users can update own projects" on public.projects;
create policy "Users can update own projects"
on public.projects for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "Users can delete own projects" on public.projects;
create policy "Users can delete own projects"
on public.projects for delete
to authenticated
using (user_id = auth.uid());

drop policy if exists "Users can read own conversations" on public.conversations;
create policy "Users can read own conversations"
on public.conversations for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "Users can create own conversations" on public.conversations;
create policy "Users can create own conversations"
on public.conversations for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "Users can update own conversations" on public.conversations;
create policy "Users can update own conversations"
on public.conversations for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "Users can delete own conversations" on public.conversations;
create policy "Users can delete own conversations"
on public.conversations for delete
to authenticated
using (user_id = auth.uid());

drop policy if exists "Users can read messages in own conversations" on public.messages;
create policy "Users can read messages in own conversations"
on public.messages for select
to authenticated
using (
  exists (
    select 1
    from public.conversations c
    where c.id = messages.conversation_id
      and c.user_id = auth.uid()
  )
);

drop policy if exists "Users can create messages in own conversations" on public.messages;
create policy "Users can create messages in own conversations"
on public.messages for insert
to authenticated
with check (
  exists (
    select 1
    from public.conversations c
    where c.id = messages.conversation_id
      and c.user_id = auth.uid()
  )
);

drop policy if exists "Users can read ingestion runs" on public.rag_ingestion_runs;
create policy "Users can read ingestion runs"
on public.rag_ingestion_runs for select
to authenticated
using (true);
