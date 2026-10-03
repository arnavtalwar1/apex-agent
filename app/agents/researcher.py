from typing import Any
from app.graph.state import AgentState
from app.tools.search import search_web


def researcher_node(state: AgentState) -> dict[str, Any]:
	query = state.get("user_goal", "").strip()[:150]
	results = search_web(query)
	# Compact, high-signal intelligence extraction (top 3 snippets capped to avoid token bloat)
	compact_snippets = []
	for r in results[:3]:
		title = r.get("title", "Reference")
		content = (r.get("content") or "").strip()[:200]
		compact_snippets.append(f"- **{title}**: {content}")

	combined = "\n".join(compact_snippets)
	state["research_data"] = combined
	return {"research_data": combined}

