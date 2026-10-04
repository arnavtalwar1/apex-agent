# APEX review and polish

Reviewed the deployed public dashboard/sign-in experience and repository frontend, authentication, task APIs, execution lifecycle, sandbox, migrations, and tests. The deployed dashboard redirects to sign-in; authenticated live workflows and real provider quality were not evaluated. Local production build passed, but the cloud browser could not reach localhost, so local visual verification is incomplete.

## Fixed

- Replaced the publicly known fallback JWT key with a random development key. Production must set a persistent `JWT_SECRET_KEY` (Render already generates one); an unset key changes on restart and differs between workers.
- Disabled automatic demo-account creation by default. Demo credentials appear only with `NEXT_PUBLIC_ENABLE_DEMO_ACCOUNT=true`; backend seeding requires `ENABLE_DEMO_ACCOUNT=True`. Existing demo users are not deleted automatically; disable them explicitly in deployed databases if they are no longer needed.
- Reject inactive users at login and protected endpoints; validate malformed refresh-token subjects; logout can revoke both supplied tokens.
- Share frontend refresh-token rotation across concurrent requests, retry protected requests once, preserve sessions on transient refresh failures, and display readable validation errors. Requests have bounded initial response waits.
- Consolidated streaming and background task execution into one lifecycle. Atomically reject duplicate starts, reject reruns of rejected tasks, and block edits/deletes of running tasks. Persist interrupted streams as failed so they can be retried.
- Removed request-time DDL and swallowed startup migration failures. Alembic owns existing-schema upgrades; migration 002 checks existing columns before adding them and updates PostgreSQL enum values outside transactions.
- Preserve authoritative checkpoint state, including cleared errors, and record the actual error before reflection resets it. Run synchronous fallback synthesis off the event loop.
- Delete reflection children through the ORM for legacy schemas that lack database cascade rules.
- Validate and bound task input and list limits; respect configured code execution timeout.
- Restrict sandbox imports to calculation/data libraries; block indirect filesystem access, dynamic builtin aliases, and common introspection escapes; remove inherited `PYTHONPATH`. Failed search returns no evidence instead of fabricated context.
- Correct dashboard completion rate: completed / finished, with no fabricated 100% for empty accounts. Clarify copy, wrap mobile controls, expose approval states and buttons, show honest health status, improve keyboard focus, enable keyboard task links, safely render citation links, and poll active tasks when revisiting their pages.
- Remove starter SVGs, obsolete Tailwind v3 config, an unused CSS entry, unused CSS utilities, and unused Python imports. Preserve tested cost/memory modules even where integration is incomplete.
- Add real frontend API tests, backend regression tests, isolated mocked providers, and GitHub CI. Previously `npm test` only ran lint.

## Deploying

1. Set a stable secret with `JWT_SECRET_KEY`; keep it identical across backend instances.
2. Run `alembic upgrade head` before starting the backend. Do not rely on startup to upgrade existing tables. Render's start command already does this.
3. Use Node 22.18+ (CI uses Node 24). Configure `NEXT_PUBLIC_API_BASE` at frontend build time when changing backend origin.
4. Leave demo flags off for normal production. Remove or deactivate any previously seeded shared account through your normal database administration process.
5. Rebuild/redeploy both frontend and backend after merging. This review does not deploy or merge changes.

## Validation

- Backend: offline pytest suite, including auth, workflow recovery, sandbox restrictions, task ownership, execution guards, input validation, and deletion cascade.
- Frontend: six Node tests for concurrent refresh, readable errors, transient failures, SSE CRLF parsing, API-base normalization, and safe redirects; strict ESLint and Next.js production build.
- Fresh SQLite Alembic upgrade and repeat upgrade verified. PostgreSQL migration behavior is reviewed but not tested against a running PostgreSQL server.

## Remaining production work

- AST checks and a subprocess are not a secure isolation boundary for hostile code. Use a dedicated container/microVM execution service with network, memory, CPU, disk, and output limits before exposing execution to untrusted tenants. Output is currently truncated after capture, so large output can consume memory.
- Tokens remain in localStorage; move to an appropriately designed HttpOnly cookie session. Revocation and refresh-token replay protection are in memory and do not work reliably across workers/restarts; move them to durable shared storage and make rotation atomic.
- BackgroundTasks and MemorySaver are process-local. Introduce a durable worker queue and checkpoint store for restart recovery and multi-instance execution. Returning to an interrupted task cannot resume its previous graph automatically.
- Cost tracking is not integrated into the workflow, and tracing lacks per-node timing. Zero cost is not measured free execution.
- List metrics describe the returned page (default 50 tasks), not an account-wide aggregate. Add pagination and dedicated aggregate endpoints when histories grow.
- Password recovery, rate limiting, and email verification need backend implementations. The misleading password-recovery demo action was removed.
- Backend requirements are broad version ranges. Establish a supported dependency lock and upgrade policy rather than relying on historical test claims.
