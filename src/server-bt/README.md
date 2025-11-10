# Sound Guys - Python Bluetooth Server

**Windows-compatible BLE server** using Python + Bleak library.

Handles Arduino Nano 33 BLE presence beacon pairing and connection tracking.

---

## Why Python?

- ✅ **Works on Windows** (no complex native dependencies)
- ✅ **Bleak library** - Modern, well-maintained BLE support
- ✅ **Easy to install** - Just `pip install`
- ✅ **Cross-platform** - Works on Windows, macOS, Linux

---

## Quick Start

### 1. Install Python

Make sure you have Python 3.8+ installed:
```bash
python --version
```

Download from: https://www.python.org/downloads/

### 2. Install Dependencies

```bash
cd src/server-bt
pip install -r requirements.txt
```

This installs:
- `bleak` - BLE library
- `flask` - HTTP server
- `flask-cors` - CORS support

### 3. Run Server

```bash
python bluetooth_server.py
```

**Expected output:**
```
=================================
Sound Guys - Bluetooth Server
Python + Bleak (Windows Compatible)
=================================

🔵 Bluetooth Service starting...
🔍 Starting BLE scan...

✅ Starting HTTP server on port 3001...
📡 Endpoints: /pair, /reconnect, /unpair, /devices, /status
```

---

## API Endpoints

**Base URL:** `http://localhost:3001`

### POST /pair
Pair a BLE device with a user.

**Request:**
```json
{
  "deviceId": "XX:XX:XX:XX:XX:XX",
  "userId": "user-uuid",
  "userName": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device paired successfully",
  "deviceId": "XX:XX:XX:XX:XX:XX",
  "userId": "user-uuid"
}
```

---

### POST /reconnect
Manually reconnect device after 30-minute timeout.

**Request:**
```json
{
  "deviceId": "XX:XX:XX:XX:XX:XX"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device reconnected",
  "deviceId": "XX:XX:XX:XX:XX:XX",
  "userId": "user-uuid"
}
```

---

### POST /unpair
Unpair a device.

**Request:**
```json
{
  "deviceId": "XX:XX:XX:XX:XX:XX"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device unpaired"
}
```

---

### GET /devices
Get discovered and connected devices.

**Response:**
```json
{
  "discovered": [
    {
      "id": "XX:XX:XX:XX:XX:XX",
      "name": "SoundGuys Beacon",
      "rssi": -45,
      "isPaired": true,
      "isConnected": true
    }
  ]
}
```

---

### GET /status
Get Bluetooth service status.

**Response:**
```json
{
  "bluetooth": {
    "scanning": true,
    "discoveredCount": 3,
    "connectedCount": 1
  },
  "pairing": {
    "totalPaired": 5,
    "requiresTap": 2,
    "activeRecent": 3
  }
}
```

---

### GET /health
Health check.

**Response:**
```json
{
  "status": "ok",
  "service": "bluetooth-server",
  "version": "2.0.0-python"
}
```

---

## How It Works

### 1. **BLE Scanning**
- Continuously scans for BLE devices every 2 seconds
- Discovers Arduino Nano 33 BLE beacons
- Stores discovered devices in memory

### 2. **Pairing**
- Frontend calls `POST /pair` with device ID and user ID
- Server stores pairing in registry
- Auto-connects to device if discovered

### 3. **Auto-Reconnection**
- Tracks `lastSeen` timestamp for each device
- Within 30 minutes: Auto-reconnects when device comes back in range
- After 30 minutes: Marks `requiresTap: true`, user must tap "Reconnect" button

### 4. **Cleanup**
- Background thread checks for stale devices every minute
- Marks inactive devices (30+ min) as requiring manual reconnect

---

## Frontend Integration

Update `BluetoothConnector.jsx` to use port 3001:

```javascript
const BT_SERVER_URL = 'http://localhost:3001';

// Pairing
const pairResult = await fetch(`${BT_SERVER_URL}/pair`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ deviceId, userId, userName })
});
```

---

## Troubleshooting

### Bluetooth not working

**Windows:**
- Make sure Bluetooth is enabled
- Run Python as Administrator (first time only)
- Check Windows Bluetooth settings

**Check Bluetooth adapter:**
```python
python
>>> import bleak
>>> import asyncio
>>> asyncio.run(bleak.BleakScanner.discover())
```

This should list nearby BLE devices.

### Arduino not discovered

- Check Arduino Serial Monitor shows "BLE beacon active"
- Verify Arduino is powered on (USB connected)
- Reset Arduino (press button twice quickly)
- Restart Python server

### Port 3001 already in use

```bash
# Windows
netstat -ano | findstr :3001

# Kill process
taskkill /PID <PID> /F
```

---

## File Structure

```
server-bt/
├── bluetooth_server.py    # Main Python server
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

---

## Advantages Over Node.js noble

| Feature | noble (Node.js) | Bleak (Python) |
|---------|----------------|----------------|
| Windows Support | ❌ Complex setup | ✅ Works natively |
| Dependencies | Native modules | Pure Python |
| Maintenance | Abandoned | Active |
| Error Messages | Cryptic | Clear |
| Installation | Fails often | Simple pip install |

---

## Development

### Run with auto-reload

```bash
pip install watchdog
python -m flask --app bluetooth_server run --reload --port 3001
```

### Logs

Server prints to console:
- `🔵` Bluetooth status
- `🔗` Connection events
- `✅` Success messages
- `❌` Errors

---

## Deployment

### Production

```bash
# Install production WSGI server
pip install gunicorn

# Run with gunicorn
gunicorn -w 1 -b 0.0.0.0:3001 bluetooth_server:app
```

**Note:** Use `-w 1` (single worker) because BLE scanning runs in a background thread.

---

## Testing

### Test device discovery

```bash
curl http://localhost:3001/devices
```

### Test pairing

```bash
curl -X POST http://localhost:3001/pair \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"XX:XX:XX:XX:XX:XX","userId":"test-user","userName":"Test User"}'
```

### Test status

```bash
curl http://localhost:3001/status
```

---

## Resources

- **Bleak Documentation:** https://bleak.readthedocs.io/
- **Flask Documentation:** https://flask.palletsprojects.com/
- **Arduino Nano 33 BLE:** https://docs.arduino.cc/hardware/nano-33-ble

---

**Created:** 2025-01-09
**Language:** Python 3.8+
**Platform:** Windows, macOS, Linux
**Status:** ✅ Production Ready
