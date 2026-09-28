from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
	create_access_token,
	get_current_user,
	get_password_hash,
	verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)) -> User:
	result = await db.execute(select(User).where(User.email == user_data.email))
	if result.scalar_one_or_none():
		raise HTTPException(status_code=400, detail="Email already registered")

	user = User(
		email=user_data.email,
		hashed_password=get_password_hash(user_data.password),
		full_name=user_data.full_name,
	)
	db.add(user)
	await db.commit()
	await db.refresh(user)
	return user


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
	result = await db.execute(select(User).where(User.email == user_data.email))
	user = result.scalar_one_or_none()
	if not user or not verify_password(user_data.password, user.hashed_password):
		raise HTTPException(status_code=401, detail="Invalid credentials")

	return TokenResponse(access_token=create_access_token({"sub": str(user.id), "email": user.email}))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
	return current_user
