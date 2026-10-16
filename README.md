# Ghost

Ghost is an AI-powered social media growth and revenue operations platform in planning for YouTube, Facebook, and Instagram.

## Skill library

The repository now contains a planned library of **200 specialist skill specifications**, organized as 25 domain packs under [skills/packs](skills/packs/) and indexed in [CATALOG.md](CATALOG.md). Each skill has a unique ID and a detailed mission, triggers, inputs/outputs, workflow, quality gates, failure handling, specialist prompt, evaluation cases, and runtime integration notes.

## Engineering standards

- Evidence before claims; distinguish measured results from estimates.
- Account isolation, least privilege, secure secrets, platform terms, and user consent.
- Free-first resource policy; never silently trigger paid services.
- Independent quality gates, bounded retries, auditable changes, and human escalation for unresolved high-risk actions.
- No promises of virality, monetization approval, or guaranteed revenue.

## Validation and implementation

See [quality gates](docs/QUALITY-GATES.md), [validation matrix](tests/VALIDATION-MATRIX.md), [skill engineering standard](docs/SKILL-ENGINEERING-STANDARD.md), and [integration roadmap](docs/INTEGRATION-ROADMAP.md).

**Important:** these files are detailed instructions, not executable workers. Runtime adapters, platform permissions, end-to-end tests, and benchmarks must be verified before production claims.
