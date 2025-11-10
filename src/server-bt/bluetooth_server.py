"""
Sound Guys - Python Bluetooth Server with Supabase Integration
Manages user sessions based on physical presence (Bluetooth connection)
"""

import asyncio
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from bleak import BleakScanner, BleakClient
from supabase import create_client, Client
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv('PORT', 3001))
RECONNECT_TIMEOUT = int(os.getenv('RECONNECT_TIMEOUT', 1800))  # 30 minutes in seconds
BLE_SERVICE_UUID = os.getenv('BLE_SERVICE_UUID', '19b10000-e8f2-537e-4f6c-d104768a1214')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Initialize Supabase client (service role for admin access)
supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("[OK] Supabase client initialized")
else:
    print("[WARN] Warning: Supabase credentials not configured")

# Flask app
app = Flask(__name__)
CORS(app)

# Pairing registry: deviceId -> {userId, userName, authToken, lastSeen, requiresTap, pairedAt}
pairing_registry = {}

# Discovered devices: address -> device object
discovered_devices = {}

# Connected devices: address -> client object
connected_devices = {}

# Scanning state
is_scanning = False


class BluetoothService:
    """Handles BLE device discovery, connection, and session management"""

    def __init__(self):
        self.loop = None
        self.running = False

    async def scan_devices(self):
        """Continuously scan for BLE devices"""
        global is_scanning, discovered_devices

        print("[SCAN] Starting BLE scan...")
        is_scanning = True

        while self.running:
            try:
                devices = await BleakScanner.discover(timeout=5.0)

                for device in devices:
                    device_id = device.address
                    device_name = device.name or "Unknown Device"

                    # Store discovered device
                    discovered_devices[device_id] = {
                        "address": device.address,
                        "name": device_name,
                        "rssi": device.rssi if hasattr(device, 'rssi') else None,
                        "device": device
                    }

                    # Check if paired and should auto-reconnect
                    if device_id in pairing_registry:
                        update_last_seen(device_id)

                        if can_auto_reconnect(device_id) and device_id not in connected_devices:
                            print(f"[RETRY] Auto-reconnecting to {device_name} ({device_id})")
                            asyncio.create_task(self.connect_device(device_id))

            except Exception as e:
                print(f"[ERROR] Scan error: {e}")

            await asyncio.sleep(2)  # Scan every 2 seconds

        is_scanning = False

    async def connect_device(self, device_id: str):
        """Connect to a BLE device and create Supabase session"""
        global connected_devices

        if device_id not in discovered_devices:
            print(f"[ERROR] Device {device_id} not discovered")
            return False

        if device_id in connected_devices:
            print(f"[WARN] Device {device_id} already connected")
            return True

        device_info = discovered_devices[device_id]
        device = device_info["device"]

        try:
            print(f"[CONN] Connecting to {device_info['name']}...")

            client = BleakClient(device.address)
            await client.connect()

            if client.is_connected:
                print(f"[OK] Connected to {device_id}")
                connected_devices[device_id] = {
                    "client": client,
                    "connectedAt": time.time()
                }

                # Create/activate session in Supabase
                if device_id in pairing_registry:
                    user_id = pairing_registry[device_id]["userId"]
                    auth_token = pairing_registry[device_id].get("authToken")
                    await self.create_session_in_supabase(user_id, auth_token)

                # Set up disconnect callback
                def disconnection_callback(client):
                    print(f"[DISC] Device {device_id} disconnected")
                    if device_id in connected_devices:
                        del connected_devices[device_id]

                    # End session in Supabase
                    if device_id in pairing_registry:
                        user_id = pairing_registry[device_id]["userId"]
                        auth_token = pairing_registry[device_id].get("authToken")
                        asyncio.create_task(self.end_session_in_supabase(user_id, auth_token))

                client.set_disconnected_callback(disconnection_callback)

                return True
            else:
                print(f"[ERROR] Failed to connect to {device_id}")
                return False

        except Exception as e:
            print(f"[ERROR] Connection error for {device_id}: {e}")
            return False

    async def disconnect_device(self, device_id: str):
        """Disconnect from a BLE device and end Supabase session"""
        if device_id not in connected_devices:
            return False

        try:
            client = connected_devices[device_id]["client"]
            await client.disconnect()
            del connected_devices[device_id]

            # End session in Supabase
            if device_id in pairing_registry:
                user_id = pairing_registry[device_id]["userId"]
                auth_token = pairing_registry[device_id].get("authToken")
                await self.end_session_in_supabase(user_id, auth_token)

            print(f"[DISC] Disconnected from {device_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Disconnect error: {e}")
            return False

    async def create_session_in_supabase(self, user_id: str, auth_token: str = None):
        """Create or reactivate user session in Supabase (check-in)"""
        if not supabase:
            print("[WARN] Supabase not configured, skipping session creation")
            return

        try:
            # Calculate expiration (60 minutes from now)
            expires_at = (datetime.utcnow() + timedelta(minutes=60)).isoformat()

            # Check if user has an active session
            existing = supabase.table('sessions').select('*').eq('user_id', user_id).eq('status', 'active').execute()

            if existing.data:
                # Update existing session
                result = supabase.table('sessions').update({
                    'checked_in_at': datetime.utcnow().isoformat(),
                    'expires_at': expires_at,
                    'status': 'active'
                }).eq('user_id', user_id).execute()

                print(f"[OK] Session updated for user {user_id} (expires: {expires_at})")
            else:
                # Create new session
                result = supabase.table('sessions').insert({
                    'user_id': user_id,
                    'checked_in_at': datetime.utcnow().isoformat(),
                    'expires_at': expires_at,
                    'status': 'active'
                }).execute()

                print(f"[OK] Session created for user {user_id} (expires: {expires_at})")

        except Exception as e:
            print(f"[ERROR] Error creating session in Supabase: {e}")

    async def end_session_in_supabase(self, user_id: str, auth_token: str = None):
        """End user session in Supabase (check-out)"""
        if not supabase:
            print("[WARN] Supabase not configured, skipping session end")
            return

        try:
            # Mark all active sessions as inactive
            result = supabase.table('sessions').update({
                'status': 'inactive'
            }).eq('user_id', user_id).eq('status', 'active').execute()

            print(f"[OK] Session ended for user {user_id}")

        except Exception as e:
            print(f"[ERROR] Error ending session in Supabase: {e}")

    def start(self):
        """Start the Bluetooth service"""
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        print("[BT] Bluetooth Service starting...")
        self.loop.run_until_complete(self.scan_devices())


# Pairing registry functions
def update_last_seen(device_id: str):
    """Update last seen timestamp for a device"""
    if device_id in pairing_registry:
        pairing_registry[device_id]["lastSeen"] = time.time()
        pairing_registry[device_id]["requiresTap"] = False


def can_auto_reconnect(device_id: str) -> bool:
    """Check if device can auto-reconnect (within 30-minute window)"""
    if device_id not in pairing_registry:
        return False

    session = pairing_registry[device_id]
    if not session.get("paired"):
        return False

    time_since_last_seen = time.time() - session["lastSeen"]
    return time_since_last_seen < RECONNECT_TIMEOUT


def cleanup_stale_devices():
    """Mark devices that need manual reconnect"""
    while True:
        time.sleep(60)  # Check every minute

        now = time.time()
        for device_id, session in pairing_registry.items():
            time_since_last_seen = now - session["lastSeen"]

            if time_since_last_seen > RECONNECT_TIMEOUT and not session.get("requiresTap"):
                session["requiresTap"] = True
                print(f"[TIMEOUT] Device {device_id} now requires manual tap ({int(time_since_last_seen / 60)} min inactive)")


# Flask HTTP Endpoints

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "service": "bluetooth-server",
        "version": "2.0.0-python",
        "supabase": "connected" if supabase else "not configured"
    })


@app.route('/pair', methods=['POST'])
def pair_device():
    """Pair a BLE device with a user"""
    data = request.get_json()
    device_id = data.get('deviceId')
    user_id = data.get('userId')
    user_name = data.get('userName')
    auth_token = data.get('authToken')  # User's JWT token

    if not device_id or not user_id:
        return jsonify({"error": "deviceId and userId required"}), 400

    print(f"[OK] Pairing device {device_id} with user {user_id}")

    pairing_registry[device_id] = {
        "paired": True,
        "userId": user_id,
        "userName": user_name,
        "authToken": auth_token,
        "lastSeen": time.time(),
        "requiresTap": False,
        "pairedAt": time.time()
    }

    # Attempt to connect if device is discovered
    if device_id in discovered_devices:
        asyncio.run_coroutine_threadsafe(
            bt_service.connect_device(device_id),
            bt_service.loop
        )

    return jsonify({
        "success": True,
        "message": "Device paired successfully",
        "deviceId": device_id,
        "userId": user_id
    })


@app.route('/reconnect', methods=['POST'])
def reconnect_device():
    """Manually reconnect device after 30-minute timeout"""
    data = request.get_json()
    device_id = data.get('deviceId')

    if not device_id:
        return jsonify({"error": "deviceId required"}), 400

    if device_id not in pairing_registry:
        return jsonify({"error": "Device not paired"}), 400

    session = pairing_registry[device_id]
    session["lastSeen"] = time.time()
    session["requiresTap"] = False

    # Attempt to reconnect
    asyncio.run_coroutine_threadsafe(
        bt_service.connect_device(device_id),
        bt_service.loop
    )

    return jsonify({
        "success": True,
        "message": "Device reconnected",
        "deviceId": device_id,
        "userId": session["userId"]
    })


@app.route('/unpair', methods=['POST'])
def unpair_device():
    """Unpair a device"""
    data = request.get_json()
    device_id = data.get('deviceId')

    if not device_id:
        return jsonify({"error": "deviceId required"}), 400

    # Disconnect if connected (this will end session in Supabase)
    if device_id in connected_devices:
        asyncio.run_coroutine_threadsafe(
            bt_service.disconnect_device(device_id),
            bt_service.loop
        )

    # Remove from registry
    if device_id in pairing_registry:
        del pairing_registry[device_id]

    return jsonify({
        "success": True,
        "message": "Device unpaired"
    })


@app.route('/devices', methods=['GET'])
def get_devices():
    """Get discovered and connected devices"""
    devices = []
    for device_id, info in discovered_devices.items():
        devices.append({
            "id": device_id,
            "name": info["name"],
            "rssi": info.get("rssi"),
            "isPaired": device_id in pairing_registry,
            "isConnected": device_id in connected_devices
        })

    return jsonify({"discovered": devices})


@app.route('/status', methods=['GET'])
def get_status():
    """Get Bluetooth service status"""
    total_paired = len(pairing_registry)
    requires_tap = sum(1 for s in pairing_registry.values() if s.get("requiresTap"))
    active_recent = sum(1 for s in pairing_registry.values() if time.time() - s["lastSeen"] < 5 * 60)

    return jsonify({
        "bluetooth": {
            "scanning": is_scanning,
            "discoveredCount": len(discovered_devices),
            "connectedCount": len(connected_devices)
        },
        "pairing": {
            "totalPaired": total_paired,
            "requiresTap": requires_tap,
            "activeRecent": active_recent
        },
        "supabase": {
            "connected": supabase is not None
        }
    })


# Initialize Bluetooth service
bt_service = BluetoothService()


if __name__ == '__main__':
    print("=================================")
    print("Sound Guys - Bluetooth Server")
    print("Python + Bleak + Supabase")
    print("=================================\n")

    # Start Bluetooth service in a separate thread
    bt_thread = threading.Thread(target=bt_service.start, daemon=True)
    bt_thread.start()

    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_stale_devices, daemon=True)
    cleanup_thread.start()

    # Give BLE service time to initialize
    time.sleep(2)

    # Start Flask HTTP server
    print("\n[OK] Starting HTTP server on port", PORT)
    print("[API] Endpoints: /pair, /reconnect, /unpair, /devices, /status")
    print("[DB] Supabase integration: Session management based on Bluetooth connection\n")

    app.run(host='0.0.0.0', port=PORT, debug=False)
