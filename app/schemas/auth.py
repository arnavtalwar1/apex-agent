from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
	email: EmailStr
	password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
	full_name: str


class UserLogin(BaseModel):
	email: EmailStr
	password: str


class TokenResponse(BaseModel):
	access_token: str
	refresh_token: str | None = None
	token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
	refresh_token: str


class MessageResponse(BaseModel):
	detail: str


class UserResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	email: str
	full_name: str | None
	is_active: bool
	is_superuser: bool
