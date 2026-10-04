import asyncio
import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_db
from app.core.observability import finish_trace, start_trace
from app.core.security import get_current_user
from app.graph.state import AgentState
from app.graph.workflow import app_graph
from app.models.reflection import Reflection
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse


router = APIRouter(prefix="/tasks", tags=["Tasks"])


async def execute_task_lifecycle(task_id: int, thread_id: str):
	"""Drain the same lifecycle used by the streaming endpoint."""
	async for _ in task_events(task_id, thread_id):
		pass


async def claim_task(db: AsyncSession, task: Task) -> None:
	"""Atomically claim execution so concurrent requests cannot run a task twice."""
	active = [TaskStatus.PLANNING, TaskStatus.RESEARCHING, TaskStatus.EXECUTING, TaskStatus.REFLECTING]
	result = await db.execute(
		update(Task).where(Task.id == task.id, Task.status.not_in(active + [TaskStatus.REJECTED]))
		.values(status=TaskStatus.PLANNING, current_node="supervisor", final_output=None)
	)
	if result.rowcount != 1:
		raise HTTPException(status_code=409, detail="Task is already running or has been rejected")
	await db.commit()


async def task_events(task_id: int, thread_id: str):
	trace = start_trace(task_id=task_id, custom_trace_id=thread_id)
	config = {"configurable": {"thread_id": thread_id}}
	async with AsyncSessionLocal() as session:
		db_task = await session.get(Task, task_id)
		if not db_task:
			finish_trace(trace.trace_id)
			return
		db_task.trace_id = trace.trace_id
		initial_state: AgentState = {
			"user_goal": db_task.goal, "plan": "", "research_data": "",
			"execution_result": "", "reflection_critique": "", "iteration_count": 0,
			"next_node": "", "error": "", "execution_mode": "sequential",
		}
		accumulated_state = dict(initial_state)
		try:
			async for update in app_graph.astream(initial_state, config, stream_mode="updates"):
				previous_error = accumulated_state.get("error", "")
				for node_name, node_state in update.items():
					if isinstance(node_state, dict):
						accumulated_state.update(node_state)
					if db_task and isinstance(node_state, dict):
						n_lower = node_name.lower()
						if n_lower == "supervisor":
							next_n = node_state.get("next_node", "").lower()
							if next_n:
								db_task.current_node = next_n
						elif n_lower == "planner":
							db_task.current_node = "planner"
							db_task.status = TaskStatus.PLANNING
							if "plan" in node_state:
								db_task.plan = node_state["plan"]
						elif n_lower == "researcher":
							db_task.current_node = "researcher"
							db_task.status = TaskStatus.RESEARCHING
						elif n_lower == "executor":
							db_task.current_node = "executor"
							db_task.status = TaskStatus.EXECUTING
						elif n_lower == "reflector":
							db_task.current_node = "reflector"
							db_task.status = TaskStatus.REFLECTING
						await session.commit()

				if "reflector" in update and db_task:
					reflector_state = update["reflector"]
					reflection = Reflection(
						task_id=db_task.id,
						iteration=reflector_state.get("iteration_count", 1),
						failed_node="executor",
						error_trace=str(previous_error),
						verbal_critique=reflector_state.get("reflection_critique", ""),
						corrected_strategy=reflector_state.get("plan", ""),
					)
					session.add(reflection)
					await session.commit()

				yield f"data: {json.dumps(update, default=str)}\n\n"

			final_state = await app_graph.aget_state(config)
			state = final_state.values if final_state and final_state.values else dict(accumulated_state)
			if db_task:
				plan_content = state.get("plan", "")
				exec_res = (state.get("execution_result") or "").strip()
				error = (state.get("error") or "").strip()

				if error or not exec_res or exec_res.startswith("FAILED") or exec_res.startswith("EXCEPTION"):
					if plan_content and state.get("user_goal"):
						try:
							from app.agents.executor import synthesize_answer
							diag_note = f"Execution note: Sandbox execution encountered: {error or exec_res}. Synthesizing comprehensive technical deliverable from research context and strategic plan."
							fallback = await asyncio.to_thread(synthesize_answer, state, sandbox_output=diag_note, executed=False)
							if fallback.get("execution_result") and not fallback.get("error"):
								exec_res = fallback["execution_result"]
								error = ""
						except Exception:
							pass

				if error:
					db_task.status = TaskStatus.FAILED
					db_task.final_output = exec_res if (exec_res and "failed" in exec_res.lower()) else (f"{exec_res}\n\nError: {error}" if exec_res else error)
				elif exec_res and (exec_res.startswith("FAILED") or exec_res.startswith("EXCEPTION") or exec_res.startswith("Answer generation failed")):
					db_task.status = TaskStatus.FAILED
					db_task.final_output = exec_res
				elif exec_res:
					db_task.status = TaskStatus.COMPLETED
					db_task.final_output = exec_res
				else:
					db_task.status = TaskStatus.FAILED
					db_task.final_output = "Answer generation failed: No deliverable was produced."

				db_task.plan = plan_content
				db_task.reflection_count = state.get("iteration_count", 0)
				db_task.token_cost = trace.estimated_cost_usd
				await session.commit()

			final_status = db_task.status.value if db_task else ("failed" if state.get("error") else "completed")
			yield f"data: {json.dumps({'status': final_status})}\n\n"
			if final_status == "failed":
				err_msg = (db_task.final_output if db_task else state.get("error")) or "Execution failed."
				yield f"data: {json.dumps({'error': err_msg})}\n\n"
		except (asyncio.CancelledError, GeneratorExit):
			db_task.status = TaskStatus.FAILED
			db_task.final_output = "Execution interrupted. You can run this task again."
			await asyncio.shield(session.commit())
			raise
		except Exception as err:
			if db_task:
				db_task.status = TaskStatus.FAILED
				db_task.final_output = f"Workflow execution error: {err}"
				await session.commit()
			yield f"data: {json.dumps({'error': str(err)})}\n\n"
		finally:
			finish_trace(trace.trace_id)
		yield "data: [DONE]\n\n"


@router.post("/", response_model=TaskResponse)
async def create_task(
	task_data: TaskCreate,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Task:
	requires_appr = task_data.requires_approval or settings.REQUIRE_APPROVAL_FOR_CODE_EXECUTION
	task = Task(
		user_id=current_user.id, title=task_data.title or task_data.goal[:50],
		goal=task_data.goal, status=TaskStatus.PENDING,
		requires_approval=requires_appr, approval_status="pending" if requires_appr else "none",
	)
	db.add(task)
	await db.commit()
	await db.refresh(task)
	return task

@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
	limit: int = Query(default=50, ge=1, le=200),
) -> list[Task]:
	result = await db.execute(
		select(Task)
		.where(Task.user_id == current_user.id)
		.order_by(desc(Task.created_at))
		.limit(limit)
	)
	return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Task:
	result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
	task = result.scalar_one_or_none()
	if not task:
		raise HTTPException(status_code=404, detail="Task not found")
	return task


@router.post("/{task_id}/approve", response_model=TaskResponse)
async def approve_task(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Task:
	result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
	task = result.scalar_one_or_none()
	if not task:
		raise HTTPException(status_code=404, detail="Task not found")

	if task.status in {TaskStatus.PLANNING, TaskStatus.RESEARCHING, TaskStatus.EXECUTING, TaskStatus.REFLECTING}:
		raise HTTPException(status_code=409, detail="Cannot modify a running task")

	task.approval_status = "approved"
	if task.status == TaskStatus.AWAITING_APPROVAL:
		task.status = TaskStatus.PENDING
	await db.commit()
	await db.refresh(task)
	return task


@router.post("/{task_id}/reject", response_model=TaskResponse)
async def reject_task(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Task:
	result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
	task = result.scalar_one_or_none()
	if not task:
		raise HTTPException(status_code=404, detail="Task not found")

	if task.status in {TaskStatus.PLANNING, TaskStatus.RESEARCHING, TaskStatus.EXECUTING, TaskStatus.REFLECTING}:
		raise HTTPException(status_code=409, detail="Cannot modify a running task")

	task.approval_status = "rejected"
	task.status = TaskStatus.REJECTED
	task.final_output = "Task execution rejected by user."
	await db.commit()
	await db.refresh(task)
	return task


@router.delete("/{task_id}")
async def delete_task(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
	task = result.scalar_one_or_none()
	if not task:
		raise HTTPException(status_code=404, detail="Task not found")

	if task.status in {TaskStatus.PLANNING, TaskStatus.RESEARCHING, TaskStatus.EXECUTING, TaskStatus.REFLECTING}:
		raise HTTPException(status_code=409, detail="Cannot modify a running task")

	await db.delete(task)
	await db.commit()
	return {"detail": "Task deleted successfully"}


@router.post("/{task_id}/run-background")
async def run_task_background(
	task_id: int,
	background_tasks: BackgroundTasks,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
	task = result.scalar_one_or_none()
	if not task:
		raise HTTPException(status_code=404, detail="Task not found")

	if task.status == TaskStatus.REJECTED:
		raise HTTPException(status_code=409, detail="Task has been rejected")

	if task.requires_approval and task.approval_status != "approved":
		task.status = TaskStatus.AWAITING_APPROVAL
		await db.commit()
		return {
			"task_id": task.id,
			"status": "awaiting_approval",
			"message": "Human approval required before background execution.",
		}

	thread_id = str(uuid.uuid4())
	await claim_task(db, task)
	background_tasks.add_task(execute_task_lifecycle, task_id, thread_id)
	return {
		"task_id": task.id,
		"status": "started",
		"thread_id": thread_id,
		"mode": "background",
	}


@router.api_route("/{task_id}/run", methods=["GET", "POST"])
async def run_task(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
	result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
	task = result.scalar_one_or_none()
	if not task:
		raise HTTPException(status_code=404, detail="Task not found")

	# Check Human-in-the-Loop approval gate
	if task.status == TaskStatus.REJECTED:
		raise HTTPException(status_code=409, detail="Task has been rejected")

	if task.requires_approval and task.approval_status != "approved":
		task.status = TaskStatus.AWAITING_APPROVAL
		await db.commit()

		async def approval_required_stream():
			yield f"data: {json.dumps({'status': 'awaiting_approval', 'message': 'Human approval required before execution.'})}\n\n"
			yield "data: [DONE]\n\n"

		return StreamingResponse(approval_required_stream(), media_type="text/event-stream")

	thread_id = str(uuid.uuid4())
	await claim_task(db, task)
	return StreamingResponse(
		task_events(task_id, thread_id), media_type="text/event-stream",
		headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
	)
