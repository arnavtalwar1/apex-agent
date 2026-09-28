from app.graph.state import AgentState
from app.tools.search import search_web


def researcher_node(state: AgentState) -> AgentState:
	query = state.get("user_goal", "").strip()[:200]
	results = search_web(query)
	state["research_data"] = "\n".join(
		f"- {result['title']}: {result.get('content', '')}" for result in results[:5]
	)
	return state
