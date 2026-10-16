# API authentication foundation

The API uses Supabase-issued JWT access tokens. Configure these **backend-only** environment variables:

- `SUPABASE_URL`: project URL, for example `https://your-project.supabase.co`.
- `SUPABASE_JWKS_URL`: optional override for the project's JWKS endpoint.
- `SUPABASE_JWT_ISSUER`: optional issuer override; defaults to `{SUPABASE_URL}/auth/v1`.
- `SUPABASE_JWT_AUDIENCE`: expected audience; defaults to `authenticated`.

The verifier accepts asymmetric ES256/RS256 tokens only, checks the signature using the configured JWKS, and validates issuer, audience, expiry, and subject. It fails closed when auth is unconfigured. Tenant identity is taken only from verified `app_metadata.tenant_id`; users without a tenant assignment are denied.

## Tenant assignment

Populate `app_metadata.tenant_id` only through trusted server-side administrative workflows. Do not put tenant membership in user-editable `user_metadata`, and do not trust tenant IDs supplied in request bodies, query parameters, or headers. Configure row-level security as an additional boundary if direct database access is enabled.

## Current scope

This adds a reusable authenticated-principal dependency and tests. It does not yet protect business endpoints because profile CRUD routes are not exposed in this change. It does not provision Supabase, create users, assign tenants, or store any credentials. Validate issuer and signing-key behavior against your own Supabase project before production use.
