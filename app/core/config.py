import re
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	APP_NAME: str = "APEX Agent"
	DEBUG: bool = False

	OPENAI_API_KEY: Optional[str] = None
	OPENAI_BASE_URL: Optional[str] = None
	GROQ_API_KEY: Optional[str] = None
	OPENROUTER_API_KEY: Optional[str] = None
	TAVILY_API_KEY: Optional[str] = None

	DATABASE_URL: str = "sqlite+aiosqlite:///./apex.db"
	REDIS_URL: Optional[str] = None

	JWT_SECRET_KEY: str = "apex-production-secret-key-replace-with-env"
	JWT_ALGORITHM: str = "HS256"
	JWT_EXPIRE_MINUTES: int = 60
	JWT_REFRESH_EXPIRE_DAYS: int = 7

	# Sandbox & Security
	SECURE_SANDBOX_ENABLED: bool = True
	MAX_CODE_TIMEOUT_SECONDS: int = 15
	MAX_CODE_OUTPUT_CHARS: int = 25000
	REQUIRE_APPROVAL_FOR_CODE_EXECUTION: bool = False

	# Governance, Cost limits & Observability
	MAX_COST_PER_TASK_USD: float = 0.50
	ENABLE_OBSERVABILITY_TRACING: bool = True

	MAX_ITERATIONS: int = 2
	MAX_TOKENS: int = 4096
	MODEL_NAME: str = "gpt-4o-mini"

	ALLOWED_ORIGINS: str = "*"
	ALLOWED_HOSTS: str = "*"

	@property
	def async_database_url(self) -> str:
		return re.sub(r"^postgres(ql)?://", "postgresql+asyncpg://", self.DATABASE_URL)

	@property
	def origins_list(self) -> list[str]:
		if not self.ALLOWED_ORIGINS or self.ALLOWED_ORIGINS.strip() == "*":
			return ["*"]
		return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

	@property
	def hosts_list(self) -> list[str]:
		if not self.ALLOWED_HOSTS or self.ALLOWED_HOSTS.strip() == "*":
			return ["*"]
		return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

	model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
