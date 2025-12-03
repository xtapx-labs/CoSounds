# Django Bluetooth Presence Detection Backend

Django backend for CoSounds Bluetooth presence detection system using Raspberry Pi scanner.

## Overview

This Django backend receives device detection reports from a Raspberry Pi BLE scanner and manages presence-based sessions with a 15-minute grace period.

**Architecture:**
- Raspberry Pi 3 scans for Bluetooth devices every 10 seconds
- Reports detected devices to Django via HTTP POST
- Django validates JWT tokens and manages user sessions
- 15-minute grace period for temporary disconnections

## Setup

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your values
```

**Required variables:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key (NOT anon key)
- `SUPABASE_JWT_SECRET` - JWT secret from Supabase API settings
- `SCANNER_API_KEY` - Random string for Pi scanner authentication
- `SECRET_KEY` - Django secret key (generate with `django-admin generate-secret-key`)

### 4. Run Database Migration

Open Supabase SQL Editor and run:
```bash
# File: docs/migrations/004_update_bt_test_tables_for_scanner.sql
```

This updates `test_bt_devices` and `test_bt_sessions` tables for scanner-based detection.

### 5. Start Django Server

```bash
python manage.py runserver 0.0.0.0:8000
```

**Test:**
```bash
curl http://localhost:8000/api/health
# Should return: {"status":"ok","service":"bluetooth-presence-django","version":"1.0.0"}
```

## API Endpoints

### POST /api/register-device

Register device MAC on first NFC tap.

**Headers:** `Authorization: Bearer {jwt_token}`

**Body:**
```json
{
  "device_mac": "AA:BB:CC:DD:EE:FF",
  "device_name": "My Laptop"
}
```

### POST /api/check-in

Check in on subsequent NFC taps (start new session).

**Headers:** `Authorization: Bearer {jwt_token}`

**Body:** `{}` (empty)

### POST /api/scanner/device-detected

Pi scanner reports device detection (called every 10s).

**Headers:** `X-Scanner-API-Key: {scanner_api_key}`

**Body:**
```json
{
  "device_mac": "AA:BB:CC:DD:EE:FF",
  "device_name": "Laptop Name",
  "rssi": -45
}
```

### GET /api/my-status

Get user's device and connection status.

**Headers:** `Authorization: Bearer {jwt_token}`

**Response:**
```json
{
  "success": true,
  "has_device": true,
  "device_mac": "AA:BB:CC:DD:EE:FF",
  "status": "connected",
  "last_seen": "2025-12-03T10:30:00Z"
}
```

### GET /api/health

Health check (no auth required).

## Background Tasks

**Grace Period Cleanup:**
- Runs every 30 seconds (configurable via `DETECTION_TIMEOUT_SECONDS`)
- Devices not detected for 30s → enter grace period (15 min)
- Expired grace periods → end session and disconnect

## Logging

View logs in terminal:
```bash
# Django outputs logs to console
# Check for:
# - "Device registered"
# - "User checked in"
# - "Device detected"
# - "Grace period started/ended"
```

## Troubleshooting

**"SUPABASE_URL and SUPABASE_SERVICE_KEY must be set":**
- Check `.env` file exists and has correct values
- Ensure service role key (not anon key) is used

**"Invalid token" errors:**
- Verify `SUPABASE_JWT_SECRET` matches your Supabase project
- Check JWT token hasn't expired

**Scanner can't connect:**
- Verify `SCANNER_API_KEY` matches in both Django and Pi scanner
- Check Django is running on 0.0.0.0:8000 (accessible from network)
- Confirm Pi can reach Django server (ping test)

**Grace period not working:**
- Check background scheduler started (look for "Background scheduler started" in logs)
- Verify `DETECTION_TIMEOUT_SECONDS` and `GRACE_PERIOD_MINUTES` are set

## Development

**Run tests:**
```bash
python manage.py test bluetooth_api
```

**Generate secret key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Production Deployment

**Use Gunicorn:**
```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

**Set environment:**
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,your-server-ip
```

## File Structure

```
src/server-bt-django/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (git-ignored)
├── config/                      # Django project config
│   ├── settings.py              # Settings
│   ├── urls.py                  # Main URL config
│   └── wsgi.py                  # WSGI application
└── bluetooth_api/               # Bluetooth API app
    ├── views.py                 # API endpoints
    ├── urls.py                  # API URL routes
    ├── middleware.py            # JWT/API key auth
    ├── services.py              # Supabase operations
    └── tasks.py                 # Background scheduler
```

## Architecture

```
┌─────────────────────────────────────────┐
│   Raspberry Pi 3 (BLE Scanner)          │
│   - Scans for devices every 10s         │
│   - Reports to Django                   │
└─────────────────┬───────────────────────┘
                  │ POST /api/scanner/device-detected
                  ↓
┌─────────────────────────────────────────┐
│   Django Backend (This Service)         │
│   - Validates scanner API key           │
│   - Updates last_seen timestamps        │
│   - Manages grace periods               │
│   - Handles user check-ins              │
└─────────────────┬───────────────────────┘
                  │ Supabase Python SDK
                  ↓
┌─────────────────────────────────────────┐
│   Supabase (PostgreSQL)                 │
│   - test_bt_devices                     │
│   - test_bt_sessions                    │
└─────────────────────────────────────────┘
                  ↑
                  │ JWT Auth + HTTP
┌─────────────────┴───────────────────────┐
│   React Frontend                        │
│   - Register device on first NFC tap    │
│   - Check-in on subsequent taps         │
└─────────────────────────────────────────┘
```

## License

Part of CoSounds project - University of Alberta
