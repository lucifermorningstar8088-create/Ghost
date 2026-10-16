# Database persistence implementation status

## Added in this increment

- SQLAlchemy engine factory for PostgreSQL (including Supabase PostgreSQL connection URLs) and local SQLite tests.
- PostgreSQL driver support through psycopg.
- Initial `channel_profiles` persistence model with a tenant/profile uniqueness constraint.
- Repository operations for create, tenant-filtered list, and tenant-filtered get.
- Unit tests for persistence, tenant isolation at repository level, duplicate IDs, and missing database configuration.

## Important limits

- No database is provisioned or connected by this change.
- No migration tool or migration history has been added yet. `Base.metadata.create_all` is used only in isolated tests; production schema changes must use reviewed migrations.
- Repository functions are not exposed as HTTP endpoints. Do not expose profile routes until authentication, authorization, tenant identity derivation, validation against the canonical profile schema, audit events, and rate limits are implemented.
- Supabase Auth, OAuth, provider credentials, social publishing, and Telegram remain unconnected.
- Configure `DATABASE_URL` only in the server runtime. Never place database passwords or Supabase service-role keys in frontend environment variables.

## Next gates

1. Confirm CI tests pass.
2. Add Alembic migrations and explicit startup/config validation.
3. Add authenticated tenant identity and authorization tests.
4. Add schema-validated profile API routes and connect the UI to them.
5. Verify both local PostgreSQL and a user-provisioned Supabase project before claiming either deployment works.
