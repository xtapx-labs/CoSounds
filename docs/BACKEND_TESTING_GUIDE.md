# Backend Testing Guide: Display Name & Leaderboard

## Test Environment Setup

### Prerequisites
- Backend server running on `http://localhost:3000`
- Database migration completed (display_name column added)
- Valid JWT token for authenticated requests
- Test user account created

### Get a JWT Token
```bash
# Login via your auth flow and extract the JWT token
# Store it in an environment variable for easy testing
$JWT = "your-jwt-token-here"
```

---

## Test Suite 1: Display Name Endpoints

### Test 1.1: Set Display Name (Success)

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT"; "Content-Type" = "application/json" } `
  -Body '{"display_name":"TestUser123"}'
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "message": "Display name updated",
  "data": {
    "id": "user-uuid",
    "email": "test@example.com",
    "name": "Test User",
    "display_name": "TestUser123"
  }
}
```

**Validation:**
- ✅ Status code: 200
- ✅ Response has `success: true`
- ✅ `data.display_name` equals "TestUser123"

---

### Test 1.2: Set Display Name (Empty - Should Fail)

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT"; "Content-Type" = "application/json" } `
  -Body '{"display_name":""}' `
  -ErrorAction Stop
```

**Expected Response (400 Bad Request):**
```json
{
  "error": "Display name required"
}
```

**Validation:**
- ✅ Status code: 400
- ✅ Error message indicates empty name not allowed

---

### Test 1.3: Set Display Name (Too Long - Should Fail)

**Request:**
```powershell
$longName = "A" * 51  # 51 characters
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT"; "Content-Type" = "application/json" } `
  -Body "{`"display_name`":`"$longName`"}" `
  -ErrorAction Stop
```

**Expected Response (400 Bad Request):**
```json
{
  "error": "Display name too long (max 50 characters)"
}
```

**Validation:**
- ✅ Status code: 400
- ✅ Error indicates max length exceeded

---

### Test 1.4: Set Display Name (No Auth - Should Fail)

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"display_name":"TestUser"}' `
  -ErrorAction Stop
```

**Expected Response (401 Unauthorized):**
```json
{
  "error": "Authentication required"
}
```

**Validation:**
- ✅ Status code: 401
- ✅ Requires authentication

---

### Test 1.5: Update Existing Display Name

**Request:**
```powershell
# First set
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT"; "Content-Type" = "application/json" } `
  -Body '{"display_name":"FirstName"}'

# Then update
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT"; "Content-Type" = "application/json" } `
  -Body '{"display_name":"SecondName"}'
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "message": "Display name updated",
  "data": {
    "display_name": "SecondName"
  }
}
```

**Validation:**
- ✅ Display name successfully updated
- ✅ Old value overwritten

---

### Test 1.6: Get Profile Includes Display Name

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/profile" `
  -Method GET `
  -Headers @{ "Authorization" = "Bearer $JWT" }
```

**Expected Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "test@example.com",
  "name": "Test User",
  "display_name": "TestUser123"
}
```

**Validation:**
- ✅ Response includes `display_name` field
- ✅ Value matches last set display name
- ✅ Returns `null` if never set

---

## Test Suite 2: Leaderboard Endpoints

### Test 2.1: Get Leaderboard (Public - No Auth)

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard" `
  -Method GET
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "month": "November 2025",
  "count": 3,
  "data": [
    {
      "user_id": "uuid-1",
      "display_name": "TopVoter",
      "total_votes": 100,
      "positive_votes": 75,
      "negative_votes": 25
    },
    {
      "user_id": "uuid-2",
      "display_name": "SecondPlace",
      "total_votes": 85,
      "positive_votes": 60,
      "negative_votes": 25
    }
  ]
}
```

**Validation:**
- ✅ Status code: 200
- ✅ No authentication required
- ✅ Returns array sorted by total_votes (descending)
- ✅ Max 10 entries
- ✅ Correct month displayed
- ✅ `positive_votes + negative_votes ≤ total_votes`

---

### Test 2.2: Leaderboard Shows Display Names

**Setup:** Create votes for users with and without display names

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard" `
  -Method GET
```

**Validation:**
- ✅ Users with `display_name` set: Shows display_name
- ✅ Users without `display_name`: Shows first name from Google name
- ✅ Users with no name at all: Shows "Anonymous"

---

### Test 2.3: Leaderboard Only Shows Current Month

**Setup:** Create votes with different timestamps

**Test Data:**
```sql
-- Current month vote
INSERT INTO vote (user_id, song, vote_value, vote_time)
VALUES ('test-user', 'Song A', 1, NOW());

-- Previous month vote
INSERT INTO vote (user_id, song, vote_value, vote_time)
VALUES ('test-user', 'Song B', 1, NOW() - INTERVAL '1 month');
```

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard" `
  -Method GET
```

**Validation:**
- ✅ Only counts votes from current calendar month
- ✅ Previous month's votes excluded
- ✅ Vote counts reflect current month only

---

### Test 2.4: Leaderboard Vote Counting

**Setup:** Create specific votes for a test user

**Test Data:**
```sql
-- User: test-user
-- 3 positive votes, 2 negative votes
INSERT INTO vote (user_id, song, vote_value, vote_time)
VALUES 
  ('test-user', 'Song 1', 1, NOW()),  -- Positive
  ('test-user', 'Song 2', 1, NOW()),  -- Positive
  ('test-user', 'Song 3', -1, NOW()), -- Negative
  ('test-user', 'Song 4', 1, NOW()),  -- Positive
  ('test-user', 'Song 5', -1, NOW()); -- Negative
```

**Request:**
```powershell
$leaderboard = Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard" -Method GET
$testUser = $leaderboard.data | Where-Object { $_.user_id -eq 'test-user' }
```

**Expected:**
```json
{
  "user_id": "test-user",
  "display_name": "TestUser",
  "total_votes": 5,
  "positive_votes": 3,
  "negative_votes": 2
}
```

**Validation:**
- ✅ `total_votes` = 5
- ✅ `positive_votes` = 3 (vote_value > 0)
- ✅ `negative_votes` = 2 (vote_value < 0)
- ✅ Math: 3 + 2 = 5 ✓

---

### Test 2.5: Leaderboard Sorting

**Setup:** Create users with different vote counts

**Test Data:**
```sql
-- User A: 10 votes
-- User B: 25 votes
-- User C: 15 votes
```

**Request:**
```powershell
$leaderboard = Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard" -Method GET
```

**Validation:**
- ✅ Order: User B (25), User C (15), User A (10)
- ✅ Sorted by total_votes descending
- ✅ Ranking preserved in array order

---

### Test 2.6: Get My Stats (Authenticated)

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard/me" `
  -Method GET `
  -Headers @{ "Authorization" = "Bearer $JWT" }
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "month": "November 2025",
  "data": {
    "user_id": "your-uuid",
    "display_name": "YourDisplayName",
    "total_votes": 42,
    "positive_votes": 30,
    "negative_votes": 12
  }
}
```

**Validation:**
- ✅ Status code: 200
- ✅ Returns current user's stats only
- ✅ Counts match actual votes in database
- ✅ Correct month displayed

---

### Test 2.7: My Stats Without Auth (Should Fail)

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard/me" `
  -Method GET `
  -ErrorAction Stop
```

**Expected Response (401 Unauthorized):**
```json
{
  "error": "Authentication required"
}
```

**Validation:**
- ✅ Status code: 401
- ✅ Requires authentication

---

### Test 2.8: My Stats with No Votes

**Setup:** User with no votes this month

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard/me" `
  -Method GET `
  -Headers @{ "Authorization" = "Bearer $JWT" }
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "month": "November 2025",
  "data": {
    "user_id": "your-uuid",
    "display_name": "YourDisplayName",
    "total_votes": 0,
    "positive_votes": 0,
    "negative_votes": 0
  }
}
```

**Validation:**
- ✅ Returns zeros instead of error
- ✅ User still gets their stats

---

## Test Suite 3: Edge Cases

### Test 3.1: Duplicate Display Names

**Setup:** Set same display name for multiple users

```powershell
# User 1
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT1"; "Content-Type" = "application/json" } `
  -Body '{"display_name":"MusicFan"}'

# User 2 (different JWT)
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT2"; "Content-Type" = "application/json" } `
  -Body '{"display_name":"MusicFan"}'
```

**Validation:**
- ✅ Both succeed (no unique constraint)
- ✅ Leaderboard can show multiple "MusicFan" entries
- ✅ Distinguished by user_id in frontend

---

### Test 3.2: Special Characters in Display Name

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT"; "Content-Type" = "application/json" } `
  -Body '{"display_name":"Music🎵Fan"}'
```

**Validation:**
- ✅ Accepts emoji and special characters
- ✅ Stores and retrieves correctly
- ✅ Displays in leaderboard properly

---

### Test 3.3: Whitespace Handling

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT"; "Content-Type" = "application/json" } `
  -Body '{"display_name":"  TestUser  "}'
```

**Expected:**
- ✅ Trimmed to "TestUser" (no leading/trailing spaces)
- ✅ Stored as "TestUser"

---

### Test 3.4: Leaderboard with No Votes

**Setup:** Empty vote table for current month

**Request:**
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard" -Method GET
```

**Expected Response:**
```json
{
  "success": true,
  "month": "November 2025",
  "count": 0,
  "data": []
}
```

**Validation:**
- ✅ Returns empty array
- ✅ No error
- ✅ Count is 0

---

## Test Suite 4: Integration Tests

### Test 4.1: Full User Flow

**Scenario:** New user sets display name and votes

```powershell
# 1. Login (get JWT)
$JWT = "new-user-jwt"

# 2. Check profile (no display name yet)
$profile = Invoke-RestMethod -Uri "http://localhost:3000/api/auth/profile" `
  -Headers @{ "Authorization" = "Bearer $JWT" }
# Expect: display_name = null

# 3. Set display name
Invoke-RestMethod -Uri "http://localhost:3000/api/auth/display-name" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT"; "Content-Type" = "application/json" } `
  -Body '{"display_name":"NewUser"}'

# 4. Create some votes
Invoke-RestMethod -Uri "http://localhost:3000/api/votes" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $JWT"; "Content-Type" = "application/json" } `
  -Body '{"song":"Song A","vote_value":1}'

# 5. Check my stats
$stats = Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard/me" `
  -Headers @{ "Authorization" = "Bearer $JWT" }
# Expect: display_name = "NewUser", total_votes = 1

# 6. Check leaderboard
$leaderboard = Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard"
# Expect: "NewUser" appears in leaderboard
```

**Validation:**
- ✅ Complete flow works end-to-end
- ✅ Display name persists across endpoints
- ✅ Votes counted correctly
- ✅ Appears in leaderboard

---

### Test 4.2: Privacy Verification

**Setup:** User with Google name but no display name

**Request:**
```powershell
$leaderboard = Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard"
```

**Validation:**
- ✅ Full Google name NOT shown (only first name)
- ✅ Email NOT exposed
- ✅ user_id shown (safe, just UUID)

---

## Automated Test Script

Save as `Test-LeaderboardAPI.ps1`:

```powershell
param(
    [string]$BaseUrl = "http://localhost:3000",
    [Parameter(Mandatory=$true)]
    [string]$JWT
)

$ErrorActionPreference = "Stop"
$headers = @{ 
    "Authorization" = "Bearer $JWT"
    "Content-Type" = "application/json"
}

Write-Host "🧪 Testing Display Name & Leaderboard API" -ForegroundColor Cyan
Write-Host ""

# Test 1: Set Display Name
Write-Host "Test 1: Setting display name..." -ForegroundColor Yellow
$result = Invoke-RestMethod -Uri "$BaseUrl/api/auth/display-name" `
    -Method POST -Headers $headers `
    -Body '{"display_name":"AutoTest"}'

if ($result.success) {
    Write-Host "✅ Display name set successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to set display name" -ForegroundColor Red
}

# Test 2: Get Profile
Write-Host "Test 2: Getting profile..." -ForegroundColor Yellow
$profile = Invoke-RestMethod -Uri "$BaseUrl/api/auth/profile" `
    -Headers $headers

if ($profile.display_name -eq "AutoTest") {
    Write-Host "✅ Profile includes display name" -ForegroundColor Green
} else {
    Write-Host "❌ Display name not in profile" -ForegroundColor Red
}

# Test 3: Get Leaderboard (Public)
Write-Host "Test 3: Getting leaderboard..." -ForegroundColor Yellow
$leaderboard = Invoke-RestMethod -Uri "$BaseUrl/api/leaderboard"

if ($leaderboard.success) {
    Write-Host "✅ Leaderboard retrieved (public)" -ForegroundColor Green
    Write-Host "   Top voter: $($leaderboard.data[0].display_name) with $($leaderboard.data[0].total_votes) votes" -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to get leaderboard" -ForegroundColor Red
}

# Test 4: Get My Stats
Write-Host "Test 4: Getting my stats..." -ForegroundColor Yellow
$stats = Invoke-RestMethod -Uri "$BaseUrl/api/leaderboard/me" `
    -Headers $headers

if ($stats.success) {
    Write-Host "✅ My stats retrieved" -ForegroundColor Green
    Write-Host "   Your votes: $($stats.data.total_votes)" -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to get stats" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 All tests completed!" -ForegroundColor Cyan
```

**Usage:**
```powershell
.\Test-LeaderboardAPI.ps1 -JWT "your-jwt-token-here"
```

---

## Performance Testing

### Load Test: Leaderboard Endpoint

```powershell
# Test response time with concurrent requests
1..10 | ForEach-Object -Parallel {
    $start = Get-Date
    Invoke-RestMethod -Uri "http://localhost:3000/api/leaderboard"
    $end = Get-Date
    ($end - $start).TotalMilliseconds
} | Measure-Object -Average -Maximum -Minimum

# Expected: 
# - Average: < 100ms
# - Maximum: < 500ms
```

---

## Test Data Cleanup

After testing, clean up test data:

```sql
-- Remove test display names
UPDATE profiles 
SET display_name = NULL 
WHERE display_name LIKE 'Test%' OR display_name = 'AutoTest';

-- Remove test votes (optional)
DELETE FROM vote 
WHERE user_id IN (SELECT id FROM profiles WHERE email LIKE 'test%');
```

---

## Checklist: Pre-Deployment Testing

- [ ] All Test Suite 1 tests pass (Display Name)
- [ ] All Test Suite 2 tests pass (Leaderboard)
- [ ] All Test Suite 3 tests pass (Edge Cases)
- [ ] Integration tests complete successfully
- [ ] Automated test script runs without errors
- [ ] Performance acceptable (< 100ms avg)
- [ ] Error responses include helpful messages
- [ ] No sensitive data leaked in responses
- [ ] RLS policies enforced correctly
- [ ] Database migration completed
- [ ] API documentation reviewed and accurate

---

**Happy Testing! 🧪**
