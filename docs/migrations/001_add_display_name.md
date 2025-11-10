# Database Migration: Display Name Feature

## Overview
Add `display_name` column to the `profiles` table to support user-chosen public names for the leaderboard.

---

## Migration SQL

### Add display_name Column

```sql
-- Add display_name column to profiles table
ALTER TABLE profiles 
ADD COLUMN display_name TEXT;
```

### Verification Query

```sql
-- Check if column was added successfully
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'profiles' 
  AND column_name = 'display_name';
```

Expected result:
```
column_name   | data_type | is_nullable
--------------+-----------+------------
display_name  | text      | YES
```

---

## Schema Details

### Column Specifications
- **Name:** `display_name`
- **Type:** `TEXT`
- **Nullable:** YES (optional field)
- **Default:** `NULL`
- **Constraints:** None

### Why No Constraints?

❌ **No UNIQUE constraint**  
- Multiple users can have the same display name
- Simplifies user experience
- No "username already taken" errors

❌ **No NOT NULL constraint**  
- Display name is optional
- Falls back to first name from Google if not set

❌ **No CHECK constraint**  
- Length validation handled in application layer (max 50 chars)
- Allows flexibility for future changes

❌ **No INDEX**  
- Not used for searching/filtering
- Only displayed in leaderboard output

---

## Row Level Security (RLS)

No additional RLS policies needed if your existing `profiles` table RLS is set up correctly:

### Required Policies

**1. Users can read their own profile:**
```sql
CREATE POLICY "Users can view own profile"
ON profiles FOR SELECT
USING (auth.uid() = id);
```

**2. Users can update their own profile:**
```sql
CREATE POLICY "Users can update own profile"
ON profiles FOR UPDATE
USING (auth.uid() = id);
```

These existing policies automatically cover the `display_name` column.

---

## Testing the Migration

### 1. Test Column Exists
```sql
SELECT display_name FROM profiles LIMIT 1;
```

### 2. Test INSERT (if needed)
```sql
-- Insert new profile with display_name
INSERT INTO profiles (id, email, name, display_name)
VALUES (
  'test-uuid-here',
  'test@example.com',
  'Test User',
  'TestDisplayName'
);
```

### 3. Test UPDATE
```sql
-- Update existing profile's display_name
UPDATE profiles 
SET display_name = 'NewDisplayName'
WHERE id = 'your-user-id-here';
```

### 4. Test Leaderboard Query
```sql
-- Test the leaderboard join query
SELECT 
  v.user_id,
  p.display_name,
  p.name,
  COUNT(*) as total_votes
FROM vote v
INNER JOIN profiles p ON p.id = v.user_id
WHERE v.vote_time >= date_trunc('month', CURRENT_TIMESTAMP)
GROUP BY v.user_id, p.display_name, p.name
ORDER BY total_votes DESC
LIMIT 10;
```

---

## Rollback Plan

If you need to remove the display_name feature:

```sql
-- Remove the display_name column
ALTER TABLE profiles 
DROP COLUMN display_name;
```

⚠️ **Warning:** This will permanently delete all display names. Make a backup first if needed:

```sql
-- Backup display names before dropping
CREATE TABLE profiles_display_name_backup AS
SELECT id, display_name, created_at
FROM profiles
WHERE display_name IS NOT NULL;
```

---

## Data Population (Optional)

### Option 1: Auto-populate from existing names
```sql
-- Set display_name to first name for existing users
UPDATE profiles
SET display_name = SPLIT_PART(name, ' ', 1)
WHERE display_name IS NULL 
  AND name IS NOT NULL;
```

### Option 2: Leave NULL (Recommended)
Leave display_name as NULL and let users choose their own names through the UI. The application will automatically fall back to their first name if not set.

---

## Monitoring Queries

### Check how many users have set a display name
```sql
SELECT 
  COUNT(*) FILTER (WHERE display_name IS NOT NULL) as users_with_display_name,
  COUNT(*) FILTER (WHERE display_name IS NULL) as users_without_display_name,
  COUNT(*) as total_users
FROM profiles;
```

### View all display names
```sql
SELECT 
  id,
  name,
  display_name,
  COALESCE(display_name, SPLIT_PART(name, ' ', 1), 'Anonymous') as effective_display_name
FROM profiles
ORDER BY created_at DESC;
```

### Find duplicate display names (not a problem, just informational)
```sql
SELECT 
  display_name,
  COUNT(*) as count
FROM profiles
WHERE display_name IS NOT NULL
GROUP BY display_name
HAVING COUNT(*) > 1
ORDER BY count DESC;
```

---

## Migration Checklist

- [ ] Review current `profiles` table schema
- [ ] Backup database (if production)
- [ ] Run ALTER TABLE command
- [ ] Verify column exists with query
- [ ] Test SELECT with display_name
- [ ] Test UPDATE display_name
- [ ] Verify RLS policies work correctly
- [ ] Test leaderboard query with new column
- [ ] Deploy backend code changes
- [ ] Monitor for any errors

---

## Supabase Dashboard Migration

If using Supabase Dashboard SQL Editor:

1. Go to **SQL Editor** in Supabase Dashboard
2. Click **New Query**
3. Paste the migration SQL:
   ```sql
   ALTER TABLE profiles 
   ADD COLUMN display_name TEXT;
   ```
4. Click **Run**
5. Verify in **Table Editor** → `profiles` table
6. Check that `display_name` column appears

---

## Expected Timeline

- **Migration execution:** < 1 second (non-blocking)
- **Zero downtime:** Column is nullable, doesn't break existing code
- **Backward compatible:** Existing API endpoints continue working

---

**Migration Date:** [To be filled when executed]  
**Executed By:** [To be filled]  
**Result:** [To be filled]
