from typing import Any
from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_llm(
	temperature: float = 0,
	max_tokens: int | None = None,
	tier: str = "fast",
) -> Any:
	"""
	Returns a LangChain LLM configured with automatic failover/fallback.
	Supports 'fast' (token-efficient, ultra-low latency) and 'reasoning' (high-capacity) tiers.
	Enforces granular max_tokens caps to minimize token waste and eliminate runaway burns.
	"""
	llms = []
	limit_tokens = max_tokens or settings.MAX_TOKENS

	# 1. Groq (Primary - Fastest & Free tier)
	groq_key = settings.GROQ_API_KEY or (
		settings.OPENAI_API_KEY if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("gsk_") else None
	)
	if groq_key:
		# Use fast, token-efficient 20b model by default; reserve 120b for deep reasoning tier
		if tier == "fast":
			groq_model = "openai/gpt-oss-20b"
			backup_groq_model = "openai/gpt-oss-120b"
		else:
			groq_model = "openai/gpt-oss-120b"
			backup_groq_model = "openai/gpt-oss-20b"

		# If user configured a specific non-default model in settings, honor it
		if settings.MODEL_NAME and not any(legacy in settings.MODEL_NAME.lower() for legacy in ["llama-3.3", "llama-3.1", "llama3"]):
			if any(valid in settings.MODEL_NAME.lower() for valid in ["20b", "120b", "qwen", "allam"]):
				groq_model = settings.MODEL_NAME

		# Primary Groq model
		llms.append(
			ChatOpenAI(
				model=groq_model,
				temperature=temperature,
				max_tokens=limit_tokens,
				api_key=groq_key,
				base_url=settings.OPENAI_BASE_URL or "https://api.groq.com/openai/v1",
				max_retries=1,
			)
		)

		# Secondary Groq fallback model
		llms.append(
			ChatOpenAI(
				model=backup_groq_model,
				temperature=temperature,
				max_tokens=limit_tokens,
				api_key=groq_key,
				base_url=settings.OPENAI_BASE_URL or "https://api.groq.com/openai/v1",
				max_retries=1,
			)
		)

	# 2. OpenRouter (Fallback)
	openrouter_key = settings.OPENROUTER_API_KEY or (
		settings.OPENAI_API_KEY if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-or-") else None
	)
	if openrouter_key:
		or_model = settings.MODEL_NAME
		if "/" not in or_model:
			or_model = f"openai/{or_model}"

		llms.append(
			ChatOpenAI(
				model=or_model,
				temperature=temperature,
				max_tokens=limit_tokens,
				api_key=openrouter_key,
				base_url="https://openrouter.ai/api/v1",
				max_retries=1,
			)
		)

	# 3. Standard OpenAI (Last Resort)
	is_standard_openai = (
		settings.OPENAI_API_KEY
		and not settings.OPENAI_API_KEY.startswith("gsk_")
		and not settings.OPENAI_API_KEY.startswith("sk-or-")
	)
	if is_standard_openai:
		llms.append(
			ChatOpenAI(
				model=settings.MODEL_NAME,
				temperature=temperature,
				max_tokens=limit_tokens,
				api_key=settings.OPENAI_API_KEY,
				base_url=settings.OPENAI_BASE_URL,
				max_retries=1,
			)
		)

	if not llms:
		return ChatOpenAI(
			model=settings.MODEL_NAME,
			temperature=temperature,
			max_tokens=limit_tokens,
			api_key="dummy-key",
		)

	main_llm = llms[0]
	fallbacks = llms[1:]

	if fallbacks:
		return main_llm.with_fallbacks(fallbacks)

	return main_llm
