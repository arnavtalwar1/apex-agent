import re
import urllib.request
from typing import Any
from app.graph.state import AgentState
from app.tools.search import search_web


def extract_github_repo(goal: str) -> str | None:
	url_match = re.search(r"https?://(?:www\.)?github\.com/([\w.-]+/[\w.-]+)", goal, re.IGNORECASE)
	if url_match:
		return url_match.group(1).removesuffix(".git")
	# Do not interpret portions of unrelated URLs as owner/repository names.
	without_urls = re.sub(r"https?://\S+", "", goal)
	match = re.search(r"(?<![\w./])([\w.-]+/[\w.-]+)(?![\w./])", without_urls)
	return match.group(1).removesuffix(".git") if match else None


def fetch_github_raw(repo_path: str) -> str:
	"""Fetch a public repository README with bounded network timeouts."""
	clean_repo = repo_path.strip().strip("/")
	for branch in ("main", "master"):
		url = f"https://raw.githubusercontent.com/{clean_repo}/{branch}/README.md"
		try:
			req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
			with urllib.request.urlopen(req, timeout=3.5) as resp:
				data = resp.read().decode("utf-8", errors="replace")
				if data and len(data.strip()) > 50:
					return data.strip()[:12000]
		except Exception:
			continue
	return ""


def researcher_node(state: AgentState) -> dict[str, Any]:
	raw_goal = state.get("user_goal", "").strip()
	repo = extract_github_repo(raw_goal)

	# 1. Ground truth repository fetch if target repository is detected
	if repo:
		raw_readme = fetch_github_raw(repo)
		if raw_readme:
			combined = f"### GitHub README evidence (README only; repository code and metrics have not been inspected) ({repo}):\nSource: https://github.com/{repo}\n{raw_readme}"
			state["research_data"] = combined
			return {"research_data": combined}

	# 2. General web intelligence lookup
	clean = re.sub(r"(?i)\b(analyse|analyze|generate|create|build|write|report|pipeline|task|objective)\b", "", raw_goal)
	query = " ".join(clean.split())[:120] or raw_goal[:120]

	results = search_web(query, max_results=5)
	compact_snippets = []
	for r in results[:5]:
		title = r.get("title", "Reference")
		content = (r.get("content") or "").strip()[:1500]
		url = r.get("url", "")
		if content:
			compact_snippets.append(f"- **{title}**\n  Source: {url or 'URL unavailable'}\n  {content}")

	combined = "\n".join(compact_snippets) or "No external sources could be retrieved. Do not claim live verification or invent current facts; disclose missing evidence."
	state["research_data"] = combined
	return {"research_data": combined}
