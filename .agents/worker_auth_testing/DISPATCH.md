# Dispatch for Worker Auth Testing (R1)

You are worker_auth_testing (type: teamwork_preview_worker).
Your working directory is: c:\Users\ASUS\apex-agent\.agents\worker_auth_testing
Project root: c:\Users\ASUS\apex-agent

User original request path (MANDATORY TO READ FIRST):
c:\Users\ASUS\apex-agent\.agents\ORIGINAL_REQUEST.md

Survey findings to reference:
c:\Users\ASUS\apex-agent\.agents\explorer_survey_2\auth_survey.md
c:\Users\ASUS\apex-agent\.agents\explorer_survey_2\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Task:
Perform exhaustive testing of Authentication Flow (R1: Registration and Login):
1. Test against the live backend (http://127.0.0.1:8000) and frontend proxy (http://localhost:3000):
   - User Registration:
     * Happy path: register new valid user (e.g., new unique email and password). Verify status 200, JWT returned, User object created.
     * Duplicate email rejection: attempt to register with existing email (e.g. test@example.com). Verify HTTP 400 with "Email already registered".
     * Invalid email formats (missing @, invalid domain). Verify HTTP 422 Unprocessable Entity.
     * Password edge cases: empty password, short password, long password, special characters.
   - User Login:
     * Happy path: login with pre-seeded demo user (test@example.com / pass123) and newly registered user. Verify HTTP 200, access_token returned, token_type is "bearer".
     * Invalid password: login with correct email but wrong password. Verify HTTP 401 Unauthorized with "Incorrect email or password".
     * Nonexistent email: login with unregistered email. Verify HTTP 401 Unauthorized.
     * Empty credentials / missing fields. Verify HTTP 422.
   - Protected Route & Session Verification:
     * Access GET /api/v1/auth/me with valid Bearer token. Verify HTTP 200 and user profile matches.
     * Access GET /api/v1/auth/me with invalid / expired / missing token. Verify HTTP 401 / 403.
     * Test token query parameter support (?token=...) as used by SSE event stream.
   - Run backend test suite:
     * .\.venv\Scripts\pytest tests/test_auth.py tests/test_security.py -v
   - Evaluate frontend auth UX & components:
     * Inspect frontend/app/login/page.tsx, frontend/app/register/page.tsx, frontend/components/Navbar.tsx, frontend/lib/api.ts.
     * Check error message rendering, loading states, password reset behavior (mock alert), token storage in localStorage, and logout behavior.
2. Document all findings, executed test cases, pass/fail statuses, and step-by-step reproduction instructions for any identified bugs/quirks/gaps in `c:\Users\ASUS\apex-agent\.agents\worker_auth_testing\auth_test_results.md`.
3. Provide a structured handoff report in `c:\Users\ASUS\apex-agent\.agents\worker_auth_testing\handoff.md`.

## 2026-09-22T16:55:10Z
**Context**: System Restart Recovery for Auth Flow Testing (R1).
**Content**: A server restart occurred which briefly paused execution. Your briefing and progress trackers are intact. Please resume execution immediately from Step 3 (verify live backend at 8000 and frontend at 3000, run pytest auth/security tests, execute live API tests for registration/login/tokens/edge cases, inspect frontend auth UX/components, and produce auth_test_results.md and handoff.md).
**Action**: Resume execution, complete all R1 test procedures, and deliver your handoff report.

## 2026-09-22T17:00:38Z
**Context**: System Restart Recovery #2 for Auth Flow Testing (R1).
**Content**: Server restart #2 occurred. Please resume immediately. Run the auth tests, test live endpoints (login, register, me, edge cases), check frontend components, write c:\Users\ASUS\apex-agent\.agents\worker_auth_testing\auth_test_results.md and deliver handoff.md.
**Action**: Execute test suite, document all results in auth_test_results.md, and send handoff.

