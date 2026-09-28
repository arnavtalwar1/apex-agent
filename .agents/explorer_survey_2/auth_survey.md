# Authentication Flow Survey (R1: Registration and Login)

> **Investigator**: explorer_survey_2  
> **Target**: APEX AI Platform — Authentication Flow  
> **Date**: 2026-09-22  
> **Status**: Complete Investigation  

---

## Executive Summary

The APEX AI Platform implements an asynchronous JWT-based authentication system with bcrypt password hashing.
- **Backend**: Built on FastAPI with SQLAlchemy (async) and Pydantic v2. Endpoints are exposed under `/api/v1/auth` (`/register`, `/login`, `/me`).
- **Frontend**: Built on Next.js 16 (App Router) with React 19 and Tailwind CSS. Dedicated `/login` and `/register` client components handle user credentials, persist JWT tokens to browser `localStorage`, and enforce client-side redirection for authenticated/unauthenticated routes.
- **Persistence**: Relational database storage (`sqlite+aiosqlite` in development, PostgreSQL ready in production) with a dedicated `users` table managed via Alembic migrations.
- **Test Coverage**: 13 automated tests across `tests/test_auth.py` and `tests/test_security.py` verify registration, duplicate email handling, login validation, token issuance, credential non-exposure, and expired token rejection. All 13 tests currently pass.

---

## 1. Frontend Auth Components & User Experience

### 1.1 Architecture & Component Mapping

| Route / File | Component Type | Core Responsibility |
|---|---|---|
| `frontend/app/register/page.tsx` | Client Component (`"use client"`) | User registration form (full name, email, password), automatic post-registration login, redirect to `/`. |
| `frontend/app/login/page.tsx` | Client Component (`"use client"`) | User login form (email, password), token acquisition and storage, redirect to `/`. |
| `frontend/components/Navbar.tsx` | Client Component (`"use client"`) | Top navigation bar containing the Logout button; clears session token and routes to `/login`. |
| `frontend/lib/api.ts` | Utility / API Client | Centralized HTTP client (`api.register`, `api.login`, `api.getMe`, `api.logout`), handles `localStorage` token storage, injects `Authorization: Bearer <token>`, and intercepts 401 errors. |
| `frontend/types/index.ts` | TypeScript Definitions | Type definitions for `User`, `AuthResponse`, and `Task`. |
| `frontend/app/page.tsx` | Client Component (`"use client"`) | Protected dashboard route; checks `getToken()`, redirects unauthenticated users to `/login`. |
| `frontend/app/tasks/[id]/page.tsx` | Client Component (`"use client"`) | Protected task detail route; checks `getToken()`, redirects unauthenticated users to `/login`. |

### 1.2 Registration Flow (`frontend/app/register/page.tsx`)
- **State Managed**: `fullName` (string), `email` (string), `password` (string), `loading` (boolean), `error` (string).
- **Validation**:
  - Client-side check: `if (!email || !password)` displays `"Please fill in all required fields."`.
  - HTML5 form constraints: `required` and `type="email"` for email, `required` and `type="password"` for password.
  - Full name is optional on the UI; if omitted, `frontend/lib/api.ts:58` defaults `full_name` to `"User"`.
- **Submission & Transition**:
  1. Prevents default submit (`e.preventDefault()`).
  2. Submits `POST /api/v1/auth/register` via `api.register()`.
  3. Immediately invokes `api.login({ email, password })` to obtain and persist the JWT.
  4. Calls Next.js router `router.push("/")` to send the user directly to the dashboard.
- **Error Presentation**: Displays errors inside an alert banner with a pulsing red indicator (`border-apex-red/30 bg-apex-red/10 text-apex-red`).
- **Navigation Links**: Includes `<Link href="/login">` ("Sign In").

### 1.3 Login Flow (`frontend/app/login/page.tsx`)
- **State Managed**: `email` (string), `password` (string), `loading` (boolean), `error` (string).
- **Validation**:
  - Client-side check: `if (!email || !password)` displays `"Please fill in all fields."`.
  - HTML5 attributes: `required` and `type="email"` / `type="password"`.
- **Submission & Transition**:
  1. Submits `POST /api/v1/auth/login` via `api.login()`.
  2. Receives `AuthResponse` (`{ access_token, token_type }`).
  3. Saves `access_token` into `localStorage.setItem("access_token", token)`.
  4. Redirects to `/` via `router.push("/")`.
- **Reset Password Button**: Includes a button "Reset Password?" with `onClick={() => alert("Password reset link sent to your email!")}`. *Note: This is a placeholder mock alert; there is no backend password reset route.*
- **Navigation Links**: Includes `<Link href="/register">` ("Register").

### 1.4 Session & Token Lifecycle Handling (`frontend/lib/api.ts`)
- **Storage Mechanism**: JWT access token is stored in the browser's `localStorage` under key `"access_token"`.
- **Request Authentication**:
  - `authHeaders(withAuth = true)` retrieves token via `getToken()` and attaches `Authorization: Bearer <token>`.
- **Response Interception (401 Handling)**:
  - In `handleJsonResponse()`:
    ```typescript
    if (response.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    ```
- **Logout Action**:
  - `api.logout()` purges `"access_token"` from `localStorage` and triggers `window.location.href = "/login"`.
- **SSE Stream Authentication**:
  - `runTask` in `frontend/lib/api.ts` provides authentication for live Server-Sent Events via two methods:
    1. Browser `EventSource`: Token passed in query string (`?token=${encodeURIComponent(token)}`).
    2. Fallback `fetch` streaming: Token passed in `Authorization: Bearer ${token}` header.

---

## 2. Backend Auth Endpoints & Security Architecture

### 2.1 Router Configuration
- **Prefix**: `/api/v1/auth` (mounted in `app/main.py:51`).
- **Tag**: `Authentication`.
- **File**: `app/api/auth.py`.

### 2.2 Endpoint Details

#### 1. `POST /api/v1/auth/register`
- **Request Body**: `UserRegister` (`app/schemas/auth.py`):
  ```python
  class UserRegister(BaseModel):
      email: EmailStr
      password: str
      full_name: str
  ```
- **Logic**:
  1. Executes `select(User).where(User.email == user_data.email)`.
  2. If duplicate, raises `HTTPException(status_code=400, detail="Email already registered")`.
  3. Hashes password: `hashed_password = get_password_hash(user_data.password)`.
  4. Instantiates `User(email=..., hashed_password=..., full_name=...)` and commits to DB.
- **Response**: `UserResponse` (`id: int`, `email: str`, `full_name: str | None`, `is_active: bool`, `is_superuser: bool`).
- **Status Code**: `200 OK`.

#### 2. `POST /api/v1/auth/login`
- **Request Body**: `UserLogin` (`app/schemas/auth.py`):
  ```python
  class UserLogin(BaseModel):
      email: EmailStr
      password: str
  ```
- **Logic**:
  1. Executes `select(User).where(User.email == user_data.email)`.
  2. Verifies password: `verify_password(user_data.password, user.hashed_password)`.
  3. If user is null or password fails, raises `HTTPException(status_code=401, detail="Invalid credentials")`.
  4. Generates token: `create_access_token({"sub": str(user.id), "email": user.email})`.
- **Response**: `TokenResponse` (`access_token: str`, `token_type: "bearer"`).
- **Status Code**: `200 OK`.

#### 3. `GET /api/v1/auth/me`
- **Security Dependency**: `Depends(get_current_user)` (`app/core/security.py`).
- **Supported Authentication Modes**:
  - `HTTPBearer` header: `Authorization: Bearer <token>`
  - Query parameter: `?token=<token>` (utilized by SSE endpoints).
- **Logic**:
  1. Extracts token from `credentials.credentials` or `token` query param.
  2. Decodes JWT using `settings.JWT_SECRET_KEY` and `HS256`.
  3. Extracts subject `user_id = payload.get("sub")`.
  4. Queries database: `select(User).where(User.id == int(user_id))`.
  5. Returns active `User` instance or raises 401 ("Invalid token", "Invalid user ID", or "User not found").
- **Response**: `UserResponse`.
- **Status Code**: `200 OK`.

### 2.3 Cryptography & Token Configuration (`app/core/security.py` & `app/core/config.py`)
- **Password Hashing**:
  - Algorithm: `bcrypt`.
  - Salt: Generated per hash with `bcrypt.gensalt()`.
  - Truncation Safety: Truncates `password_bytes` to 72 bytes (`[:72]`) to adhere to bcrypt standard limits and avoid runtime `ValueError`.
- **Token Format & Parameters**:
  - Algorithm: `HS256` (`JWT_ALGORITHM = "HS256"`).
  - Expiration: `JWT_EXPIRE_MINUTES = 60` (1 hour default).
  - Claims:
    - `"sub"`: User ID string.
    - `"email"`: User email.
    - `"exp"`: UTC timestamp (`datetime.now(timezone.utc) + timedelta(...)`).
  - Secret: `JWT_SECRET_KEY` loaded from `.env` (`your-super-secret-jwt-key-change-this`).

---

## 3. Database Schema, Models & Storage

### 3.1 `users` Table Definition
- **Model**: `app/models/user.py:User`
- **Alembic Migration**: `migrations/versions/001_initial_tables.py`
- **Table Name**: `users`

| Column | SQL Type | Constraints / Defaults | Index | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Primary Key, Autoincrement | Yes (`ix_users_id`) | Unique user identifier |
| `email` | `VARCHAR(255)` | `NOT NULL`, `UNIQUE` | Yes (`ix_users_email`) | User email address |
| `hashed_password` | `VARCHAR(255)` | `NOT NULL` | No | Bcrypt hashed string |
| `full_name` | `VARCHAR(255)` | `NULLABLE` | No | User's display name |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | No | Account status flag |
| `is_superuser` | `BOOLEAN` | `DEFAULT FALSE` | No | Administrative privilege flag |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | `DEFAULT CURRENT_TIMESTAMP` | No | Account creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | `ON UPDATE CURRENT_TIMESTAMP` | No | Last update timestamp |

### 3.2 Relationships
- Foreign key reference: `tasks.user_id -> users.id` (`sa.ForeignKeyConstraint(['user_id'], ['users.id'])`).
- Multi-tenancy and data isolation: Every task created in `app/api/tasks.py` is scoped to `current_user.id`, guaranteeing tenant isolation (validated in `test_idor_protection_tasks`).

---

## 4. Test Suite, Fixtures & Mock Data

### 4.1 Automated Test Suite Results
Tests were executed in the project virtual environment (`.\.venv\Scripts\pytest tests/test_auth.py tests/test_security.py -v`). All 13 tests passed:

```
tests/test_auth.py::test_root_and_health PASSED                          [  7%]
tests/test_auth.py::test_register_success PASSED                         [ 15%]
tests/test_auth.py::test_register_duplicate_email PASSED                 [ 23%]
tests/test_auth.py::test_login_success PASSED                            [ 30%]
tests/test_auth.py::test_login_invalid_credentials PASSED                [ 38%]
tests/test_auth.py::test_get_me_authenticated PASSED                     [ 46%]
tests/test_auth.py::test_get_me_unauthorized PASSED                      [ 53%]
tests/test_security.py::test_passwords_never_exposed_in_api PASSED       [ 61%]
tests/test_security.py::test_idor_protection_tasks PASSED                [ 69%]
tests/test_security.py::test_idor_protection_reflections PASSED          [ 76%]
tests/test_security.py::test_sql_injection_resilience PASSED             [ 84%]
tests/test_security.py::test_xss_payload_safety PASSED                   [ 92%]
tests/test_security.py::test_expired_jwt_rejection PASSED                [100%]

============================= 13 passed in 5.57s ==============================
```

### 4.2 Seed & Mock Data

| Environment / Context | Location | Email | Password | Full Name | Notes |
|---|---|---|---|---|---|
| Development / Production Seeding | `app/main.py:23-31` (FastAPI Lifespan) | `test@example.com` | `pass123` | Demo User | Automatically inserted into `apex.db` on server startup if not present. |
| Test Fixture | `tests/conftest.py:56-68` (`auth_user`) | `agent_tester@example.com` | `testpass123` | Agent Tester | Created dynamically in in-memory test database (`sqlite+aiosqlite:///:memory:`). |

---

## 5. Identified Gaps, Edge Cases & Recommendations

| # | Category | Finding / Gap | Risk / Impact | Recommendation |
|---|---|---|---|---|
| 1 | Input Validation | No password length or complexity rules in `UserRegister` schema or frontend. | Empty string or 1-character passwords are syntactically permitted. | Add Pydantic `Field(min_length=8)` and client-side validation for minimum password length. |
| 2 | Registration Form | Frontend `RegisterPage` lacks a "Confirm Password" input. | Users risk mis-typing their password during registration without recourse. | Add a "Confirm Password" field and check equality before calling `api.register()`. |
| 3 | Password Reset | "Reset Password?" in `LoginPage` calls `alert("Password reset link sent to your email!")`. | Non-functional UX placeholder; creates false expectation. | Either remove the button until reset infrastructure is built or implement a reset endpoint with email verification. |
| 4 | Token Revocation | No server-side `/auth/logout` endpoint, token blacklist, or refresh tokens. | Logged-out tokens remain valid until expiration (up to 60 minutes) if intercepted. | For enterprise hardening, consider implementing a Redis-backed token blacklist or short-lived tokens with refresh token rotation. |
| 5 | Route Protection | No Next.js server-side `middleware.ts`; route protection relies on client `useEffect`. | Unauthenticated users may experience a brief visual flash of the dashboard before client redirect occurs. | Add a Next.js `middleware.ts` to inspect auth cookies if moving away from pure `localStorage`. |
| 6 | Frontend Linting | `npm run lint` flagged 2 unescaped quote errors in `frontend/app/tasks/[id]/page.tsx:282`. | Auth pages themselves passed linting cleanly, but project build may fail without escaping quotes. | Escape quotes in `page.tsx` line 282 using `&quot;`. |

---

## 6. Verification Commands

To independently reproduce and verify this investigation:
```bash
# 1. Run auth and security test suite
.\.venv\Scripts\pytest tests/test_auth.py tests/test_security.py -v

# 2. Verify frontend auth pages lint cleanly
cd frontend
npm run lint
```
