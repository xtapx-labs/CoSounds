# V3 Database Design & Architecture Plan

## 1. Architecture Overview (The Hybrid Model)

We strictly follow the "Best of Both Worlds" approach:
- **Node.js (V1)**: Handles User Logic (Votes, Sessions, Preferences). It is the "Brain" that calculates recommendations.
- **Django (V2)**: Handles Admin (S3 Uploads) and Player API (Physical devices). It is the "Manager".
- **Supabase (DB + Auth)**: The Single Source of Truth.

### Data Flow: Recommendation Engine
1.  **Users** vote via Node.js App.
2.  **Node.js** updates `profiles.preference_vector` and `sessions`.
3.  **Supabase Cron/Function** (or Node.js Scheduler) calculates the "Collective Vector" (average of active sessions).
4.  **Database** runs `recommend_with_penalty` to find the next song.
5.  **Database** writes the result to `player_queues`.
6.  **Physical Player** polls **Django**.
7.  **Django** reads `player_queues` from Supabase and tells Player what to play.

---

## 2. Database Schema (Supabase PostgreSQL)

### A. User & Auth (Supabase Managed)

#### `profiles`
Extends `auth.users`.
- `id` (uuid, PK): FK to `auth.users.id`
- `email` (text)
- `name` (text)
- `display_name` (text)
- `preference_vector` (vector(5)): The user's AI taste profile.
- `created_at` (timestamptz)

#### `roles`
RBAC for Django Admin.
- `id` (uuid, PK)
- `user_id` (uuid, FK): `profiles.id`
- `role` (text): 'admin', 'manager' (Default users have no entry)

### B. Music & Storage (S3 Backed)

#### `songs`
- `id` (uuid, PK)
- `title` (text)
- `artist` (text)
- `file_url` (text): **S3 URL** (e.g., `https://bucket.s3.amazonaws.com/...`)
- `type` (text): 'soundscape' | 'instrumental'
- `embedding` (vector(5)): ML feature vector.
- `duration` (int): Seconds.
- `bpm` (int): Optional metadata.
- `created_at` (timestamptz)

### C. Player System (The "Happy" Compromise)

#### `players`
Represents physical devices (e.g., "Lobby Speaker").
- `id` (uuid, PK)
- `name` (text)
- `token` (text, unique): API Key for the device (NFC tag ID or Device ID).
- `status` (text): 'online', 'offline', 'playing', 'idle'.
- `current_song_id` (uuid, FK): What is playing *right now*.
- `last_poll` (timestamptz): Heartbeat to track online status.
- `manager_id` (uuid, FK): The Admin/Manager responsible for this unit.

#### `player_library`
Explicitly defines which songs a player can access.
- `id` (uuid, PK)
- `player_id` (uuid, FK)
- `song_id` (uuid, FK)
- *Note*: If a player has entries here, it plays *only* these. If empty, it plays *global* recommendations.

#### `player_queue`
The bridge between ML (Node) and Playback (Django).
- `id` (uuid, PK)
- `player_id` (uuid, FK)
- `song_id` (uuid, FK)
- `position` (int): 1, 2, 3...
- `added_at` (timestamptz)

### D. User Interaction (V1 Logic)

#### `sessions`
Tracks "Active Listeners" for the algorithm.
- `id` (uuid, PK)
- `user_id` (uuid, FK)
- `checked_in_at` (timestamptz)
- `expires_at` (timestamptz)
- `status` (text): 'active' | 'inactive'

#### `votes`
- `id` (uuid, PK)
- `user_id` (uuid, FK)
- `song_id` (uuid, FK)
- `vote_value` (int): 1-5
- `vote_time` (timestamptz)

#### `songs_playing` (History)
- `id` (uuid, PK)
- `player_id` (uuid, FK): Which player played it?
- `song_id` (uuid, FK)
- `played_at` (timestamptz)

---

## 3. Django Configuration Plan (The "Rewrite")

**Goal:** Django is *stateless* regarding DB schema. It just reads/writes.

1.  **Connection**: `django.db.backends.postgresql` -> Supabase Connection String.
2.  **Auth**: Custom Middleware that validates Supabase JWTs (for Admin access) or API Tokens (for Players).
3.  **Models**: All models set to `managed = False`.
4.  **Admin Panel**:
    - `SongAdmin`: Uses `django-storages` to upload files to AWS S3, then saves the URL to `songs` table.
    - `PlayerAdmin`: View status, assign songs to `player_library`.

---

## 4. SQL Migration Script

```sql
-- Enable Vector
create extension if not exists vector;

-- 1. Profiles (User + ML)
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  name text,
  display_name text,
  preference_vector vector(5) default '[0,0,0,0,0]',
  created_at timestamptz default now()
);

-- 2. Roles (Admin)
create table roles (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  role text check (role in ('admin', 'manager'))
);

-- 3. Songs (S3)
create table songs (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_url text not null,
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  duration int,
  created_at timestamptz default now()
);

-- 4. Players (Physical Devices)
create table players (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  token text unique not null,
  status text default 'offline',
  current_song_id uuid references songs(id),
  last_poll timestamptz,
  manager_id uuid references profiles(id),
  created_at timestamptz default now()
);

-- 5. Player Library (Access Control)
create table player_library (
  id uuid default gen_random_uuid() primary key,
  player_id uuid references players(id) on delete cascade,
  song_id uuid references songs(id) on delete cascade
);

-- 6. Player Queue (The Bridge)
create table player_queue (
  id uuid default gen_random_uuid() primary key,
  player_id uuid references players(id) on delete cascade,
  song_id uuid references songs(id) on delete cascade,
  position int,
  added_at timestamptz default now()
);

-- 7. Sessions (Active Listeners)
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  checked_in_at timestamptz default now(),
  expires_at timestamptz,
  status text default 'active'
);

-- 8. Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  song_id uuid references songs(id) on delete cascade,
  vote_value int not null,
  vote_time timestamptz default now()
);

-- 9. History
create table songs_playing (
  id uuid default gen_random_uuid() primary key,
  player_id uuid references players(id),
  song_id uuid references songs(id),
  played_at timestamptz default now()
);

-- RLS Policies
alter table profiles enable row level security;
alter table songs enable row level security;
alter table votes enable row level security;

-- Public Read
create policy "Public profiles" on profiles for select using (true);
create policy "Public songs" on songs for select using (true);
create policy "Public players" on players for select using (true);

-- User Write
create policy "User votes" on votes for insert with check (auth.uid() = user_id);
create policy "User sessions" on sessions for insert with check (auth.uid() = user_id);
```

