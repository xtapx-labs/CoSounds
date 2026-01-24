# V1 Original Player - Running Status

## ✅ Successfully Running!

The V1 Original audio player is now operational in both modes:

### 1. **Local Mode (Recommended for Demo)**
- **Script:** `local_player.py`
- **Command:** `python local_player.py`
- **Features:**
  - Plays local audio files from `.audio/` directory
  - 30-second crossfade transitions
  - Infinite looping of each track
  - Automatic random song selection
  - No backend dependency

**Current Status:**
```
✅ Running on Windows
✅ Playing wind_sound.wav with fade-in
✅ Found 5 audio files in .audio/:
   - 67.wav
   - rain_sounds.wav
   - thunder_sound.wav
   - wave_sounds.wav
   - wind_sound.wav
```

### 2. **Backend-Connected Mode**
- **Backend:** Node.js Express + Supabase
- **Player:** FastAPI + pygame.mixer
- **Ports:**
  - Backend: http://localhost:3000
  - Player API: http://localhost:8000

**Backend Status:**
```
✅ Server running on http://localhost:3000
✅ Connected to Supabase database
✅ ML recommendation engine active
✅ User preference vectors working
```

**Player Status:**
```
⚠️ Requires database songs to exist locally
⚠️ Backend recommends: rain_through_open_window.wav (not in .audio/)
⚠️ Backend recommends: deep_forest_rain.wav (not in .audio/)
```

---

## Architecture Comparison: V1 vs V2

### V1 Original (Currently Running)
**Stack:**
- Backend: Node.js/Express + Supabase PostgreSQL
- Player: FastAPI + pygame.mixer (2 channels)
- ML: pgvector with cosine similarity
- Auth: JWT via Supabase

**Features:**
✅ Working personalization (gradient descent)
✅ 5D user preference vectors
✅ Cosine similarity recommendations
✅ Penalty system for recent songs
✅ 30-second crossfade transitions
✅ 2-channel audio playback (current + next)
✅ Session tracking and leaderboards
✅ OAuth (Spotify, Google)

**Audio Behavior:**
- Infinite loops on each track
- Smooth 30s crossfade between tracks
- Polls backend every 30 seconds for new recommendation
- Manual volume-based crossfade implementation

---

### V2 Slop (Broken/Incomplete)
**Stack:**
- Backend: Django 6.0 + django-ninja
- Player: Flet desktop GUI + pygame.mixer (16 channels)
- ML: None (RandomSoundClassifier)
- Auth: Session-based with insecure OTP

**Issues:**
❌ No personalization (ML code commented out)
❌ AWS S3 credentials missing (file uploads broken)
❌ Security vulnerabilities (16 found)
❌ Random vote values (not based on similarity)
❌ 62 duplicate migrations committed
❌ 140 lines of duplicate code
❌ No working recommendation system

**Audio Behavior:**
- 16 independent channels for layering
- Soundscapes loop, instrumentals play once
- 6-second fade transitions
- Manifest.json tracking system

---

## How the ML Works (V1 Only)

### Preference Vector Update
When a user votes, their 5D preference vector is updated using gradient descent:

**Like (α = 0.12):**
```
u' = normalize((1 - α)u + α·s)
```
Shifts user preference 12% toward the song's embedding.

**Dislike (α = 0.12, β = 0.7):**
```
u' = normalize(u - α·β·(u·s)·s)
```
Pushes preference away proportional to similarity (70% softness).

### Song Recommendation
1. **Average all active users' preference vectors** → `mean_vector`
2. **Query pgvector:** `SELECT * FROM sounds ORDER BY cosine_distance(embedding, mean_vector) LIMIT 10`
3. **Apply recency penalty** to prevent repetition
4. **Return top match** to player

### Current Recommendation Engine Output
```json
{
  "success": true,
  "user_count": 4,
  "users_used": ["1fbd0b02...", "00d7e8e1...", "4c637a4f...", "7c3fbe0f..."],
  "mean_vector": [0.763, 0.172, 0.251, 0.215, 0.528],
  "recommendations": [{
    "id": "4dc0288e-28c3-4725-ba2c-a5cd11a3ecbf",
    "title": "deep_forest_rain",
    "distance": 0.231,
    "similarity": 0.769,
    "adjusted_distance": 0.231,
    "last_played": "2025-11-25T23:38:27.379+00:00"
  }]
}
```

---

## Running Instructions

### Quick Start (Local Player)
```bash
cd "c:\Users\talwa\Desktop\Atom\soundguys\src\V1 Original\player"
python local_player.py
```

### Full System (Backend + Player)

**Terminal 1 - Backend:**
```bash
cd "c:\Users\talwa\Desktop\Atom\soundguys\src\V1 Original\server"
npm install
npm start
```

**Terminal 2 - Player API:**
```bash
cd "c:\Users\talwa\Desktop\Atom\soundguys\src\V1 Original\player"
python -m pip install fastapi httpx pygame uvicorn
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Audio Files Required
Place `.wav`, `.mp3`, or `.ogg` files in:
```
src/V1 Original/player/.audio/
```

**Currently Available:**
- 67.wav (428 KB)
- rain_sounds.wav (1.1 MB)
- thunder_sound.wav (2.3 MB)
- wave_sounds.wav (2.2 MB)
- wind_sound.wav (4.8 MB)

---

## Key Differences

| Feature | V1 Original | V2 Slop |
|---------|------------|---------|
| **Personalization** | ✅ Working (gradient descent) | ❌ None (random) |
| **Vector DB** | ✅ pgvector + cosine similarity | ❌ Unused |
| **Crossfade** | ✅ 30 seconds | ✅ 6 seconds |
| **Channels** | 2 (current + next) | 16 (layering) |
| **Looping** | Infinite on each track | Soundscapes loop, instruments play once |
| **Auth** | ✅ OAuth (Supabase) | ⚠️ Insecure OTP |
| **File Storage** | Cloud (Supabase) | ⚠️ Broken S3 |
| **Sessions** | ✅ Tracked with leaderboards | ❌ None |
| **Vote Impact** | ✅ Updates preferences | ❌ No effect |
| **Security** | Better | 16 vulnerabilities |

---

## Technical Highlights

### V1 Player Architecture
```
FastAPI (port 8000)
    ↓
Background Task (polls every 30s)
    ↓
GET /api/model/recommend (backend)
    ↓
Supabase pgvector query
    ↓
Returns song with best cosine similarity
    ↓
pygame.mixer crossfade
    ↓
2-channel system:
    - Channel 0: Current track (volume 1.0 → 0.0)
    - Channel 1: Next track (volume 0.0 → 1.0)
```

### V2 Player Architecture
```
Flet Desktop GUI
    ↓
LayerManager (16 channels)
    ↓
manifest.json (downloaded files)
    ↓
Django API (port 8000)
    ↓
No recommendation engine
    ↓
Random song selection
```

---

## What's Actually Working

### ✅ V1 Local Player
- Plays local files
- Smooth crossfades
- Infinite looping
- No backend required

### ✅ V1 Backend
- Express server running
- Supabase connection active
- ML recommendations working
- User preference updates working

### ⚠️ V1 Player + Backend Integration
- Backend recommends database songs
- Local files don't match database
- Would need to download songs from Supabase storage

### ❌ V2 Everything
- No personalization
- Broken file uploads
- Security issues
- No recommendation system

---

## Conclusion

The **V1 Original** player demonstrates:
1. ✅ Proper ML-based music recommendation
2. ✅ User preference learning via gradient descent
3. ✅ Smooth audio crossfading
4. ✅ Scalable architecture (Supabase + Node.js)
5. ✅ Session and leaderboard tracking

The **V2 Slop** player is:
1. ❌ Missing all ML functionality
2. ❌ Full of security vulnerabilities
3. ❌ Using placeholder/random code
4. ⚠️ Better GUI (Flet) but no substance

**Recommendation:** Use V1 Original as the base for future development. V2 can provide UI inspiration but needs complete backend rewrite.
