-- Run this once in Supabase Dashboard → SQL Editor before deploying.
create table if not exists public.card_rooms (
  id uuid primary key default gen_random_uuid(),
  card_id text not null,
  creator_name text not null check (char_length(creator_name) between 1 and 16),
  creator_response jsonb not null,
  creator_token_hash text not null,
  share_code_hash text not null unique,
  partner_name text,
  partner_response jsonb,
  partner_token_hash text,
  status text not null default 'waiting' check (status in ('waiting', 'paired')),
  expires_at timestamptz not null,
  paired_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists card_rooms_expires_at_idx on public.card_rooms (expires_at);
create index if not exists card_rooms_creator_token_hash_idx on public.card_rooms (creator_token_hash);
create index if not exists card_rooms_partner_token_hash_idx on public.card_rooms (partner_token_hash);

alter table public.card_rooms enable row level security;
revoke all on public.card_rooms from anon, authenticated;

-- The browser never accesses this table directly. Only Next.js server routes
-- use SUPABASE_SERVICE_ROLE_KEY, which must remain a Vercel-only secret.

-- Session-based experience: two people enter one shared journey with a code.
create table if not exists public.conversation_sessions (
  id uuid primary key default gen_random_uuid(),
  join_code_hash text not null unique,
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);

create table if not exists public.session_members (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.conversation_sessions(id) on delete cascade,
  display_name text not null check (char_length(display_name) between 1 and 16),
  access_token_hash text not null unique,
  joined_at timestamptz not null default now()
);

create index if not exists session_members_session_idx on public.session_members (session_id);

alter table public.session_members add column if not exists user_id uuid references auth.users(id) on delete cascade;
create unique index if not exists session_members_session_user_idx on public.session_members (session_id, user_id) where user_id is not null;

create table if not exists public.session_answers (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.conversation_sessions(id) on delete cascade,
  member_id uuid not null references public.session_members(id) on delete cascade,
  card_id text not null,
  response jsonb not null,
  status text not null default 'draft' check (status in ('draft', 'ready', 'published')),
  published_at timestamptz,
  updated_at timestamptz not null default now(),
  unique(session_id, member_id, card_id)
);

create index if not exists session_answers_session_idx on public.session_answers (session_id);

alter table public.conversation_sessions enable row level security;
alter table public.session_members enable row level security;
alter table public.session_answers enable row level security;
revoke all on public.conversation_sessions, public.session_members, public.session_answers from anon, authenticated;
grant usage on schema public to service_role;
grant select, insert, update, delete on public.conversation_sessions, public.session_members, public.session_answers to service_role;
