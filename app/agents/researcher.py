import re
import urllib.request
from typing import Any
from app.graph.state import AgentState
from app.tools.search import search_web


def fetch_github_raw(repo_path: str) -> str:
	"""Directly fetch repository README from GitHub raw content (0 auth, 0 rate limit, < 0.4s)."""
	clean_repo = repo_path.strip().strip("/")
	for branch in ("main", "master"):
		url = f"https://raw.githubusercontent.com/{clean_repo}/{branch}/README.md"
		try:
			req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
			with urllib.request.urlopen(req, timeout=3.5) as resp:
				data = resp.read().decode("utf-8", errors="replace")
				if data and len(data.strip()) > 50:
					return data.strip()[:2000]
		except Exception:
			continue
	return ""


def researcher_node(state: AgentState) -> dict[str, Any]:
	raw_goal = state.get("user_goal", "").strip()
	repo_match = re.search(r"([\w.-]+/[\w.-]+)", raw_goal)

	# 1. Ground truth repository fetch if target repository is detected
	if repo_match:
		raw_readme = fetch_github_raw(repo_match.group(1))
		if raw_readme:
			combined = f"### GitHub Repository Ground Truth ({repo_match.group(1)}):\n{raw_readme}"
			state["research_data"] = combined
			return {"research_data": combined}

	# 2. General web intelligence lookup
	clean = re.sub(r"(?i)\b(analyse|analyze|generate|create|build|write|report|pipeline|task|objective)\b", "", raw_goal)
	query = " ".join(clean.split())[:120] or raw_goal[:120]

	results = search_web(query)
	compact_snippets = []
	for r in results[:3]:
		title = r.get("title", "Reference")
		content = (r.get("content") or "").strip()[:200]
		compact_snippets.append(f"- **{title}**: {content}")

	combined = "\n".join(compact_snippets)
	state["research_data"] = combined
	return {"research_data": combined}

