# V3 Database Design (Supabase + PostgreSQL)

## Overview
This schema combines the working ML/Personalization from V1 with the advanced audio layering potential of V2, while strictly avoiding S3 and complex Django overhead. It is designed for Supabase.

## Extensions
- `vector`: For ML embeddings (cosine similarity).

## Tables

### 1. `profiles`
Extends Supabase Auth users. Stores the user's personalization vector.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK, References `auth.users.id` |
| `display_name` | `text` | Public username |
| `avatar_url` | `text` | Profile picture |
| `preference_vector` | `vector(5)` | The 5D user preference vector (updated via gradient descent) |
| `created_at` | `timestamptz` | Account creation |
| `updated_at` | `timestamptz` | Last update |

**RLS Policies:**
- Public read access.
- Users can update their own profile.

### 2. `sounds`
Stores metadata and vector embeddings for audio files. Files are stored in Supabase Storage or local `.audio/` directory (mapped by `file_path`).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK, Default `gen_random_uuid()` |
| `title` | `text` | Song title |
| `artist` | `text` | Artist name (optional) |
| `file_path` | `text` | Path in storage bucket or local system |
| `type` | `text` | Enum: 'soundscape', 'instrumental' (V2 feature) |
| `embedding` | `vector(5)` | 5D audio feature vector |
| `duration` | `int` | Duration in seconds |
| `created_at` | `timestamptz` | Upload time |

**RLS Policies:**
- Public read access.
- Admin-only write access.

### 3. `votes`
Records user interactions to train the model.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK `profiles.id` |
| `sound_id` | `uuid` | FK `sounds.id` |
| `value` | `int` | 1-5 rating or -1/1 like/dislike |
| `created_at` | `timestamptz` | When the vote happened |

**RLS Policies:**
- Users can insert their own votes.
- Users can read their own votes.

### 4. `sessions`
Tracks active listeners for the "Collective AI" feature (averaging preferences of active users).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK `profiles.id` |
| `status` | `text` | 'active', 'idle' |
| `last_active_at` | `timestamptz` | Last heartbeat |
| `expires_at` | `timestamptz` | When session is considered dead |

**RLS Policies:**
- Users can upsert their own session.
- Public read (for "Active Listeners" count).

### 5. `mixes` (New - V2 Feature Port)
Stores 16-channel layer configurations. This allows the backend to serve complex soundscapes (V2 style) using V1's robust storage.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `name` | `text` | Mix name (e.g., "Rainy Cafe") |
| `creator_id` | `uuid` | FK `profiles.id` |
| `layers` | `jsonb` | Array of `{sound_id, volume, loop, delay}` |
| `is_public` | `boolean` | If true, anyone can play this mix |
| `created_at` | `timestamptz` | Creation time |

**RLS Policies:**
- Public read for public mixes.
- Users can CRUD their own mixes.

## Migration Strategy (V1 -> V3)

1. **Consolidate User Data**: Move `preferences` table data into `profiles.preference_vector`.
2. **Standardize Sounds**: Ensure all local `.audio` files have entries in `sounds` with calculated embeddings.
3. **Port V2 Concepts**: Create `mixes` table to support future multi-channel playback.

## SQL Definition

```sql
-- Enable Vector Extension
create extension if not exists vector;

-- Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  display_name text,
  avatar_url text,
  preference_vector vector(5) default '[0,0,0,0,0]',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Sounds
create table sounds (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_path text not null,
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  duration int,
  created_at timestamptz default now()
);

-- Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  sound_id uuid references sounds(id) on delete cascade not null,
  value int not null,
  created_at timestamptz default now()
);

-- Sessions
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  status text default 'active',
  last_active_at timestamptz default now(),
  expires_at timestamptz generated always as (last_active_at + interval '1 hour') stored
);

-- Mixes (for 16-channel support)
create table mixes (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  creator_id uuid references profiles(id) on delete cascade,
  layers jsonb not null, -- Structure: [{sound_id, vol, ...}]
  is_public boolean default false,
  created_at timestamptz default now()
);

-- RLS Policies (Examples)
alter table profiles enable row level security;
create policy "Public profiles are viewable by everyone." on profiles for select using (true);
create policy "Users can insert their own profile." on profiles for insert with check (auth.uid() = id);
create policy "Users can update own profile." on profiles for update using (auth.uid() = id);
```


## Overview
This schema combines the working ML/Personalization from V1 with the advanced audio layering potential of V2, while strictly avoiding S3 and complex Django overhead. It is designed for Supabase.

## Extensions
- `vector`: For ML embeddings (cosine similarity).

## Tables

### 1. `profiles`
Extends Supabase Auth users. Stores the user's personalization vector.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK, References `auth.users.id` |
| `display_name` | `text` | Public username |
| `avatar_url` | `text` | Profile picture |
| `preference_vector` | `vector(5)` | The 5D user preference vector (updated via gradient descent) |
| `created_at` | `timestamptz` | Account creation |
| `updated_at` | `timestamptz` | Last update |

**RLS Policies:**
- Public read access.
- Users can update their own profile.

### 2. `sounds`
Stores metadata and vector embeddings for audio files. Files are stored in Supabase Storage or local `.audio/` directory (mapped by `file_path`).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK, Default `gen_random_uuid()` |
| `title` | `text` | Song title |
| `artist` | `text` | Artist name (optional) |
| `file_path` | `text` | Path in storage bucket or local system |
| `type` | `text` | Enum: 'soundscape', 'instrumental' (V2 feature) |
| `embedding` | `vector(5)` | 5D audio feature vector |
| `duration` | `int` | Duration in seconds |
| `created_at` | `timestamptz` | Upload time |

**RLS Policies:**
- Public read access.
- Admin-only write access.

### 3. `votes`
Records user interactions to train the model.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK `profiles.id` |
| `sound_id` | `uuid` | FK `sounds.id` |
| `value` | `int` | 1-5 rating or -1/1 like/dislike |
| `created_at` | `timestamptz` | When the vote happened |

**RLS Policies:**
- Users can insert their own votes.
- Users can read their own votes.

### 4. `sessions`
Tracks active listeners for the "Collective AI" feature (averaging preferences of active users).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK `profiles.id` |
| `status` | `text` | 'active', 'idle' |
| `last_active_at` | `timestamptz` | Last heartbeat |
| `expires_at` | `timestamptz` | When session is considered dead |

**RLS Policies:**
- Users can upsert their own session.
- Public read (for "Active Listeners" count).

### 5. `mixes` (New - V2 Feature Port)
Stores 16-channel layer configurations. This allows the backend to serve complex soundscapes (V2 style) using V1's robust storage.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `name` | `text` | Mix name (e.g., "Rainy Cafe") |
| `creator_id` | `uuid` | FK `profiles.id` |
| `layers` | `jsonb` | Array of `{sound_id, volume, loop, delay}` |
| `is_public` | `boolean` | If true, anyone can play this mix |
| `created_at` | `timestamptz` | Creation time |

**RLS Policies:**
- Public read for public mixes.
- Users can CRUD their own mixes.

## Migration Strategy (V1 -> V3)

1. **Consolidate User Data**: Move `preferences` table data into `profiles.preference_vector`.
2. **Standardize Sounds**: Ensure all local `.audio` files have entries in `sounds` with calculated embeddings.
3. **Port V2 Concepts**: Create `mixes` table to support future multi-channel playback.

## SQL Definition

```sql
-- Enable Vector Extension
create extension if not exists vector;

-- Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  display_name text,
  avatar_url text,
  preference_vector vector(5) default '[0,0,0,0,0]',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Sounds
create table sounds (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_path text not null,
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  duration int,
  created_at timestamptz default now()
);

-- Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  sound_id uuid references sounds(id) on delete cascade not null,
  value int not null,
  created_at timestamptz default now()
);

-- Sessions
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  status text default 'active',
  last_active_at timestamptz default now(),
  expires_at timestamptz generated always as (last_active_at + interval '1 hour') stored
);

-- Mixes (for 16-channel support)
create table mixes (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  creator_id uuid references profiles(id) on delete cascade,
  layers jsonb not null, -- Structure: [{sound_id, vol, ...}]
  is_public boolean default false,
  created_at timestamptz default now()
);

-- RLS Policies (Examples)
alter table profiles enable row level security;
create policy "Public profiles are viewable by everyone." on profiles for select using (true);
create policy "Users can insert their own profile." on profiles for insert with check (auth.uid() = id);
create policy "Users can update own profile." on profiles for update using (auth.uid() = id);
```


## Overview
This schema combines the working ML/Personalization from V1 with the advanced audio layering potential of V2, while strictly avoiding S3 and complex Django overhead. It is designed for Supabase.

## Extensions
- `vector`: For ML embeddings (cosine similarity).

## Tables

### 1. `profiles`
Extends Supabase Auth users. Stores the user's personalization vector.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK, References `auth.users.id` |
| `display_name` | `text` | Public username |
| `avatar_url` | `text` | Profile picture |
| `preference_vector` | `vector(5)` | The 5D user preference vector (updated via gradient descent) |
| `created_at` | `timestamptz` | Account creation |
| `updated_at` | `timestamptz` | Last update |

**RLS Policies:**
- Public read access.
- Users can update their own profile.

### 2. `sounds`
Stores metadata and vector embeddings for audio files. Files are stored in Supabase Storage or local `.audio/` directory (mapped by `file_path`).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK, Default `gen_random_uuid()` |
| `title` | `text` | Song title |
| `artist` | `text` | Artist name (optional) |
| `file_path` | `text` | Path in storage bucket or local system |
| `type` | `text` | Enum: 'soundscape', 'instrumental' (V2 feature) |
| `embedding` | `vector(5)` | 5D audio feature vector |
| `duration` | `int` | Duration in seconds |
| `created_at` | `timestamptz` | Upload time |

**RLS Policies:**
- Public read access.
- Admin-only write access.

### 3. `votes`
Records user interactions to train the model.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK `profiles.id` |
| `sound_id` | `uuid` | FK `sounds.id` |
| `value` | `int` | 1-5 rating or -1/1 like/dislike |
| `created_at` | `timestamptz` | When the vote happened |

**RLS Policies:**
- Users can insert their own votes.
- Users can read their own votes.

### 4. `sessions`
Tracks active listeners for the "Collective AI" feature (averaging preferences of active users).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK `profiles.id` |
| `status` | `text` | 'active', 'idle' |
| `last_active_at` | `timestamptz` | Last heartbeat |
| `expires_at` | `timestamptz` | When session is considered dead |

**RLS Policies:**
- Users can upsert their own session.
- Public read (for "Active Listeners" count).

### 5. `mixes` (New - V2 Feature Port)
Stores 16-channel layer configurations. This allows the backend to serve complex soundscapes (V2 style) using V1's robust storage.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `name` | `text` | Mix name (e.g., "Rainy Cafe") |
| `creator_id` | `uuid` | FK `profiles.id` |
| `layers` | `jsonb` | Array of `{sound_id, volume, loop, delay}` |
| `is_public` | `boolean` | If true, anyone can play this mix |
| `created_at` | `timestamptz` | Creation time |

**RLS Policies:**
- Public read for public mixes.
- Users can CRUD their own mixes.

## Migration Strategy (V1 -> V3)

1. **Consolidate User Data**: Move `preferences` table data into `profiles.preference_vector`.
2. **Standardize Sounds**: Ensure all local `.audio` files have entries in `sounds` with calculated embeddings.
3. **Port V2 Concepts**: Create `mixes` table to support future multi-channel playback.

## SQL Definition

```sql
-- Enable Vector Extension
create extension if not exists vector;

-- Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  display_name text,
  avatar_url text,
  preference_vector vector(5) default '[0,0,0,0,0]',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Sounds
create table sounds (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_path text not null,
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  duration int,
  created_at timestamptz default now()
);

-- Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  sound_id uuid references sounds(id) on delete cascade not null,
  value int not null,
  created_at timestamptz default now()
);

-- Sessions
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  status text default 'active',
  last_active_at timestamptz default now(),
  expires_at timestamptz generated always as (last_active_at + interval '1 hour') stored
);

-- Mixes (for 16-channel support)
create table mixes (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  creator_id uuid references profiles(id) on delete cascade,
  layers jsonb not null, -- Structure: [{sound_id, vol, ...}]
  is_public boolean default false,
  created_at timestamptz default now()
);

-- RLS Policies (Examples)
alter table profiles enable row level security;
create policy "Public profiles are viewable by everyone." on profiles for select using (true);
create policy "Users can insert their own profile." on profiles for insert with check (auth.uid() = id);
create policy "Users can update own profile." on profiles for update using (auth.uid() = id);
```


## Overview
This schema combines the working ML/Personalization from V1 with the advanced audio layering potential of V2, while strictly avoiding S3 and complex Django overhead. It is designed for Supabase.

## Extensions
- `vector`: For ML embeddings (cosine similarity).

## Tables

### 1. `profiles`
Extends Supabase Auth users. Stores the user's personalization vector.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK, References `auth.users.id` |
| `display_name` | `text` | Public username |
| `avatar_url` | `text` | Profile picture |
| `preference_vector` | `vector(5)` | The 5D user preference vector (updated via gradient descent) |
| `created_at` | `timestamptz` | Account creation |
| `updated_at` | `timestamptz` | Last update |

**RLS Policies:**
- Public read access.
- Users can update their own profile.

### 2. `sounds`
Stores metadata and vector embeddings for audio files. Files are stored in Supabase Storage or local `.audio/` directory (mapped by `file_path`).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK, Default `gen_random_uuid()` |
| `title` | `text` | Song title |
| `artist` | `text` | Artist name (optional) |
| `file_path` | `text` | Path in storage bucket or local system |
| `type` | `text` | Enum: 'soundscape', 'instrumental' (V2 feature) |
| `embedding` | `vector(5)` | 5D audio feature vector |
| `duration` | `int` | Duration in seconds |
| `created_at` | `timestamptz` | Upload time |

**RLS Policies:**
- Public read access.
- Admin-only write access.

### 3. `votes`
Records user interactions to train the model.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK `profiles.id` |
| `sound_id` | `uuid` | FK `sounds.id` |
| `value` | `int` | 1-5 rating or -1/1 like/dislike |
| `created_at` | `timestamptz` | When the vote happened |

**RLS Policies:**
- Users can insert their own votes.
- Users can read their own votes.

### 4. `sessions`
Tracks active listeners for the "Collective AI" feature (averaging preferences of active users).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK `profiles.id` |
| `status` | `text` | 'active', 'idle' |
| `last_active_at` | `timestamptz` | Last heartbeat |
| `expires_at` | `timestamptz` | When session is considered dead |

**RLS Policies:**
- Users can upsert their own session.
- Public read (for "Active Listeners" count).

### 5. `mixes` (New - V2 Feature Port)
Stores 16-channel layer configurations. This allows the backend to serve complex soundscapes (V2 style) using V1's robust storage.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | PK |
| `name` | `text` | Mix name (e.g., "Rainy Cafe") |
| `creator_id` | `uuid` | FK `profiles.id` |
| `layers` | `jsonb` | Array of `{sound_id, volume, loop, delay}` |
| `is_public` | `boolean` | If true, anyone can play this mix |
| `created_at` | `timestamptz` | Creation time |

**RLS Policies:**
- Public read for public mixes.
- Users can CRUD their own mixes.

## Migration Strategy (V1 -> V3)

1. **Consolidate User Data**: Move `preferences` table data into `profiles.preference_vector`.
2. **Standardize Sounds**: Ensure all local `.audio` files have entries in `sounds` with calculated embeddings.
3. **Port V2 Concepts**: Create `mixes` table to support future multi-channel playback.

## SQL Definition

```sql
-- Enable Vector Extension
create extension if not exists vector;

-- Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  display_name text,
  avatar_url text,
  preference_vector vector(5) default '[0,0,0,0,0]',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Sounds
create table sounds (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_path text not null,
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  duration int,
  created_at timestamptz default now()
);

-- Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  sound_id uuid references sounds(id) on delete cascade not null,
  value int not null,
  created_at timestamptz default now()
);

-- Sessions
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade not null,
  status text default 'active',
  last_active_at timestamptz default now(),
  expires_at timestamptz generated always as (last_active_at + interval '1 hour') stored
);

-- Mixes (for 16-channel support)
create table mixes (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  creator_id uuid references profiles(id) on delete cascade,
  layers jsonb not null, -- Structure: [{sound_id, vol, ...}]
  is_public boolean default false,
  created_at timestamptz default now()
);

-- RLS Policies (Examples)
alter table profiles enable row level security;
create policy "Public profiles are viewable by everyone." on profiles for select using (true);
create policy "Users can insert their own profile." on profiles for insert with check (auth.uid() = id);
create policy "Users can update own profile." on profiles for update using (auth.uid() = id);
```

