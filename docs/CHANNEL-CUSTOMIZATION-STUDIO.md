# Channel Customization Studio

## Status and scope

This document defines the product contract for per-channel and per-page customization in Ghost. It is an implementation specification, not evidence that a UI, database model, or generation runtime already exists. The initial delivery should be built incrementally behind a feature flag and must not change publishing behavior until validated.

## Product goal

An operator can select one connected channel/page from a searchable dropdown, choose a content type, write custom instructions, preview the final prompt, generate a draft, and save or restore a profile. One channel's settings must never leak into another channel's job.

Support YouTube channels, Facebook Pages, Instagram accounts, and future platform adapters through a platform-neutral profile model. A connected account must be selected from authorized account records; never trust a user-entered account ID as proof of access.

## Main workspace

1. **Channel selector**: searchable dropdown grouped by platform; show display name, platform, masked account identifier, connection state, and last sync. Only show accounts authorized for the current tenant/user.
2. **Channel profile**: niche, audience, language, tone, brand guide, recurring characters, visual identity, default duration/aspect ratio, research rules, prohibited topics, CTA rules, and quality gates.
3. **Content-type selector**: built-in templates plus custom content types. A custom type is scoped to one channel by default. Explicitly support duplicate/export/share actions rather than silently sharing profiles.
4. **Custom prompt editor**: multi-line prompt editor with version history, validation, unsaved-change warning, and preview of assembled instructions.
5. **Generation settings**: duration, output format, language, voice profile, visual treatment, scene/section structure, references/assets, research mode, and approval mode. Unsupported settings must be disabled with an explanation, not silently ignored.
6. **Prompt preview**: show the resolved profile version, content-type version, one-time override, model/adapter, and policy constraints before generation.
7. **Test generation**: create a draft/test job without publishing. Show outputs and quality-check results.
8. **Save and history**: save profile changes as a new immutable version; allow restore by creating a new version from an older one. Do not erase audit history.
9. **Job history**: show queued/running/retry/needs-review/failed/completed status, job ID, selected profile versions, error category, retry action, and downloadable/exportable draft where supported.

## Profile boundaries and inheritance

Use these layers, in this exact order:

1. **Platform and system safety rules**: authorization, privacy, platform policies, rights checks, budget ceilings, and safety constraints. Not overridable by prompts.
2. **Workspace/global defaults**: common brand or production defaults, if configured.
3. **Channel/page profile**: channel-specific niche, audience, voice, brand, research, visual, and quality defaults.
4. **Content-type profile**: structure and rules for the selected format.
5. **One-time job override**: instructions for the current generation only.
6. **Runtime constraints**: actual model/token limits, provider capabilities, available assets, and output schema validation.

Later layers can refine earlier creative preferences, but cannot weaken security, rights, safety, platform, approval, or budget rules. Resolve conflicts deterministically and show a warning in preview when a lower layer requests a disallowed override.

## Data model

### ChannelProfile
- `profile_id`: stable UUID.
- `tenant_id`: tenant/workspace owner.
- `connected_account_id`: foreign key to an authorized connected account.
- `platform`: enum such as youtube, facebook, instagram, or other supported adapter.
- `display_name`: display-only name copied from authorized account metadata.
- `status`: draft, active, disabled, or needs_review.
- `profile_version`: monotonically increasing version.
- `niche`, `audience`, `language`, `tone`, `brand_guide`.
- `visual_rules`, `voice_profile_ref`, `recurring_character_refs`.
- `default_output`: duration, aspect ratio, resolution, and format where applicable.
- `research_rules`, `rights_rules`, `blocked_topics`, `cta_rules`, `quality_gates`.
- `created_at`, `updated_at`, `created_by`, `change_summary`.

### ContentTypeProfile
- `content_type_id`, `tenant_id`, `owner_profile_id` (nullable only for explicitly shared workspace templates).
- `name`, `description`, `version`, `status`.
- `structure`: sections/scenes, duration allocation, output schema, required fields.
- `creative_rules`, `visual_rules`, `voice_rules`, `research_rules`, `quality_gates`.
- `created_at`, `updated_at`, `created_by`.

### GenerationJob
- `job_id`, `tenant_id`, `connected_account_id`, `profile_id`, `profile_version`.
- `content_type_id`, `content_type_version`, `override_text`, `assembled_prompt_hash`.
- `status`, `idempotency_key`, `created_at`, `updated_at`, `retry_count`.
- `output_refs`, `validation_results`, `error_code`, `error_summary_redacted`.
- Store the minimum necessary prompt/output data under the configured retention policy. Never store provider secrets in profiles or job logs.

### AuditEvent
Record actor, tenant, action, resource ID, resource version, timestamp, and a redacted change summary. Never include secret values or unnecessarily sensitive prompt/output content in audit logs.

## Prompt assembly contract

The runtime should produce a structured prompt package, not just concatenate untrusted strings:

- `system_constraints`: trusted and non-overridable.
- `workspace_defaults`: optional.
- `channel_profile_snapshot`: immutable versioned snapshot.
- `content_type_snapshot`: immutable versioned snapshot.
- `job_override`: optional, limited to the current job.
- `runtime_capabilities`: available output modes and constraints.
- `output_contract`: expected JSON/schema or deliverable format.
- `provenance`: profile IDs/versions and prompt hash.

Treat user prompts, imported documents, and web pages as untrusted content. They may specify creative requirements but cannot issue tool commands, grant permissions, disable policy checks, reveal secrets, or change account identity. Validate the output against the selected content type's schema before accepting a job as successful.

An empty job override is valid and means "use saved settings." A missing or disabled channel profile must never silently fall back to a different channel's profile.

## Content-type builder

A content type should be configurable without code changes for normal creative settings:
- Name and purpose.
- Supported platforms and output formats.
- Target duration and aspect ratio.
- Script/scene/slide structure and timing.
- Hook, explanation, evidence, payoff, and CTA requirements as applicable.
- Voice/language and visual style.
- Asset sourcing and rights requirements.
- Required facts/sources and freshness policy.
- Output schema and quality checks.
- Retry policy and human-review thresholds.

Include examples such as Explainer Short, Cinematic Story, Documentary, Tutorial, Comedy Skit, Carousel/Image Post, and Custom. These are starter templates only; users can create new types. Platform-specific fields must be capability-checked.

## Job workflow

1. Load authorized account list and select the exact account.
2. Load the active channel profile and available content types scoped to that profile.
3. Validate all form values and permissions.
4. Assemble a version-pinned prompt package and display a preview.
5. Create a draft job with an idempotency key.
6. Generate content through approved adapters.
7. Validate structure, completeness, duration constraints, source/rights metadata, and relevant policy gates.
8. If validation fails, mark needs_review or failed with a useful reason; do not claim success or publish partial output.
9. Save draft outputs and validation evidence.
10. Require explicit approval before any external publishing action unless a separately configured and validated policy permits it.
11. Before retrying an irreversible action, read back remote state and check idempotency to avoid duplicate posts.

## Isolation, permissions, and security

- Enforce tenant and connected-account ownership server-side on every read/write; hiding an option in the UI is not authorization.
- Scope profile, content type, asset, voice, job, and history queries by tenant and authorized account.
- Use least-privilege OAuth scopes and official APIs where available.
- Never expose OAuth tokens, API keys, service-role keys, or secret references to the browser or prompt text.
- Sanitize logs and errors. Rate-limit profile edits and generation requests.
- Require confirmation for deleting profiles or changing connected-account bindings.
- Do not auto-publish as a side effect of saving a profile or testing a prompt.
- Keep an audit trail and immutable version snapshots.
- If authorization or profile resolution fails, stop the job rather than guessing.

## Failure behavior

- Account disconnected/unauthorized: block generation and offer reconnect.
- Profile missing/disabled: ask the user to select or restore a valid profile.
- Content type incompatible with platform: block or offer a compatible type.
- Model/provider unavailable: use only a registered, approved fallback that passes the same output contract; otherwise persist the job and report the blocker.
- Quota/budget limit reached: pause or use an explicitly approved lower-cost route; never silently incur cost.
- Output malformed/incomplete: retry within bounded limits if safe, then move to needs_review.
- Asset rights unknown: block the asset or request review.
- Publishing status uncertain: read back remote state before any retry.

## Delivery phases

### Phase 1: specification and fixtures
- Add schema, example profiles/content types, acceptance tests, and documentation.
- Validate examples against schemas in CI when the runtime is introduced.

### Phase 2: persistence and API
- Implement migrations and typed request/response models.
- Add tenant-scoped CRUD, profile versioning, content-type CRUD, and audit events.
- Add tests for authorization and isolation.

### Phase 3: UI
- Build searchable channel dropdown, profile editor, content-type builder, prompt preview, version history, and test generation flow.
- Include loading, empty, disconnected, error, and unsaved-change states.

### Phase 4: generation runtime
- Assemble versioned prompt packages, apply policy gates, validate outputs, and preserve job status/evidence.
- Add retries, idempotency, budget checks, and observability.

### Phase 5: publishing integration
- Keep publishing separate from generation.
- Validate platform permissions, approval gates, read-back, duplicate prevention, and recovery before enabling.

## Definition of done

- [ ] Authorized channels/pages appear in a searchable selector with correct platform identity.
- [ ] Each account has an isolated profile and isolated custom content types by default.
- [ ] Custom prompts can be saved, previewed, versioned, and restored.
- [ ] A one-time override does not mutate the saved profile.
- [ ] Prompt precedence is deterministic and non-overridable safety rules remain enforced.
- [ ] Missing/disabled profiles never borrow another channel's settings.
- [ ] Every job records the exact profile/content-type versions and a prompt hash.
- [ ] Profile and job APIs enforce tenant/account authorization server-side.
- [ ] Malformed output and provider failures create truthful failure states and preserve recoverable work.
- [ ] Test generation cannot publish content.
- [ ] Automated isolation, authorization, schema, versioning, and failure tests pass.
- [ ] Runtime and UI are not described as live until implemented and verified in the target environment.
