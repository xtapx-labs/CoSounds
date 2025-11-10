# Database Migration: Bluetooth Devices Table

## Overview
Create `bluetooth_devices` table to track Bluetooth device pairing and reconnection state for the Arduino Nano 33 BLE voting system. Supports 30-minute auto-reconnect window.

---

## Migration SQL

```sql
-- Create bluetooth_devices table
CREATE TABLE bluetooth_devices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  device_id TEXT UNIQUE NOT NULL,
  device_name TEXT,
  paired_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'requires_reconnect')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_bt_devices_user ON bluetooth_devices(user_id);
CREATE INDEX idx_bt_devices_device_id ON bluetooth_devices(device_id);
CREATE INDEX idx_bt_devices_status ON bluetooth_devices(status);
CREATE INDEX idx_bt_devices_last_seen ON bluetooth_devices(last_seen);

-- Add comment
COMMENT ON TABLE bluetooth_devices IS 'Bluetooth device pairing registry for Arduino Nano 33 BLE buttons';

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_bluetooth_devices_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER bluetooth_devices_updated_at
BEFORE UPDATE ON bluetooth_devices
FOR EACH ROW
EXECUTE FUNCTION update_bluetooth_devices_updated_at();
```

---

## Update Vote Table (Optional)

Add device_id column to vote table to track which device submitted the vote:

```sql
-- Add device_id column to vote table
ALTER TABLE vote ADD COLUMN device_id TEXT;

-- Create index for device-based queries
CREATE INDEX idx_vote_device_id ON vote(device_id);

-- Add comment
COMMENT ON COLUMN vote.device_id IS 'Bluetooth device ID (for BLE votes) or NFC tag ID';
```

---

## RLS Policies

```sql
-- Enable RLS
ALTER TABLE bluetooth_devices ENABLE ROW LEVEL SECURITY;

-- Users can view their own devices
CREATE POLICY "Users can view own devices"
ON bluetooth_devices FOR SELECT
USING (auth.uid() = user_id);

-- Users can insert their own devices
CREATE POLICY "Users can create own devices"
ON bluetooth_devices FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Users can update their own devices
CREATE POLICY "Users can update own devices"
ON bluetooth_devices FOR UPDATE
USING (auth.uid() = user_id);

-- Users can delete their own devices
CREATE POLICY "Users can delete own devices"
ON bluetooth_devices FOR DELETE
USING (auth.uid() = user_id);

-- Service role can view all devices (for Bluetooth server)
CREATE POLICY "Service role can view all devices"
ON bluetooth_devices FOR SELECT
USING (auth.role() = 'service_role');

-- Service role can update all devices (for Bluetooth server)
CREATE POLICY "Service role can update all devices"
ON bluetooth_devices FOR UPDATE
USING (auth.role() = 'service_role');
```

---

## Verification Queries

### Check table exists
```sql
SELECT * FROM information_schema.tables
WHERE table_name = 'bluetooth_devices';
```

### Check columns
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'bluetooth_devices'
ORDER BY ordinal_position;
```

Expected columns:
```
id               | uuid                     | NO
user_id          | uuid                     | NO
device_id        | text                     | NO
device_name      | text                     | YES
paired_at        | timestamp with time zone | YES
last_seen        | timestamp with time zone | YES
status           | text                     | YES
created_at       | timestamp with time zone | YES
updated_at       | timestamp with time zone | YES
```

### Check indexes
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'bluetooth_devices';
```

---

## How It Works

### 🔵 **30-Minute Auto-Reconnect Window**

Devices automatically reconnect if last_seen was within 30 minutes:

```sql
-- Check if device can auto-reconnect (last seen < 30 min ago)
SELECT
  device_id,
  device_name,
  user_id,
  last_seen,
  (NOW() - last_seen) < INTERVAL '30 minutes' as can_auto_reconnect,
  EXTRACT(EPOCH FROM (NOW() - last_seen)) / 60 as minutes_since_last_seen
FROM bluetooth_devices
WHERE device_id = 'your-device-id-here';
```

### Device States

1. **active** - Device is connected and working
2. **inactive** - Device was explicitly disconnected/unpaired
3. **requires_reconnect** - Device hasn't been seen for 30+ minutes, needs manual tap

### Timeline Example:
```
2:00 PM - User pairs Arduino Nano 33 BLE
          → paired_at = 2:00 PM
          → last_seen = 2:00 PM
          → status = 'active'

2:15 PM - User walks out of range
          → Device disconnects (no database update yet)

2:40 PM - User comes back within range (25 min)
          → Auto-reconnects (within 30-min window)
          → last_seen = 2:40 PM

3:15 PM - User leaves library again

3:50 PM - User returns (35 minutes later, beyond 30-min window)
          → Shows "Tap to reconnect" button
          → After tap: last_seen = 3:50 PM, status = 'active'
```

---

## Test Data

### Insert test device
```sql
INSERT INTO bluetooth_devices (user_id, device_id, device_name, status)
VALUES (
  'your-user-id-here',
  'arduino_nano_33_test_001',
  'Arduino Nano 33 BLE',
  'active'
);
```

### Check active devices
```sql
SELECT
  bd.id,
  bd.device_id,
  bd.device_name,
  p.name as user_name,
  bd.paired_at,
  bd.last_seen,
  bd.status,
  (NOW() - bd.last_seen) < INTERVAL '30 minutes' as can_auto_reconnect,
  ROUND(EXTRACT(EPOCH FROM (NOW() - bd.last_seen)) / 60) as minutes_inactive
FROM bluetooth_devices bd
LEFT JOIN profiles p ON p.id = bd.user_id
WHERE bd.status = 'active'
ORDER BY bd.last_seen DESC;
```

### Find devices that need reconnection
```sql
SELECT
  device_id,
  device_name,
  last_seen,
  (NOW() - last_seen) as time_inactive
FROM bluetooth_devices
WHERE status = 'active'
  AND (NOW() - last_seen) > INTERVAL '30 minutes';
```

---

## Cleanup (Optional)

Delete unpaired devices older than 30 days:

```sql
DELETE FROM bluetooth_devices
WHERE status = 'inactive'
  AND updated_at < NOW() - INTERVAL '30 days';
```

Or create a function:

```sql
CREATE OR REPLACE FUNCTION cleanup_old_bluetooth_devices()
RETURNS void AS $$
BEGIN
  DELETE FROM bluetooth_devices
  WHERE status = 'inactive'
    AND updated_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Run manually when needed
SELECT cleanup_old_bluetooth_devices();
```

---

## Rollback

If you need to remove the bluetooth_devices table:

```sql
-- Backup first (optional)
CREATE TABLE bluetooth_devices_backup AS SELECT * FROM bluetooth_devices;

-- Drop trigger first
DROP TRIGGER IF EXISTS bluetooth_devices_updated_at ON bluetooth_devices;
DROP FUNCTION IF EXISTS update_bluetooth_devices_updated_at();

-- Drop table
DROP TABLE IF EXISTS bluetooth_devices CASCADE;

-- Rollback vote table change (optional)
ALTER TABLE vote DROP COLUMN IF EXISTS device_id;
```

---

## Performance Notes

### Indexes Explained

1. **`idx_bt_devices_user`** - Fast lookup of user's devices
2. **`idx_bt_devices_device_id`** - Fast device ID lookups (for pairing checks)
3. **`idx_bt_devices_status`** - Fast filtering by device status
4. **`idx_bt_devices_last_seen`** - Fast time-based queries for reconnection logic

### Expected Performance

- Insert (pairing): < 10ms
- Query device status: < 5ms
- Update last_seen: < 10ms
- Check reconnection eligibility: < 5ms

---

## Monitoring Queries

### Count devices by status
```sql
SELECT
  status,
  COUNT(*) as device_count,
  COUNT(DISTINCT user_id) as unique_users
FROM bluetooth_devices
GROUP BY status
ORDER BY device_count DESC;
```

### See active devices and their activity
```sql
SELECT
  bd.device_name,
  p.name as user_name,
  bd.last_seen,
  ROUND(EXTRACT(EPOCH FROM (NOW() - bd.last_seen)) / 60) as minutes_inactive,
  CASE
    WHEN (NOW() - bd.last_seen) < INTERVAL '5 minutes' THEN '🟢 Active'
    WHEN (NOW() - bd.last_seen) < INTERVAL '30 minutes' THEN '🟡 Can Auto-Reconnect'
    ELSE '🔴 Needs Manual Reconnect'
  END as connection_status
FROM bluetooth_devices bd
JOIN profiles p ON p.id = bd.user_id
WHERE bd.status = 'active'
ORDER BY bd.last_seen DESC;
```

### Votes by device type
```sql
SELECT
  CASE
    WHEN device_id LIKE 'arduino%' THEN 'Bluetooth (Arduino)'
    WHEN device_id LIKE '%nfc%' THEN 'NFC Tag'
    WHEN device_id IS NULL THEN 'Manual Button'
    ELSE 'Other'
  END as vote_method,
  COUNT(*) as vote_count,
  COUNT(DISTINCT user_id) as unique_users
FROM vote
GROUP BY vote_method
ORDER BY vote_count DESC;
```

---

## Integration with Bluetooth Server

The Bluetooth server (server-bt) should update this table:

### On device pairing
```sql
INSERT INTO bluetooth_devices (user_id, device_id, device_name, status)
VALUES ($1, $2, $3, 'active')
ON CONFLICT (device_id)
DO UPDATE SET
  user_id = EXCLUDED.user_id,
  device_name = EXCLUDED.device_name,
  paired_at = NOW(),
  last_seen = NOW(),
  status = 'active';
```

### On device activity (button press, connection)
```sql
UPDATE bluetooth_devices
SET last_seen = NOW(), status = 'active'
WHERE device_id = $1;
```

### On explicit unpair
```sql
UPDATE bluetooth_devices
SET status = 'inactive'
WHERE device_id = $1;
```

---

## Migration Checklist

- [ ] Review schema
- [ ] Backup database (if production)
- [ ] Run CREATE TABLE command
- [ ] Create indexes
- [ ] Set up RLS policies
- [ ] Create trigger for updated_at
- [ ] (Optional) Add device_id to vote table
- [ ] Verify with test queries
- [ ] Insert test device
- [ ] Query active devices
- [ ] Test reconnection logic (manually set last_seen to 35 min ago)
- [ ] Update Bluetooth server to use this table
- [ ] Test pairing flow end-to-end
- [ ] Test 30-minute reconnection window
- [ ] Test button press → vote submission

---

**Migration Date:** [To be filled]
**Executed By:** [To be filled]
**Result:** [To be filled]
