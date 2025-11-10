-- Migration: Bluetooth Pairing and Session Tables
-- Purpose: Store permanent device pairings and temporary sessions for auto-reconnect

-- Permanent pairing registry
-- Stores all devices that have been paired with users
CREATE TABLE IF NOT EXISTS paired_devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  device_id TEXT NOT NULL, -- BLE device ID from browser
  device_name TEXT, -- Device name (e.g., "SoundGuys Beacon")
  paired_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Ensure one device per user
  UNIQUE(user_id, device_id)
);

-- Temporary session tracking with auto-reconnect window
-- Sessions expire after 30 minutes of disconnect
CREATE TABLE IF NOT EXISTS bluetooth_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  device_id TEXT NOT NULL,
  paired_device_id UUID REFERENCES paired_devices(id) ON DELETE CASCADE,

  -- Connection timestamps
  connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  disconnected_at TIMESTAMP WITH TIME ZONE,
  auto_reconnect_until TIMESTAMP WITH TIME ZONE, -- 30 min after disconnect

  -- Session status
  is_active BOOLEAN DEFAULT true,

  -- Only one active session per user
  CONSTRAINT one_active_session_per_user UNIQUE(user_id, is_active)
    WHERE is_active = true
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_paired_devices_user ON paired_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_paired_devices_device ON paired_devices(device_id);
CREATE INDEX IF NOT EXISTS idx_bluetooth_sessions_user ON bluetooth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_bluetooth_sessions_device ON bluetooth_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_bluetooth_sessions_active ON bluetooth_sessions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_bluetooth_sessions_reconnect ON bluetooth_sessions(auto_reconnect_until) WHERE auto_reconnect_until IS NOT NULL;

-- Enable Row Level Security
ALTER TABLE paired_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE bluetooth_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for paired_devices
CREATE POLICY "Users can view their own paired devices"
  ON paired_devices FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own paired devices"
  ON paired_devices FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own paired devices"
  ON paired_devices FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own paired devices"
  ON paired_devices FOR DELETE
  USING (auth.uid() = user_id);

-- RLS Policies for bluetooth_sessions
CREATE POLICY "Users can view their own bluetooth sessions"
  ON bluetooth_sessions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own bluetooth sessions"
  ON bluetooth_sessions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own bluetooth sessions"
  ON bluetooth_sessions FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own bluetooth sessions"
  ON bluetooth_sessions FOR DELETE
  USING (auth.uid() = user_id);
