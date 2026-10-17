# Supabase browser sign-in setup

The web app supports passwordless email magic-link sign-in through Supabase Auth.

## Frontend environment

Copy `apps/web/.env.example` to `apps/web/.env.local` and set:

- `VITE_SUPABASE_URL`: your Supabase project URL.
- `VITE_SUPABASE_ANON_KEY`: the public anon/publishable key.
- `VITE_GHOST_API_URL`: the Ghost API base URL.

Only public client values belong in `VITE_*` variables. Never put a service-role key, database password, social OAuth secret, or provider API key in the browser.

## Supabase dashboard

1. Enable the Email provider in Authentication.
2. Add the local origin (usually `http://localhost:5173`) and deployed web origin to Authentication URL Configuration's allowed redirect URLs.
3. Set the Site URL to the deployed app origin before production.
4. Configure email link delivery/templates and suitable rate limits.

Supabase JS manages the browser session. Ghost does not manually copy access tokens into local storage.

## API tenant authorization

Successful sign-in alone does not grant access to tenant-scoped profile endpoints. The API requires a verified access token with `app_metadata.tenant_id` assigned by a trusted server-side administrative workflow. Never set tenant membership from user-editable metadata or a browser request. Follow `apps/api/docs/AUTHENTICATION.md` and test against the real project before enabling profile CRUD.

The Channels & Profiles screen now includes a separate Saved profiles panel that lists, creates, edits, and deletes records through `profileApi.ts` using the active Supabase access token. The older channel cards remain local demo data and are not database-backed. Live profile CRUD still requires a configured Supabase project, trusted server-side `app_metadata.tenant_id`, a reachable Ghost API, and a migrated database.
