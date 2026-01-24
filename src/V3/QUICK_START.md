# V3 Quick Start Guide

## 🚀 Getting Started

### Step 1: Setup Database

1. **Go to Supabase SQL Editor**
2. **Run the schema:**
   ```bash
   # Copy contents of DATABASE_SCHEMA.sql
   # Paste in SQL Editor
   # Click "Run"
   ```

3. **Verify tables created:**
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```
   Should see: `profiles`, `preferences`, `songs`, `votes`, `sessions`, `players`, etc.

---

### Step 2: Configure Environment Variables

Create `env/.env` in project root:

```bash
# Supabase
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Node.js Server
PORT=3000
NODE_ENV=development
```

---

### Step 3: Start Node.js Server (User API)

```bash
cd "src/V3/server user"

# Install dependencies (if not already)
npm install

# Start server
npm start
```

**Expected Output:**
```
Server running on http://localhost:3000
✓ Connected to Supabase
```

---

### Step 4: Test API Endpoints

#### Health Check
```bash
curl http://localhost:3000/health
```

Expected: `{"status":"healthy"}`

#### Test Auth (Get Profile)
First, login via web app to get a JWT token, then:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:3000/api/auth/profile
```

Expected:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "John"
  }
}
```

#### Test Preferences
```bash
# Get preferences
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:3000/api/preferences

# Create/Update preferences
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"preferences": [0.5, 0.8, 0.2, 0.9, 0.4]}' \
  http://localhost:3000/api/preferences
```

#### Test Sessions
```bash
# Check in (create 1-hour session)
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:3000/api/checkin

# Get session status
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:3000/api/session
```

#### Test Model Endpoints
```bash
# Get all songs
curl http://localhost:3000/api/model/songs

# Get all preferences
curl http://localhost:3000/api/model/preferences

# Get active users
curl http://localhost:3000/api/model/active-users

# Get recommendation
curl http://localhost:3000/api/model/recommend?limit=5
```

---

### Step 5: Start React Web App

```bash
cd "src/V3/web"

# Install dependencies (if not already)
npm install

# Create .env file
cat > .env << EOF
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_URL=http://localhost:3000
EOF

# Start dev server
npm run dev
```

**Open:** http://localhost:5173

**Test Flow:**
1. Click "Continue with Google"
2. Login with Google
3. Redirected to preferences survey
4. Submit preferences → Check console for API call
5. Go to Vote page → Submit a vote

---

## 🧪 Testing Checklist

### ✅ Authentication
- [ ] Google OAuth login works
- [ ] JWT token stored in localStorage
- [ ] Profile fetched successfully

### ✅ Preferences
- [ ] GET /api/preferences returns default [0,0,0,0,0]
- [ ] POST /api/preferences updates successfully
- [ ] GET /api/preferences returns updated values

### ✅ Sessions
- [ ] POST /api/checkin creates session
- [ ] GET /api/session returns active session
- [ ] Session expires after 1 hour

### ✅ Votes
- [ ] POST /api/votes inserts into `votes` table
- [ ] Vote triggers preference update (gradient descent)
- [ ] GET /api/votes returns user's votes

### ✅ Model Endpoints
- [ ] GET /api/model/songs returns from `songs` table
- [ ] GET /api/model/preferences returns all user preferences
- [ ] GET /api/model/active-users returns users with active sessions
- [ ] GET /api/model/recommend returns recommendations

### ✅ Leaderboard
- [ ] GET /api/leaderboard returns monthly rankings
- [ ] GET /api/leaderboard/me returns user's stats

---

## 🐛 Troubleshooting

### "Supabase connection failed"
- Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
- Verify Supabase project is active

### "relation does not exist"
- Run `DATABASE_SCHEMA.sql` in Supabase SQL Editor
- Check table names are correct (e.g., `votes` not `vote`)

### "JWT expired" or "Invalid token"
- Re-login to get new JWT token
- Check token is being sent in `Authorization: Bearer <token>` header

### "No users available to compute group preference"
- At least one user needs to have preferences set
- Run `POST /api/preferences` with a test user first

### CORS errors
- Make sure `VITE_API_URL=http://localhost:3000` in web/.env
- Node.js server should have CORS enabled (check `index.js`)

---

## 📝 Next Steps

### Add Test Data

```sql
-- Create a test song (in Supabase SQL Editor)
INSERT INTO songs (title, artist, file_url, type, embedding)
VALUES 
  ('Rain Sounds', 'Nature', 'https://example.com/rain.wav', 'soundscape', '[0.9, 0.1, 0.2, 0.1, 0.8]'),
  ('Jazz Piano', 'Artist', 'https://example.com/jazz.mp3', 'instrumental', '[0.2, 0.3, 0.8, 0.2, 0.4]');
```

### Test Voting Flow

1. Login as User A
2. Check in (create session)
3. Vote on "Rain Sounds" with value 5
4. Check `votes` table - new row should exist
5. Check `preferences` table - preference vector should update
6. Call GET /api/model/recommend - should recommend similar songs

---

## 🎯 Current Status

✅ **Completed:**
- Database schema created
- Node.js routes updated (`vote` → `votes`)
- Preferences API working
- Sessions API working
- Model endpoints updated

⏳ **Next:**
- Add test songs to database
- Test full voting flow
- Setup Django admin
- Configure player API

---

## 📞 API Reference

See `API_OVERVIEW.md` for complete endpoint documentation.

**Base URL:** http://localhost:3000

**Auth Header:** `Authorization: Bearer <jwt_token>`

**Key Endpoints:**
- `POST /api/checkin` - Create session
- `GET /api/preferences` - Get user preferences
- `POST /api/votes` - Submit vote
- `GET /api/model/recommend` - Get recommendations
- `GET /api/leaderboard` - Monthly rankings

