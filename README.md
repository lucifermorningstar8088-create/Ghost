# Ghost

Ghost is an AI-powered social media growth and revenue operations platform in planning for YouTube, Facebook, and Instagram.

## Skill library

The repository contains a planned library of **200 specialist skill specifications**, organized as 25 domain packs under [skills/packs](skills/packs/) and indexed in [CATALOG.md](CATALOG.md). Each skill has a unique ID and a detailed mission, triggers, inputs/outputs, workflow, quality gates, failure handling, specialist prompt, evaluation cases, and runtime integration notes.

## Tool coverage and reliability

- [Tool coverage and fallback standard](docs/TOOL-COVERAGE-AND-FALLBACK.md) defines critical capabilities, primary routes, fallback routes, safe-stop behavior, security, and readiness gates.
- [Machine-readable tool inventory](config/tools.yaml) lists proposed capability routes and implementation records.
- Tool entries marked proposed are planning records, not proof of an installed, authenticated, tested, or production-ready integration.

## Engineering standards

- Evidence before claims; distinguish measured results from estimates.
- Account isolation, least privilege, secure secrets, platform terms, and user consent.
- Free-first resource policy; never silently trigger paid services.
- Independent quality gates, bounded retries, auditable changes, and human escalation for unresolved high-risk actions.
- No promises of virality, monetization approval, or guaranteed revenue.
- Progressive tool discovery: load only the tools needed for a task rather than flooding every model call with every schema.

## Validation and implementation

See [quality gates](docs/QUALITY-GATES.md), [validation matrix](tests/VALIDATION-MATRIX.md), [skill engineering standard](docs/SKILL-ENGINEERING-STANDARD.md), and [integration roadmap](docs/INTEGRATION-ROADMAP.md).

**Important:** skill and tool files are specifications, not executable workers. Runtime adapters, platform permissions, end-to-end tests, fallback drills, and benchmarks must be verified before production claims.
