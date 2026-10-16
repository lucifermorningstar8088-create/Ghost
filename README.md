# Ghost

Ghost is an AI-powered social media growth and revenue operations platform in planning for YouTube, Facebook, and Instagram.

## Skill library

The repository contains a planned library of **200 specialist skill specifications**, organized as 25 domain packs under [skills/packs](skills/packs/) and indexed in [CATALOG.md](CATALOG.md). Each skill has a unique ID and a detailed mission, triggers, inputs/outputs, workflow, quality gates, failure handling, specialist prompt, evaluation cases, and runtime integration notes.

## Channel Customization Studio

- [Studio specification](docs/CHANNEL-CUSTOMIZATION-STUDIO.md) defines channel/page dropdown selection, independent profiles, custom prompts, content-type builder, prompt preview, version history, test generation, job lifecycle, access control, and delivery phases.
- [Channel profile JSON Schema](config/channel-profile.schema.json) defines the versioned channel/page configuration contract.
- [Content type JSON Schema](config/content-type.schema.json) defines reusable, configurable content formats.
- [Example channel profiles](config/channel-profiles.example.yaml) and [example content types](config/content-types.example.yaml) are illustrative fixtures, not connected accounts or active production settings.
- [Channel customization acceptance matrix](tests/CHANNEL-CUSTOMIZATION-ACCEPTANCE.md) defines isolation, authorization, versioning, prompt precedence, failure, and publishing-boundary tests.

Design rule: system safety, permissions, platform policy, rights checks, and budget constraints cannot be overridden by channel prompts. Channel profiles and content types are isolated by default; one-time prompt overrides affect only the current job. Test generation must never publish.

## Configuration validation and implementation backlog

- [Consolidated implementation backlog](docs/IMPLEMENTATION-BACKLOG.md) separates completed specifications from the remaining API, UI, runtime, testing, and publishing work.
- [Configuration validation script](scripts/validate_configs.py) checks JSON Schemas, example YAML fixtures, cross-references, and the proposed tool registry.
- [Development validation dependencies](requirements-dev.txt) and [GitHub Actions workflow](.github/workflows/validate-configs.yml) run those checks on pull requests and pushes. A successful run must be observed before claiming CI validation passed.

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

**Important:** skill, tool, and customization files currently define specifications and examples, not a fully implemented runtime or UI. Runtime adapters, database migrations, platform permissions, executable automated tests, end-to-end tests, fallback drills, and benchmarks must be implemented and verified before production claims.
