# Channel & Pages Connection Center

## Implemented API foundation

- Tenant-scoped connection records for YouTube, Facebook Pages, Instagram, TikTok, X, Telegram and generic providers.
- The Integrations screen is wired to the authenticated API for manual credential storage, listing, testing and disconnecting.
- Credentials are encrypted with Fernet using the server-only `GHOST_SECRET_ENCRYPTION_KEY`; API responses never return credential material.
- Telegram `getMe` and X `/2/users/me` perform live verification. Providers without an implemented live adapter remain unverified and return HTTP 501 on test rather than being falsely marked connected.
- Credentials are rejected in metadata. All records are scoped to the verified tenant claim.

## Required setup

Generate a stable key and configure it in the API process environment:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set `GHOST_SECRET_ENCRYPTION_KEY` only in the server environment. Never commit it or place it in a `VITE_*` variable. Back up the key securely; changing or losing it prevents decrypting existing credentials.

Database defaults to local SQLite when `DATABASE_URL` is unset. Apply migration `0005_social_connections` deliberately after reviewing/backing up the database.

## API

- `GET /api/v1/connections`: list safe metadata and status.
- `POST /api/v1/connections`: store encrypted manual credentials. Fields: `platform`, `label`, `method`, `credentials`, optional non-secret `metadata` and `permissions`.
- `POST /api/v1/connections/{connection_id}/test`: live test where an adapter exists.
- `DELETE /api/v1/connections/{connection_id}`: remove credentials and the connection record.

Every endpoint requires a verified Ghost bearer token and tenant assignment. Provider API access, app registration, platform review and permission grants remain necessary.

## Known gaps, not production-ready

OAuth authorization/callback/token refresh is not implemented for YouTube, Meta, TikTok or X. Facebook/Instagram page discovery and YouTube channel discovery require provider-specific OAuth scopes and adapters. TikTok and Meta verification adapters are not yet live. Telegram and X have live verification only; this is not equivalent to publishing support. Do not treat saved credentials as a verified connection or use this foundation as proof that publishing works.
