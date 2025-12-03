-- Complete Supabase Triggers Setup for Bluetooth Sessions
-- Run this entire script in Supabase SQL Editor

-- ============================================================
-- STEP 1: Add 'tap' column to test_bt_devices (if not exists)
-- ============================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'test_bt_devices' AND column_name = 'tap'
    ) THEN
        ALTER TABLE test_bt_devices ADD COLUMN tap BOOLEAN DEFAULT false;
        COMMENT ON COLUMN test_bt_devices.tap IS 'Set to true when user taps NFC, consumed on session creation';
    END IF;
END $$;

-- ============================================================
-- TRIGGER 1: Auto-create session when device connects
-- ============================================================

CREATE OR REPLACE FUNCTION create_session_on_connect()
RETURNS TRIGGER AS $$
BEGIN
  -- If device status changed to 'connected' AND tap is true (user tapped NFC)
  IF NEW.status = 'connected' AND NEW.tap = true AND (OLD.status IS NULL OR OLD.status != 'connected' OR OLD.tap = false) THEN
    -- Create a new session
    INSERT INTO test_bt_sessions (
      device_mac,
      device_name,
      connected_at,
      status,
      user_id
    ) VALUES (
      NEW.device_mac,
      NEW.device_name,
      NOW(),
      'active',
      NEW.user_id
    );
    
    -- Consume the tap - set it back to false
    NEW.tap := false;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_create_session_on_connect ON test_bt_devices;
CREATE TRIGGER trigger_create_session_on_connect
  AFTER UPDATE ON test_bt_devices
  FOR EACH ROW
  EXECUTE FUNCTION create_session_on_connect();

-- ============================================================
-- TRIGGER 2: Auto-end session when device disconnects
-- ============================================================

CREATE OR REPLACE FUNCTION end_active_sessions_on_disconnect()
RETURNS TRIGGER AS $$
BEGIN
  -- If device status changed to 'disconnected' from 'connected'
  IF NEW.status = 'disconnected' AND OLD.status = 'connected' THEN
    -- Update all active sessions for this device
    UPDATE test_bt_sessions
    SET 
      disconnected_at = NOW(),
      status = 'ended'
    WHERE 
      device_mac = NEW.device_mac 
      AND status = 'active'
      AND disconnected_at IS NULL;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_end_sessions_on_disconnect ON test_bt_devices;
CREATE TRIGGER trigger_end_sessions_on_disconnect
  AFTER UPDATE ON test_bt_devices
  FOR EACH ROW
  EXECUTE FUNCTION end_active_sessions_on_disconnect();

-- ============================================================
-- TRIGGER 3: Auto-end session when entering grace period
-- ============================================================

CREATE OR REPLACE FUNCTION end_sessions_on_grace_period()
RETURNS TRIGGER AS $$
BEGIN
  -- If device entered grace_period from connected
  IF NEW.status = 'grace_period' AND OLD.status = 'connected' THEN
    -- End all active sessions for this device
    UPDATE test_bt_sessions
    SET 
      disconnected_at = NOW(),
      status = 'ended'
    WHERE 
      device_mac = NEW.device_mac 
      AND status = 'active'
      AND disconnected_at IS NULL;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_end_sessions_on_grace_period ON test_bt_devices;
CREATE TRIGGER trigger_end_sessions_on_grace_period
  AFTER UPDATE ON test_bt_devices
  FOR EACH ROW
  EXECUTE FUNCTION end_sessions_on_grace_period();

-- ============================================================
-- Verify all triggers were created
-- ============================================================

SELECT 
  trigger_name, 
  event_manipulation, 
  event_object_table,
  action_timing,
  action_statement
FROM information_schema.triggers
WHERE trigger_name LIKE 'trigger_%session%'
ORDER BY trigger_name;

-- ============================================================
-- Test the triggers (optional)
-- ============================================================

-- Test 1: Connect a device (should create a session)
-- UPDATE test_bt_devices 
-- SET status = 'connected', last_seen = NOW()
-- WHERE device_mac = 'AC:F2:3C:D9:97:4E';

-- Check if session was created:
-- SELECT * FROM test_bt_sessions WHERE device_mac = 'AC:F2:3C:D9:97:4E' ORDER BY connected_at DESC LIMIT 1;

-- Test 2: Disconnect the device (should end the session)
-- UPDATE test_bt_devices 
-- SET status = 'disconnected', last_seen = NOW()
-- WHERE device_mac = 'AC:F2:3C:D9:97:4E';

-- Check if session was ended:
-- SELECT * FROM test_bt_sessions WHERE device_mac = 'AC:F2:3C:D9:97:4E' ORDER BY connected_at DESC LIMIT 1;

-- ============================================================
-- SUCCESS! 
-- ============================================================
-- Your triggers are now active. Sessions will be automatically:
-- ✅ Created when device status changes to 'connected'
-- ✅ Ended when device status changes to 'disconnected'
-- ✅ Ended when device enters 'grace_period'
