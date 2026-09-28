import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.executor import executor_node
from app.agents.planner import planner_node
from app.agents.reflector import reflector_node
from app.agents.researcher import researcher_node
from app.agents.supervisor import supervisor_node
from app.core.config import settings
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("executor", executor_node)
workflow.add_node("reflector", reflector_node)


VALID_NODES = {"planner", "researcher", "executor", "reflector"}


def route_next(state: AgentState) -> str:
	node = state.get("next_node", "").strip().lower()
	return node if node in VALID_NODES and state.get("iteration_count", 0) < settings.MAX_ITERATIONS else END


workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
	"supervisor",
	route_next,
	{
		"planner": "planner",
		"researcher": "researcher",
		"executor": "executor",
		"reflector": "reflector",
		END: END,
	},
)
for node in ("planner", "researcher", "executor", "reflector"):
	workflow.add_edge(node, "supervisor")


def get_checkpointer():
	try:
		from langgraph.checkpoint.redis import RedisSaver
		saver = RedisSaver(settings.REDIS_URL)
		saver.setup()
		return saver
	except Exception as error:
		logger.warning("Redis checkpointer unavailable (%s). Falling back to MemorySaver.", error)
		return MemorySaver()


checkpointer = get_checkpointer()
app_graph = workflow.compile(checkpointer=checkpointer)

