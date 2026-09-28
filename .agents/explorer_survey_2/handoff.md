# Handoff Report: Authentication Flow Investigation (R1)

> **Agent**: explorer_survey_2  
> **Type**: Hard Handoff (Investigation Complete)  
> **Timestamp**: 2026-09-22T16:47:00Z  
> **Deliverable Path**: `c:\Users\ASUS\apex-agent\.agents\explorer_survey_2\auth_survey.md`  

---

## 1. Observation

1. **Frontend Authentication Architecture**:
   - `frontend/app/register/page.tsx` (lines 17–41): Form handles `fullName`, `email`, `password`. Submits `api.register` and then immediately chains `api.login` before routing to `/` via Next.js `useRouter().push("/")`.
   - `frontend/app/login/page.tsx` (lines 16–34): Form takes `email` and `password`. Submits `api.login` and routes to `/`. Contains a "Reset Password?" placeholder triggering `alert("Password reset link sent to your email!")` (line 69).
   - `frontend/components/Navbar.tsx` (lines 12–15): Renders Logout button calling `api.logout()` and navigating to `/login`.
   - `frontend/lib/api.ts` (lines 5–10, 27–48): Manages token retrieval and persistence with `localStorage.getItem("access_token")` / `setItem`. Intercepts 401 status codes in `handleJsonResponse` to purge `"access_token"` and redirect to `/login`.
   - `frontend/app/page.tsx` (lines 20–25) and `frontend/app/tasks/[id]/page.tsx` (lines 41–46): Client-side session checks via `useEffect` redirecting to `/login` if `!getToken()`.
   - `frontend/next.config.ts` (lines 3–12): Rewrites `/api/:path*` to `http://localhost:8000/api/:path*`.

2. **Backend Authentication Routes & Security**:
   - `app/main.py` (lines 23–31, 39–45, 51): FastAPIs `lifespan` seeds demo user `test@example.com` / `pass123` with `Demo User` if not present. CORS middleware allows `http://localhost:3000`. Auth router mounted at prefix `/api/v1` via `app.include_router(auth.router, prefix="/api/v1")`.
   - `app/api/auth.py` (lines 19–49): Defines 3 endpoints:
     - `POST /api/v1/auth/register` (lines 19–34): Validates uniqueness of `email`, hashes password with `get_password_hash`, saves `User`, returns `UserResponse`.
     - `POST /api/v1/auth/login` (lines 36–44): Verifies credentials with `verify_password`, returns `TokenResponse` with JWT token.
     - `GET /api/v1/auth/me` (lines 46–48): Returns `UserResponse` for current user.
   - `app/core/security.py` (lines 21–76):
     - `verify_password` and `get_password_hash` use `bcrypt` with standard 72-byte truncation (`[:72]`) and `bcrypt.gensalt()`.
     - `create_access_token` creates `HS256` JWT with claims `sub`, `email`, and `exp`.
     - `get_current_user` supports both HTTPBearer authorization header and `?token=` query parameter (needed for browser `EventSource` in SSE).
   - `app/schemas/auth.py`: Defines `UserRegister`, `UserLogin`, `TokenResponse`, and `UserResponse`. Note that `UserRegister` lacks minimum length constraints on `password`.

3. **Database Schema & Persistence**:
   - `app/models/user.py` and `migrations/versions/001_initial_tables.py` (lines 22–35):
     - `users` table: `id` (INTEGER PK), `email` (VARCHAR(255) UNIQUE INDEX), `hashed_password` (VARCHAR(255) NOT NULL), `full_name` (VARCHAR(255)), `is_active` (BOOLEAN DEFAULT TRUE), `is_superuser` (BOOLEAN DEFAULT FALSE), `created_at` (TIMESTAMP), `updated_at` (TIMESTAMP).
   - Default database is SQLite via `aiosqlite` (`DATABASE_URL=sqlite+aiosqlite:///./apex.db`).

4. **Testing and Verification Results**:
   - Ran `.\.venv\Scripts\pytest tests/test_auth.py tests/test_security.py -v`:
     - 13 passed in 5.57s. Verifies registration, duplicate email rejection (400), login success/failure (401), `/auth/me` retrieval, IDOR protection, SQL injection resistance, and expired JWT rejection.
   - Ran `npm run lint` in `frontend`:
     - Auth components (`login/page.tsx`, `register/page.tsx`, `Navbar.tsx`, `api.ts`) passed with 0 errors.
     - `frontend/app/tasks/[id]/page.tsx:282` has 2 unescaped quote errors (`react/no-unescaped-entities`).

---

## 2. Logic Chain

1. From Observation 1, the frontend implements full manual user entry for Registration and Login using controlled React forms. It chains registration into automatic login and persists tokens in browser `localStorage`.
2. From Observation 2, backend authentication endpoints (`/register`, `/login`, `/me`) strictly decouple password storage from API responses using Pydantic schemas (`UserResponse` excludes `hashed_password`), implement industry-standard bcrypt hashing, and generate standard `HS256` JWT tokens with 60-minute expiration.
3. From Observation 2 and 3, user identity is enforced on backend database queries: all protected task and reflection queries in `app/api/tasks.py` filter by `user_id == current_user.id`, preventing horizontal privilege escalation (IDOR).
4. From Observation 4, all 13 backend authentication and security unit tests are passing. The seed credentials `test@example.com` / `pass123` are guaranteed to exist locally on backend launch.
5. Inconsistencies/Gaps identified:
   - There is no backend `/auth/logout` endpoint or token revocation list; logout is entirely client-side `localStorage.removeItem("access_token")`.
   - The "Reset Password?" button on `/login` uses a browser `alert()` stub.
   - Neither frontend nor backend enforces password complexity or minimum length.
   - Route protection is client-side (`useEffect`) rather than server-side Next.js middleware.

---

## 3. Caveats

- **No live browser testing performed**: Investigation was performed via static source analysis, automated test execution, and schema inspection. Manual browser click-through was not executed in this turn.
- **Email casing**: Pydantic `EmailStr` validates email format, but database uniqueness and lookups rely on exact casing unless normalized to lower-case during registration.
- **Production Redis**: Local dev uses in-memory / SQLite checkpointers; production Redis checkpointer was not connected or tested.

---

## 4. Conclusion

The APEX AI Authentication Flow (R1) is well-structured, functional, and fully backed by passing automated test suites. 
- For exploratory and manual testing of R1, testers can authenticate using the pre-seeded account (`test@example.com` / `pass123`) or register any new valid email/password combination on `/register`.
- The frontend seamlessly logs in new users upon registration and redirects them to the dashboard.
- Key recommendations for the team's `qa_report.md` include:
  1. Add minimum password length validation (currently permits short/empty passwords).
  2. Add "Confirm Password" input to registration form.
  3. Replace or remove mock `alert()` on the "Reset Password?" button.
  4. Escaping quotes in `frontend/app/tasks/[id]/page.tsx` line 282 to clean up frontend linting.

---

## 5. Verification Method

To independently reproduce and verify this investigation:
1. **Pytest Auth Suite**:
   ```powershell
   .\.venv\Scripts\pytest tests/test_auth.py tests/test_security.py -v
   ```
   *Expected outcome*: 13 tests pass.
2. **Frontend Linting**:
   ```powershell
   cd frontend
   npm run lint
   ```
   *Expected outcome*: 0 errors in auth files; 2 syntax warnings/errors in task detail page.
3. **Inspect Survey Report**:
   Inspect `c:\Users\ASUS\apex-agent\.agents\explorer_survey_2\auth_survey.md`.
