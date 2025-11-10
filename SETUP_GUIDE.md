# Sound Guys - Complete Setup Guide

## ✅ System Architecture

**Two servers + Frontend:**

1. **Express API** (Node.js) - Port 3000
   - NFC voting (already works!)
   - Session management
   - Preferences
   - Authentication

2. **Bluetooth Server** (Python) - Port 3001
   - Arduino Nano 33 BLE pairing
   - Connection tracking
   - 30-minute auto-reconnect

3. **React Frontend** (Vite) - Port 5173
   - User interface
   - NFC voting
   - Bluetooth pairing UI

---

## 🚀 Quick Start

### Step 1: Install Dependencies

**Express API:**
```bash
cd src/server
npm install
```

**Python Bluetooth Server:**
```bash
cd src/server-bt
pip install -r requirements.txt
```

**Frontend:**
```bash
cd src/web
npm install
```

---

### Step 2: Start All Servers

**Terminal 1 - Express API:**
```bash
cd src/server
npm start
```

Expected output:
```
🚀 Server running on http://localhost:3000
📡 NFC voting ready
```

**Terminal 2 - Python Bluetooth Server:**
```bash
cd src/server-bt
python bluetooth_server.py
```

Expected output:
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

**Terminal 3 - Frontend:**
```bash
cd src/web
npm run dev
```

Expected output:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
  ➜  Network: http://172.x.x.x:5173/
```

**Access from any device:**
- Use `localhost` on the same machine
- Use network IP (e.g., `http://192.168.x.x:5173`) from phones/tablets on same network

---

### Step 3: Upload Arduino Sketch

1. Open Arduino IDE
2. Install "ArduinoBLE" library (Tools → Manage Libraries)
3. Copy sketch from `docs/ARDUINO_NANO_33_BLE_SETUP.md`
4. Upload to Arduino Nano 33 BLE
5. Verify Serial Monitor shows "BLE beacon active"

---

### Step 4: Program NFC Tags

**Tools needed:**
- NFC tags (NTAG213)
- NFC Tools app (iOS/Android)

**Green sticker (Thumbs Up):**
```
URL: https://yourdomain.com/vote?nfctagid=green001&voteValue=1
```

**Red sticker (Thumbs Down):**
```
URL: https://yourdomain.com/vote?nfctagid=red001&voteValue=0
```

---

## 🎯 How It Works

### User Flow

1. **User opens app** → `http://localhost:5173`
2. **Login with Spotify** → OAuth authentication
3. **Pair with Arduino beacon** → Click "Connect Device" button
   - Web Bluetooth pairing
   - Python server stores pairing
   - 60-minute session created
4. **Tap NFC green sticker** → Thumbs up vote
   - URL opens with `?voteValue=1`
   - Vote.jsx detects parameter
   - POST to Express API
   - Vote saved to database
5. **Tap NFC red sticker** → Thumbs down vote
   - URL opens with `?voteValue=0`
   - Vote saved

### Architecture Diagram

```
┌─────────────────────┐
│ Arduino Nano 33 BLE │ (Presence beacon)
└──────────┬──────────┘
           │ Bluetooth
           ▼
┌─────────────────────┐
│ Web Browser         │
│ - BluetoothConnector│
└──────────┬──────────┘
           │ HTTP /pair
           ▼
┌─────────────────────┐
│ Python BT Server    │ (Port 3001)
│ - Pairing registry  │
│ - 30-min reconnect  │
└─────────────────────┘

      ┌─ SEPARATE: NFC VOTING ─┐

┌─────────────────────┐
│ NFC Tag (Sticker)   │
└──────────┬──────────┘
           │ Tap phone
           ▼
┌─────────────────────┐
│ URL with ?voteValue │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Vote.jsx (Frontend) │
└──────────┬──────────┘
           │ POST /api/votes
           ▼
┌─────────────────────┐
│ Express API         │ (Port 3000)
│ - Session check     │
│ - Save to DB        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Supabase Database   │
└─────────────────────┘
```

---

## 📡 API Endpoints

### Express API (Port 3000)

- `POST /api/checkin` - Create 60-min session
- `GET /api/session` - Get active session
- `POST /api/votes` - Submit vote (NFC)
- `POST /api/preferences` - Save audio preferences
- `GET /api/leaderboard` - Get rankings
- `GET /health` - Health check

### Python Bluetooth Server (Port 3001)

- `POST /pair` - Pair device
- `POST /reconnect` - Reconnect after 30 min
- `POST /unpair` - Remove pairing
- `GET /devices` - List discovered devices
- `GET /status` - Server status
- `GET /health` - Health check

---

## 🐛 Troubleshooting

### Express server won't start

```bash
cd src/server
npm install
npm start
```

Check for port conflicts:
```bash
netstat -ano | findstr :3000
```

### Python server won't start

**Install Python 3.8+:**
https://www.python.org/downloads/

**Install dependencies:**
```bash
cd src/server-bt
pip install -r requirements.txt
```

**Windows Bluetooth issues:**
- Enable Bluetooth in Windows settings
- Run Python as Administrator (first time)

**Test Bluetooth:**
```python
python
>>> import bleak
>>> import asyncio
>>> asyncio.run(bleak.BleakScanner.discover())
```

### Arduino not discovered

- Check Serial Monitor shows "BLE beacon active"
- Verify Arduino powered on (USB)
- Reset Arduino (press button twice quickly)
- Restart Python Bluetooth server

### NFC vote not saving

- Check user paired with Arduino (Bluetooth connected)
- Check active session (< 60 minutes)
- Check Express API logs
- Verify NFC tag URL format

### Frontend not loading

```bash
cd src/web
npm install
npm run dev
```

Check `.env` file exists with:
```env
VITE_API_URL=http://localhost:3000
VITE_SUPABASE_URL=your-url
VITE_SUPABASE_ANON_KEY=your-key
```

---

## ✅ Testing Checklist

- [ ] Express server starts on port 3000
- [ ] Python server starts on port 3001
- [ ] Frontend starts on port 5173
- [ ] Arduino uploads successfully
- [ ] Serial Monitor shows "BLE beacon active"
- [ ] Python server discovers Arduino
- [ ] Web Bluetooth pairing works
- [ ] NFC tag programmed
- [ ] NFC tag opens vote URL
- [ ] Vote saves to database
- [ ] Disconnect/reconnect works
- [ ] 30-minute timeout tested

---

## 📦 File Structure

```
soundguys/
├── src/
│   ├── server/              # Express API (Node.js, Port 3000)
│   │   ├── index.js
│   │   ├── routes/
│   │   └── middleware/
│   │
│   ├── server-bt/           # Bluetooth Server (Python, Port 3001)
│   │   ├── bluetooth_server.py
│   │   ├── requirements.txt
│   │   └── README.md
│   │
│   └── web/                 # React Frontend (Vite, Port 5173)
│       └── src/
│           ├── Components/
│           │   └── BluetoothConnector.jsx
│           └── Pages/
│               └── Vote.jsx
│
└── docs/
    ├── ARDUINO_NANO_33_BLE_SETUP.md
    └── BLUETOOTH_IMPLEMENTATION_GUIDE.md
```

---

## 🎉 You're Ready!

**What works:**
✅ Express API (NFC voting)
✅ Python Bluetooth server (presence tracking)
✅ React frontend
✅ Arduino beacon
✅ NFC voting
✅ Session management
✅ 30-minute auto-reconnect

**Start all three servers and you're ready to demo!**

---

**Created:** 2025-01-09
**Platform:** Windows, macOS, Linux
**Languages:** Node.js + Python + React
**Status:** ✅ Ready for Hackathon
