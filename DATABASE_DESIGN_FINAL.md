# V3 Database Design & Migration Plan

## 1. Database Schema (Supabase PostgreSQL)

This schema strictly follows your screenshot requirements while integrating the necessary "Player" and "S3" components from V2.

### Core Tables (Matches Screenshot)

#### `profiles`
Extends Supabase Auth.
- `id` (uuid, PK): References `auth.users.id`
- `email` (text): User email
- `name` (text): Full name
- `display_name` (text): Public handle
- `created_at` (timestamptz)

#### `roles`
RBAC system.
- `id` (uuid, PK)
- `role` (text): 'admin', 'user', 'manager'
- `user_id` (uuid, FK): References `profiles.id` (One-to-One or One-to-Many depending on need)

#### `songs`
Stores metadata and S3 links.
- `id` (uuid, PK)
- `title` (text)
- `artist` (text)
- `file_url` (text): **S3 URL** (e.g., `https://bucket.s3.amazonaws.com/...`)
- `type` (text): 'soundscape' | 'instrumental' (V2 feature)
- `embedding` (vector(5)): For ML personalization
- `created_at` (timestamptz)
- `last_played` (timestamptz)

#### `songs_playing`
History log.
- `id` (uuid, PK)
- `song_id` (uuid, FK): References `songs.id`
- `played_at` (timestamptz)

#### `votes`
User feedback.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `song_id` (uuid, FK): References `songs.id`
- `vote_value` (int): 1-5 or -1/1
- `vote_time` (timestamptz)

#### `sessions`
Active listener tracking.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `checked_in_at` (timestamptz)
- `expires_at` (timestamptz)
- `status` (text): 'active' | 'inactive'
- `created_at` (timestamptz)

#### `preferences`
User ML vectors.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `preference` (vector(5)): The 5D user preference vector
- `updated_at` (timestamptz)

### New Table: `players` (The "Happy" Compromise)
Keeps the V2 concept of physical players/clients without the bloat.
- `id` (uuid, PK)
- `name` (text): e.g., "Lobby Speaker", "Desktop Client"
- `token` (text): Hashed API token for the player to authenticate
- `status` (text): 'online' | 'offline'
- `manager_id` (uuid, FK): References `profiles.id` (The Admin/Manager who owns this player)
- `created_at` (timestamptz)

---

## 2. Django Migration Strategy (The "Rewrite")

**Goal:** Keep Django as the Admin/Player interface but strip its backend logic in favor of Supabase.

### Step 1: Connect Django to Supabase DB
Instead of using a local `db.sqlite3`, configure Django to connect directly to the Supabase PostgreSQL instance.

**`settings.py`**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'YOUR_SUPABASE_DB_PASSWORD',
        'HOST': 'db.YOUR_PROJECT_REF.supabase.co',
        'PORT': '5432',
    }
}
```

### Step 2: Use Unmanaged Models (`managed = False`)
Since Supabase (and your V1 Node app) owns the schema, Django should just **read/write** to it, not manage migrations.

**Example `models.py` in Django:**
```python
class Profile(models.Model):
    id = models.UUIDField(primary_key=True)
    display_name = models.CharField(max_length=255)
    # ... other fields
    
    class Meta:
        managed = False  # Django won't try to create/alter this table
        db_table = 'profiles'
```

### Step 3: Auth Bridge
Django's default User model is incompatible with Supabase `auth.users`.
1.  **Admin Login:** Keep using Django's `User` table *only* for superusers who need to access the Django Admin panel.
2.  **App Login:** For actual app users (Managers), use a custom Authentication Backend that verifies Supabase JWTs.

### Step 4: S3 Integration
Use `django-storages` and `boto3` in Django only for the **Admin Upload** interface.
- When an Admin uploads a song in Django, it goes to S3.
- Django saves the S3 URL to the `songs` table in Supabase.
- The V1 Node server reads this URL to play the music.

---

## 3. SQL Setup Script

```sql
-- Enable Vector Extension
create extension if not exists vector;

-- 1. Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  name text,
  display_name text,
  created_at timestamptz default now()
);

-- 2. Roles
create table roles (
  id uuid default gen_random_uuid() primary key,
  role text check (role in ('admin', 'manager', 'user')),
  user_id uuid references profiles(id) on delete cascade
);

-- 3. Songs (S3 Support)
create table songs (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_url text not null, -- S3 URL
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  created_at timestamptz default now(),
  last_played timestamptz
);

-- 4. Songs Playing (History)
create table songs_playing (
  id uuid default gen_random_uuid() primary key,
  song_id uuid references songs(id) on delete set null,
  played_at timestamptz default now()
);

-- 5. Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  song_id uuid references songs(id) on delete cascade,
  vote_value int not null,
  vote_time timestamptz default now()
);

-- 6. Sessions
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  checked_in_at timestamptz default now(),
  expires_at timestamptz,
  status text default 'active',
  created_at timestamptz default now()
);

-- 7. Preferences
create table preferences (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  preference vector(5),
  updated_at timestamptz default now()
);

-- 8. Players (New)
create table players (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  token text unique not null,
  status text default 'offline',
  manager_id uuid references profiles(id) on delete set null,
  created_at timestamptz default now()
);

-- RLS Policies (Basic Security)
alter table profiles enable row level security;
alter table songs enable row level security;
alter table votes enable row level security;

create policy "Public profiles" on profiles for select using (true);
create policy "Public songs" on songs for select using (true);
create policy "User votes" on votes for insert with check (auth.uid() = user_id);
```


## 1. Database Schema (Supabase PostgreSQL)

This schema strictly follows your screenshot requirements while integrating the necessary "Player" and "S3" components from V2.

### Core Tables (Matches Screenshot)

#### `profiles`
Extends Supabase Auth.
- `id` (uuid, PK): References `auth.users.id`
- `email` (text): User email
- `name` (text): Full name
- `display_name` (text): Public handle
- `created_at` (timestamptz)

#### `roles`
RBAC system.
- `id` (uuid, PK)
- `role` (text): 'admin', 'user', 'manager'
- `user_id` (uuid, FK): References `profiles.id` (One-to-One or One-to-Many depending on need)

#### `songs`
Stores metadata and S3 links.
- `id` (uuid, PK)
- `title` (text)
- `artist` (text)
- `file_url` (text): **S3 URL** (e.g., `https://bucket.s3.amazonaws.com/...`)
- `type` (text): 'soundscape' | 'instrumental' (V2 feature)
- `embedding` (vector(5)): For ML personalization
- `created_at` (timestamptz)
- `last_played` (timestamptz)

#### `songs_playing`
History log.
- `id` (uuid, PK)
- `song_id` (uuid, FK): References `songs.id`
- `played_at` (timestamptz)

#### `votes`
User feedback.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `song_id` (uuid, FK): References `songs.id`
- `vote_value` (int): 1-5 or -1/1
- `vote_time` (timestamptz)

#### `sessions`
Active listener tracking.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `checked_in_at` (timestamptz)
- `expires_at` (timestamptz)
- `status` (text): 'active' | 'inactive'
- `created_at` (timestamptz)

#### `preferences`
User ML vectors.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `preference` (vector(5)): The 5D user preference vector
- `updated_at` (timestamptz)

### New Table: `players` (The "Happy" Compromise)
Keeps the V2 concept of physical players/clients without the bloat.
- `id` (uuid, PK)
- `name` (text): e.g., "Lobby Speaker", "Desktop Client"
- `token` (text): Hashed API token for the player to authenticate
- `status` (text): 'online' | 'offline'
- `manager_id` (uuid, FK): References `profiles.id` (The Admin/Manager who owns this player)
- `created_at` (timestamptz)

---

## 2. Django Migration Strategy (The "Rewrite")

**Goal:** Keep Django as the Admin/Player interface but strip its backend logic in favor of Supabase.

### Step 1: Connect Django to Supabase DB
Instead of using a local `db.sqlite3`, configure Django to connect directly to the Supabase PostgreSQL instance.

**`settings.py`**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'YOUR_SUPABASE_DB_PASSWORD',
        'HOST': 'db.YOUR_PROJECT_REF.supabase.co',
        'PORT': '5432',
    }
}
```

### Step 2: Use Unmanaged Models (`managed = False`)
Since Supabase (and your V1 Node app) owns the schema, Django should just **read/write** to it, not manage migrations.

**Example `models.py` in Django:**
```python
class Profile(models.Model):
    id = models.UUIDField(primary_key=True)
    display_name = models.CharField(max_length=255)
    # ... other fields
    
    class Meta:
        managed = False  # Django won't try to create/alter this table
        db_table = 'profiles'
```

### Step 3: Auth Bridge
Django's default User model is incompatible with Supabase `auth.users`.
1.  **Admin Login:** Keep using Django's `User` table *only* for superusers who need to access the Django Admin panel.
2.  **App Login:** For actual app users (Managers), use a custom Authentication Backend that verifies Supabase JWTs.

### Step 4: S3 Integration
Use `django-storages` and `boto3` in Django only for the **Admin Upload** interface.
- When an Admin uploads a song in Django, it goes to S3.
- Django saves the S3 URL to the `songs` table in Supabase.
- The V1 Node server reads this URL to play the music.

---

## 3. SQL Setup Script

```sql
-- Enable Vector Extension
create extension if not exists vector;

-- 1. Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  name text,
  display_name text,
  created_at timestamptz default now()
);

-- 2. Roles
create table roles (
  id uuid default gen_random_uuid() primary key,
  role text check (role in ('admin', 'manager', 'user')),
  user_id uuid references profiles(id) on delete cascade
);

-- 3. Songs (S3 Support)
create table songs (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_url text not null, -- S3 URL
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  created_at timestamptz default now(),
  last_played timestamptz
);

-- 4. Songs Playing (History)
create table songs_playing (
  id uuid default gen_random_uuid() primary key,
  song_id uuid references songs(id) on delete set null,
  played_at timestamptz default now()
);

-- 5. Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  song_id uuid references songs(id) on delete cascade,
  vote_value int not null,
  vote_time timestamptz default now()
);

-- 6. Sessions
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  checked_in_at timestamptz default now(),
  expires_at timestamptz,
  status text default 'active',
  created_at timestamptz default now()
);

-- 7. Preferences
create table preferences (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  preference vector(5),
  updated_at timestamptz default now()
);

-- 8. Players (New)
create table players (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  token text unique not null,
  status text default 'offline',
  manager_id uuid references profiles(id) on delete set null,
  created_at timestamptz default now()
);

-- RLS Policies (Basic Security)
alter table profiles enable row level security;
alter table songs enable row level security;
alter table votes enable row level security;

create policy "Public profiles" on profiles for select using (true);
create policy "Public songs" on songs for select using (true);
create policy "User votes" on votes for insert with check (auth.uid() = user_id);
```


## 1. Database Schema (Supabase PostgreSQL)

This schema strictly follows your screenshot requirements while integrating the necessary "Player" and "S3" components from V2.

### Core Tables (Matches Screenshot)

#### `profiles`
Extends Supabase Auth.
- `id` (uuid, PK): References `auth.users.id`
- `email` (text): User email
- `name` (text): Full name
- `display_name` (text): Public handle
- `created_at` (timestamptz)

#### `roles`
RBAC system.
- `id` (uuid, PK)
- `role` (text): 'admin', 'user', 'manager'
- `user_id` (uuid, FK): References `profiles.id` (One-to-One or One-to-Many depending on need)

#### `songs`
Stores metadata and S3 links.
- `id` (uuid, PK)
- `title` (text)
- `artist` (text)
- `file_url` (text): **S3 URL** (e.g., `https://bucket.s3.amazonaws.com/...`)
- `type` (text): 'soundscape' | 'instrumental' (V2 feature)
- `embedding` (vector(5)): For ML personalization
- `created_at` (timestamptz)
- `last_played` (timestamptz)

#### `songs_playing`
History log.
- `id` (uuid, PK)
- `song_id` (uuid, FK): References `songs.id`
- `played_at` (timestamptz)

#### `votes`
User feedback.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `song_id` (uuid, FK): References `songs.id`
- `vote_value` (int): 1-5 or -1/1
- `vote_time` (timestamptz)

#### `sessions`
Active listener tracking.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `checked_in_at` (timestamptz)
- `expires_at` (timestamptz)
- `status` (text): 'active' | 'inactive'
- `created_at` (timestamptz)

#### `preferences`
User ML vectors.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `preference` (vector(5)): The 5D user preference vector
- `updated_at` (timestamptz)

### New Table: `players` (The "Happy" Compromise)
Keeps the V2 concept of physical players/clients without the bloat.
- `id` (uuid, PK)
- `name` (text): e.g., "Lobby Speaker", "Desktop Client"
- `token` (text): Hashed API token for the player to authenticate
- `status` (text): 'online' | 'offline'
- `manager_id` (uuid, FK): References `profiles.id` (The Admin/Manager who owns this player)
- `created_at` (timestamptz)

---

## 2. Django Migration Strategy (The "Rewrite")

**Goal:** Keep Django as the Admin/Player interface but strip its backend logic in favor of Supabase.

### Step 1: Connect Django to Supabase DB
Instead of using a local `db.sqlite3`, configure Django to connect directly to the Supabase PostgreSQL instance.

**`settings.py`**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'YOUR_SUPABASE_DB_PASSWORD',
        'HOST': 'db.YOUR_PROJECT_REF.supabase.co',
        'PORT': '5432',
    }
}
```

### Step 2: Use Unmanaged Models (`managed = False`)
Since Supabase (and your V1 Node app) owns the schema, Django should just **read/write** to it, not manage migrations.

**Example `models.py` in Django:**
```python
class Profile(models.Model):
    id = models.UUIDField(primary_key=True)
    display_name = models.CharField(max_length=255)
    # ... other fields
    
    class Meta:
        managed = False  # Django won't try to create/alter this table
        db_table = 'profiles'
```

### Step 3: Auth Bridge
Django's default User model is incompatible with Supabase `auth.users`.
1.  **Admin Login:** Keep using Django's `User` table *only* for superusers who need to access the Django Admin panel.
2.  **App Login:** For actual app users (Managers), use a custom Authentication Backend that verifies Supabase JWTs.

### Step 4: S3 Integration
Use `django-storages` and `boto3` in Django only for the **Admin Upload** interface.
- When an Admin uploads a song in Django, it goes to S3.
- Django saves the S3 URL to the `songs` table in Supabase.
- The V1 Node server reads this URL to play the music.

---

## 3. SQL Setup Script

```sql
-- Enable Vector Extension
create extension if not exists vector;

-- 1. Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  name text,
  display_name text,
  created_at timestamptz default now()
);

-- 2. Roles
create table roles (
  id uuid default gen_random_uuid() primary key,
  role text check (role in ('admin', 'manager', 'user')),
  user_id uuid references profiles(id) on delete cascade
);

-- 3. Songs (S3 Support)
create table songs (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_url text not null, -- S3 URL
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  created_at timestamptz default now(),
  last_played timestamptz
);

-- 4. Songs Playing (History)
create table songs_playing (
  id uuid default gen_random_uuid() primary key,
  song_id uuid references songs(id) on delete set null,
  played_at timestamptz default now()
);

-- 5. Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  song_id uuid references songs(id) on delete cascade,
  vote_value int not null,
  vote_time timestamptz default now()
);

-- 6. Sessions
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  checked_in_at timestamptz default now(),
  expires_at timestamptz,
  status text default 'active',
  created_at timestamptz default now()
);

-- 7. Preferences
create table preferences (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  preference vector(5),
  updated_at timestamptz default now()
);

-- 8. Players (New)
create table players (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  token text unique not null,
  status text default 'offline',
  manager_id uuid references profiles(id) on delete set null,
  created_at timestamptz default now()
);

-- RLS Policies (Basic Security)
alter table profiles enable row level security;
alter table songs enable row level security;
alter table votes enable row level security;

create policy "Public profiles" on profiles for select using (true);
create policy "Public songs" on songs for select using (true);
create policy "User votes" on votes for insert with check (auth.uid() = user_id);
```


## 1. Database Schema (Supabase PostgreSQL)

This schema strictly follows your screenshot requirements while integrating the necessary "Player" and "S3" components from V2.

### Core Tables (Matches Screenshot)

#### `profiles`
Extends Supabase Auth.
- `id` (uuid, PK): References `auth.users.id`
- `email` (text): User email
- `name` (text): Full name
- `display_name` (text): Public handle
- `created_at` (timestamptz)

#### `roles`
RBAC system.
- `id` (uuid, PK)
- `role` (text): 'admin', 'user', 'manager'
- `user_id` (uuid, FK): References `profiles.id` (One-to-One or One-to-Many depending on need)

#### `songs`
Stores metadata and S3 links.
- `id` (uuid, PK)
- `title` (text)
- `artist` (text)
- `file_url` (text): **S3 URL** (e.g., `https://bucket.s3.amazonaws.com/...`)
- `type` (text): 'soundscape' | 'instrumental' (V2 feature)
- `embedding` (vector(5)): For ML personalization
- `created_at` (timestamptz)
- `last_played` (timestamptz)

#### `songs_playing`
History log.
- `id` (uuid, PK)
- `song_id` (uuid, FK): References `songs.id`
- `played_at` (timestamptz)

#### `votes`
User feedback.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `song_id` (uuid, FK): References `songs.id`
- `vote_value` (int): 1-5 or -1/1
- `vote_time` (timestamptz)

#### `sessions`
Active listener tracking.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `checked_in_at` (timestamptz)
- `expires_at` (timestamptz)
- `status` (text): 'active' | 'inactive'
- `created_at` (timestamptz)

#### `preferences`
User ML vectors.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `preference` (vector(5)): The 5D user preference vector
- `updated_at` (timestamptz)

### New Table: `players` (The "Happy" Compromise)
Keeps the V2 concept of physical players/clients without the bloat.
- `id` (uuid, PK)
- `name` (text): e.g., "Lobby Speaker", "Desktop Client"
- `token` (text): Hashed API token for the player to authenticate
- `status` (text): 'online' | 'offline'
- `manager_id` (uuid, FK): References `profiles.id` (The Admin/Manager who owns this player)
- `created_at` (timestamptz)

---

## 2. Django Migration Strategy (The "Rewrite")

**Goal:** Keep Django as the Admin/Player interface but strip its backend logic in favor of Supabase.

### Step 1: Connect Django to Supabase DB
Instead of using a local `db.sqlite3`, configure Django to connect directly to the Supabase PostgreSQL instance.

**`settings.py`**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'YOUR_SUPABASE_DB_PASSWORD',
        'HOST': 'db.YOUR_PROJECT_REF.supabase.co',
        'PORT': '5432',
    }
}
```

### Step 2: Use Unmanaged Models (`managed = False`)
Since Supabase (and your V1 Node app) owns the schema, Django should just **read/write** to it, not manage migrations.

**Example `models.py` in Django:**
```python
class Profile(models.Model):
    id = models.UUIDField(primary_key=True)
    display_name = models.CharField(max_length=255)
    # ... other fields
    
    class Meta:
        managed = False  # Django won't try to create/alter this table
        db_table = 'profiles'
```

### Step 3: Auth Bridge
Django's default User model is incompatible with Supabase `auth.users`.
1.  **Admin Login:** Keep using Django's `User` table *only* for superusers who need to access the Django Admin panel.
2.  **App Login:** For actual app users (Managers), use a custom Authentication Backend that verifies Supabase JWTs.

### Step 4: S3 Integration
Use `django-storages` and `boto3` in Django only for the **Admin Upload** interface.
- When an Admin uploads a song in Django, it goes to S3.
- Django saves the S3 URL to the `songs` table in Supabase.
- The V1 Node server reads this URL to play the music.

---

## 3. SQL Setup Script

```sql
-- Enable Vector Extension
create extension if not exists vector;

-- 1. Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  name text,
  display_name text,
  created_at timestamptz default now()
);

-- 2. Roles
create table roles (
  id uuid default gen_random_uuid() primary key,
  role text check (role in ('admin', 'manager', 'user')),
  user_id uuid references profiles(id) on delete cascade
);

-- 3. Songs (S3 Support)
create table songs (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_url text not null, -- S3 URL
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  created_at timestamptz default now(),
  last_played timestamptz
);

-- 4. Songs Playing (History)
create table songs_playing (
  id uuid default gen_random_uuid() primary key,
  song_id uuid references songs(id) on delete set null,
  played_at timestamptz default now()
);

-- 5. Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  song_id uuid references songs(id) on delete cascade,
  vote_value int not null,
  vote_time timestamptz default now()
);

-- 6. Sessions
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  checked_in_at timestamptz default now(),
  expires_at timestamptz,
  status text default 'active',
  created_at timestamptz default now()
);

-- 7. Preferences
create table preferences (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  preference vector(5),
  updated_at timestamptz default now()
);

-- 8. Players (New)
create table players (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  token text unique not null,
  status text default 'offline',
  manager_id uuid references profiles(id) on delete set null,
  created_at timestamptz default now()
);

-- RLS Policies (Basic Security)
alter table profiles enable row level security;
alter table songs enable row level security;
alter table votes enable row level security;

create policy "Public profiles" on profiles for select using (true);
create policy "Public songs" on songs for select using (true);
create policy "User votes" on votes for insert with check (auth.uid() = user_id);
```


## 1. Database Schema (Supabase PostgreSQL)

This schema strictly follows your screenshot requirements while integrating the necessary "Player" and "S3" components from V2.

### Core Tables (Matches Screenshot)

#### `profiles`
Extends Supabase Auth.
- `id` (uuid, PK): References `auth.users.id`
- `email` (text): User email
- `name` (text): Full name
- `display_name` (text): Public handle
- `created_at` (timestamptz)

#### `roles`
RBAC system.
- `id` (uuid, PK)
- `role` (text): 'admin', 'user', 'manager'
- `user_id` (uuid, FK): References `profiles.id` (One-to-One or One-to-Many depending on need)

#### `songs`
Stores metadata and S3 links.
- `id` (uuid, PK)
- `title` (text)
- `artist` (text)
- `file_url` (text): **S3 URL** (e.g., `https://bucket.s3.amazonaws.com/...`)
- `type` (text): 'soundscape' | 'instrumental' (V2 feature)
- `embedding` (vector(5)): For ML personalization
- `created_at` (timestamptz)
- `last_played` (timestamptz)

#### `songs_playing`
History log.
- `id` (uuid, PK)
- `song_id` (uuid, FK): References `songs.id`
- `played_at` (timestamptz)

#### `votes`
User feedback.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `song_id` (uuid, FK): References `songs.id`
- `vote_value` (int): 1-5 or -1/1
- `vote_time` (timestamptz)

#### `sessions`
Active listener tracking.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `checked_in_at` (timestamptz)
- `expires_at` (timestamptz)
- `status` (text): 'active' | 'inactive'
- `created_at` (timestamptz)

#### `preferences`
User ML vectors.
- `id` (uuid, PK)
- `user_id` (uuid, FK): References `profiles.id`
- `preference` (vector(5)): The 5D user preference vector
- `updated_at` (timestamptz)

### New Table: `players` (The "Happy" Compromise)
Keeps the V2 concept of physical players/clients without the bloat.
- `id` (uuid, PK)
- `name` (text): e.g., "Lobby Speaker", "Desktop Client"
- `token` (text): Hashed API token for the player to authenticate
- `status` (text): 'online' | 'offline'
- `manager_id` (uuid, FK): References `profiles.id` (The Admin/Manager who owns this player)
- `created_at` (timestamptz)

---

## 2. Django Migration Strategy (The "Rewrite")

**Goal:** Keep Django as the Admin/Player interface but strip its backend logic in favor of Supabase.

### Step 1: Connect Django to Supabase DB
Instead of using a local `db.sqlite3`, configure Django to connect directly to the Supabase PostgreSQL instance.

**`settings.py`**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'YOUR_SUPABASE_DB_PASSWORD',
        'HOST': 'db.YOUR_PROJECT_REF.supabase.co',
        'PORT': '5432',
    }
}
```

### Step 2: Use Unmanaged Models (`managed = False`)
Since Supabase (and your V1 Node app) owns the schema, Django should just **read/write** to it, not manage migrations.

**Example `models.py` in Django:**
```python
class Profile(models.Model):
    id = models.UUIDField(primary_key=True)
    display_name = models.CharField(max_length=255)
    # ... other fields
    
    class Meta:
        managed = False  # Django won't try to create/alter this table
        db_table = 'profiles'
```

### Step 3: Auth Bridge
Django's default User model is incompatible with Supabase `auth.users`.
1.  **Admin Login:** Keep using Django's `User` table *only* for superusers who need to access the Django Admin panel.
2.  **App Login:** For actual app users (Managers), use a custom Authentication Backend that verifies Supabase JWTs.

### Step 4: S3 Integration
Use `django-storages` and `boto3` in Django only for the **Admin Upload** interface.
- When an Admin uploads a song in Django, it goes to S3.
- Django saves the S3 URL to the `songs` table in Supabase.
- The V1 Node server reads this URL to play the music.

---

## 3. SQL Setup Script

```sql
-- Enable Vector Extension
create extension if not exists vector;

-- 1. Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  name text,
  display_name text,
  created_at timestamptz default now()
);

-- 2. Roles
create table roles (
  id uuid default gen_random_uuid() primary key,
  role text check (role in ('admin', 'manager', 'user')),
  user_id uuid references profiles(id) on delete cascade
);

-- 3. Songs (S3 Support)
create table songs (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  artist text,
  file_url text not null, -- S3 URL
  type text check (type in ('soundscape', 'instrumental')),
  embedding vector(5),
  created_at timestamptz default now(),
  last_played timestamptz
);

-- 4. Songs Playing (History)
create table songs_playing (
  id uuid default gen_random_uuid() primary key,
  song_id uuid references songs(id) on delete set null,
  played_at timestamptz default now()
);

-- 5. Votes
create table votes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  song_id uuid references songs(id) on delete cascade,
  vote_value int not null,
  vote_time timestamptz default now()
);

-- 6. Sessions
create table sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  checked_in_at timestamptz default now(),
  expires_at timestamptz,
  status text default 'active',
  created_at timestamptz default now()
);

-- 7. Preferences
create table preferences (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references profiles(id) on delete cascade,
  preference vector(5),
  updated_at timestamptz default now()
);

-- 8. Players (New)
create table players (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  token text unique not null,
  status text default 'offline',
  manager_id uuid references profiles(id) on delete set null,
  created_at timestamptz default now()
);

-- RLS Policies (Basic Security)
alter table profiles enable row level security;
alter table songs enable row level security;
alter table votes enable row level security;

create policy "Public profiles" on profiles for select using (true);
create policy "Public songs" on songs for select using (true);
create policy "User votes" on votes for insert with check (auth.uid() = user_id);
```

