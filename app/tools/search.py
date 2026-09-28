from typing import Any

from app.core.config import settings


def search_web(query: str, max_results: int = 3) -> list[dict[str, Any]]:
	"""Search Tavily first and use DuckDuckGo as a no-key fallback."""
	if settings.TAVILY_API_KEY:
		try:
			from tavily import TavilyClient

			response = TavilyClient(api_key=settings.TAVILY_API_KEY).search(
				query, max_results=max_results
			)
			return [
				{
					"title": result["title"],
					"content": result["content"],
					"url": result.get("url", ""),
				}
				for result in response.get("results", [])
			]
		except Exception as error:
			print(f"Tavily error: {error}")

	try:
		from duckduckgo_search import DDGS

		with DDGS() as ddgs:
			results = list(ddgs.text(query, max_results=max_results))
		return [
			{"title": result["title"], "content": result["body"], "url": result.get("href", "")}
			for result in results
		]
	except Exception as error:
		return [{"title": "Search unavailable", "content": f"Error: {error}", "url": ""}]
