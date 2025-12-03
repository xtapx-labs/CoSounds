-- Bluetooth Presence Detection Test Tables
-- Run this script in Supabase SQL Editor

-- 1. Create test_bt_devices table
CREATE TABLE test_bt_devices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  beacon_name TEXT DEFAULT 'SoundGuys Beacon',
  last_detected TIMESTAMPTZ,
  status TEXT DEFAULT 'disconnected' CHECK (status IN ('connected', 'grace_period', 'disconnected')),
  grace_period_ends_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);

CREATE INDEX idx_test_bt_devices_user ON test_bt_devices(user_id);
CREATE INDEX idx_test_bt_devices_status ON test_bt_devices(status);
CREATE INDEX idx_test_bt_devices_grace_period ON test_bt_devices(grace_period_ends_at);

-- 2. Create test_bt_sessions table
CREATE TABLE test_bt_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  beacon_name TEXT,
  connected_at TIMESTAMPTZ DEFAULT NOW(),
  disconnected_at TIMESTAMPTZ,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'ended')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_test_bt_sessions_user ON test_bt_sessions(user_id);
CREATE INDEX idx_test_bt_sessions_status ON test_bt_sessions(status);

-- 3. Enable Row Level Security
ALTER TABLE test_bt_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_bt_sessions ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS Policies (service role can manage everything)
CREATE POLICY "Service role can manage devices"
  ON test_bt_devices FOR ALL
  USING (true);

CREATE POLICY "Service role can manage sessions"
  ON test_bt_sessions FOR ALL
  USING (true);

-- Optional: Allow users to view their own data
CREATE POLICY "Users can view own devices"
  ON test_bt_devices FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view own sessions"
  ON test_bt_sessions FOR SELECT
  USING (auth.uid() = user_id);
