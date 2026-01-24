# V2 Slop API overview

This is a compact map of server routes under `src/V2 Slop/server/src`. It lists the public HTTP entry points and their base paths.

## Base routes (config)
- `/api/` -> Core API (Django Ninja)
- `/voter/` -> Voting + auth UI (Django views / HTMX)
- `/upload/` -> django-file-form upload routes
- `/admin/` -> Django admin

## Core API (Django Ninja)
Base path: `/api/core`
- `GET /client/list`
  - Auth: HTTP Basic (username/password)
  - Returns: PlayerAccount list
- `GET /player/list`
  - Auth: `X-API-Key: account_{pk}` (PlayerAccount pseudo-token)
  - Returns: Players for that account
- `GET /player/library?player={player_token}`
  - Auth: `X-API-Key` (player token or `account_{pk}`)
  - Returns: sounds in the player's library
- `GET /cosound?player={player_token}`
  - Auth: `X-API-Key` (player token or `account_{pk}`)
  - Returns: current cosound payload (soundscapes + instrumental)

## Voter routes (Django views)
Base path: `/voter`
- `GET /vote/?player_token=...&choice=true|false`
  - Voting page; creates a vote for logged-in users
- `GET /htmx/auth/options/`
  - HTMX auth modal options partial
- `GET|POST /htmx/login/email/`
  - HTMX login step 1 (email)
- `GET|POST /htmx/login/code/`
  - HTMX login step 2 (code)
- `POST /guest/login/`
  - Create a guest user + login
- `/login/`, `/verify/`, `/logout/`
  - django-allauth auth endpoints
- `/signup/`, `/signin/`
  - Redirects to login code request

## Upload routes
Base path: `/upload`
- Provided by `django_file_form` (see that package for exact paths)
