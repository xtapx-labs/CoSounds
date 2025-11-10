# Database Migration: Sessions Table (1-Hour Auto-Expire)

## Overview
Create `sessions` table to track user check-ins with automatic 1-hour expiration. No cron job needed - sessions auto-expire based on timestamp comparison.

---

## Migration SQL

```sql
-- Create sessions table
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  checked_in_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_active ON sessions(status, expires_at);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- Add comment
COMMENT ON TABLE sessions IS '1-hour auto-expiring sessions for active user tracking';
```

---

## RLS Policies

```sql
-- Enable RLS
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Users can view their own sessions
CREATE POLICY "Users can view own sessions"
ON sessions FOR SELECT
USING (auth.uid() = user_id);

-- Users can insert their own sessions
CREATE POLICY "Users can create own sessions"
ON sessions FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Users can update their own sessions
CREATE POLICY "Users can update own sessions"
ON sessions FOR UPDATE
USING (auth.uid() = user_id);

-- Service role can view all sessions (for model API)
CREATE POLICY "Service role can view all sessions"
ON sessions FOR SELECT
USING (auth.role() = 'service_role');
```

---

## Verification Queries

### Check table exists
```sql
SELECT * FROM information_schema.tables 
WHERE table_name = 'sessions';
```

### Check columns
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'sessions'
ORDER BY ordinal_position;
```

Expected columns:
```
id               | uuid                     | NO
user_id          | uuid                     | NO
checked_in_at    | timestamp with time zone | YES
expires_at       | timestamp with time zone | NO
status           | text                     | YES
created_at       | timestamp with time zone | YES
```

### Check indexes
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'sessions';
```

---

## How It Works

### ✅ **No Cron Job Needed**

Sessions automatically expire through query filtering:

```sql
-- Get active users (only non-expired sessions)
SELECT * FROM sessions
WHERE status = 'active'
  AND expires_at > NOW();
```

### Timeline Example:
```
2:00 PM - User checks in
          → checked_in_at = 2:00 PM
          → expires_at = 3:00 PM
          → status = 'active'

2:30 PM - Model queries active users
          → Query: WHERE expires_at > NOW()
          → User IS included (3:00 PM > 2:30 PM ✓)

3:05 PM - Model queries active users
          → Query: WHERE expires_at > NOW()
          → User NOT included (3:00 PM < 3:05 PM ✗)
```

**The session is automatically "inactive" without any manual update!**

---

## Test Data

### Insert test session
```sql
INSERT INTO sessions (user_id, checked_in_at, expires_at, status)
VALUES (
  'your-user-id-here',
  NOW(),
  NOW() + INTERVAL '1 hour',
  'active'
);
```

### Check active sessions
```sql
SELECT 
  s.id,
  s.user_id,
  p.name,
  s.checked_in_at,
  s.expires_at,
  s.status,
  (s.expires_at > NOW()) as is_active,
  EXTRACT(EPOCH FROM (s.expires_at - NOW())) / 60 as minutes_remaining
FROM sessions s
LEFT JOIN profiles p ON p.id = s.user_id
WHERE s.status = 'active'
ORDER BY s.checked_in_at DESC;
```

---

## Cleanup (Optional)

Delete sessions older than 7 days (run periodically or don't - doesn't affect functionality):

```sql
DELETE FROM sessions
WHERE created_at < NOW() - INTERVAL '7 days';
```

Or create a function:

```sql
CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS void AS $$
BEGIN
  DELETE FROM sessions
  WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Run manually when needed
SELECT cleanup_old_sessions();
```

---

## Rollback

If you need to remove the sessions table:

```sql
-- Backup first (optional)
CREATE TABLE sessions_backup AS SELECT * FROM sessions;

-- Drop table
DROP TABLE IF EXISTS sessions CASCADE;
```

---

## Performance Notes

### Indexes Explained

1. **`idx_sessions_user`** - Fast lookup of user's sessions
2. **`idx_sessions_active`** - Fast filtering by status + expiration
3. **`idx_sessions_expires`** - Fast time-based queries

### Expected Performance

- Insert: < 10ms
- Query active users: < 50ms (even with 1000+ sessions)
- Update status: < 10ms

---

## Monitoring Queries

### Count active vs expired sessions
```sql
SELECT 
  COUNT(*) FILTER (WHERE status = 'active' AND expires_at > NOW()) as active_sessions,
  COUNT(*) FILTER (WHERE status = 'active' AND expires_at <= NOW()) as expired_but_marked_active,
  COUNT(*) FILTER (WHERE status = 'inactive') as manually_checked_out,
  COUNT(*) as total
FROM sessions;
```

### See who's currently active
```sql
SELECT 
  p.name,
  p.display_name,
  s.checked_in_at,
  s.expires_at,
  ROUND(EXTRACT(EPOCH FROM (s.expires_at - NOW())) / 60) as mins_remaining
FROM sessions s
JOIN profiles p ON p.id = s.user_id
WHERE s.status = 'active'
  AND s.expires_at > NOW()
ORDER BY s.checked_in_at DESC;
```

### Average session duration
```sql
SELECT 
  AVG(EXTRACT(EPOCH FROM (expires_at - checked_in_at)) / 60) as avg_duration_minutes,
  COUNT(*) as total_sessions
FROM sessions
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

## Migration Checklist

- [ ] Review schema
- [ ] Backup database (if production)
- [ ] Run CREATE TABLE command
- [ ] Create indexes
- [ ] Set up RLS policies
- [ ] Verify with test queries
- [ ] Insert test session
- [ ] Query active sessions
- [ ] Test expiration (wait 1 hour or manually set expires_at in past)
- [ ] Deploy backend code
- [ ] Test API endpoints

---

**Migration Date:** [To be filled]  
**Executed By:** [To be filled]  
**Result:** [To be filled]
