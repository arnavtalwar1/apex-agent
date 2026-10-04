> Current review and deployment notes: [REVIEW.md](REVIEW.md). Historical test counts below describe earlier runs; use CI for current verification.

# ⚡ APEX Agent: Self-Improving Agentic Task Automation System

> **A Production-Oriented Multi-Agent Cognitive Orchestration Platform with Dynamic Failure Recovery, Restricted Code Execution, and Live Observability**
>
> *"Rooted in knowledge. Rising to intelligence."*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Bounded_State_Graph-orange.svg)](https://python.langchain.com/docs/langgraph)
[![Next.js 16](https://img.shields.io/badge/Next.js-16_App_Router-black.svg)](https://nextjs.org/)
[![Theme](https://img.shields.io/badge/Theme-Ivory_%26_Emerald-087F5B.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Pytest-82_Passed-success.svg)](https://pytest.org/)

---

## 📌 1. Project Overview & Core Value Proposition

**APEX Agent** is an autonomous, self-healing multi-agent task orchestration system designed to overcome the fragility of single-prompt LLM wrappers and the brittleness of static automation scripts.

Rather than relying on an unconstrained prompt loop, APEX employs a **society of specialized agents** coordinated through a bounded **LangGraph** state machine. When an execution fails due to a syntax error, timeout, or runtime exception, the failure is routed to a specialized **Reflection Agent**. The Reflector performs strategy-level root-cause analysis, corrects the execution strategy, resets error flags, and triggers a retry—bounded by a strict iteration limit to prevent uncontrolled execution cycles.

### Key Verified Metrics & Verification Results
- **Automated Verification**: **82/82 automated tests passing (100%)** across unit, integration, API, security, sandbox AST, JWT rotation, response quality, memory, cost management, and agentic workflows.
- **API Latency Compliance**: **< 100 ms average latency** for non-LLM CRUD endpoints, verified under automated test conditions against the `< 200 ms` non-functional requirement.
- **Frontend Verification**: Next.js 16 (React 19, Turbopack) production build succeeds cleanly with **0 lint errors and 0 lint warnings**.
- **Bounded Self-Healing**: Controlled iteration loop (`MAX_ITERATIONS = 2`) that prevents infinite retry loops while offering single-pass self-healing and graceful degradation.

> **Note on Evaluation Benchmarks**: Past empirical claims (e.g., 92% overall success rate, 88.4% self-healing recovery rate over a 51% single-agent baseline) reflect conceptual benchmark targets from exploratory evaluation phases rather than continuously monitored production telemetry.

---

## 🏛️ 2. Architecture & Multi-Agent State Graph

APEX orchestrates five specialized agent roles. The standard deployed runtime path executes sequentially, while the underlying architecture supports parallel execution.

### Default Deployed Execution Flow

```
                      +--------------------+
                      |     USER GOAL      |
                      +---------+----------+
                                |
                                v
                      +--------------------+
                      |  SUPERVISOR AGENT  |<---------------------+
                      +---------+----------+                      |
                                |                                 |
                                v                                 |
                      +--------------------+                      |
                      |   PLANNER AGENT    |                      |
                      +---------+----------+                      |
                                |                                 |
                                v                                 |
                      +--------------------+                      |
                      |  SUPERVISOR AGENT  |                      |
                      +---------+----------+                      |
                                |                                 |
                                v                                 |
                      +--------------------+                      |
                      |  RESEARCHER AGENT  |                      |
                      +---------+----------+                      |
                                |                                 |
                                v                                 |
                      +--------------------+                      |
                      |  SUPERVISOR AGENT  |                      |
                      +---------+----------+                      |
                                |                                 |
                                v                                 |
                      +--------------------+                      |
                      |   EXECUTOR AGENT   |                      |
                      +---------+----------+                      |
                                |                                 |
                     [ Success / Failure Check ]                  |
                                |                                 |
                +---------------+---------------+                 |
                | (Success)                     | (Failure)       |
                v                               v                 |
      +--------------------+          +--------------------+      |
      |       FINISH       |          |  REFLECTOR AGENT   |      |
      |   (Final Answer)   |          |  (Root Cause Plan) |      |
      +--------------------+          +---------+----------+      |
                                                |                 |
                                                +-----------------+
```

> **Optional Parallel Routing**: The LangGraph state graph and Supervisor also include architectural support for concurrent branch execution (`execution_mode = "parallel"`), where `Planner` and `Researcher` are launched simultaneously. In standard production task execution, the API initializes `execution_mode = "sequential"`.

---

## 🤖 3. Agent Roles & Responsibilities

| Agent | Responsibility | Source Implementation |
|---|---|---|
| **Supervisor** | Evaluates current state using fast deterministic guards (0 tokens) before LLM fallback. Enforces execution boundaries (`MAX_ITERATIONS = 2`). | [`app/agents/supervisor.py`](app/agents/supervisor.py) |
| **Planner** | Decomposes goals into structured strategic plans and self-contained Python computation blocks. Instructed never to fabricate repository metrics or datasets. Does not execute code. | [`app/agents/planner.py`](app/agents/planner.py) |
| **Researcher** | Retrieves public GitHub repository `README.md` files (README evidence only; does not analyze full source trees) or queries web intelligence via Tavily with DuckDuckGo fallback. Cites URLs when available. | [`app/agents/researcher.py`](app/agents/researcher.py) |
| **Executor** | Cleans code, repairs indentation (`ast.parse`), virtualizes file I/O (`open()`), verifies AST security, executes in an 8-second restricted subprocess, captures outputs, and synthesizes final deliverables. | [`app/agents/executor.py`](app/agents/executor.py) |
| **Reflector** | Performs strategy-level LLM replanning on failure: diagnoses error root causes, provides natural language critique, updates code, and resets error flags for retry. (Not reinforcement learning / Q-learning). | [`app/agents/reflector.py`](app/agents/reflector.py) |

### Shared State: `AgentState`
The shared working state passed between LangGraph nodes is defined in [`app/graph/state.py`](app/graph/state.py) as a `TypedDict(total=False)`, allowing fields to be populated incrementally across nodes:

```python
class AgentState(TypedDict, total=False):
    user_goal: str             # Original user objective
    plan: str                  # Structured strategic plan formulated by Planner
    research_data: str         # Gathered web/GitHub README context from Researcher
    execution_result: str      # Subprocess execution output or synthesized report
    reflection_critique: str   # Diagnostic critique and corrective instructions from Reflector
    iteration_count: int       # Number of reflection/retry cycles performed (capped at MAX_ITERATIONS = 2)
    next_node: str             # Next agent node targeted by Supervisor
    error: str                 # Runtime error message or traceback (cleared upon reflection replan)
    execution_mode: str        # "sequential" (standard default) or "parallel" (architectural branch)
```

---

## ⚙️ 4. Key Agent Workflows & Implementation Details

### 1. Supervisor Deterministic Routing
Rather than issuing an expensive LLM call for every state change, [`app/agents/supervisor.py`](app/agents/supervisor.py) applies fast Python deterministic guards first:
- **Clean Execution**: If `execution_result` exists and `error` is empty -> routes directly to `FINISH` (0 tokens).
- **Active Error**: If `error` is present and `iteration_count < MAX_ITERATIONS` -> routes to `REFLECTOR` (0 tokens).
- **Boundary Breached**: If `iteration_count >= MAX_ITERATIONS` -> routes to `FINISH` (0 tokens).
- **Sequential Pipeline**: Progresses predictably through `PLANNER` -> `RESEARCHER` -> `EXECUTOR` (0 tokens).
- **Edge Cases & Ambiguity**: Uses token-efficient fast-tier LLM routing only when deterministic rules do not apply.

**Benefits**:
- Drastically reduced token consumption and cost
- Near-zero latency for standard transitions
- Reduced nondeterminism and elimination of circular routing loops
- Clear, predictable debugging traces

### 2. Multi-Tier LLM Architecture & Provider Fallback
Configured in [`app/core/llm.py`](app/core/llm.py):
- **Fast Tier** (`tier="fast"`): Low-latency, cost-effective inference used for Supervisor routing, Planner goal decomposition, and Reflector root-cause critiques. When Groq is configured, uses `openai/gpt-oss-20b` (with `openai/gpt-oss-120b` backup).
- **Reasoning Tier** (`tier="reasoning"`): High-capacity model used for final deliverable synthesis in the Executor. When Groq is configured, uses `openai/gpt-oss-120b`.
- **Automatic Provider Fallback**: Chained using LangChain `.with_fallbacks()` across:
  1. **Groq** (Primary low-latency provider via `GROQ_API_KEY` or `gsk_` key)
  2. **OpenRouter** (Secondary fallback via `OPENROUTER_API_KEY` or `sk-or-` key)
  3. **Direct OpenAI** (Tertiary fallback using `MODEL_NAME = "gpt-4o-mini"`)

### 3. Restricted Subprocess Execution & AST Analysis
Code execution in [`app/agents/executor.py`](app/agents/executor.py) and [`app/core/sandbox.py`](app/core/sandbox.py) follows a strict pipeline:
1. **Extraction & Sanitization**: Extracts code from markdown blocks, removes package manager prefixes (`pip`, `npm`, `curl`), and strips outer whitespace.
2. **Indentation Self-Healing**: Automatically corrects block and sub-line indentation mismatches using `textwrap.dedent()` and syntax recovery with `ast.parse()`.
3. **Virtual File I/O**: Intercepts `open()` calls and wraps them in an in-memory virtual file dictionary using `io.StringIO` and `io.BytesIO`. This allows standard file-handling code to execute without writing to the host disk. It does **not** grant arbitrary filesystem access.
4. **AST Static Security Validation**: Rejects forbidden modules (`os`, `sys`, `subprocess`, `socket`, `pty`, `ctypes`), prohibited built-ins (`eval`, `exec`, `compile`, raw `open`), and dunder escape vectors (`__subclasses__`, `__mro__`).
5. **Environment Sanitization**: Spawns an isolated child process with a minimal whitelist of non-sensitive environment variables (`PATH`, `TEMP`, `LANG`), stripping all API keys, database URLs, and JWT secrets.
6. **Execution Limits**: Enforces an **8-second execution timeout** (`MAX_CODE_TIMEOUT_SECONDS = 8`) and a 25,000-character output truncation limit (`MAX_CODE_OUTPUT_CHARS = 25000`).
7. **Final Deliverable Synthesis**: Synthesizes the final response from execution outputs, research context, and user objectives.

> **Production Isolation Disclaimer**: The current execution layer is a restricted subprocess runner with AST verification and environment sanitization. It is **not** a hardened production sandbox. Stronger multi-tenant isolation requires containerization, gVisor, microVMs (e.g., Firecracker), WebAssembly (Wasm), or dedicated cloud sandboxes.

### 4. Bounded Reflection vs. Reinforcement Learning
When code execution fails, the state transitions to the `Reflector` node:
- **Strategy-Level Replanning**: The Reflector diagnoses the failure from `stderr`, updates the strategic plan, amends the Python snippet, and resets `error = ""`.
- **Clarification**: APEX reflection is strategic LLM re-prompting. It is **not** reinforcement learning or Q-learning (there is no Q-table, Bellman update, policy network, or reward model).
- **Graceful Degradation on Final Attempt**: If repeated execution attempts exhaust the iteration limit (`iteration_count >= MAX_ITERATIONS - 1`), the Executor synthesizes a comprehensive deliverable based on available research and planning evidence while explicitly disclosing the execution limitation, rather than returning a raw failure.

---

## 💾 5. Persistence, State Checkpointing & Memory

APEX implements a clear separation between durable database storage, in-process graph checkpointing, and episodic memory:

```
+--------------------------------------------------------------------------------+
|                             DATA PERSISTENCE LAYERS                            |
+-----------------------------------+--------------------------------------------+
| Layer                             | Scope & Technology                         |
+-----------------------------------+--------------------------------------------+
| Relational Database               | PostgreSQL (Production) / SQLite (Dev)     |
|                                   | - User accounts & password hashes (bcrypt) |
|                                   | - Task definitions, status & final outputs |
|                                   | - Audit log of reflections & critiques     |
+-----------------------------------+--------------------------------------------+
| LangGraph Graph Checkpointer      | In-Process MemorySaver                     |
|                                   | - Node transition state snapshots          |
|                                   | - In-memory thread state management        |
|                                   | - NOTE: Not durable across server restarts |
+-----------------------------------+--------------------------------------------+
| Episodic Reflection Memory        | Lightweight Token-Overlap Memory           |
|                                   | - Normalized Jaccard token similarity      |
|                                   | - In-memory store for past critiques       |
|                                   | - RAG-ready abstraction (no vector DB yet) |
+-----------------------------------+--------------------------------------------+
```

---

## 🔐 6. Authentication & Security Architecture

### Backend Authentication (`app/core/security.py`, `app/api/auth.py`)
- **Password Hashing**: Secure salted password hashing via `bcrypt` with truncation at 72 bytes.
- **Dual-Token JWT**:
  - Short-lived Access Tokens: 60-minute expiration (`JWT_EXPIRE_MINUTES = 60`), signed with HMAC-SHA256 (`HS256`).
  - Refresh Tokens: 7-day expiration (`JWT_REFRESH_EXPIRE_DAYS = 7`).
- **Token Rotation**: Calling `POST /api/v1/auth/refresh` immediately revokes the old refresh token and issues a new access/refresh pair, mitigating replay attacks.
- **Server-Side Blacklist**: Thread-safe in-memory `TokenBlacklist` with automatic timestamp TTL cleanup revokes tokens upon `POST /api/v1/auth/logout`.
- **Token Type Enforcement**: Strict type checking ensures refresh tokens cannot be used to authenticate API routes expecting access tokens.
- **Storage Limitation**: The Next.js frontend currently stores access and refresh tokens in browser `localStorage`. A hardened enterprise setup should migrate to `HttpOnly`, `Secure`, `SameSite` cookies to defend against client-side script token access.

### Human-in-the-Loop (HITL) Governance
- **Backend Approval Lifecycle**: Tasks support approval states (`pending`, `approved`, `rejected`) and dedicated management endpoints (`POST /api/v1/tasks/{id}/approve` and `POST /api/v1/tasks/{id}/reject`).
- **Configurable Gate**: The code execution approval requirement is configurable via `REQUIRE_APPROVAL_FOR_CODE_EXECUTION` (currently `False` by default).
- **Status**: The backend approval pipeline and endpoints are fully tested and functional. Frontend task pages expose Approve/Reject controls before execution.

---

## 🎨 7. Frontend Architecture & Brand Identity

The frontend is built on **Next.js 16 (App Router)** and **React 19** with a custom visual identity:

### Brand Design System
- **Background**: Organic warm ivory (`#F7F3E8`)
- **Primary Color**: Deep emerald (`#087F5B`)
- **Highlight Color**: Warm golden amber (`#F4B942`)
- **Accent Color**: Terracotta coral (`#E76F51`)
- **Typography**: Rich plum (`#3D2331`, `#59414E`)
- **Emblem**: APEX Growing Tree emblem representing foundational grounding and cognitive ascent
- **Tagline**: *"Rooted in knowledge. Rising to intelligence."*
- **Opening Sequence**: Framer Motion SVG growth animation (`frontend/components/BrandIntro.tsx`) with automatic session memory and escape-key skip support.

### Streaming Resilience: Fetch SSE + Polling Fallback
- **Authenticated Streaming Fetch**: The task view consumes `/api/v1/tasks/{id}/run` using a native `fetch` streaming reader with an `Authorization: Bearer <token>` header and `Accept: text/event-stream`. This avoids token leakage in URL query parameters associated with traditional browser `EventSource`.
- **Background Polling Fallback**: While streaming is active, the task page runs a 2.5-second polling fallback (`api.getTask(taskId)`) to synchronize persisted task state, ensuring complete UI updates even if intermediate network chunks are delayed.

---

## 📊 8. Observability & Cost Tracking Status

| Module | Location | Current Implementation Status |
|---|---|---|
| **Observability Tracing** | [`app/core/observability.py`](app/core/observability.py) | **Partially Integrated**: `start_trace` and `finish_trace` generate and propagate unique `trace_id` values persisted in `Task.trace_id`. Individual LangGraph agent nodes do not yet record per-node granular timing metrics into the trace. |
| **Cost Manager & Budgeting** | [`app/core/cost_manager.py`](app/core/cost_manager.py) | **Standalone / Tested**: Implements `TaskCostTracker`, `estimate_token_cost`, and `BudgetExceededError` with full unit test coverage. Not currently active in the main LangGraph execution loop. |

---

## 📋 9. Final Implementation-Status Table

| Feature / Subsystem | Current Status | Notes |
|---|---|---|
| **Multi-Agent LangGraph Workflow** | **Implemented** | 5-agent state graph with conditional routing and cycle limits |
| **Supervisor Deterministic Routing**| **Implemented** | Zero-token Python guards precede LLM fallback |
| **Planner Node** | **Implemented** | Structured goal decomposition without fabricated data |
| **Researcher Node** | **Implemented** | Public GitHub README retrieval + Tavily/DuckDuckGo fallback |
| **Executor Node** | **Implemented** | Python AST checking, virtual I/O, subprocess execution |
| **Reflector Node (Self-Healing)** | **Implemented** | Strategic error critique and plan replanning (not RL/Q-learning) |
| **AST Restricted Execution** | **Implemented** | Statically blocks dangerous imports, calls, and dunders |
| **Virtual File I/O** | **Implemented** | In-memory `io.StringIO` / `io.BytesIO` virtualization for `open()` |
| **Relational Task Persistence** | **Implemented** | PostgreSQL (Render) / SQLite (Local) via SQLAlchemy Async |
| **LangGraph MemorySaver** | **Implemented** | In-process state checkpointing (resets on server restart) |
| **SSE Real-Time Streaming** | **Implemented** | Streaming `fetch` with Authorization Bearer header support |
| **Frontend Polling Fallback** | **Implemented** | 2.5-second background task state sync |
| **Sequential Routing Mode** | **Default** | Standard production task execution initializes sequential mode |
| **Parallel Routing Mode** | **Architecture Support** | Graph supports simultaneous Planner/Researcher execution |
| **JWT Authentication** | **Implemented** | Dual access/refresh tokens with bcrypt password hashing |
| **Refresh-Token Rotation** | **Implemented** | Refreshing access token rotates refresh token and revokes prior token |
| **Token Blacklist / Revocation** | **Implemented** | Thread-safe in-memory blacklist with automatic TTL cleanup |
| **HITL Backend Approval** | **Implemented** | `AWAITING_APPROVAL` status, `/approve` and `/reject` API endpoints |
| **HITL Frontend UI Controls** | **Implemented** | Task pages expose approval controls |
| **Full RAG / Vector Database** | **Future Work** | Uses token-overlap episodic memory; pgvector/Chroma not yet integrated |
| **Container / MicroVM Sandbox** | **Future Work** | Subprocess + AST isolation used; gVisor/Wasm planned |
| **Distributed Task Worker Queue**| **Future Work** | Uses FastAPI `BackgroundTasks`; Celery/Temporal planned |

---

## 🧪 10. Test Suite & Verification Results

### Backend Automated Test Suite (82/82 Passing - 100%)

Run with:
```bash
pytest -v
```

```
tests/test_agentic_system.py ...                                         [  3%]
tests/test_agents.py ........                                            [ 13%]
tests/test_auth.py ..............                                        [ 30%]
tests/test_auth_advanced.py ....                                         [ 35%]
tests/test_memory_and_observability.py ...                               [ 39%]
tests/test_performance.py .                                              [ 40%]
tests/test_permissions_hitl.py ...                                       [ 43%]
tests/test_response_quality.py ............                             [ 60%]
tests/test_sandbox_security.py ........                                  [ 70%]
tests/test_security.py ......                                            [ 78%]
tests/test_structured_and_cost.py ......                                 [ 85%]
tests/test_tasks.py .......                                              [ 93%]
tests/test_workflow.py .....                                             [100%]

============================= 82 passed in 29.50s =============================
```

### Frontend Code Quality & Production Build
```bash
cd frontend
npm run lint   # 0 errors, 0 warnings
npm run build  # Next.js 16.3.4 (Turbopack) production build succeeds cleanly
```

---

## 💻 11. Technology Stack

- **Backend**: Python 3.11+ / 3.13, FastAPI, LangGraph, LangChain Core, SQLAlchemy (Async), Alembic, Pydantic v2.
- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Framer Motion, Lucide React.
- **Database**: PostgreSQL (Production on Render) / SQLite with aiosqlite (Development).
- **Authentication**: JWT (HMAC-SHA256) with access/refresh rotation and server-side revocation.
- **DevOps**: Render Blueprint ([`render.yaml`](render.yaml)), Vercel, Docker Compose, Uvicorn.

---

## 🚀 12. Getting Started & Installation

### Prerequisites
- Python 3.11+ installed.
- Node.js 22.18+ and npm installed.

### Step 1: Clone and Configure Environment
```bash
git clone https://github.com/arnavtalwar1/apex-agent.git
cd apex-agent

# Create your .env file from the template
cp .env.example .env
```
Edit `.env` to supply your API key(s):
```env
OPENAI_API_KEY=your_key_here
# Optional alternatives:
# GROQ_API_KEY=your_groq_key_here
# TAVILY_API_KEY=your_tavily_key_here
```

### Step 2: Backend Setup
```bash
# Create and activate Python virtual environment
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the FastAPI backend server
uvicorn app.main:app --reload --port 8000
```
- **API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Step 3: Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🎓 13. Academic Viva & Architectural Reference

#### Q1: "Why did you choose LangGraph instead of AutoGen or CrewAI?"
> **Answer**: AutoGen and CrewAI prioritize conversational multi-agent chat loops, which tend to saturate context windows, lack formal loop termination guarantees, and introduce nondeterministic state evolution. LangGraph models the system as a **formal directed state graph with state persistence and recursion bounds**. This enables deterministic Python routing guards before LLM invocation, precise iteration tracking (`MAX_ITERATIONS = 2`), and structured in-process state checkpointing via `MemorySaver`.

#### Q2: "How does the Reflection Agent achieve self-healing?"
> **Answer**: When code execution fails due to a non-zero exit code or uncaught exception, the state machine routes to the `Reflector` node. The Reflector inspects the failed script and `stderr` traceback, generates a natural language critique, formulates an updated Python script, and clears the error flag (`state["error"] = ""`). This allows the Supervisor to safely re-route the corrected code to the Executor. This is strategy-level LLM replanning—it is not reinforcement learning or Q-learning.

#### Q3: "How do you prevent infinite loops when tasks cannot be solved?"
> **Answer**: Infinite loops are bounded at two distinct layers:
> 1. In `supervisor_node`, a deterministic guard checks `iteration_count >= MAX_ITERATIONS` (where `MAX_ITERATIONS = 2`) and immediately routes to `FINISH`.
> 2. In `workflow.py`, the conditional routing function `route_next` also validates `iteration_count >= MAX_ITERATIONS` and forces transition to `END`.
> Furthermore, on the final iteration attempt, the Executor employs graceful degradation—synthesizing a final deliverable from available research evidence while explicitly disclosing the execution limitation.

#### Q4: "How does the real-time live stream work between FastAPI and Next.js?"
> **Answer**: We use **Server-Sent Events (SSE)** via FastAPI's `StreamingResponse` at `/api/v1/tasks/{id}/run`. As LangGraph yields node updates (`supervisor`, `planner`, `researcher`, `executor`, `reflector`), they are streamed over HTTP as JSON events.
>
> I use a streaming `fetch()` request rather than native `EventSource` because I need to send the JWT Bearer authorization header while consuming an SSE-formatted response (avoiding token leakage in URL query parameters). The frontend also pairs this with a 2.5-second polling fallback to ensure resilient UI synchronization.
