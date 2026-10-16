# Community Inbox and Natural Reply Management

## Status
This document specifies product and runtime behavior. It does not mean social-platform APIs, comment ingestion, moderation, or automatic replies are already connected.

## Goal
Manage comments and messages from authorized YouTube channels, Facebook Pages, Instagram accounts, and future supported platforms in one inbox. Draft replies that sound context-aware and natural, while keeping factual, sensitive, and high-impact cases under human control.

## Inbox and account binding
Every item must be tied to a verified platform, authorized account/page, remote comment/message ID, parent thread when available, timestamp, language, and sync provenance. Display the exact destination account before an action. Enforce account and tenant authorization on the server for reads and writes.

Use official APIs and permissions. Clearly mark unsupported inbox types or missing scopes; do not scrape or pretend that an account is connected. Support pagination, incremental sync, rate-limit handling, webhook verification where available, deletion/tombstone handling, and duplicate suppression using stable remote IDs.

## Comment classification
For each item, store separate classifications and confidence values:
- Intent: question, praise, criticism, correction, request, complaint, spam, promotion, or other.
- Sentiment: positive, neutral, negative, mixed, or uncertain.
- Risk: ordinary, factual dispute, harassment, personal data, threat, self-harm concern, legal/medical/financial claim, minors/safety concern, or other sensitive case.
- Action recommendation: reply draft, ask for clarification, fact-check, hide/report only when platform permission and policy support it, or human escalation.

Low-confidence, ambiguous, adversarial, sensitive, or high-impact classifications must be escalated instead of treated as certain. Classification is assistive, not a substitute for platform rules or human judgment.

## Natural reply engine
Replies should address the specific point made, not just repeat a generic thank-you. Use this pipeline:
1. Read the comment and relevant parent thread, without exposing unrelated private messages.
2. Resolve the authorized channel profile and its language, tone, vocabulary, brand boundaries, and reply preferences.
3. Identify the user's actual question, claim, emotion, or correction.
4. If the comment contains a factual question or correction, verify against reliable/primary sources before asserting a fact. If verification is unavailable, say so or queue for review.
5. Draft one concise, specific reply in the comment's language where supported. Preserve the intended meaning; use emoji only when natural for that channel.
6. Check for invented facts, false promises, repetitive phrasing, personal-data disclosure, insults, arguments, manipulative language, and policy violations.
7. Run a repetition check against recent replies for that channel/thread and revise overly templated wording.
8. Save a draft with rationale, classification, confidence, evidence links when applicable, and the exact account binding.
9. Apply the configured send policy. A draft is never considered sent until the platform API confirms the action.

Do not pretend to be a named human or claim personal experiences the account owner has not provided. Do not use fake intimacy, pressure, engagement bait, or arguments. Avoid promising future content, prizes, prices, or actions unless confirmed in configured facts.

## Reply modes
- **Draft only:** create suggestions, never send.
- **Review before sending:** all replies wait for an authorized human.
- **Low-risk auto-send:** optional, disabled by default, only for narrow categories explicitly allow-listed by the owner. Require high confidence, a successful factual/policy check where relevant, no sensitive-risk flags, no unresolved thread ambiguity, no duplicate reply, and valid account permissions. Log the reason for eligibility.
- **Pause all sending:** immediate kill switch.
- Sensitive cases always require human review regardless of mode.

Do not auto-send replies about threats, personal information, medical/legal/financial advice, safety concerns, allegations, serious complaints, disputed facts, account security, or uncertain claims. Do not automatically delete, block, report, or hide comments unless the owner explicitly enables that specific action, the platform supports it, and the applicable policy and audit requirements pass.

## Human review and moderation
The review workspace should show original comment, thread context, author/display name as supplied by platform, channel/page, time, classification and confidence, proposed reply, supporting evidence, policy flags, send mode, and edit history. Provide approve, edit, regenerate, save draft, escalate, dismiss, and retry-after-safe-check actions. Bulk approval must show item counts and a sample, and must not bypass per-item risk gates.

Escalate:
- threats, credible safety concerns, harassment, doxxing, or personal data;
- legal, medical, financial, or other high-stakes claims;
- factual disputes without reliable verification;
- complaints about products, payments, privacy, account access, or alleged misconduct;
- comments involving minors or ambiguous safeguarding issues;
- low-confidence language detection, sarcasm, context, or sentiment;
- any item whose platform permission or remote state is unclear.

For harmful content, follow the platform's documented moderation tools and the owner's explicit policy. Preserve an audit record of actions; avoid repeating sensitive text in notifications.

## Community voice and per-channel controls
Each channel/page can configure:
- language and language-matching behavior;
- tone, formality, emoji use, typical reply length, and words/phrases to avoid;
- approved facts, URLs, FAQs, product/service details, and response boundaries;
- topics that must be escalated;
- reply modes and eligible low-risk categories;
- duplicate/repetition thresholds and rate limits;
- business hours, quiet hours, and response-time targets.

Channel-specific preferences cannot override safety, platform policy, privacy, authorization, or approval gates. Missing profile or account binding blocks sending; never borrow another channel's voice or identity silently.

## Operations, reliability, and metrics
- Sync status and last successful sync per account.
- Queue states: new, classifying, draft-ready, needs-review, approved, sending, sent, failed, escalated, ignored, and remote-state-unknown.
- Idempotency keys and remote read-back to avoid duplicate replies.
- Rate limits per platform/account and safe backoff on transient errors.
- A failed or timed-out send is not automatically resent until remote state is checked.
- Track median/percentile response time, drafts approved/edited/rejected, escalation rate, duplicate suppression, send failures, and verified helpfulness signals where available. Do not optimize solely for reply volume or engagement.
- Telegram alerts contain minimal redacted context and a secure link to the review queue, not tokens or full sensitive threads.

## Acceptance criteria
- Connected accounts are authorized and clearly identified before reply actions.
- Each suggested reply is grounded in the actual comment and correct channel profile.
- Factual corrections are checked or escalated; no unsupported claim is presented as verified.
- Sensitive and uncertain cases cannot enter the auto-send path.
- Auto-send is disabled by default and has a kill switch, allow-list, rate limits, audit logs, and remote read-back.
- Draft, approval, send, failure, and unknown remote-state transitions are visible and recoverable.
- Duplicate sync events and retries do not create duplicate public replies.
- UI tests cover editing, approval, rejection, escalation, account switching, and pause-all.
