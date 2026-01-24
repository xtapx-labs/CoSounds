# V3 Implementation Checklist

## ✅ Completed

- [x] Created V3 folder structure
- [x] Documented architecture (README.md)
- [x] Designed database schema (DATABASE_SCHEMA.sql)
- [x] Created Django integration guide (SUPABASE_INTEGRATION.md)
- [x] Organized existing code into V3 structure

## 🔄 In Progress

### 1. Database Setup
- [ ] Run `DATABASE_SCHEMA.sql` in Supabase SQL Editor
- [ ] Verify all tables created successfully
- [ ] Test `recommend_with_penalty()` function
- [ ] Create test data (1-2 songs, 1 user, 1 player)

### 2. Django (server admin/)
- [ ] Update `src/core/models.py` with unmanaged models
- [ ] Configure `.env` with Supabase `DATABASE_URL`
- [ ] Configure AWS S3 credentials
- [ ] Test database connection: `uv run python src/main.py check`
- [ ] Create Django superuser: `uv run python src/main.py createsuperuser`
- [ ] Update `src/core/admin.py` for Song/Player management
- [ ] Update `src/core/api.py` for Player API endpoints
- [ ] Test S3 upload in Django Admin
- [ ] Test Player API: `GET /api/player/queue`

### 3. Node.js (server user/)
- [ ] Update `.env` with Supabase credentials
- [ ] Update `routes/prefVote.js` to use new schema:
  - Change `preferences` table → `profiles.preference_vector`
  - Update vote insertion to use `votes` table
- [ ] Update `routes/modelRoutes.js`:
  - Change `preferences` query → `profiles.preference_vector`
  - Update recommendation to use `recommend_with_penalty()`
- [ ] Update `routes/session.js` (should work as-is)
- [ ] Update `routes/leaderboard.js` (should work as-is)
- [ ] Test: `npm start` (port 3000)

### 4. React Web (web/)
- [ ] Update `.env` with:
  ```
  VITE_SUPABASE_URL=https://xxx.supabase.co
  VITE_SUPABASE_ANON_KEY=eyJxxx...
  VITE_API_URL=http://localhost:3000
  ```
- [ ] Test Google OAuth login
- [ ] Test voting flow
- [ ] Test session check-in
- [ ] Verify preference updates

### 5. Player (player/)
- [ ] Update `.env` with:
  ```
  DJANGO_API_URL=http://localhost:8000
  PLAYER_TOKEN=<from_django_admin>
  ```
- [ ] Update `src/app/client.py` to poll Django API
- [ ] Test player authentication
- [ ] Test queue polling
- [ ] Test audio playback

### 6. ML Model (ml_model/)
- [ ] Generate embeddings for existing songs
- [ ] Run `batch_predict.py` to populate `songs.embedding`
- [ ] Verify embeddings saved to database

## 🧪 Testing Checklist

### End-to-End Flow
1. [ ] Admin uploads song in Django → S3
2. [ ] ML generates embedding → saves to database
3. [ ] User logs in via Google OAuth
4. [ ] User checks in (creates session)
5. [ ] User votes on song
6. [ ] Preference vector updates
7. [ ] Recommendation engine runs
8. [ ] Song added to player queue
9. [ ] Player polls Django API
10. [ ] Player downloads from S3
11. [ ] Player plays audio
12. [ ] Playback logged to `songs_playing`

### API Endpoints to Test

**Node.js (port 3000)**
- `POST /api/checkin` - Create session
- `POST /api/votes` - Submit vote
- `GET /api/model/recommend` - Get recommendation
- `GET /api/leaderboard` - Monthly leaderboard
- `GET /api/session` - Check session status

**Django (port 8000)**
- `GET /api/player/queue` - Player queue
- `GET /api/player/library` - Player library
- `POST /admin/core/song/add/` - Upload song

## 📋 Migration from V1/V2

### Data Migration Script Needed
```sql
-- Migrate V1 users to V3 profiles
INSERT INTO profiles (id, email, name, display_name, preference_vector, created_at)
SELECT 
  id,
  email,
  name,
  display_name,
  preference::vector(5),  -- Convert from V1 preferences table
  created_at
FROM v1_users;

-- Migrate V1 songs to V3 songs
INSERT INTO songs (id, title, artist, file_url, embedding, created_at)
SELECT
  id,
  title,
  artist,
  's3://bucket/' || file_path,  -- Update with actual S3 URLs
  embedding::vector(5),
  created_at
FROM v1_sounds;

-- Migrate V1 votes to V3 votes
INSERT INTO votes (id, user_id, song_id, vote_value, vote_time)
SELECT 
  gen_random_uuid(),
  user_id,
  song_id,
  vote_value,
  vote_time
FROM v1_vote;
```

## 🚀 Deployment

### Prerequisites
- Supabase project created
- AWS S3 bucket created
- Domain configured (optional)

### Environment Variables (Production)
```bash
# Supabase
DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.com:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_KEY=eyJxxx...

# AWS S3
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_STORAGE_BUCKET_NAME=soundguys-audio
AWS_S3_REGION_NAME=us-east-1

# Django
SECRET_KEY=<generate_with_python_secrets>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Node.js
PORT=3000
NODE_ENV=production
```

### Deployment Steps
1. [ ] Deploy database schema to Supabase
2. [ ] Configure S3 bucket with CORS
3. [ ] Deploy Django to Render/Railway/Fly.io
4. [ ] Deploy Node.js to Render/Railway/Fly.io
5. [ ] Deploy React to Vercel/Netlify
6. [ ] Configure environment variables
7. [ ] Test production flow
8. [ ] Set up monitoring (Sentry, LogRocket)

## 📝 Documentation Updates Needed
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Player setup guide (NFC tag configuration)
- [ ] Admin user manual
- [ ] Troubleshooting guide
- [ ] Architecture diagrams

## 🔒 Security Checklist
- [ ] Enable RLS policies in Supabase
- [ ] Configure HTTPS redirect in Django
- [ ] Add password validators
- [ ] Enable HSTS headers
- [ ] Configure CORS properly
- [ ] Rate limit API endpoints
- [ ] Audit S3 bucket permissions
- [ ] Rotate API keys/tokens
- [ ] Enable Supabase Auth MFA (optional)

## 🎯 Next Immediate Steps

1. **Run Database Schema** (5 min)
   - Copy `DATABASE_SCHEMA.sql` to Supabase SQL Editor
   - Execute and verify tables created

2. **Configure Django** (15 min)
   - Update models.py with unmanaged models
   - Set DATABASE_URL in .env
   - Test connection with `python src/main.py check`

3. **Update Node.js Routes** (30 min)
   - Modify prefVote.js for new schema
   - Update modelRoutes.js for new schema
   - Test with existing V1 frontend

4. **Test End-to-End** (1 hour)
   - Upload a song in Django
   - Vote on it from React
   - Verify recommendation works
   - Test player playback

---

**Estimated Total Implementation Time**: 8-12 hours (for one developer)

**Current Status**: Architecture complete, ready for implementation.

