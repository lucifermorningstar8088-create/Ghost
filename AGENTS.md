# Repository Engineering Rules

## Mandatory Windows launchers

The repository-root `setup.bat` and `run.bat` are required entry points for Windows users. Keep both files in sync with every change that affects installation, dependencies, environment configuration, service startup, ports, or the local development workflow.

- `setup.bat` must remain the double-click setup entry point and delegate reusable setup logic to maintained scripts under `scripts/windows/`.
- `run.bat` must remain the double-click startup entry point and validate prerequisites before starting services.
- Keep reusable setup, startup, health-check, and test logic in `scripts/windows/`; avoid duplicating complex logic in batch files.
- When a feature adds a required dependency, environment variable, migration prerequisite, service, port, or startup step, update the relevant PowerShell script, root batch launcher, README instructions, and tests in the same change.
- Never silently run destructive migrations, reset databases, publish social content, or trigger paid provider usage during setup/startup.
- Never put provider secrets, database passwords, OAuth client secrets, or Supabase service-role keys in frontend `VITE_*` variables or commit them to source control.
- Before considering a change complete, run configuration checks, API tests, frontend typecheck/build, and startup checks where the environment supports them. Report checks that could not be run; do not claim unexecuted tests passed.
- Every pull request that changes runtime behavior must explicitly confirm whether `setup.bat`, `run.bat`, `scripts/windows/`, and README instructions were updated or verified unaffected.
