# Channel Customization Acceptance Matrix

Status: planned acceptance criteria. These are not claims that automated tests currently exist or pass.

| ID | Scenario | Expected result |
|---|---|---|
| CH-001 | User loads connected accounts | Only authorized accounts in the current tenant are selectable |
| CH-002 | User selects a channel | Its own profile and content types load; no other channel's values appear |
| CH-003 | User changes prompt and saves | New immutable profile version is created and audit event is recorded |
| CH-004 | User adds one-time override | Current job changes; saved profile remains byte-for-byte unchanged |
| CH-005 | User previews prompt | Preview shows global constraints, profile/content type versions, override, output contract, and prompt hash |
| CH-006 | Prompt asks to ignore security or disclose secrets | System constraints remain enforced; unsafe instruction is rejected or ignored with an observable warning |
| CH-007 | Selected profile is missing or disabled | Job is blocked with a clear reason; no other profile is used as a fallback |
| CH-008 | Content type belongs to another channel | It is unavailable unless explicitly shared and authorized |
| CH-009 | Content type is unsupported on selected platform | Generation is blocked or user is offered a compatible type |
| CH-010 | Output misses required sections or is truncated | Job is not marked successful; bounded retry or needs_review is used |
| CH-011 | Provider fails or quota is exhausted | Approved fallback is used only if contract-compatible; otherwise job is preserved with blocker details |
| CH-012 | User clicks test generation | A draft/test job runs and cannot publish |
| CH-013 | Two jobs use different profile versions | Each job retains its own immutable profile/content type snapshot |
| CH-014 | User restores an older profile version | A new version is created from that snapshot; history remains intact |
| CH-015 | User attempts cross-tenant profile access | Server rejects request regardless of UI state |
| CH-016 | Account authorization expires | Generation and publishing are blocked until reconnect/reauthorization |
| CH-017 | Retry after uncertain publish result | Remote state is read back and idempotency checked before retry |
| CH-018 | Secret or token appears in an exception | Redaction prevents secret from being persisted or displayed |
| CH-019 | User saves a profile without a custom prompt | Valid defaults are used; no stale prompt from another job is reused |
| CH-020 | User duplicates a content type | New type is independently versioned and scoped to the target profile |
| CH-021 | Profile edit races with generation | Job uses one consistent version snapshot, not a mixed set of fields |
| CH-022 | Profile delete is requested | Confirmation and retention/audit policy apply; referenced jobs remain explainable |
| CH-023 | Invalid schema or extra unrecognized fields submitted | Request is rejected with a field-level validation message |
| CH-024 | Generation has incomplete voiceover or scene plan | Quality gate fails; partial output is not presented as final |
| CH-025 | Save or network operation fails | UI preserves unsaved user text and reports failure without false success |

## Minimum automated test groups

1. Schema validation for both JSON schemas and example fixtures.
2. Unit tests for prompt precedence and protected system constraints.
3. Tenant/account authorization tests for every profile/content-type/job endpoint.
4. Isolation tests that deliberately alternate between two accounts and compare profile IDs, prompt hashes, and output metadata.
5. Versioning tests for save, restore, duplicate, and concurrent edits.
6. Job lifecycle tests for queued, running, retry, needs_review, failed, and completed states.
7. Failure injection for timeouts, rate limits, invalid provider output, expired authorization, and quota ceilings.
8. UI tests for channel selection, empty/disconnected states, unsaved changes, preview, and test-generation non-publishing.
9. Integration tests against mocked platform/model adapters before any live credentials are used.
10. End-to-end publishing tests only in an explicitly authorized test environment, with idempotency and read-back.

## Release gate

Do not enable production generation or publishing until schema validation, isolation, authorization, prompt precedence, failure behavior, and test-generation boundaries pass in CI. A documented test plan is not a substitute for an executed test report.
