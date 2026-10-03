import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
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
	"""Executes the task workflow asynchronously, persisting logs, reflections, and output."""
	async with AsyncSessionLocal() as session:
		db_task = await session.get(Task, task_id)
		if not db_task:
			return

		trace = start_trace(task_id=task_id, custom_trace_id=thread_id)
		db_task.trace_id = trace.trace_id
		db_task.status = TaskStatus.PLANNING
		await session.commit()

		config = {"configurable": {"thread_id": thread_id}}
		initial_state: AgentState = {
			"user_goal": db_task.goal,
			"plan": "",
			"research_data": "",
			"execution_result": "",
			"reflection_critique": "",
			"iteration_count": 0,
			"next_node": "",
			"error": "",
		}

		try:
			async for update in app_graph.astream(initial_state, config, stream_mode="updates"):
				if "supervisor" in update:
					node = update["supervisor"].get("next_node", "").lower()
					status_map = {
						"planner": TaskStatus.PLANNING,
						"researcher": TaskStatus.RESEARCHING,
						"executor": TaskStatus.EXECUTING,
						"reflector": TaskStatus.REFLECTING,
					}
					if node in status_map and db_task:
						db_task.current_node = node
						db_task.status = status_map[node]
						await session.commit()

				if "reflector" in update and db_task:
					reflector_state = update["reflector"]
					reflection = Reflection(
						task_id=db_task.id,
						iteration=reflector_state.get("iteration_count", 1),
						failed_node="executor",
						error_trace=db_task.current_node or "executor",
						verbal_critique=reflector_state.get("reflection_critique", ""),
						corrected_strategy=reflector_state.get("plan", ""),
					)
					session.add(reflection)
					await session.commit()

			final_state = await app_graph.aget_state(config)
			state = final_state.values if final_state and final_state.values else {}
			if db_task:
				plan_content = state.get("plan", "")
				exec_res = state.get("execution_result", "")
				research_data = state.get("research_data", "")

				if exec_res and exec_res.strip() and not exec_res.startswith("FAILED") and not exec_res.startswith("EXCEPTION") and exec_res != "SUCCESS:\nNo output":
					if plan_content and "SUCCESS:" in exec_res:
						db_task.final_output = f"{plan_content}\n\n---\n### 🧪 Sandbox Execution Output\n```\n{exec_res}\n```"
					else:
						db_task.final_output = exec_res
				elif plan_content:
					verification_badge = "\n\n---\n✅ **Sandbox Verification:** Execution verified successfully (exit code 0)." if "SUCCESS" in exec_res else ""
					failure_note = f"\n\n---\n### 🧪 Sandbox Verification Note\n```\n{exec_res}\n```" if (exec_res and "FAILED" in exec_res) else ""
					db_task.final_output = f"{plan_content}{verification_badge}{failure_note}"
				elif research_data:
					db_task.final_output = research_data
				else:
					db_task.final_output = exec_res or "Task completed successfully."

				db_task.plan = plan_content
				db_task.reflection_count = state.get("iteration_count", 0)
				db_task.status = TaskStatus.FAILED if state.get("error") else TaskStatus.COMPLETED
				db_task.token_cost = trace.estimated_cost_usd
				await session.commit()
		except Exception as err:
			if db_task:
				db_task.status = TaskStatus.FAILED
				db_task.final_output = f"Workflow execution error: {err}"
				await session.commit()
		finally:
			finish_trace(trace.trace_id)


@router.post("/", response_model=TaskResponse)
async def create_task(
	task_data: TaskCreate,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Task:
	try:
		requires_appr = task_data.requires_approval or settings.REQUIRE_APPROVAL_FOR_CODE_EXECUTION
		task = Task(
			user_id=current_user.id,
			title=task_data.title or task_data.goal[:50],
			goal=task_data.goal,
			status=TaskStatus.PENDING,
			requires_approval=requires_appr,
			approval_status="pending" if requires_appr else "none",
		)
		db.add(task)
		await db.commit()
		await db.refresh(task)
		return task
	except Exception as exc:
		await db.rollback()
		import traceback
		trace = traceback.format_exc()
		print(f"Task creation exception: {trace}")
		raise HTTPException(status_code=400, detail=f"Database error on task creation: {exc}")


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
	limit: int = 50,
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

	if task.requires_approval and task.approval_status != "approved":
		task.status = TaskStatus.AWAITING_APPROVAL
		await db.commit()
		return {
			"task_id": task.id,
			"status": "awaiting_approval",
			"message": "Human approval required before background execution.",
		}

	thread_id = str(uuid.uuid4())
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
	if task.requires_approval and task.approval_status != "approved":
		task.status = TaskStatus.AWAITING_APPROVAL
		await db.commit()

		async def approval_required_stream():
			yield f"data: {json.dumps({'status': 'awaiting_approval', 'message': 'Human approval required before execution.'})}\n\n"
			yield "data: [DONE]\n\n"

		return StreamingResponse(approval_required_stream(), media_type="text/event-stream")

	thread_id = str(uuid.uuid4())
	trace = start_trace(task_id=task_id, custom_trace_id=thread_id)
	task.trace_id = trace.trace_id
	config = {"configurable": {"thread_id": thread_id}}
	initial_state: AgentState = {
		"user_goal": task.goal,
		"plan": "",
		"research_data": "",
		"execution_result": "",
		"reflection_critique": "",
		"iteration_count": 0,
		"next_node": "",
		"error": "",
	}
	task.status = TaskStatus.PLANNING
	await db.commit()

	async def event_generator():
		async with AsyncSessionLocal() as session:
			db_task = await session.get(Task, task_id)
			try:
				async for update in app_graph.astream(initial_state, config, stream_mode="updates"):
					if "supervisor" in update:
						state = update["supervisor"]
						node = state.get("next_node", "").lower()
						status_map = {
							"planner": TaskStatus.PLANNING,
							"researcher": TaskStatus.RESEARCHING,
							"executor": TaskStatus.EXECUTING,
							"reflector": TaskStatus.REFLECTING,
						}
						if node in status_map and db_task:
							db_task.current_node = node
							db_task.status = status_map[node]
							await session.commit()

					if "reflector" in update and db_task:
						reflector_state = update["reflector"]
						reflection = Reflection(
							task_id=db_task.id,
							iteration=reflector_state.get("iteration_count", 1),
							failed_node="executor",
							error_trace=db_task.current_node or "executor",
							verbal_critique=reflector_state.get("reflection_critique", ""),
							corrected_strategy=reflector_state.get("plan", ""),
						)
						session.add(reflection)
						await session.commit()

					yield f"data: {json.dumps(update, default=str)}\n\n"

				final_state = await app_graph.aget_state(config)
				state = final_state.values if final_state and final_state.values else {}
				if db_task:
					plan_content = state.get("plan", "")
					exec_res = state.get("execution_result", "")
					research_data = state.get("research_data", "")

					if exec_res and exec_res.strip() and not exec_res.startswith("FAILED") and not exec_res.startswith("EXCEPTION") and exec_res != "SUCCESS:\nNo output":
						if plan_content and "SUCCESS:" in exec_res:
							db_task.final_output = f"{plan_content}\n\n---\n### 🧪 Sandbox Execution Output\n```\n{exec_res}\n```"
						else:
							db_task.final_output = exec_res
					elif plan_content:
						verification_badge = "\n\n---\n✅ **Sandbox Verification:** Execution verified successfully (exit code 0)." if "SUCCESS" in exec_res else ""
						failure_note = f"\n\n---\n### 🧪 Sandbox Verification Note\n```\n{exec_res}\n```" if (exec_res and "FAILED" in exec_res) else ""
						db_task.final_output = f"{plan_content}{verification_badge}{failure_note}"
					elif research_data:
						db_task.final_output = research_data
					else:
						db_task.final_output = exec_res or "Task completed successfully."

					db_task.plan = plan_content
					db_task.reflection_count = state.get("iteration_count", 0)
					db_task.status = TaskStatus.FAILED if state.get("error") else TaskStatus.COMPLETED
					db_task.token_cost = trace.estimated_cost_usd
					await session.commit()
				yield f"data: {json.dumps({'status': 'completed'})}\n\n"
			except Exception as err:
				if db_task:
					db_task.status = TaskStatus.FAILED
					db_task.final_output = f"Workflow execution error: {err}"
					await session.commit()
				yield f"data: {json.dumps({'error': str(err)})}\n\n"
			finally:
				finish_trace(trace.trace_id)
				yield "data: [DONE]\n\n"

	return StreamingResponse(event_generator(), media_type="text/event-stream")
