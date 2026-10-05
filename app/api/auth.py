from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
	create_access_token,
	create_password_reset_token,
	create_refresh_token,
	decode_token,
	get_current_user,
	get_password_hash,
	revoke_token,
	security,
	verify_password,
)
from app.models.user import User
from app.schemas.auth import (
	ForgotPasswordRequest,
	ForgotPasswordResponse,
	MessageResponse,
	RefreshTokenRequest,
	ResetPasswordRequest,
	TokenResponse,
	UserLogin,
	UserRegister,
	UserResponse,
)


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
	if not user or not user.is_active or not verify_password(user_data.password, user.hashed_password):
		raise HTTPException(status_code=401, detail="Invalid credentials")

	user_claims = {"sub": str(user.id), "email": user.email}
	access_token = create_access_token(user_claims)
	refresh_token = create_refresh_token(user_claims)
	return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
	body: RefreshTokenRequest,
	db: AsyncSession = Depends(get_db),
) -> TokenResponse:
	payload = await decode_token(body.refresh_token, expected_type="refresh")
	user_id = payload.get("sub")
	if not user_id:
		raise HTTPException(status_code=401, detail="Invalid refresh token")

	try:
		user_id = int(user_id)
	except (ValueError, TypeError) as exc:
		raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
	result = await db.execute(select(User).where(User.id == user_id))
	user = result.scalar_one_or_none()
	if not user or not user.is_active:
		raise HTTPException(status_code=401, detail="User account is inactive or not found")

	# Rotate refresh token to prevent replay attacks
	revoke_token(body.refresh_token)
	user_claims = {"sub": str(user.id), "email": user.email}
	new_access = create_access_token(user_claims)
	new_refresh = create_refresh_token(user_claims)
	return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout", response_model=MessageResponse)
async def logout(
	body: RefreshTokenRequest | None = Body(default=None),
	credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
	current_user: User = Depends(get_current_user),
) -> MessageResponse:
	if body:
		payload = await decode_token(body.refresh_token, expected_type="refresh")
		if str(payload.get("sub")) != str(current_user.id):
			raise HTTPException(status_code=401, detail="Invalid refresh token")
		revoke_token(body.refresh_token)
	if credentials and credentials.credentials:
		revoke_token(credentials.credentials)
	return MessageResponse(detail="Successfully logged out and session revoked")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
	return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
	body: ForgotPasswordRequest,
	db: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
	"""
	Generate a secure password reset token for the requested email.
	Always returns a success acknowledgement to prevent user enumeration.
	"""
	result = await db.execute(select(User).where(User.email == body.email))
	user = result.scalar_one_or_none()

	reset_token = None
	if user and user.is_active:
		reset_token = create_password_reset_token({"sub": str(user.id), "email": user.email})

	return ForgotPasswordResponse(
		detail="If the email is registered, password reset instructions have been generated.",
		reset_token=reset_token,
	)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
	body: ResetPasswordRequest,
	db: AsyncSession = Depends(get_db),
) -> MessageResponse:
	"""
	Verify the password reset token and update the user's password.
	"""
	payload = await decode_token(body.token, expected_type="password_reset")
	user_id = payload.get("sub")
	if not user_id:
		raise HTTPException(status_code=400, detail="Invalid reset token payload")

	try:
		user_id_int = int(user_id)
	except (ValueError, TypeError) as exc:
		raise HTTPException(status_code=400, detail="Invalid reset token payload") from exc

	result = await db.execute(select(User).where(User.id == user_id_int))
	user = result.scalar_one_or_none()
	if not user or not user.is_active:
		raise HTTPException(status_code=404, detail="User account not found or inactive")

	# Update password with bcrypt hash and revoke reset token
	user.hashed_password = get_password_hash(body.new_password)
	revoke_token(body.token)
	await db.commit()
	return MessageResponse(detail="Password has been successfully reset. You can now log in.")
