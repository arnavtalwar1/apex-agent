import re
from typing import Any
from app.graph.state import AgentState
from app.tools.search import search_web


def researcher_node(state: AgentState) -> dict[str, Any]:
	raw_goal = state.get("user_goal", "").strip()
	# ponytail: regex targets owner/repo or strips prompt noise for precision search
	repo_match = re.search(r"([\w.-]+/[\w.-]+)", raw_goal)
	if repo_match:
		query = f"{repo_match.group(1)} github README architecture"
	else:
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

