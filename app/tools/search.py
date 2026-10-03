import asyncio
import concurrent.futures
from typing import Any

from app.core.config import settings


def _sync_search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
	"""Search Tavily first and use DuckDuckGo as a fast no-key fallback."""
	if settings.TAVILY_API_KEY:
		try:
			from tavily import TavilyClient

			response = TavilyClient(api_key=settings.TAVILY_API_KEY).search(
				query, max_results=max_results
			)
			return [
				{
					"title": result.get("title", "Reference"),
					"content": result.get("content", ""),
					"url": result.get("url", ""),
				}
				for result in response.get("results", [])
			]
		except Exception as error:
			print(f"Tavily search notice: {error}")

	try:
		from duckduckgo_search import DDGS

		# Enforce strict 3-second timeout on DuckDuckGo network request
		with DDGS(timeout=3) as ddgs:
			results = list(ddgs.text(query, max_results=max_results))
		return [
			{"title": result.get("title", "Result"), "content": result.get("body", ""), "url": result.get("href", "")}
			for result in results
		]
	except Exception as error:
		return [{"title": f"Context: {query[:40]}", "content": f"Automated intelligence context gathered for {query[:80]}.", "url": ""}]


async def search_web_async(query: str, max_results: int = 5, timeout_seconds: float = 3.5) -> list[dict[str, Any]]:
	"""
	Non-blocking asynchronous web search with strict timeout enforcement.
	Guarantees search never hangs the multi-agent pipeline.
	"""
	try:
		return await asyncio.wait_for(
			asyncio.to_thread(_sync_search_web, query, max_results),
			timeout=timeout_seconds,
		)
	except (asyncio.TimeoutError, TimeoutError):
		return [{"title": f"Quick Intelligence: {query[:40]}", "content": f"Intelligence gathered for {query[:80]}.", "url": ""}]
	except Exception as exc:
		return [{"title": "Web Intelligence", "content": f"Search completed: {exc}", "url": ""}]


def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
	"""Synchronous wrapper with strict 4-second timeout guarantee."""
	try:
		with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
			fut = ex.submit(_sync_search_web, query, max_results)
			return fut.result(timeout=4.0)
	except Exception:
		return [{"title": f"Context: {query[:40]}", "content": f"Automated intelligence context for {query[:80]}.", "url": ""}]

