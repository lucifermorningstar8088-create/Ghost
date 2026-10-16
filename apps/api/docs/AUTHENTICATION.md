# API authentication

The API uses Supabase-issued JWT access tokens. Configure these **backend-only** environment variables:

- `SUPABASE_URL`: project URL, for example `https://your-project.supabase.co`.
- `SUPABASE_JWKS_URL`: optional override for the project's JWKS endpoint.
- `SUPABASE_JWT_ISSUER`: optional issuer override; defaults to `{SUPABASE_URL}/auth/v1`.
- `SUPABASE_JWT_AUDIENCE`: expected audience; defaults to `authenticated`.

The verifier accepts asymmetric ES256/RS256 tokens only, checks the signature using the configured JWKS, and validates issuer, audience, expiry, and subject. Missing auth configuration returns HTTP 503. Invalid or expired tokens return HTTP 401. A JWKS endpoint connection failure returns HTTP 503 because the provider is temporarily unavailable, not because the token has been proven invalid. Tenant identity is taken only from verified `app_metadata.tenant_id`; users without a tenant assignment are denied with HTTP 403.

## Tenant assignment

Populate `app_metadata.tenant_id` only through trusted server-side administrative workflows. Do not put tenant membership in user-editable `user_metadata`, and do not trust tenant IDs supplied in request bodies, query parameters, or headers. Profile CRUD routes derive tenant scope from the verified principal. Configure row-level security as an additional boundary if direct database access is enabled.

## Production checklist

- Set the real Supabase project URL and issuer/JWKS settings in the backend environment.
- Ensure trusted server-side workflows assign `app_metadata.tenant_id` before users call tenant-scoped routes.
- Verify the signing algorithm and issuer against the target Supabase project; do not disable signature, issuer, audience, or expiry checks.
- Keep database credentials and any service-role key backend-only. Never put secrets in frontend `VITE_*` variables or commit them to Git.
- Test authentication against the real project in a controlled environment before production use.

This code does not provision Supabase, create users, assign tenants, or store credentials. Automated tests mock token verification and do not prove that a live Supabase project is configured correctly.
