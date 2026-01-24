# V1 Original API overview

This is a compact map of server routes under `src/V1 Original/server`.

## Base routes
- `/api/auth` -> Auth/profile endpoints (Bearer JWT)
- `/api` -> Preferences, votes, sessions
- `/api/model` -> Model/data endpoints (no auth enforced in code)
- `/api/leaderboard` -> Leaderboard endpoints
- `/health` -> Health check

## Auth (Bearer JWT)
- `GET /api/auth/profile`
- `POST /api/auth/display-name` (body: `{ display_name }`)

## Preferences (Bearer JWT)
- `GET /api/preferences/exists`
- `GET /api/preferences`
- `POST /api/preferences` (body: `{ preferences: [n,n,n,n,n] }`)

## Votes (Bearer JWT)
- `GET /api/votes` (optional `?song=`)
- `POST /api/votes` (body: `{ song, vote_value }`)
- `PUT /api/votes/:id`
- `DELETE /api/votes/:id`
- `GET /api/current-song` (public)

## Sessions (Bearer JWT)
- `POST /api/checkin`
- `POST /api/extend`
- `POST /api/checkout`
- `GET /api/session`

## Leaderboard
- `GET /api/leaderboard` (public)
- `GET /api/leaderboard/me` (Bearer JWT)

## Model/data (no auth enforced in code)
- `GET /api/model/users`
- `GET /api/model/songs`
- `GET /api/model/preferences`
- `GET /api/model/active-users`
- `GET /api/model/votes`
- `GET /api/model/preferences/:userId`
- `GET /api/model/votes/:userId`
- `GET /api/model/votes/song/:songName`
- `GET /api/model/recommend` (query: `?limit=` optional)
- `POST /api/model/currentSong` (body: `{ song_title }`)
- `GET /api/model/currentSong`

## Health
- `GET /health`
