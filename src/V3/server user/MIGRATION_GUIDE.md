# V1 → V3 Migration Guide (Node.js Server)

## Overview
The V1 API structure is **excellent** and requires only minor schema updates to work with V3 Supabase database.

## Changes Required

### 1. Preferences Table → `profiles.preference_vector`

**Old (V1)**:
```sql
preferences
├── id
├── user_id
├── preference (jsonb: "[0.5, 0.8, ...]")
└── updated_at
```

**New (V3)**:
```sql
profiles
├── id
├── preference_vector (vector(5))  -- Native pgvector type
└── updated_at
```

**Code Changes**:
- `from('preferences')` → `from('profiles')`
- `JSON.parse(data.preference)` → Direct array access (pgvector returns arrays)
- `JSON.stringify(preferences)` → Direct array (pgvector accepts arrays)

### 2. Vote Table Rename

**Old**: `from('vote')`  
**New**: `from('votes')`

Simple find-replace across all files.

### 3. Songs Table (New Structure)

**Old (V1)**: Songs were referenced by `song` (text field in votes)  
**New (V3)**: Songs have dedicated `songs` table with UUIDs

```sql
songs
├── id (uuid)
├── title
├── file_url (S3)
├── embedding (vector(5))
└── ...
```

**Impact**: 
- Votes now reference `song_id` (uuid) instead of `song` (text)
- Need to query `songs` table for metadata

### 4. Recommendation Function (Supabase Cron)

**Old (V1)**: Node.js calculates recommendations on-demand  
**New (V3)**: Supabase cron job runs `recommend_with_penalty()` every 30s

**Node.js Role**: Just read from `player_queue` table (already populated by cron)

---

## File-by-File Changes

### ✅ No Changes Needed
- `middleware/auth.js` - JWT validation works as-is
- `routes/auth.js` - Profile endpoints work as-is
- `routes/session.js` - Sessions table unchanged
- `index.js` - Server setup unchanged

### 🔧 Minor Updates

#### `routes/prefVote.js`

**Line 21-24**: Change `preferences` → `profiles`
```javascript
// OLD
const { data, error } = await req.supabase
  .from('preferences')
  .select('preference')
  .eq('user_id', req.user.id)

// NEW
const { data, error } = await req.supabase
  .from('profiles')
  .select('preference_vector')
  .eq('id', req.user.id)
```

**Line 34**: No JSON.parse needed (pgvector returns arrays)
```javascript
// OLD
const prefs = JSON.parse(data.preference);

// NEW
const prefs = data.preference_vector || [0, 0, 0, 0, 0];
```

**Line 50-54**: Same change
```javascript
// OLD
.from('preferences')

// NEW
.from('profiles')
.select('preference_vector')
```

**Line 66**: Default preferences
```javascript
// OLD
preference: [0, 0, 0, 0, 0]

// NEW
preference_vector: [0, 0, 0, 0, 0]
```

**Line 75**: No JSON.parse
```javascript
// OLD
preference: JSON.parse(data.preference)

// NEW
preference_vector: data.preference_vector
```

**Line 107-127**: Update/Insert preferences
```javascript
// OLD
const { data: existing } = await req.supabase
  .from('preferences')
  .select('id')
  .eq('user_id', req.user.id)
  .single();

if (existing) {
  await req.supabase
    .from('preferences')
    .update({ preference: JSON.stringify(preferences) })
    .eq('user_id', req.user.id);
} else {
  await req.supabase
    .from('preferences')
    .insert({ user_id: req.user.id, preference: JSON.stringify(preferences) });
}

// NEW (Simpler - just update profiles)
await req.supabase
  .from('profiles')
  .update({ preference_vector: preferences })
  .eq('id', req.user.id);
```

**Line 200+**: Vote table rename
```javascript
// OLD
.from('vote')

// NEW
.from('votes')
```

**Line 321-390**: Vote processing (gradient descent)
This section is **perfect** - just update table names:
- `from('vote')` → `from('votes')`
- `from('preferences')` → `from('profiles')` with `preference_vector`

#### `routes/modelRoutes.js`

**Line 79-91**: Get preferences
```javascript
// OLD
.from('preferences')
.select('*');
// Parse JSON
preference: JSON.parse(pref.preference)

// NEW
.from('profiles')
.select('id, display_name, preference_vector, updated_at');
// No parsing needed
preference_vector: pref.preference_vector
```

**Line 109-148**: Active users
```javascript
// OLD
const { data: prefs } = await supabase
  .from('preferences')
  .select('preference')
  .eq('user_id', session.user_id)
  .single();

preferences: prefs ? JSON.parse(prefs.preference) : [0, 0, 0, 0, 0]

// NEW
const { data: profile } = await supabase
  .from('profiles')
  .select('preference_vector')
  .eq('id', session.user_id)
  .single();

preference_vector: profile?.preference_vector || [0, 0, 0, 0, 0]
```

**Line 200-300**: Recommend endpoint
```javascript
// OLD (Complex averaging + cosine similarity in Node.js)
const activeUsers = await getActiveUsers();
const avgVector = calculateAverage(activeUsers);
const recommendations = await findSimilarSongs(avgVector);

// NEW (Call Supabase function)
const { data: recommendations, error } = await req.supabase
  .rpc('recommend_with_penalty', {
    p_vec: avgVector,  // Still calculate average in Node
    p_limit: limit || 10
  });
```

**Line 50-70**: Songs endpoint
```javascript
// OLD (Get unique song names from votes)
.from('vote')
.select('song')  // song is text

// NEW (Get from songs table)
.from('songs')
.select('id, title, artist, type, duration')
```

#### `routes/leaderboard.js`

**Line 24-31**: Vote table rename
```javascript
// OLD
.from('vote')

// NEW
.from('votes')
```

---

## Environment Variables (Unchanged)

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...  # For admin operations
PORT=3000
```

---

## Testing Checklist

After making changes, test these endpoints:

### Preferences
- [ ] `GET /api/preferences/exists` - Returns correct status
- [ ] `GET /api/preferences` - Returns vector array
- [ ] `POST /api/preferences` - Updates `profiles.preference_vector`

### Votes
- [ ] `POST /api/votes` - Inserts into `votes` table
- [ ] `GET /api/votes` - Retrieves user votes
- [ ] Verify gradient descent updates `profiles.preference_vector`

### Model
- [ ] `GET /api/model/active-users` - Returns users with vectors
- [ ] `GET /api/model/recommend` - Calls Supabase function
- [ ] `GET /api/model/songs` - Returns from `songs` table

### Sessions (Should work unchanged)
- [ ] `POST /api/checkin`
- [ ] `GET /api/session`

### Leaderboard (Should work unchanged)
- [ ] `GET /api/leaderboard`

---

## Supabase Cron Job (Recommendation Engine)

**Setup in Supabase Dashboard** → Database → Cron Jobs:

```sql
-- Run every 30 seconds
select cron.schedule(
  'update-player-queues',
  '30 seconds',
  $$
  -- Get average preference vector of active users
  with active_prefs as (
    select avg(p.preference_vector) as avg_vector
    from sessions s
    join profiles p on p.id = s.user_id
    where s.status = 'active'
      and s.expires_at > now()
  ),
  -- Get recommendation
  recommendation as (
    select * from recommend_with_penalty(
      (select avg_vector from active_prefs),
      1  -- Get top 1 song
    )
    limit 1
  )
  -- Update player queues
  insert into player_queue (player_id, song_id, position)
  select 
    p.id,
    r.id,
    1
  from players p
  cross join recommendation r
  on conflict (player_id, position) 
  do update set song_id = excluded.song_id, added_at = now();
  $$
);
```

This cron job:
1. Averages active users' `preference_vector`
2. Calls `recommend_with_penalty()`
3. Updates `player_queue` for all players
4. Node.js just reads from `player_queue` (no calculation needed)

---

## Summary

**Total Changes**: ~50 lines across 3 files  
**Time Estimate**: 1-2 hours  
**Risk Level**: Low (mostly find-replace)

The V1 API design is **excellent** - it just needs schema alignment. The core logic (gradient descent, session management, JWT auth) remains unchanged.

