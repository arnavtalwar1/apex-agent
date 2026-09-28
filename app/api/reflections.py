from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.reflection import Reflection
from app.models.task import Task
from app.models.user import User
from app.schemas.reflection import ReflectionResponse


router = APIRouter(prefix="/reflections", tags=["Reflections"])


@router.get("/task/{task_id}", response_model=list[ReflectionResponse])
async def get_task_reflections(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> list[Reflection]:
	result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
	if not result.scalar_one_or_none():
		raise HTTPException(status_code=404, detail="Task not found")

	result = await db.execute(
		select(Reflection).where(Reflection.task_id == task_id).order_by(desc(Reflection.created_at))
	)
	return list(result.scalars().all())
