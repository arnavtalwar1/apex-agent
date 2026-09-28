# Task Flow Survey & Deep Investigation (R2)

**Author:** `explorer_survey_3`  
**Date:** 2026-09-22  
**Target Flow:** Task Creation, Viewing, and Deletion on Dashboard (Requirement R2)  
**Project Root:** `c:\Users\ASUS\apex-agent`  

---

## 1. Executive Summary

A comprehensive architectural and empirical investigation of the APEX Agent platform was conducted focusing on **Task Flow (R2)**, which encompasses task creation, viewing (listing and detail inspection), and deletion across both the Next.js frontend and FastAPI backend.

### Key Discoveries:
1. **Frontend Implementation**:
   - Task dashboard is located at `frontend/app/page.tsx`.
   - Task cards and deletion handlers are located at `frontend/components/TaskList.tsx`.
   - Task detail & live execution runner is located at `frontend/app/tasks/[id]/page.tsx`.
   - Status badge styling is located at `frontend/components/StatusBadge.tsx`.
   - API client wrapper is located at `frontend/lib/api.ts`.
2. **Backend Implementation**:
   - Task CRUD endpoints are defined in `app/api/tasks.py` and mounted at `/api/v1/tasks`.
   - Endpoints include `POST /api/v1/tasks/` (create), `GET /api/v1/tasks/` (list), `GET /api/v1/tasks/{task_id}` (get), `DELETE /api/v1/tasks/{task_id}` (delete), and `GET/POST /api/v1/tasks/{task_id}/run` (SSE streaming).
3. **Database Architecture**:
   - SQLAlchemy model `Task` in `app/models/task.py` with enum `TaskStatus` (`pending`, `planning`, `researching`, `executing`, `reflecting`, `completed`, `failed`).
   - Foreign key relationship to `User` model.
4. **Critical Bugs & Gaps Identified**:
   - **Bug 1 (Case Mismatch in Dashboard Success Rate)**: `frontend/app/page.tsx` line 61 checks `t.status === "COMPLETED"`, whereas backend serializes status as lowercase `"completed"`. The success rate KPI is perpetually stuck at 0%.
   - **Bug 2 (No Cascade Deletion for Reflections / Potential 500 Internal Server Error)**: `app/models/reflection.py` links `task_id` without `ondelete="CASCADE"`, and `app/models/task.py` has no `relationship("Reflection", cascade="all, delete-orphan")`. Deleting a task that contains reflection records leaves orphaned records in SQLite and will cause a foreign key constraint violation (HTTP 500) under PostgreSQL.
   - **Bug 3 (Frontend Lint Failure)**: `npm run lint` fails with 2 errors and 1 warning in `frontend/app/tasks/[id]/page.tsx` (unused `error` state variable and unescaped quotes in JSX), contradicting `README.md`.
   - **Gap 1 (Zero Test Coverage for Deletion)**: Neither `tests/test_tasks.py` nor any other test file contains tests for `DELETE /api/v1/tasks/{id}`.
   - **Gap 2 (No Status Filters)**: Neither frontend nor backend supports filtering tasks by status.
   - **UX Quirk (Task Submit Button)**: Submit button displays `"Join Now"` instead of `"Deploy Agent"` or `"Create Task"`.

---

## 2. Frontend Pages & Components Breakdown

### 2.1 Dashboard Page (`frontend/app/page.tsx`)
- **Route**: `/`
- **Type**: Next.js Client Component (`"use client"`)
- **Key Functionality**:
  1. **Authentication Check**:
     ```typescript
     // Lines 20-25
     const token = getToken();
     if (!token) {
       router.push("/login");
       return;
     }
     ```
  2. **Data Fetching**:
     - Calls `api.listTasks()` on mount (`useEffect`, lines 27-40).
     - Maintains `tasks` state: `const [tasks, setTasks] = useState<Task[]>([])`.
  3. **Success Rate KPI Calculation (BUG)**:
     ```typescript
     // Line 60-62
     const successRate = tasks.length > 0 
       ? Math.round((tasks.filter(t => t.status === "COMPLETED").length / tasks.length) * 100) 
       : 0;
     ```
     *Bug detail*: Because the backend returns `"completed"` (lowercase), `t.status === "COMPLETED"` always evaluates to `false`. Success rate will display `0%` even after tasks complete successfully.
  4. **Task Creation Form (Omnibar style)**:
     - Form container: Lines 100-140.
     - Submits through `handleCreateTask` (lines 42-58):
       - Validates non-empty trimmed goal: `if (!goal.trim()) return;`.
       - Calls `api.createTask(goal.trim())`.
       - Prepend new task to local state: `setTasks((prev) => [newTask, ...prev])`.
       - Resets goal: `setGoal("")`.
       - Immediately redirects to execution view: `router.push("/tasks/" + newTask.id)`.
     - *Button Copy*: Line 130 displays `{submitting ? "Deploying..." : "Join Now"}`.
  5. **Status Filters**:
     - **ABSENT**: There are no status filters, tabs, or search inputs on the dashboard.
  6. **Task List Rendering**:
     - Lines 160-164: Passes `tasks` and `onTaskDeleted` callback to `<TaskList>`.

### 2.2 Task List Component (`frontend/components/TaskList.tsx`)
- **Type**: Client Component (`"use client"`)
- **Props**: `{ tasks: Task[], onTaskDeleted?: (id: number) => void }`
- **Key Functionality**:
  1. **Empty State**:
     - Lines 18-24: If `tasks.length === 0`, displays: `"No tasks yet. Create your first task above!"`.
  2. **Task Cards**:
     - Rendered in a responsive 2-column grid (`grid gap-5 md:grid-cols-2`).
     - Animated with `framer-motion` stagger effect.
     - Card click navigates to `/tasks/${task.id}`.
     - Displays `StatusBadge`, reflection badge (`RotateCcw` icon + count), Title, 2-line truncated Goal, formatted creation date, and Task ID.
  3. **Deletion Handler & Button**:
     - Lines 80-86: Trash icon button (`Trash2` from `lucide-react`) styled with red pill highlight (`bg-apex-red/10 text-apex-red`).
     - Lines 26-37:
       ```typescript
       const handleDelete = async (e: React.MouseEvent, id: number) => {
         e.stopPropagation();
         try {
           await api.deleteTask(id);
           if (onTaskDeleted) {
             onTaskDeleted(id);
           }
         } catch (err) {
           console.error("Failed to delete task", err);
           alert("Failed to delete task");
         }
       };
       ```
     - Uses `e.stopPropagation()` to avoid triggering card navigation.
     - Falls back to native `alert()` upon network or API error.

### 2.3 Status Badge Component (`frontend/components/StatusBadge.tsx`)
- **Role**: Standardized status indicator with animated ping dots for active states.
- **Statuses handled**:
  - `pending` (gray/slate)
  - `planning` (amber, animated pulse/ping)
  - `researching` (fuchsia, animated pulse/ping)
  - `executing` (blue, animated pulse/ping)
  - `reflecting` (purple, animated pulse/ping)
  - `completed` (emerald)
  - `failed` (rose)
- Defensively applies `.toLowerCase()`, ensuring case-insensitivity on the badge itself.

### 2.4 Task Detail & Execution Page (`frontend/app/tasks/[id]/page.tsx`)
- **Route**: `/tasks/[id]`
- **Key Functionality**:
  - Loads task via `api.getTask(taskId)` on mount.
  - "Initialize Agent" button triggers SSE execution stream via `api.runTask()`.
  - Real-time terminal log viewer for multi-agent messages (Supervisor, Planner, Researcher, Executor, Reflector).
  - Displays `task.final_output` in a code block once execution finishes.
- **Lint Errors in this file**:
  - Line 22: `const [error, setError] = useState("");` (`error` is assigned but never rendered).
  - Line 282: `<p>Press "Initialize Agent" above to start the cognitive stream.</p>` (unescaped `"` quotes in JSX).

### 2.5 API Client Methods (`frontend/lib/api.ts`)
- `createTask(goal: string, title?: string)`:
  - Calls `POST ${API_BASE}/tasks/` with `{ goal, title }`.
- `listTasks()`:
  - Calls `GET ${API_BASE}/tasks/`.
- `getTask(id: number)`:
  - Calls `GET ${API_BASE}/tasks/${id}`.
- `deleteTask(id: number)`:
  - Calls `DELETE ${API_BASE}/tasks/${id}`.
- `runTask(id: number, onEvent, onDone, onError)`:
  - Establishes SSE connection via `EventSource` to `${API_BASE}/tasks/${id}/run?token=...`, with a fallback to `fetch` streaming with `Authorization` header.

---

## 3. Backend Routes & API Handlers

All task endpoints reside in `app/api/tasks.py` and are registered with prefix `/api/v1/tasks` in `app/main.py`.

### 3.1 `POST /api/v1/tasks/` — Create Task
- **Handler**: `create_task` (lines 22-38)
- **Security**: Requires JWT authentication via `Depends(get_current_user)`.
- **Schema**:
  ```python
  class TaskCreate(BaseModel):
      goal: str
      title: str | None = None
      max_iterations: int = 5
  ```
- **Behavior**:
  - Sets `title = task_data.title or task_data.goal[:50]`.
  - Sets `user_id = current_user.id`.
  - Sets `status = TaskStatus.PENDING`.
  - Adds to DB session, commits, refreshes, and returns `TaskResponse`.
- **Edge cases / Validation gaps**:
  - `goal` has no length restriction (`min_length=1`). Empty string or whitespace-only strings are accepted by Pydantic if not validated.

### 3.2 `GET /api/v1/tasks/` — List Tasks
- **Handler**: `list_tasks` (lines 40-53)
- **Security**: Requires JWT authentication.
- **Query Parameters**: `limit: int = 50`.
- **Behavior**:
  - Filters strictly on `Task.user_id == current_user.id` (IDOR safe).
  - Sorts by `desc(Task.created_at)`.
  - Returns `list[TaskResponse]`.
- **Gaps**:
  - No `status` parameter (cannot filter by completed, pending, etc.).
  - No pagination cursor or offset (only `limit=50`).

### 3.3 `GET /api/v1/tasks/{task_id}` — Get Task by ID
- **Handler**: `get_task` (lines 55-66)
- **Security**: Requires JWT authentication.
- **Behavior**:
  - Queries `Task.id == task_id` AND `Task.user_id == current_user.id`.
  - Returns 404 with `{"detail": "Task not found"}` if nonexistent or if belonging to another user.

### 3.4 `DELETE /api/v1/tasks/{task_id}` — Delete Task
- **Handler**: `delete_task` (lines 68-82)
- **Security**: Requires JWT authentication.
- **Behavior**:
  - Queries `Task.id == task_id` AND `Task.user_id == current_user.id`.
  - Returns 404 if not found or unauthorized.
  - Deletes task:
    ```python
    await db.delete(task)
    await db.commit()
    ```
  - Returns `{"detail": "Task deleted successfully"}`.
- **Critical Flaw**:
  - Deleting a task does NOT cascade delete related `reflections` records!

### 3.5 `GET/POST /api/v1/tasks/{task_id}/run` — Run Task (SSE)
- **Handler**: `run_task` (lines 84-162)
- **Response**: `StreamingResponse(event_generator(), media_type="text/event-stream")`.
- Streams LangGraph node states and updates task model in real time.

---

## 4. Database Schema & Models

### 4.1 `Task` Model (`app/models/task.py`)
```python
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255))
    goal = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    plan = Column(Text)
    current_node = Column(String(50))
    reflection_count = Column(Integer, default=0)
    final_output = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="tasks")
```

### 4.2 `TaskStatus` Enum
```python
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RESEARCHING = "researching"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"
```
*Note*: Enum values are lowercase strings (`"pending"`, `"completed"`, etc.).

### 4.3 `Reflection` Model (`app/models/reflection.py`)
```python
class Reflection(Base):
    __tablename__ = "reflections"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    iteration = Column(Integer, nullable=False)
    failed_node = Column(String(50))
    error_trace = Column(Text)
    verbal_critique = Column(Text)
    corrected_strategy = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 4.4 ForeignKey & Cascade Inconsistency
- `Reflection.task_id` is defined as `ForeignKey("tasks.id")` with no `ondelete="CASCADE"`.
- `Task` model has no `relationship("Reflection", cascade="all, delete-orphan")`.
- **Implication**:
  - In PostgreSQL or SQLite with foreign keys enforced, deleting a task that has any `Reflection` rows throws `sqlalchemy.exc.IntegrityError`, crashing the `delete_task` endpoint with HTTP 500.
  - In SQLite without foreign key enforcement, deleting a task leaves zombie reflection rows referencing nonexistent `task_id`s.

---

## 5. Existing Tests & Test Gaps

### 5.1 Existing Tests (`tests/test_tasks.py`)
1. `test_create_and_list_tasks`: Verifies `POST /api/v1/tasks/` creates a task with status `"pending"`, and `GET /api/v1/tasks/` returns 1 item.
2. `test_get_task_by_id`: Verifies `GET /api/v1/tasks/{id}` returns the task.
3. `test_get_nonexistent_task`: Verifies 404 response.
4. `test_get_reflections_for_task`: Verifies reflections retrieval.
5. `test_tasks_unauthorized`: Verifies 401 when token is missing.

### 5.2 Security & Performance Tests
- `tests/test_security.py`:
  - `test_idor_protection_tasks`: Confirms User B cannot see User A's tasks.
  - `test_sql_injection_resilience`: Tests SQL injection strings in goal.
  - `test_xss_payload_safety`: Tests script injection strings in goal.
- `tests/test_performance.py`:
  - `test_api_latency_under_200ms`: Tests latency for `GET` and `POST` tasks.

### 5.3 Test Coverage Gaps (Action Items for QA & Dev)
| Target Area | Test Status | Gap Details |
|---|---|---|
| `DELETE /api/v1/tasks/{id}` | **MISSING (0 tests)** | No test exists for successful deletion. |
| IDOR on Task Deletion | **MISSING** | No test checking if User B can delete User A's task. |
| Deleting Task with Reflections | **MISSING** | No test checking cascade deletion integrity. |
| Empty / Whitespace Goal | **MISSING** | No validation test for `POST /api/v1/tasks/` with empty goal. |
| Frontend Component Testing | **MISSING** | No Jest/Vitest/Playwright tests for `TaskList`, `DashboardPage`, or delete button interactions. |

---

## 6. Matrix of Identified Issues & Bugs

| ID | Category | Severity | Location | Summary & Impact |
|---|---|---|---|---|
| **BUG-01** | Frontend UI Logic | Medium | `frontend/app/page.tsx:61` | **Success Rate calculation case mismatch**: Checks `t.status === "COMPLETED"`, but backend returns `"completed"`. KPI is always 0%. |
| **BUG-02** | Backend / Database | High | `app/models/reflection.py:11`, `app/models/task.py`, `app/api/tasks.py:68` | **Foreign Key Cascade Missing on Task Delete**: Deleting a task with reflections causes `IntegrityError` (HTTP 500) on foreign key enforced databases or creates orphaned reflections. |
| **BUG-03** | Frontend Build / Lint | Low | `frontend/app/tasks/[id]/page.tsx:22,282` | **ESLint Errors**: Unused `error` variable and unescaped quotes in JSX cause `npm run lint` to exit with code 1. |
| **BUG-04** | Frontend UX Copy | Low | `frontend/app/page.tsx:130` | **Misleading Button Text**: Submit button says `"Join Now"` instead of `"Deploy Agent"` or `"Create Task"`. |
| **BUG-05** | Frontend Error Handling | Low | `frontend/components/TaskList.tsx:35` | **Unfriendly Delete Error Handling**: Uses raw browser `alert("Failed to delete task")` instead of inline toast or error state. |
| **GAP-01** | Feature Completeness | Low | `frontend/app/page.tsx`, `app/api/tasks.py:40` | **No Status Filtering**: Neither UI nor API allows filtering tasks by status (`pending`, `completed`, etc.). |
| **GAP-02** | Test Coverage | High | `tests/test_tasks.py` | **No Delete Endpoint Tests**: 0 automated tests for task deletion in the test suite. |

---

## 7. Recommended Test Strategy for R2 (Manual & Exploratory QA)

When executing manual and exploratory testing for R2, the team should execute:
1. **Task Creation**:
   - Create task with standard goal: "Calculate fibonacci of 10". Verify redirect to `/tasks/{id}` and presence in `Recently Listed`.
   - Create task with long goal (> 50 chars). Verify title auto-truncation (`[:50]` or `[:47]...`).
   - Create task with special characters and HTML strings (`<script>alert(1)</script>`). Verify safe rendering.
   - Attempt to submit empty / whitespace-only goal. Verify form validation.
2. **Task Viewing**:
   - View task list on dashboard. Verify card contents: ID, StatusBadge, title, goal snippet, reflection count, formatted timestamp.
   - Verify KPI stats card: Observe that Success Rate currently remains `0%` due to BUG-01.
   - Click card: Verify navigation to `/tasks/{id}`.
   - Run task to completion on `/tasks/{id}`: Verify real-time status transitions and terminal stream. Return to dashboard and re-check status badge.
3. **Task Deletion**:
   - Delete a newly created `pending` task by clicking the trash icon. Verify confirmation/removal from dashboard list without page reload.
   - Delete a task that has executed and has `reflections > 0`: Observe if backend throws 500 or if SQLite allows orphaned rows (BUG-02).
   - Test deleting nonexistent task ID via API (`DELETE /api/v1/tasks/999999`) -> Expect 404.
   - Test IDOR deletion via API (User B deletes User A's task ID) -> Expect 404.
