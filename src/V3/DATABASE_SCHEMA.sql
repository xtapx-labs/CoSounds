-- V3 Database Schema for Supabase PostgreSQL
-- Run this in Supabase SQL Editor

-- Enable pgvector extension for ML embeddings
create extension if not exists vector;

-- ============================================
-- 1. PROFILES (User Info)
-- ============================================
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  name text,
  display_name text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============================================
-- 2. PREFERENCES (Separate table - easier migration)
-- ============================================
create table preferences (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null unique,
  preference jsonb not null default '[0,0,0,0,0]',
  updated_at timestamptz default now()
);

-- ============================================
-- 3. ROLES (Admin RBAC)
-- ============================================
create table roles (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  role text check (role in ('admin', 'manager')) not null,
  created_at timestamptz default now(),
  unique(user_id, role)
);

-- ============================================
-- 4. SONGS (Music Library)
-- ============================================
create table songs (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_url text not null,
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  duration int,
  bpm int,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Index for vector similarity search
create index on songs using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- ============================================
-- 5. PLAYERS (Physical Devices)
-- ============================================
create table players (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  token text unique not null,
  status text default 'offline' check (status in ('online', 'offline', 'playing', 'idle')),
  current_song_id uuid references songs(id) on delete set null,
  last_poll timestamptz,
  manager_id uuid references profiles(id) on delete set null,
  created_at timestamptz default now()
);

-- ============================================
-- 6. PLAYER LIBRARY (Access Control)
-- ============================================
create table player_library (
  id uuid default gen_random_uuid() primary key,
  player_id uuid references players(id) on delete cascade not null,
  song_id uuid references songs(id) on delete cascade not null,
  added_at timestamptz default now(),
  unique(player_id, song_id)
);

-- ============================================
-- 7. PLAYER QUEUE (ML → Playback Bridge)
-- ============================================
create table player_queue (
  id uuid default gen_random_uuid() primary key,
  player_id uuid references players(id) on delete cascade not null,
  song_id uuid references songs(id) on delete cascade not null,
  position int not null,
  added_at timestamptz default now(),
  unique(player_id, position)
);

-- ============================================
-- 8. SESSIONS (Active Listeners)
-- ============================================
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  checked_in_at timestamptz default now(),
  expires_at timestamptz not null,
  status text default 'active' check (status in ('active', 'inactive')),
  created_at timestamptz default now()
);

-- Index for active session queries
create index on sessions (user_id, status, expires_at);

-- ============================================
-- 9. VOTES (User Feedback)
-- ============================================
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  song_id uuid references songs(id) on delete cascade not null,
  vote_value int not null check (vote_value between 1 and 5),
  vote_time timestamptz default now()
);

-- Index for leaderboard queries
create index on votes (user_id, vote_time);
create index on votes (song_id, vote_time);

-- ============================================
-- 10. SONGS_PLAYING (History Log)
-- ============================================
create table songs_playing (
  id uuid default gen_random_uuid() primary key,
  player_id uuid references players(id) on delete set null,
  song_id uuid references songs(id) on delete set null,
  played_at timestamptz default now()
);

-- Index for penalty system (recent songs)
create index on songs_playing (song_id, played_at desc);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Profiles
alter table profiles enable row level security;
create policy "Public profiles viewable" on profiles for select using (true);
create policy "Users can update own profile" on profiles for update using (auth.uid() = id);

-- Preferences
alter table preferences enable row level security;
create policy "Users can view own preferences" on preferences for select using (auth.uid() = user_id);
create policy "Users can manage own preferences" on preferences for all using (auth.uid() = user_id);

-- Songs
alter table songs enable row level security;
create policy "Public songs viewable" on songs for select using (true);
create policy "Admins can manage songs" on songs for all using (
  exists (
    select 1 from roles
    where roles.user_id = auth.uid()
    and roles.role = 'admin'
  )
);

-- Votes
alter table votes enable row level security;
create policy "Users can insert own votes" on votes for insert with check (auth.uid() = user_id);
create policy "Users can view own votes" on votes for select using (auth.uid() = user_id);

-- Sessions
alter table sessions enable row level security;
create policy "Users can manage own sessions" on sessions for all using (auth.uid() = user_id);
create policy "Public session count" on sessions for select using (true);

-- Players (Public read for status)
alter table players enable row level security;
create policy "Public players viewable" on players for select using (true);
create policy "Managers can manage own players" on players for all using (auth.uid() = manager_id);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Update updated_at timestamp
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Triggers for updated_at
create trigger profiles_updated_at before update on profiles
  for each row execute function update_updated_at();

create trigger preferences_updated_at before update on preferences
  for each row execute function update_updated_at();

create trigger songs_updated_at before update on songs
  for each row execute function update_updated_at();

-- Recommendation function (V1 logic with penalty)
create or replace function recommend_with_penalty(
  p_vec vector(5),
  p_limit int default 10
)
returns table (
  id uuid,
  title text,
  distance float,
  similarity float,
  adjusted_distance float,
  last_played timestamptz
) as $$
begin
  return query
  select
    s.id,
    s.title,
    (s.embedding <=> p_vec::vector) as distance,
    1 - (s.embedding <=> p_vec::vector) as similarity,
    (s.embedding <=> p_vec::vector)
      + 0.05 * exp(
          - extract(epoch from (now() - coalesce(sp.last_played, now() - interval '1 day'))) / 3600 / 6
        ) as adjusted_distance,
    sp.last_played
  from songs s
  left join lateral (
    select max(played_at) as last_played
    from songs_playing
    where song_id = s.id
  ) sp on true
  where s.embedding is not null
  order by adjusted_distance asc
  limit p_limit;
end;
$$ language plpgsql;

comment on table profiles is 'User profiles';
comment on table preferences is 'User ML preference vectors (separate table for easier migration)';
comment on table songs is 'Audio files with ML embeddings';
comment on table players is 'Physical playback devices';
comment on table player_queue is 'Bridge between ML recommendations and playback';
comment on table sessions is 'Active listener tracking for collective AI';
comment on table votes is 'User feedback for preference learning';
comment on table songs_playing is 'Playback history for penalty system';
