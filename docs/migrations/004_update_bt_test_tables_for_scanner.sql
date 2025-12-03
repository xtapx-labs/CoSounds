-- Migration: Update test tables for scanner-based detection
-- Run this in Supabase SQL Editor
-- Date: 2025-12-02

-- ==================================================
-- Update test_bt_devices schema for scanner-based detection
-- ==================================================

-- 1. Drop beacon_name column (no longer needed)
ALTER TABLE test_bt_devices
  DROP COLUMN IF EXISTS beacon_name;

-- 2. Add device_mac column (laptop's Bluetooth MAC address)
ALTER TABLE test_bt_devices
  ADD COLUMN IF NOT EXISTS device_mac TEXT;

-- 3. Add device_name column (optional device name)
ALTER TABLE test_bt_devices
  ADD COLUMN IF NOT EXISTS device_name TEXT;

-- 4. Add rssi column (signal strength from scanner)
ALTER TABLE test_bt_devices
  ADD COLUMN IF NOT EXISTS rssi INTEGER;

-- 5. Rename last_detected to last_seen for clarity
ALTER TABLE test_bt_devices
  RENAME COLUMN last_detected TO last_seen;

-- 6. Add unique constraint on device_mac (one user per MAC)
CREATE UNIQUE INDEX IF NOT EXISTS idx_test_bt_devices_mac
  ON test_bt_devices(device_mac)
  WHERE device_mac IS NOT NULL;

-- 7. Add index on last_seen for performance (grace period queries)
CREATE INDEX IF NOT EXISTS idx_test_bt_devices_last_seen
  ON test_bt_devices(last_seen DESC);

-- 8. Add index on status and grace_period_ends_at (grace period cleanup)
CREATE INDEX IF NOT EXISTS idx_test_bt_devices_grace_status
  ON test_bt_devices(status, grace_period_ends_at)
  WHERE status = 'grace_period';

-- ==================================================
-- Update test_bt_sessions schema
-- ==================================================

-- 1. Add device_mac column to sessions (for tracking which device was used)
ALTER TABLE test_bt_sessions
  ADD COLUMN IF NOT EXISTS device_mac TEXT;

-- 2. Add device_name column (optional, for display)
ALTER TABLE test_bt_sessions
  ADD COLUMN IF NOT EXISTS device_name TEXT;

-- ==================================================
-- Verify schema
-- ==================================================

-- Check test_bt_devices columns
-- Expected columns: id, user_id, device_mac, device_name, last_seen, status,
--                   grace_period_ends_at, rssi, created_at, updated_at

-- Check test_bt_sessions columns
-- Expected columns: id, user_id, device_mac, device_name, connected_at,
--                   disconnected_at, status, created_at

-- ==================================================
-- Notes
-- ==================================================

-- This migration updates the test tables from beacon-based to scanner-based detection:
--
-- BEFORE (Beacon-Based):
-- - beacon_name: Name of the beacon device (fixed: "SoundGuys Beacon")
-- - Web Bluetooth API scans for beacon
--
-- AFTER (Scanner-Based):
-- - device_mac: User's laptop Bluetooth MAC address
-- - device_name: User's laptop name (e.g., "Pranav's MacBook Pro")
-- - rssi: Signal strength from Pi scanner
-- - Raspberry Pi scans for user devices
--
-- The migration is designed to be idempotent (safe to run multiple times).
