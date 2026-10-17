# Supabase browser sign-in setup

The web app's Supabase browser auth foundation reads only these public variables:

- `VITE_SUPABASE_URL`: the Supabase project URL.
- `VITE_SUPABASE_ANON_KEY`: the project's public anon/publishable key.

Copy `apps/web/.env.example` to `.env.local` for local development and fill in these public values. Do not commit real environment files. Never use a Supabase service-role key or database password in a `VITE_*` variable: browser variables are shipped to every visitor.

## Supabase dashboard

1. Open Authentication → URL Configuration.
2. Set the Site URL to the deployed web app origin.
3. Add each trusted local/deployed origin to the Redirect URLs allowlist.
4. Configure email OTP/magic-link delivery and templates.
5. Configure the API backend separately with `SUPABASE_URL` and its database settings as described in `apps/api/docs/AUTHENTICATION.md`.

The browser helper uses Supabase's SDK session handling and exposes functions to request an email magic link, read the current session, observe session changes, and sign out. It does not accept a tenant ID or elevate privileges.

## Important integration boundary

This PR adds the authentication client foundation only. It does not yet gate the operations UI, connect sign-in controls, or replace local preview profile state with API-backed state. The next UI integration must pass the current session's access token to the typed profile API client. The backend remains authoritative for JWT verification and tenant scope, sourced from verified `app_metadata.tenant_id`. Assign tenant membership only through a trusted server-side administrative workflow.

A configured browser client does not prove the backend issuer/JWKS, tenant assignment, database migration, or deployed CORS settings are correct. Verify those against the real project before production use.
