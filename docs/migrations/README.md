# Database Migrations

This directory contains SQL migrations for the Sound Guys project.

## Running Migrations

### Option 1: Supabase Dashboard (Easiest)

1. Go to your Supabase project dashboard: https://app.supabase.com/project/bjieozmcptbxgbvzpfyc
2. Click "SQL Editor" in the left sidebar
3. Click "New query"
4. Copy the contents of the migration file (e.g., `001_bluetooth_pairing_tables.sql`)
5. Paste into the SQL editor
6. Click "Run" to execute

### Option 2: Supabase CLI

```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref bjieozmcptbxgbvzpfyc

# Run migration
supabase db push
```

## Migrations

### 001_bluetooth_pairing_tables.sql

Creates two tables for Bluetooth device pairing and session management:

**Tables created:**
- `paired_devices` - Permanent storage of paired Bluetooth devices
- `bluetooth_sessions` - Temporary sessions with 30-minute auto-reconnect window

**How it works:**
1. When user first pairs device → Creates entry in `paired_devices` (permanent)
2. Creates `bluetooth_sessions` entry with `auto_reconnect_until` = now + 30 minutes
3. If device disconnects/reconnects within 30 minutes → Auto-reconnects without pairing dialog
4. After 30 minutes → User must manually reconnect (device still in `paired_devices`)

**Key features:**
- One active session per user (enforced by unique constraint)
- Auto-reconnect window expires 30 minutes after connection
- Row-Level Security (RLS) enabled - users can only see their own data
- Indexes for fast lookups

## Verifying Migration

After running the migration, verify tables were created:

```sql
-- Check paired_devices table exists
SELECT * FROM paired_devices LIMIT 1;

-- Check bluetooth_sessions table exists
SELECT * FROM bluetooth_sessions LIMIT 1;

-- Verify RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('paired_devices', 'bluetooth_sessions');
```

Expected output: Both tables should show `rowsecurity = true`
