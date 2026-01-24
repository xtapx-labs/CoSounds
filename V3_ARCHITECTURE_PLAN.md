# V3 Architecture Plan: "Unified & Working"

## 1. Core Philosophy
**Single Source of Truth:** Supabase (Auth + DB + Storage).
**Logic Split:**
- **Node.js (V1 Core):** Handles Users, Votes, Sessions, and **Music Recommendation**.
- **Django (Admin/Manager):** Handles **S3 Uploads** and **Player Management** (view-only of DB).
- **Players (Physical/Clients):** Dumb terminals that poll Node.js for "What should I play?"

---

## 2. Database Schema (Supabase PostgreSQL)

### A. User & Auth (Unified)
All users (Admins, Managers, Listeners) are in `auth.users`.
- **`profiles`**: Extends user data.
- **`roles`**: Defines permissions ('admin', 'manager', 'listener').
  - *Django Admin checks this table to allow login.*

### B. Music & Intelligence (The Brain)
- **`songs`**:
  - `id`, `title`, `artist`, `bpm`, `duration`, `key`
  - `file_url` (S3 URL)
  - `embedding` (vector(5)) - *Used by Node.js for ML*
  - `type` ('soundscape', 'instrumental')
- **`preferences`**: User's 5D vector (Updated by Node.js on vote).
- **`votes`**: Raw vote history.
- **`sessions`**: Active listener tracking (Used by Node.js to average preferences).

### C. Player System (The "Happy" Compromise)
- **`players`**:
  - `id` (uuid)
  - `name` (text)
  - `token` (text) - *NFC Tag ID / API Key*
  - `manager_id` (FK to profiles)
  - `current_song_id` (FK to songs) - *What is playing RIGHT NOW*
  - `last_poll_at` (timestamptz) - *Heartbeat*
  - `status` ('active', 'idle', 'offline')
- **`player_history`** (`songs_playing` in screenshot):
  - Log of what played when.

---

## 3. The "Loop" (How it Works)

### Step 1: The Recommendation (Node.js)
**Trigger:** Player polls `GET /api/player/next-song` (Every 30s / End of Track)
1. **Node.js** calculates "Collective Vibe":
   - Fetches all `sessions` with status='active'.
   - Averages their `preferences` vectors -> `TargetVector`.
2. **Node.js** calls Supabase RPC `recommend_with_penalty(TargetVector)`.
3. **Supabase** returns the best song (Cosine Similarity - Recency Penalty).
4. **Node.js** updates `players` table:
   - Sets `current_song_id` = New Song.
   - Returns Song URL + Metadata to Player.

### Step 2: The Playback (Physical Player)
1. **Player** receives JSON: `{ "url": "s3://...", "title": "Rainy Jazz", "crossfade": 5000 }`.
2. **Player** downloads & plays (using `pygame` or `mpv`).
3. **Player** reports back: `POST /api/player/status` -> "I am playing X".

### Step 3: The Feedback (User Vote)
1. **User** clicks "Like" on Web App.
2. **Node.js** (`prefVote.js`):
   - Updates User's `preference` vector (Gradient Descent).
   - Logs vote to `votes`.
   - *Next recommendation will now be slightly biased towards this song.*

---

## 4. Implementation Plan

### Phase 1: Database & Auth (Supabase)
1. Run SQL Migration (I will generate this).
2. Configure Supabase Auth.
3. **Crucial:** Create `recommend_with_penalty` RPC function in PostgreSQL (it's missing in V2, exists in V1).

### Phase 2: Node.js Backend (The Brain)
1. Port `modelRoutes.js` and `prefVote.js` to use new Schema.
2. Implement `GET /api/player/next-song` endpoint.
3. Implement `POST /api/player/status` heartbeat.

### Phase 3: Django Admin (The Manager)
1. Connect Django to Supabase DB.
2. Create `Unmanaged Models` for `Songs`, `Players`, `Profiles`.
3. Build **S3 Upload Form** in Django Admin (populates `songs` table).

### Phase 4: The Player (Python Client)
1. Simple Python script (`requests` + `pygame`).
2. Loop:
   - Poll `next-song`.
   - Download (if not cached).
   - Play.
   - Report Status.

---

## 5. Missing Pieces Solved
- **Auth Split:** Solved. Everyone uses Supabase. Django just verifies the role.
- **Player Logic:** Moved to Node.js (centralized). Player is just a dumb terminal.
- **Current State:** Added `current_song_id` and `last_poll_at` to `players` table.
- **Recommendation:** Explicitly defined as a Node.js -> RPC call flow.

## 6. SQL Migration Script

```sql
-- Enable Vector
create extension if not exists vector;

-- 1. Profiles (Users)
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  name text,
  display_name text,
  created_at timestamptz default now()
);

-- 2. Roles (RBAC)
create table roles (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  role text check (role in ('admin', 'manager', 'listener')),
  unique(user_id, role)
);

-- 3. Songs (S3 & ML)
create table songs (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_url text not null, -- S3 URL
  bpm int,
  duration int, -- seconds
  key text,
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  created_at timestamptz default now(),
  last_played timestamptz
);

-- 4. Players (Physical Devices)
create table players (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  token text unique not null, -- NFC ID
  manager_id uuid references profiles(id) on delete set null,
  current_song_id uuid references songs(id),
  status text default 'offline', -- 'active', 'idle', 'offline'
  last_poll_at timestamptz,
  created_at timestamptz default now()
);

-- 5. Songs Playing (History)
create table songs_playing (
  id uuid default gen_random_uuid() primary key,
  player_id uuid references players(id),
  song_id uuid references songs(id),
  played_at timestamptz default now()
);

-- 6. Sessions (Active Listeners)
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  status text default 'active',
  checked_in_at timestamptz default now(),
  expires_at timestamptz
);

-- 7. Votes & Preferences
create table preferences (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade unique,
  preference vector(5),
  updated_at timestamptz default now()
);

create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  song_id uuid references songs(id) on delete cascade,
  vote_value int not null,
  vote_time timestamptz default now()
);

-- 8. Recommendation RPC (The "Secret Sauce")
create or replace function recommend_with_penalty(
  p_vec vector(5),
  p_limit int,
  p_penalty_hours int default 4
) returns setof songs language sql as $$
  select * from songs s
  order by 
    (s.embedding <=> p_vec) + 
    (
      case 
        when s.last_played > now() - (p_penalty_hours || ' hours')::interval 
        then 10.0 -- Huge penalty for recently played
        else 0.0 
      end
    ) asc
  limit p_limit;
$$;
```

