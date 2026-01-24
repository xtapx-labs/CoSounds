# V3 Architecture - The "Best of Both Worlds" Hybrid

## Overview
V3 combines the working ML personalization from V1 with the admin/player management from V2, unified under a single Supabase database.

## Directory Structure

```
V3/
├── server user/          # Node.js + Express (User Logic)
│   ├── routes/
│   │   ├── auth.js           # Supabase JWT validation
│   │   ├── session.js        # Check-in/out, session management
│   │   ├── prefVote.js       # Vote handling + preference updates
│   │   ├── modelRoutes.js    # ML recommendations
│   │   └── leaderboard.js    # Monthly leaderboards
│   └── middleware/
│       └── auth.js           # JWT middleware
│
├── server admin/         # Django (Admin + Player API)
│   ├── core/
│   │   ├── models.py         # Unmanaged models (Supabase schema)
│   │   ├── admin.py          # Django admin for S3 uploads
│   │   └── api.py            # Player API (Django Ninja)
│   └── voter/
│       └── views.py          # Voting UI (HTMX)
│
├── web/                  # React + Vite (User Frontend)
│   ├── src/
│   │   ├── Pages/
│   │   │   ├── Login.jsx     # Google OAuth
│   │   │   ├── Vote.jsx      # Voting interface
│   │   │   └── Preferences.jsx
│   │   └── lib/
│   │       └── supabase.js   # Supabase client
│
├── player/               # Python + Flet (Physical Player Client)
│   └── src/app/
│       ├── player.py         # Audio playback (pygame)
│       ├── client.py         # Polls Django API
│       └── auth.py           # Token-based auth
│
└── ml_model/             # ML Training Scripts
    ├── train_linear.py       # Ridge regression training
    ├── predict.py            # Generate embeddings
    └── batch_predict.py      # Bulk processing
```

## Architecture Flow

### 1. User Votes (Node.js → Supabase)
```
User clicks "Like" (1-5)
    ↓
POST /api/votes (Node.js)
    ↓
Fetch song embedding from Supabase
    ↓
Calculate cosine similarity
    ↓
Update user's preference_vector (gradient descent)
    ↓
Save to Supabase profiles table
```

### 2. Recommendation Engine (Supabase Function/Cron)
```
Every 30 seconds:
    ↓
Get all active sessions
    ↓
Average their preference_vectors
    ↓
Call recommend_with_penalty(avg_vector)
    ↓
PostgreSQL finds best match (cosine similarity)
    ↓
Write to player_queue table
```

### 3. Player Playback (Django → Player)
```
Physical Player polls Django every 5s
    ↓
GET /api/cosound?player={token}
    ↓
Django reads player_queue from Supabase
    ↓
Returns song IDs + S3 URLs
    ↓
Player downloads from S3 (if not cached)
    ↓
pygame.mixer plays 16-channel mix
```

### 4. Admin Upload (Django → S3 → Supabase)
```
Admin uploads .wav file in Django Admin
    ↓
django-storages uploads to AWS S3
    ↓
Django saves S3 URL to songs table
    ↓
ML script generates embedding
    ↓
Embedding saved to songs.embedding (vector)
```

## Database (Supabase PostgreSQL)

**Single Source of Truth**: All services read/write to the same Supabase database.

### Key Tables:
- `profiles`: User info + `preference_vector(5)`
- `songs`: Metadata + `file_url` (S3) + `embedding(5)`
- `votes`: User feedback
- `sessions`: Active listeners
- `players`: Physical devices
- `player_queue`: Bridge between ML and playback
- `roles`: Admin RBAC

See `../DATABASE_DESIGN_V3_REFINED.md` for full schema.

## Authentication Strategy

### Users (Web App)
- **Provider**: Supabase Auth (Google OAuth)
- **Token**: JWT in `Authorization: Bearer <token>`
- **Middleware**: Node.js validates JWT with Supabase

### Admins (Django Admin)
- **Provider**: Supabase Auth (same as users)
- **Check**: Django checks `roles` table for 'admin' role
- **Login**: Custom auth backend validates Supabase JWT

### Players (Physical Devices)
- **Provider**: API Token (stored in `players.token`)
- **Auth**: `X-API-Key: <player_token>` header
- **Validation**: Django checks `players` table

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **User Server** | Node.js + Express | Vote handling, ML logic |
| **Admin Server** | Django + Ninja | S3 uploads, Player API |
| **Database** | Supabase (PostgreSQL + pgvector) | Single source of truth |
| **Auth** | Supabase Auth | OAuth + JWT |
| **Storage** | AWS S3 | Audio files |
| **Frontend** | React + Vite | User interface |
| **Player** | Python + Flet + pygame | Physical playback |
| **ML** | NumPy + scikit-learn | Feature extraction |

## Running V3

### 1. Database Setup
```bash
# Run in Supabase SQL Editor
psql < ../supabase_schema_v3.sql
```

### 2. Node.js Server (User Logic)
```bash
cd "server user"
npm install
npm start  # Port 3000
```

### 3. Django Server (Admin)
```bash
cd "server admin"
uv sync
uv run python src/main.py migrate
uv run python src/main.py runserver  # Port 8000
```

### 4. React Web App
```bash
cd web
npm install
npm run dev  # Port 5173
```

### 5. Player Client
```bash
cd player
uv sync
uv run python main.py
```

## Environment Variables

### Node.js (`.env`)
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_KEY=eyJxxx...
PORT=3000
```

### Django (`src/config/.env`)
```
DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_STORAGE_BUCKET_NAME=soundguys-audio
AWS_S3_REGION_NAME=us-east-1
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
```

### React (`.env`)
```
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJxxx...
VITE_API_URL=http://localhost:3000
```

### Player (`.env`)
```
DJANGO_API_URL=http://localhost:8000
PLAYER_TOKEN=<from_django_admin>
```

## Key Improvements Over V1/V2

✅ **Unified Auth**: Supabase for everyone (no more dual systems)  
✅ **Single DB**: No sync issues between services  
✅ **S3 Storage**: Scalable audio storage (not broken like V2)  
✅ **Working ML**: V1's gradient descent preserved  
✅ **Player Management**: V2's multi-device support  
✅ **Security**: Proper RLS, password validators, HTTPS enforcement  
✅ **No Code Duplication**: Cleaned up 140 lines of duplicate code  

## Migration from V1/V2

1. **Export V1 Data**: Users, songs, preferences, votes
2. **Run V3 Schema**: Apply `supabase_schema_v3.sql`
3. **Import Data**: Map V1 tables to V3 schema
4. **Upload Audio**: Move local `.audio/` files to S3
5. **Generate Embeddings**: Run `ml_model/batch_predict.py`
6. **Test**: Verify vote → recommendation → playback flow

## Next Steps

- [ ] Complete Django Supabase connection
- [ ] Implement unmanaged models in Django
- [ ] Configure S3 upload in Django Admin
- [ ] Port V1 routes to use new schema
- [ ] Test end-to-end flow
- [ ] Deploy to production

