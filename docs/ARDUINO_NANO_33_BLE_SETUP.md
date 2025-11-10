# Arduino Nano 33 BLE - Bluetooth Presence Beacon Setup

## Overview
This guide explains how to set up an Arduino Nano 33 BLE as a simple Bluetooth Low Energy (BLE) beacon for the Sound Guys project. The Arduino is used ONLY for establishing connection/presence - voting happens via NFC tag stickers.

---

## What Does the Arduino Do?

**Arduino Nano 33 BLE:**
- Advertises as a BLE device
- Users tap/pair to establish they're in the library
- Maintains connection to track presence
- **Does NOT handle voting** - that's done via NFC tags

**NFC Tags (Physical Stickers):**
- Green sticker (thumbs up) → Contains URL with `?voteValue=1`
- Red sticker (thumbs down) → Contains URL with `?voteValue=0`
- User taps sticker → URL opens → Vote is recorded

---

## Hardware Requirements

### Components
- **Arduino Nano 33 BLE** (or Arduino Nano 33 BLE Sense)
- **1x LED** (optional, for status indication)
- **1x 220Ω Resistor** (for LED)
- **USB Cable** (Micro-USB for programming and power)
- **USB Power Bank** (optional, for portable deployment)

### No Buttons Needed!
This setup is just a beacon - no physical buttons required.

---

## Circuit Diagram

### Simple Setup (LED Only)

```
Arduino Nano 33 BLE:

Status LED (Optional):
  - Anode (+) → Digital Pin 13 (built-in LED)
  - Or external LED:
    - Anode (+) → Digital Pin 2
    - Cathode (-) → 220Ω resistor → GND

Power:
  - USB power via Micro-USB port
```

### Schematic
```
                   +5V (from USB)
                     |
      ┌──────────────┴──────────────┐
      │   Arduino Nano 33 BLE       │
      │                             │
      │  (Built-in LED on D13)      │
      │                             │
      │  Or:                        │
  D2  ├─────[ LED ]──────[220Ω]────┤ GND
      │                             │
      └─────────────────────────────┘
```

**That's it!** Just plug in USB power.

---

## Arduino Sketch

### Installation Steps

1. **Install Arduino IDE**
   - Download from [arduino.cc](https://www.arduino.cc/en/software)
   - Install version 2.0 or later

2. **Install Board Support**
   - Open Arduino IDE
   - Go to **Tools → Board → Boards Manager**
   - Search for "Arduino Mbed OS Nano Boards"
   - Install the package

3. **Install ArduinoBLE Library**
   - Go to **Tools → Manage Libraries**
   - Search for "ArduinoBLE"
   - Install the latest version

---

### Arduino Code - Simple BLE Beacon

Create a new sketch and paste the following code:

```cpp
/*
 * Sound Guys - Bluetooth Presence Beacon
 * Arduino Nano 33 BLE
 *
 * Simple BLE beacon for user presence tracking.
 * Voting happens via NFC tags, not this device!
 */

#include <ArduinoBLE.h>

// Pin definitions
#define LED_STATUS LED_BUILTIN  // Use built-in LED on pin 13

// BLE Service and Characteristic UUIDs
#define SERVICE_UUID        "19b10000-e8f2-537e-4f6c-d104768a1214"
#define CHARACTERISTIC_UUID "19b10001-e8f2-537e-4f6c-d104768a1214"

// BLE objects
BLEService presenceService(SERVICE_UUID);
BLEByteCharacteristic statusCharacteristic(CHARACTERISTIC_UUID, BLERead | BLENotify);

// Connection tracking
bool isConnected = false;
unsigned long lastHeartbeat = 0;

void setup() {
  // Initialize serial communication (for debugging)
  Serial.begin(9600);
  while (!Serial && millis() < 3000);  // Wait up to 3 seconds for serial

  Serial.println("=================================");
  Serial.println("Sound Guys - Presence Beacon");
  Serial.println("Arduino Nano 33 BLE");
  Serial.println("=================================");
  Serial.println();

  // Configure LED pin
  pinMode(LED_STATUS, OUTPUT);
  digitalWrite(LED_STATUS, LOW);

  // LED startup sequence (visual confirmation)
  blinkStartup();

  // Initialize BLE
  if (!BLE.begin()) {
    Serial.println("❌ Starting BLE failed!");
    while (1) {
      // Blink rapidly to indicate error
      digitalWrite(LED_STATUS, HIGH);
      delay(100);
      digitalWrite(LED_STATUS, LOW);
      delay(100);
    }
  }

  // Set BLE device name
  BLE.setLocalName("SoundGuys Beacon");
  BLE.setDeviceName("SoundGuys Presence Beacon");

  // Add the characteristic to the service
  presenceService.addCharacteristic(statusCharacteristic);

  // Add the service
  BLE.addService(presenceService);

  // Set initial value (1 = beacon active)
  statusCharacteristic.writeValue(1);

  // Start advertising
  BLE.advertise();

  Serial.println("✅ BLE beacon active and advertising");
  Serial.print("📡 Device address: ");
  Serial.println(BLE.address());
  Serial.println();
  Serial.println("Users can now pair with this beacon.");
  Serial.println("Voting happens via NFC tags, not this device.");
  Serial.println();

  // Indicate ready with LED
  digitalWrite(LED_STATUS, HIGH);
  delay(1000);
  digitalWrite(LED_STATUS, LOW);
}

void loop() {
  // Wait for a BLE central device (laptop/phone)
  BLEDevice central = BLE.central();

  // If a central is connected
  if (central) {
    if (!isConnected) {
      // New connection
      Serial.println("=================================");
      Serial.print("✅ User connected: ");
      Serial.println(central.address());
      Serial.println("=================================");

      // Indicate connection with solid LED
      digitalWrite(LED_STATUS, HIGH);
      isConnected = true;
    }

    // While the central is connected
    while (central.connected()) {
      // Just maintain connection - no button handling needed
      // Voting happens via NFC tags!

      // Heartbeat every 5 seconds
      if (millis() - lastHeartbeat > 5000) {
        Serial.print("💓 Connection active - ");
        Serial.print(central.address());
        Serial.println(" still connected");
        lastHeartbeat = millis();
      }

      delay(100);  // Small delay
    }

    // Disconnected
    Serial.println("=================================");
    Serial.print("❌ User disconnected: ");
    Serial.println(central.address());
    Serial.println("=================================");
    Serial.println();

    digitalWrite(LED_STATUS, LOW);
    isConnected = false;
  }

  // Not connected - idle mode (heartbeat blink)
  if (!isConnected) {
    if (millis() - lastHeartbeat > 2000) {
      // Quick blink to show beacon is alive
      digitalWrite(LED_STATUS, HIGH);
      delay(50);
      digitalWrite(LED_STATUS, LOW);
      lastHeartbeat = millis();
    }
  }
}

/**
 * Startup LED sequence
 */
void blinkStartup() {
  Serial.println("Starting up...");
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_STATUS, HIGH);
    delay(100);
    digitalWrite(LED_STATUS, LOW);
    delay(100);
  }
  Serial.println("Startup complete!");
  Serial.println();
}
```

---

## Uploading the Sketch

1. **Connect Arduino to Computer**
   - Use Micro-USB cable
   - Arduino should power on (orange LED near USB port)

2. **Select Board**
   - Go to **Tools → Board → Arduino Mbed OS Nano Boards**
   - Select **Arduino Nano 33 BLE**

3. **Select Port**
   - Go to **Tools → Port**
   - Select the port with "Arduino Nano 33 BLE" (e.g., COM3 on Windows, /dev/ttyACM0 on Linux)

4. **Upload Sketch**
   - Click **Upload** button (→ icon)
   - Wait for "Done uploading" message
   - Arduino will restart automatically

5. **Verify**
   - Open **Tools → Serial Monitor**
   - Set baud rate to **9600**
   - You should see:
     ```
     =================================
     Sound Guys - Presence Beacon
     Arduino Nano 33 BLE
     =================================

     Starting up...
     Startup complete!

     ✅ BLE beacon active and advertising
     📡 Device address: XX:XX:XX:XX:XX:XX

     Users can now pair with this beacon.
     Voting happens via NFC tags, not this device.
     ```

---

## Testing the Beacon

### Test BLE Advertising

1. **Start Bluetooth Server**
   ```bash
   cd src/server-bt
   npm install
   npm start
   ```

   You should see:
   ```
   🔍 Discovered: SoundGuys Beacon (a1:b2:c3:d4:e5:f6) RSSI: -45
   ```

2. **Start Frontend**
   ```bash
   cd src/web
   npm run dev
   ```

3. **Connect from Browser**
   - Open app in Chrome/Edge
   - Click "Connect Device" button
   - Select "SoundGuys Beacon" from device list
   - Wait for pairing
   - LED should turn solid ON when connected

4. **Test Disconnection**
   - Unplug Arduino or move far away
   - LED should turn OFF
   - server-bt logs: "User disconnected"
   - Frontend shows "Reconnect" button

5. **Test 30-Minute Reconnection**
   - Reconnect Arduino (plug in or move back)
   - Should auto-reconnect if < 30 minutes
   - After 30 min: Shows "Tap to reconnect" button

---

## Physical Deployment

### Library Deployment Setup

1. **Position Arduino**
   - Place near entrance or center of library
   - Within Bluetooth range of all seating areas (~10 meters)
   - Connect to USB power bank or wall adapter

2. **Create NFC Voting Stickers**
   - **Green sticker (Thumbs Up):**
     - Program NFC tag with URL: `https://yourdomain.com/vote?nfctagid=green001&voteValue=1`
   - **Red sticker (Thumbs Down):**
     - Program NFC tag with URL: `https://yourdomain.com/vote?nfctagid=red001&voteValue=0`
   - Place stickers on tables, walls, or voting stations

3. **User Flow**
   ```
   1. User enters library
   2. User opens SoundGuys web app
   3. User pairs with Arduino beacon (Bluetooth)
      → Establishes they're present in library
      → Session starts (60 minutes)

   4. Song plays in library
   5. User taps NFC green sticker (likes song)
      → URL opens with ?voteValue=1
      → Vote.jsx detects NFC parameters
      → Vote is saved to database!

   6. User taps NFC red sticker (dislikes song)
      → URL opens with ?voteValue=0
      → Vote saved!

   7. User leaves library (Bluetooth disconnects)
      → Can reconnect within 30 minutes automatically
   ```

---

## LED Status Meanings

| LED State | Meaning |
|-----------|---------|
| Quick blink every 2 sec | Beacon active, waiting for connection |
| Solid ON | User connected |
| OFF | No power or disconnected |
| Rapid blinking | BLE initialization failed (error) |

---

## Troubleshooting

### Arduino Not Detected
- **Solution 1:** Install Arduino Mbed OS Nano Boards package
- **Solution 2:** Press reset button twice quickly (bootloader mode)
- **Solution 3:** Try different USB cable

### BLE Not Working
- **Check:** Serial Monitor shows "Starting BLE failed!"
- **Solution:** Re-upload sketch, ensure ArduinoBLE library installed
- **Verify:** BLE is built into Nano 33 BLE (no external module needed)

### Can't Find Device in Web Bluetooth
- **Browser:** Use Chrome, Edge, or Opera only
- **HTTPS:** localhost works, remote sites need HTTPS
- **Check:** Serial Monitor says "BLE beacon active"
- **Restart:** Press reset button on Arduino

### Device Disconnects Frequently
- **Power:** Use stable USB power (power bank or wall adapter)
- **Range:** Keep within 10 meters
- **Interference:** Move away from WiFi routers

---

## Power Consumption

- **Idle (advertising):** ~40mA
- **Connected:** ~60mA
- **Estimated runtime (2000mAh power bank):** ~30 hours

**Recommendation:** Use 10,000mAh power bank for multi-day deployment

---

## Enclosure (Optional)

### Simple Enclosure

- Small plastic box (5cm x 5cm x 3cm)
- USB cable exit hole
- Clear window for LED
- Label: "SoundGuys Check-In Beacon"

---

## Security Considerations

### BLE Security
- Device address used as unique identifier
- No sensitive data transmitted
- Backend validates user session

### NFC Security
- URLs contain vote parameters (public)
- Backend validates session before accepting vote
- Rate limiting prevents spam

---

## NFC Tag Programming

### Tools Needed
- **NFC Tags:** NTAG213 or compatible (13.56 MHz)
- **NFC Writer App:** "NFC Tools" (iOS/Android) or "NFC TagWriter"

### Steps to Program NFC Tags

1. **Open NFC Tools app**
2. **Select "Write"**
3. **Add Record → URL/URI**
4. **Enter URL:**
   - Thumbs Up: `https://yourdomain.com/vote?nfctagid=green001&voteValue=1`
   - Thumbs Down: `https://yourdomain.com/vote?nfctagid=red001&voteValue=0`
5. **Write to tag**
6. **Test:** Tap with phone → URL should open

### NFC Tag Placement Ideas
- **Tables:** One green, one red per table
- **Voting Station:** Dedicated kiosk with both stickers
- **Walls:** Near speakers or music control area
- **Hand-held:** Laminated cards users can carry

---

## BLE UUID Reference

These UUIDs must match in Arduino, server-bt, and frontend:

```
SERVICE_UUID        = 19b10000-e8f2-537e-4f6c-d104768a1214
CHARACTERISTIC_UUID = 19b10001-e8f2-537e-4f6c-d104768a1214
```

**If you change UUIDs:** Update in Arduino sketch, server-bt/.env, and BluetoothConnector.jsx

---

## Resources

### Documentation
- [Arduino Nano 33 BLE Guide](https://docs.arduino.cc/hardware/nano-33-ble)
- [ArduinoBLE Library](https://www.arduino.cc/reference/en/libraries/arduinoble/)
- [Web Bluetooth API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API)
- [NFC Tools App](https://www.wakdev.com/en/apps/nfc-tools-android.html)

---

**Last Updated:** 2025-01-09
**Purpose:** Presence beacon only (voting via NFC tags)
**Tested With:** Arduino Nano 33 BLE Rev 2, ArduinoBLE 1.3.6
