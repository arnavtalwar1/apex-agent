

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
	password_bytes = plain_password.encode("utf-8")
	if len(password_bytes) > 72:
		password_bytes = password_bytes[:72]
	return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
	password_bytes = password.encode("utf-8")
	if len(password_bytes) > 72:
		password_bytes = password_bytes[:72]
	salt = bcrypt.gensalt()
	return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + (
		expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
	)
	to_encode["exp"] = expire
	return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def decode_token(token: str) -> dict[str, Any]:
	try:
		return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
	except JWTError as error:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from error


async def get_current_user(
	credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
	token: Optional[str] = None,
	db: AsyncSession = Depends(get_db),
) -> User:
	raw_token = credentials.credentials if credentials else token
	if not raw_token:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

	payload = await decode_token(raw_token)
	user_id = payload.get("sub")
	if not user_id:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID")

	try:
		user_id_value = int(user_id)
	except (TypeError, ValueError) as error:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID") from error

	result = await db.execute(select(User).where(User.id == user_id_value))
	user = result.scalar_one_or_none()
	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
	return user

