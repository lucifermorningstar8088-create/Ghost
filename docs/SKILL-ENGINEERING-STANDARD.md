# Ghost Skill Engineering Standard

Each skill must be focused, composable, auditable, versionable, and independently testable. It must not claim tools unavailable in its host.

## Required sections

Mission, triggers, inputs, outputs, workflow, quality gates, failure handling, specialist prompt, evaluation cases, runtime integration notes.

## Status levels

- Specified: instruction file exists.
- Integrated: runtime discovery and authorized tools are wired and verified.
- Tested: evaluation cases have reproducible passing evidence.
- Production-approved: security, rights, reliability, performance, and rollback gates are approved.

Never infer readiness from file presence.