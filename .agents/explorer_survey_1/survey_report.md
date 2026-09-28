# APEX AI Platform — Comprehensive Repository Survey Report

**Date**: 2026-09-22  
**Investigator**: `explorer_survey_1`  
**Repository Root**: `c:\Users\ASUS\apex-agent`  
**Status**: Completed  

---

## 1. Executive Summary

The **APEX AI platform** is a full-stack, autonomous multi-agent task automation and cognitive orchestration platform. It is designed to mitigate LLM hallucinations and brittle script execution by leveraging a society of specialized agents (Supervisor, Planner, Researcher, Executor, Reflector) coordinated via a bounded LangGraph state machine with automatic reflection and self-healing.

### Current System Health & Operational State
- **Backend Service**: FastAPI running on Python 3.13 (`uvicorn app.main:app --reload --port 8000`), currently active and listening on `127.0.0.1:8000` (`/health` returns `{"status": "healthy"}`).
- **Frontend Service**: Next.js 16.3.4 (Turbopack, React 19.2.8, Tailwind CSS v4) running on Node.js v22 (`npm run dev`), currently active and listening on `http://localhost:3000` (HTTP 200 OK).
- **Database**: Local SQLite database (`apex.db`, 180 KB) with Alembic migration version `001_initial_tables`. PostgreSQL and Redis are supported via Docker Compose but SQLite + in-memory checkpointer fallback is currently used.
- **Backend Test Suite**: Pytest suite containing 34 automated tests across unit, integration, security, and agentic workflows — **34/34 passing (100%)**.
- **Frontend Code Quality**: Production build (`npm run build`) compiles cleanly; however, `npm run lint` encounters 2 errors (unescaped quotes in `frontend/app/tasks/[id]/page.tsx:282`) and 1 warning (unused variable `error`).

---

## 2. System Architecture & Multi-Agent State Machine

### 2.1 Multi-Agent State Graph (LangGraph)
APEX models task automation as a formal directed cyclic state graph (`app/graph/workflow.py`) with persistent checkpoints:
1. **User Goal Entry**: A task is submitted by an authenticated user via REST API.
2. **Supervisor Node (`app/agents/supervisor.py`)**: Central router evaluating state and determining next agent dispatch (`PLANNER`, `RESEARCHER`, `EXECUTOR`, `REFLECTOR`, or `FINISH`). Hard bounds: `MAX_ITERATIONS = 5` (or configured via `.env`).
3. **Planner Node (`app/agents/planner.py`)**: Breaks goals into sequential executable steps and formats executable Python code blocks (` ```python ... ``` `).
4. **Researcher Node (`app/agents/researcher.py` / `app/tools/search.py`)**: Queries Tavily Search API with automated fallback to DuckDuckGo search for fact-checking.
5. **Executor Node (`app/agents/executor.py`)**: Executes generated Python code inside an isolated subprocess with stdout/stderr capture and 30-second timeout.
6. **Reflector Node (`app/agents/reflector.py`)**: Triggered when execution fails or returns non-zero error traces. Formulates natural-language critique, outputs corrected code, increments iteration count, and resets the error flag to enable recovery retries.
7. **Streaming Observability (SSE)**: State updates from LangGraph nodes are streamed in real time to the browser via Server-Sent Events at `POST/GET /api/v1/tasks/{id}/run`.

---

## 3. Directory Structure & Key Files

```
c:\Users\ASUS\apex-agent\
├── .agents/                    # Agent work folders, briefings, reports, dispatch
├── .env                        # Local active environment variables (API keys, DB URLs)
├── .env.example                # Environment variable configuration template
├── alembic.ini                 # Database migration configuration
├── apex.db                     # SQLite active database (contains users, tasks, reflections)
├── app/                        # FastAPI Backend Application
│   ├── main.py                 # FastAPI application factory, CORS, lifespan seeding
│   ├── agents/                 # LangGraph agent nodes
│   │   ├── executor.py         # Subprocess code execution sandbox
│   │   ├── planner.py          # Objective decomposition & code generation
│   │   ├── reflector.py        # Error diagnosis, critique & self-healing
│   │   ├── researcher.py       # Web grounding agent
│   │   └── supervisor.py       # Orchestration & next-step decision logic
│   ├── api/                    # REST API Route Handlers
│   │   ├── auth.py             # /api/v1/auth (register, login, me)
│   │   ├── tasks.py            # /api/v1/tasks (CRUD + SSE execution stream)
│   │   └── reflections.py      # /api/v1/reflections (task reflection audit logs)
│   ├── core/                   # Core infrastructure
│   │   ├── config.py           # Pydantic BaseSettings loading from .env
│   │   ├── database.py         # SQLAlchemy async engine & sessionmaker
│   │   ├── llm.py              # LLM factory with Groq -> OpenRouter -> OpenAI failover
│   │   └── security.py         # bcrypt hashing, JWT issuance & validation
│   ├── graph/                  # LangGraph Workflow definitions
│   │   ├── state.py            # AgentState TypedDict definition
│   │   └── workflow.py         # StateGraph assembly, conditional routing, checkpointer
│   ├── models/                 # SQLAlchemy ORM Models
│   │   ├── user.py             # User model (id, email, hashed_password, full_name)
│   │   ├── task.py             # Task model (id, user_id, goal, status, plan, final_output)
│   │   └── reflection.py       # Reflection model (id, task_id, critique, corrected_strategy)
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── auth.py             # UserRegister, UserLogin, TokenResponse, UserResponse
│   │   ├── task.py             # TaskCreate, TaskResponse
│   │   └── reflection.py       # ReflectionResponse
│   └── tools/
│       └── search.py           # Tavily and DuckDuckGo search integration
├── docker/
│   ├── Dockerfile.backend      # Python 3.11-slim container spec
│   └── Dockerfile.frontend     # Frontend container placeholder
├── docker-compose.yml          # Postgres + Redis + Backend container orchestration
├── frontend/                   # Next.js 16 Frontend Web Application
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout with fonts and providers
│   │   ├── page.tsx            # Dashboard (stats bento box, omnibar task input, task list)
│   │   ├── login/page.tsx      # Login form
│   │   ├── register/page.tsx   # Registration form
│   │   └── tasks/[id]/page.tsx # Live Execution Console, SSE log stream, output viewer
│   ├── components/
│   │   ├── Navbar.tsx          # Floating pill navbar with branding and logout
│   │   ├── StatusBadge.tsx     # Color-coded pulsing status badges
│   │   └── TaskList.tsx        # Task cards grid with delete action and navigation
│   ├── lib/
│   │   └── api.ts              # Typed API client, localStorage auth, SSE stream handler
│   ├── package.json            # Frontend dependencies and npm scripts
│   ├── tailwind.config.js      # Custom theme styling & colors
│   └── tsconfig.json           # TypeScript configuration
├── migrations/                 # Alembic Database Migrations
│   ├── env.py                  # Migration runner environment
│   └── versions/
│       └── 001_initial_tables.py # Initial users, tasks, reflections tables
├── requirements.txt            # Python dependencies
├── run.bat                     # Windows cmd launcher script
├── run.ps1                     # PowerShell launcher script
├── stop.bat                    # Windows process terminator script
└── tests/                      # Pytest Automated Test Suite
    ├── conftest.py             # In-memory SQLite fixtures & async client overrides
    ├── test_agentic_system.py  # Happy-path, self-healing recovery, SSE stream tests
    ├── test_agents.py          # Unit tests for individual agent nodes
    ├── test_auth.py            # Registration, login, duplicate check, /me tests
    ├── test_performance.py     # Latency benchmarks (< 200 ms non-functional requirement)
    ├── test_security.py        # IDOR, SQL injection, XSS, JWT expiry, password leakage tests
    ├── test_tasks.py           # Task CRUD and reflections endpoints
    └── test_workflow.py        # Graph routing, max iterations, termination conditions
```

---

## 4. Tech Stack Breakdown

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Backend Framework** | FastAPI | >= 0.115.0 | Async REST API & SSE streaming |
| **Agent Orchestration**| LangGraph / LangChain | >= 0.2.38 / >= 0.3.0 | Cyclic state machine, routing, memory checkpoints |
| **LLM Inference** | Groq / OpenRouter / OpenAI | Failover chain | Primary: Groq (`llama-3.3-70b-versatile`), Fallback: OpenRouter, Last: OpenAI |
| **Search Tools** | Tavily / DuckDuckGo | tavily >= 0.5.0 / ddg >= 6.3.0 | Real-time web ground truth gathering |
| **Database ORM** | SQLAlchemy (Async) | >= 2.0.35 | Async database models and queries |
| **Database Engine** | SQLite (active) / PostgreSQL | aiosqlite >= 0.20.0 | Multi-tier persistence for users, tasks, reflections |
| **Database Migrations**| Alembic | >= 1.14.0 | Schema versioning (`001_initial_tables`) |
| **Authentication** | python-jose / bcrypt | 3.3.0 / >= 4.0.0 | JWT tokens with HMAC-SHA256, salted bcrypt hashes |
| **Frontend Framework**| Next.js (App Router) | 16.3.4 | Server and client React application |
| **UI Library** | React / React DOM | 19.2.8 | Declarative component UI |
| **Styling** | Tailwind CSS / PostCSS | ^4 | Terminal Dark Theme styling |
| **Animation / Icons** | Framer Motion / Lucide React | ^13.4.0 / ^1.47.0 | Smooth transitions and iconography |
| **Testing** | Pytest / Pytest-Asyncio / HTTPX | >= 8.3.0 / >= 0.24.0 | Automated async backend testing suite |

---

## 5. Backend Architecture & API Surface

### 5.1 Authentication System
- Password hashing: `bcrypt.hashpw` with salt (enforces 72-byte maximum bcrypt constraint).
- Access tokens: JWT with 60-minute expiry (`JWT_EXPIRE_MINUTES=60`).
- Token transport: Supports both `Authorization: Bearer <token>` header and `?token=<token>` query parameter (specifically tailored for native browser `EventSource` SSE requests).
- Seed user: On startup, `app/main.py` lifespan checks and seeds a demo user:
  - **Email**: `test@example.com`
  - **Password**: `pass123`
  - **Name**: `Demo User`

### 5.2 API Endpoints Matrix

| HTTP Method | Route | Authentication Required | Purpose |
|---|---|---|---|
| `GET` | `/` | No | Root welcome message |
| `GET` | `/health` | No | Health check (`{"status": "healthy"}`) |
| `POST` | `/api/v1/auth/register` | No | User registration (email, password, full_name) |
| `POST` | `/api/v1/auth/login` | No | User login returning JWT `access_token` |
| `GET` | `/api/v1/auth/me` | Yes | Get current authenticated user profile |
| `POST` | `/api/v1/tasks/` | Yes | Create a new task (goal, title) |
| `GET` | `/api/v1/tasks/` | Yes | List all tasks for current user |
| `GET` | `/api/v1/tasks/{task_id}` | Yes | Retrieve single task by ID |
| `DELETE`| `/api/v1/tasks/{task_id}` | Yes | Delete task by ID |
| `GET/POST`| `/api/v1/tasks/{task_id}/run`| Yes | Execute task via Server-Sent Events stream |
| `GET` | `/api/v1/reflections/task/{task_id}` | Yes | Retrieve reflection history for a task |

---

## 6. Frontend Architecture & Flow Implementation

### 6.1 State Management & API Communication (`frontend/lib/api.ts`)
- Token Storage: Stored in browser `localStorage.getItem("access_token")`.
- 401 Interception: Automatic token purge and client redirect to `/login` when unauthorized.
- Resilient SSE Streaming: `api.runTask` tries native browser `EventSource` with query parameter token first; if that encounters an error, it seamlessly falls back to a chunked `fetch()` POST stream with `Authorization: Bearer` header.

### 6.2 Key Views & Features
1. **Login Page (`/login`)**:
   - Card form with email & password inputs, password reset stub alert, error message banner.
   - Redirects to `/` upon successful authentication.
2. **Register Page (`/register`)**:
   - Fields: Full Name, Email, Password.
   - Automatically signs user in upon successful creation and navigates to `/`.
3. **Dashboard Page (`/`)**:
   - Top stats bento box: Displays system overview and dynamic task completion success rate percentage.
   - Omnibar task submission form: Creates task and immediately redirects to `/tasks/{id}`.
   - Task List grid: Shows task cards with status badge, reflection counter, and a functional delete button.
4. **Task Detail & Execution Console (`/tasks/[id]`)**:
   - Back navigation to Dashboard.
   - Status badge, reflection count badge, goal summary.
   - "Initialize Agent" button to trigger real-time SSE execution.
   - Terminal log stream showing real-time agent transitions (Supervisor, Planner, Researcher, Executor, Reflector).
   - Final execution output card displayed upon task completion.

---

## 7. Execution, Run Scripts & Running Services

### 7.1 Available Launcher Scripts
- `run.bat` / `run.ps1`:
  1. Validates Python virtual environment (`.venv\Scripts\python.exe`).
  2. Validates Node.js and npm in system PATH.
  3. Copies `.env.example` to `.env` if `.env` does not exist.
  4. Runs Alembic database migrations: `python -m alembic upgrade head`.
  5. Launches FastAPI backend on port 8000 via Uvicorn in a separate terminal.
  6. Launches Next.js frontend on port 3000 via `npm run dev` in a separate terminal.
  7. Opens `http://localhost:3000` in the default browser.
- `stop.bat`:
  - Terminates running processes listening on port 8000 (Python/Uvicorn) and port 3000 (Node.js/Next.js) via `taskkill`.
- `docker-compose.yml`:
  - Starts PostgreSQL (port 5432), Redis Stack (port 6379), and backend service container.

### 7.2 Current Live Process State
- **Port 8000**: Active listening process `python.exe` (PID 9136, Uvicorn on 127.0.0.1:8000).
- **Port 3000**: Active listening process `node.exe` (PID 10524, Next.js Turbopack dev server on :::3000).
- **Live Verification**:
  - `http://127.0.0.1:8000/health` -> HTTP 200 `{"status": "healthy"}`
  - `http://localhost:3000` -> HTTP 200 OK

---

## 8. Test Suites & Quality Verification

### 8.1 Backend Pytest Verification
Command: `.\.venv\Scripts\python.exe -m pytest -v`
Result: **34 passed in 8.17s**
- `test_agentic_system.py`: 3 tests (happy path, self-healing recovery, SSE endpoint)
- `test_agents.py`: 8 tests (extract_code, executor successes/failures, reflector, supervisor sanitization, planner, researcher)
- `test_auth.py`: 7 tests (root, health, register, duplicate email, login, invalid credentials, get_me auth/unauth)
- `test_performance.py`: 1 test (CRUD latencies < 200 ms, avg < 100 ms)
- `test_security.py`: 6 tests (passwords not exposed, task IDOR, reflection IDOR, SQL injection, XSS payload safety, expired JWT)
- `test_tasks.py`: 5 tests (create & list, get by id, 404 nonexistent, reflections, unauthorized access)
- `test_workflow.py`: 4 tests (max iterations boundary, valid node routing, finish/unknown handling, end-to-end graph stream)

### 8.2 Testing Gaps Identified in Automated Suite
1. **Task Deletion Test Missing in Pytest**:
   - `DELETE /api/v1/tasks/{task_id}` is implemented in `app/api/tasks.py` and supported in the UI (`TaskList.tsx`), but `tests/test_tasks.py` does not include an automated unit/integration test for task deletion.
2. **Frontend Test Suite Missing**:
   - There are currently no automated unit or E2E tests configured for the frontend in `frontend/package.json` (no Vitest, Jest, Playwright, or Cypress).
3. **Frontend ESLint Errors**:
   - Running `npm run lint` yields:
     - `frontend/app/tasks/[id]/page.tsx:282:26`: Unescaped double quotes `"` in JSX.
     - `frontend/app/tasks/[id]/page.tsx:22:10`: Unused state variable `error`.

---

## 9. Alignment with Original User Testing Goals

The original request (`c:\Users\ASUS\apex-agent\.agents\ORIGINAL_REQUEST.md`) specifies:
1. **R1. Auth Flow Testing**: Test Registration and Login flows to ensure users authenticate successfully.
   - *Survey Assessment*: Fully supported via `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`, and frontend `/login` and `/register` routes. Default seeded user (`test@example.com` / `pass123`) is already available in `apex.db`.
2. **R2. Task Flow Testing**: Test creation, viewing, and deletion of tasks on the dashboard.
   - *Survey Assessment*: Fully supported. Dashboard omnibar creates tasks (`POST /api/v1/tasks/`), cards view tasks (`GET /api/v1/tasks/{id}`), and the trash icon deletes tasks (`DELETE /api/v1/tasks/{id}`). Real-time SSE execution can also be tested on the task detail page (`/tasks/{id}`).
3. **R3. QA Report Generation**: Document all findings in `qa_report.md`.
   - *Survey Assessment*: Ready for manual/exploratory testing execution. Development servers are already running and fully operational.
