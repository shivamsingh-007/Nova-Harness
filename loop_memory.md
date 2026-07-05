# Loop Memory

## Current Mission
Build user authentication feature (auth model + JWT).

## Last Successful Progress
- Iteration 2: JWT generation implemented and verified (all tests PASS).

## Current Blocker
- None.

## Top 3 Open Tasks
1. `task-auth-003` — Token refresh endpoint
2. `task-auth-004` — Login rate limiting
3. `task-db-002` — Session table migration

## Recent Failed Attempts
- None this session.

## Lessons to Honor Next Run
- bcrypt cost factor 12 for password hashing.
- JWT default expiry: 1 hour.
- Always dry-run migrations before applying.

## Exact Next Action
Implement token refresh endpoint (`/auth/refresh`) with rotation.
