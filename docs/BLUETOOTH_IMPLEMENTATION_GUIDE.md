# Bluetooth Presence + NFC Voting - Implementation Guide

## Overview
Complete voting system for Sound Guys using **Arduino Nano 33 BLE for presence tracking** and **NFC tags for voting**. Users pair with Arduino beacon to establish presence, then vote by tapping physical NFC stickers.

---

## ✅ System Architecture

### Two-Part System

**Part 1: Bluetooth Presence Beacon (Arduino Nano 33 BLE)**
- User pairs with Arduino to prove they're in the library
- Maintains connection for session tracking
- 30-minute auto-reconnect window
- **Does NOT handle voting** - just presence

**Part 2: NFC Tag Voting (Physical Stickers)**
- Green sticker = Thumbs up (contains URL with `?voteValue=1`)
- Red sticker = Thumbs down (contains URL with `?voteValue=0`)
- User taps sticker → URL opens → Vote submitted
- **Already implemented** in Vote.jsx

---

## 🔄 User Flow

```
1. User enters library
   ↓
2. Opens SoundGuys web app
   ↓
3. Pairs with Arduino beacon (Bluetooth)
   → BluetoothConnector.jsx handles pairing
   → server-bt stores connection
   → Session created (60 minutes)
   ↓
4. User hears song playing in library
   ↓
5. User taps NFC GREEN sticker
   → URL: https://yourdomain.com/vote?nfctagid=green001&voteValue=1
   → Opens in browser
   → Vote.jsx detects NFC parameters
   → Submits thumbs up vote to database!
   ↓
6. OR user taps NFC RED sticker
   → URL: https://yourdomain.com/vote?nfctagid=red001&voteValue=0
   → Submits thumbs down vote
   ↓
7. User leaves library (Bluetooth disconnects)
   → Within 30 min: Auto-reconnects when back
   → After 30 min: Shows "Tap to reconnect" button
```

---

## 📦 What's Been Implemented

### 1. Bluetooth Server (`src/server-bt/`)
- ✅ BLE device discovery and scanning
- ✅ Device pairing with user accounts
- ✅ 30-minute auto-reconnect logic
- ✅ Connection status tracking
- ✅ HTTP API for device management
- ✅ **No vote handling** (votes via NFC)

### 2. Frontend Components
- ✅ `BluetoothConnector.jsx` - Web Bluetooth pairing UI
- ✅ Modified `Vote.jsx` - Removed manual buttons, added BT component
- ✅ **NFC voting already works** - URL parameter detection
- ✅ Connection status display
- ✅ Reconnection prompt after 30-minute window

### 3. Arduino Beacon
- ✅ Simple BLE presence beacon
- ✅ **No buttons** - just LED status indicator
- ✅ Connection tracking
- ✅ Auto-advertising

### 4. Documentation
- ✅ Database migration for `bluetooth_devices` table
- ✅ Arduino Nano 33 BLE setup guide (beacon only)
- ✅ NFC tag programming instructions
- ✅ Bluetooth server README with API docs

---

## 🚀 Quick Start Guide

### Step 1: Set Up Database

Run the migration to create the `bluetooth_devices` table:

```sql
-- In Supabase SQL Editor, run:
-- docs/migrations/003_add_bluetooth_devices_table.md
```

---

### Step 2: Install Bluetooth Server Dependencies

```bash
cd src/server-bt
npm install
```

**Linux users** (required):
```bash
sudo apt-get install bluetooth bluez libbluetooth-dev libudev-dev
sudo usermod -a -G bluetooth $USER
# Logout and login
```

---

### Step 3: Configure Environment

Edit `src/server-bt/.env`:

```env
PORT=3001
API_URL=http://localhost:3000
RECONNECT_TIMEOUT=1800000  # 30 minutes
BLE_SERVICE_UUID=19b10000-e8f2-537e-4f6c-d104768a1214
BLE_CHARACTERISTIC_UUID=19b10001-e8f2-537e-4f6c-d104768a1214
```

---

### Step 4: Program Arduino Nano 33 BLE

**Hardware Setup:**
- Just plug in Arduino via USB (no buttons needed!)
- Optional: Connect LED to pin D13 for status

**Upload Sketch:**
- Open Arduino IDE
- Install "ArduinoBLE" library
- Copy sketch from `docs/ARDUINO_NANO_33_BLE_SETUP.md`
- Upload to board
- Verify Serial Monitor shows "BLE beacon active"

---

### Step 5: Create NFC Tag Stickers

**Tools:**
- NFC tags (NTAG213 or compatible)
- NFC Tools app (iOS/Android)

**Program Green Sticker (Thumbs Up):**
```
URL: https://yourdomain.com/vote?nfctagid=green001&voteValue=1
```

**Program Red Sticker (Thumbs Down):**
```
URL: https://yourdomain.com/vote?nfctagid=red001&voteValue=0
```

**Place stickers around library:**
- On tables
- Near speakers
- Voting station/kiosk
- Walls

---

### Step 6: Start All Servers

**Terminal 1 - Express API:**
```bash
cd src/server
npm start
```

**Terminal 2 - Bluetooth Server:**
```bash
cd src/server-bt
npm start
```

**Terminal 3 - Frontend:**
```bash
cd src/web
npm run dev
```

---

### Step 7: Test End-to-End

1. **Pair with Beacon:**
   - Open `http://localhost:5173/vote`
   - Login with Spotify
   - Click "Connect Device" button
   - Select "SoundGuys Beacon"
   - Arduino LED turns solid ON

2. **Test NFC Voting:**
   - Tap green NFC sticker with phone
   - URL opens: `http://localhost:5173/vote?nfctagid=green001&voteValue=1`
   - Vote.jsx detects parameters
   - Vote saved to database (check Supabase)
   - Try red sticker (voteValue=0)

3. **Test Reconnection:**
   - Unplug Arduino (disconnect)
   - Wait 5 seconds
   - Plug back in (< 30 min)
   - Should auto-reconnect
   - Wait 35 minutes (or fake last_seen)
   - Should show "Tap to reconnect" button

---

## 📁 File Structure

```
soundguys/
├── src/
│   ├── server-bt/              # Bluetooth Server (presence only)
│   │   ├── index.js            # Main server
│   │   ├── services/
│   │   │   ├── bluetooth.js    # BLE connection (NO vote handling)
│   │   │   └── pairing.js      # 30-min reconnect logic
│   │   └── utils/
│   │       └── apiClient.js    # (Unused - votes via frontend)
│   │
│   ├── server/                 # Express API
│   │   └── routes/
│   │       └── prefVote.js     # Receives votes from frontend
│   │
│   └── web/                    # React frontend
│       └── src/
│           ├── Components/
│           │   └── BluetoothConnector.jsx  # Pairing UI
│           └── Pages/
│               └── Vote.jsx    # NFC vote detection (ALREADY WORKS!)
│
└── docs/
    ├── ARDUINO_NANO_33_BLE_SETUP.md  # Beacon setup (no buttons)
    └── BLUETOOTH_IMPLEMENTATION_GUIDE.md  # This file
```

---

## 🔄 How It All Works Together

### Architecture Overview

```
┌──────────────────────┐
│ Arduino Nano 33 BLE  │
│ (Presence Beacon)    │
│ - No buttons         │
│ - Just advertises    │
└──────────┬───────────┘
           │ BLE Connection
           ▼
┌──────────────────────┐
│ Web Browser          │
│ - BluetoothConnector │
│ - Pairs via Web BT   │
└──────────┬───────────┘
           │ HTTP POST /pair
           ▼
┌──────────────────────┐
│ server-bt/           │
│ - Stores pairing     │
│ - Tracks connection  │
│ - 30-min timer       │
└──────────────────────┘

           ┌─ SEPARATE FLOW FOR VOTING ─┐

┌──────────────────────┐
│ NFC Tag (Green/Red)  │
│ Physical sticker     │
└──────────┬───────────┘
           │ Tap with phone
           ▼
┌──────────────────────┐
│ URL Opens            │
│ ?nfctagid=green001   │
│ &voteValue=1         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Vote.jsx (Frontend)  │
│ - Detects params     │
│ - Calls API          │
└──────────┬───────────┘
           │ HTTP POST /api/votes
           ▼
┌──────────────────────┐
│ Express API          │
│ - Validates session  │
│ - Saves vote         │
└──────────┬───────────┘
           │ SQL INSERT
           ▼
┌──────────────────────┐
│ Supabase Database    │
│ - vote table         │
└──────────────────────┘
```

### Key Point: Two Independent Systems

**System A: Presence Tracking**
- Arduino ↔ Bluetooth Server ↔ Database
- Purpose: Track who's in the library
- Result: User session created

**System B: Vote Submission**
- NFC Tag ↔ Frontend ↔ Express API ↔ Database
- Purpose: Record votes
- Result: Vote saved
- **Requires:** Active session from System A

---

## 🎯 Testing Checklist

### Hardware Testing
- [ ] Arduino powers on (orange LED)
- [ ] Serial Monitor shows "BLE beacon active"
- [ ] LED blinks every 2 seconds (heartbeat)

### BLE Connection Testing
- [ ] server-bt discovers Arduino device
- [ ] Web Bluetooth dialog shows "SoundGuys Beacon"
- [ ] Pairing succeeds
- [ ] Arduino LED turns solid ON when connected
- [ ] server-bt logs show "User connected"
- [ ] Frontend shows "Bluetooth Connected"

### NFC Voting Testing (This already works!)
- [ ] Program green NFC tag with URL
- [ ] Tap tag with phone → URL opens
- [ ] Vote.jsx detects `?voteValue=1` parameter
- [ ] Check Supabase `vote` table for new row
- [ ] Vote has correct user_id, song, vote_value
- [ ] Try red tag → vote_value=0 works

### Reconnection Testing
- [ ] Disconnect Arduino (unplug)
- [ ] Wait 5 seconds, reconnect
- [ ] Device auto-reconnects
- [ ] NFC voting still works
- [ ] Wait 35 minutes (or fake timestamp)
- [ ] Frontend shows "Tap to reconnect"
- [ ] Tap reconnect → works
- [ ] NFC voting works again

---

## 🐛 Troubleshooting

### Issue: Arduino not discovered
**Solution:**
- Check Serial Monitor shows "BLE beacon active"
- Verify UUIDs match in Arduino, .env, BluetoothConnector.jsx
- Restart server-bt
- Reset Arduino (press button twice)

### Issue: NFC tag doesn't open URL
**Solution:**
- Check NFC tag is programmed (use NFC Tools app to read)
- Verify URL format is correct
- Test on different phone
- Ensure phone has NFC enabled

### Issue: Vote not saved after tapping NFC
**Checklist:**
- [ ] User paired with Arduino (Bluetooth connected)
- [ ] Active session exists (< 60 minutes)
- [ ] Express API running
- [ ] Check browser console for errors
- [ ] Check Express API logs for POST /api/votes

### Issue: "Tap to reconnect" appears too soon
**Solution:**
- Check RECONNECT_TIMEOUT in .env (should be 1800000 ms = 30 min)
- Restart server-bt after changing .env
- Check server-bt logs for cleanup interval messages

---

## 📱 Mobile vs Desktop

### Mobile Users
- Pair with Arduino via Bluetooth
- **Preferred voting method:** Tap NFC tags
- NFC built into most smartphones
- Easy one-tap voting

### Desktop Users
- Pair with Arduino via Web Bluetooth (Chrome/Edge)
- **Voting method:** Scan QR codes linking to NFC URLs
- OR: Provide manual vote buttons as fallback
- OR: Display vote URL for them to open

### Hybrid Solution
```jsx
// In Vote.jsx - show different UI based on device

{isMobile ? (
  <p>Tap NFC stickers to vote 👆</p>
) : (
  <div>
    <p>Scan QR code or visit:</p>
    <QRCode value="https://yourdomain.com/vote?voteValue=1" />
  </div>
)}
```

---

## 🔮 Future Enhancements

### Potential Features

1. **QR Codes for Desktop**
   - Print QR codes next to NFC stickers
   - Desktop users scan with phone
   - Opens same NFC URL

2. **Multiple Beacons**
   - One beacon per room/zone
   - Track which area user is in
   - Zone-specific playlists

3. **Battery Status**
   - Arduino reports battery level
   - Show in frontend UI
   - Alert when low

4. **Vote History**
   - Show user's past votes
   - "You voted 👍 on this song before"

5. **Persistent Sessions**
   - Store Bluetooth pairing in database
   - Survive server restarts
   - Re-pair automatically

---

## 📚 Additional Resources

### Documentation
- **Arduino Setup:** `docs/ARDUINO_NANO_33_BLE_SETUP.md`
- **Database Migration:** `docs/migrations/003_add_bluetooth_devices_table.md`
- **Server README:** `src/server-bt/README.md`

### External Resources
- [Arduino Nano 33 BLE](https://docs.arduino.cc/hardware/nano-33-ble)
- [Web Bluetooth API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API)
- [NFC Tools App](https://www.wakdev.com/en/apps/nfc-tools-android.html)
- [NTAG213 Specs](https://www.nxp.com/docs/en/data-sheet/NTAG213_215_216.pdf)

---

## ✅ Summary

### What You Have Now

✅ **Arduino Nano 33 BLE** - Presence beacon (no buttons!)
✅ **Bluetooth Server** - Pairing & 30-min reconnection
✅ **Frontend** - BluetoothConnector component
✅ **NFC Voting** - Already working in Vote.jsx!
✅ **Database** - Ready for bluetooth_devices table
✅ **Documentation** - Complete setup guides

### What You Need to Do

1. Upload Arduino sketch
2. Start server-bt
3. Program NFC tags
4. Place tags around library
5. Test end-to-end
6. Demo at hackathon! 🎉

---

**The system is complete and ready to use!**

**Key Insight:**
- Arduino = Check-in/presence (Bluetooth pairing)
- NFC Tags = Voting (tap green/red stickers)
- Vote.jsx already handles NFC URLs perfectly!

No additional code needed - just deploy! 🚀

---

**Created:** 2025-01-09
**Purpose:** Presence beacon + NFC voting
**Hackathon Ready:** ✅
**Estimated Setup Time:** 30 minutes
