

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


import uuid


class TokenBlacklist:
	"""
	Thread-safe in-memory token blacklist with auto-cleanup of expired entries.
	Designed for seamless drop-in extension with Redis in clustered environments.
	"""

	def __init__(self):
		self._blacklisted: dict[str, float] = {}

	def revoke(self, jti: str, exp_timestamp: float) -> None:
		self._blacklisted[jti] = exp_timestamp
		self._cleanup()

	def is_revoked(self, jti: str) -> bool:
		self._cleanup()
		return jti in self._blacklisted

	def _cleanup(self) -> None:
		now = datetime.now(timezone.utc).timestamp()
		expired_jtis = [jti for jti, exp in self._blacklisted.items() if exp < now]
		for jti in expired_jtis:
			self._blacklisted.pop(jti, None)


token_blacklist = TokenBlacklist()


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + (
		expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
	)
	to_encode["exp"] = expire
	if "type" not in to_encode:
		to_encode["type"] = "access"
	if "jti" not in to_encode:
		to_encode["jti"] = str(uuid.uuid4())
	return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + (
		expires_delta or timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
	)
	to_encode["exp"] = expire
	to_encode["type"] = "refresh"
	to_encode["jti"] = str(uuid.uuid4())
	return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def revoke_token(token: str) -> None:
	try:
		payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
		jti = payload.get("jti")
		exp = payload.get("exp")
		if jti and exp:
			token_blacklist.revoke(jti, float(exp))
	except JWTError:
		pass


async def decode_token(token: str, expected_type: Optional[str] = None) -> dict[str, Any]:
	try:
		payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
	except JWTError as error:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from error

	jti = payload.get("jti")
	if jti and token_blacklist.is_revoked(jti):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

	token_type = payload.get("type")
	# If expected_type is specified and token explicitly declares a type, verify matching type
	if expected_type and token_type and token_type != expected_type:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=f"Invalid token type: expected '{expected_type}', got '{token_type}'",
		)

	return payload


async def get_current_user(
	credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
	token: Optional[str] = None,
	db: AsyncSession = Depends(get_db),
) -> User:
	raw_token = credentials.credentials if credentials else token
	if not raw_token:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

	payload = await decode_token(raw_token, expected_type="access")
	user_id = payload.get("sub")
	if not user_id:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID")

	try:
		user_id_value = int(user_id)
	except (TypeError, ValueError) as error:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID") from error

	result = await db.execute(select(User).where(User.id == user_id_value))
	user = result.scalar_one_or_none()
	if not user or not user.is_active:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
	return user

