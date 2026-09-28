import os
import subprocess
import sys
import tempfile

from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.graph.state import AgentState


def extract_code(text: str) -> str:
	delim = "```python" if "```python" in text else "```" if "```" in text else None
	return text.split(delim, 1)[1].split("```", 1)[0].strip() if delim else ""


synth_prompt = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			"""You are an executive deliverable synthesizer.
Using the research findings, plan, and user goal, produce a direct, polished, high-value final answer that directly satisfies the user's objective (e.g. structured bulleted list, exact prices, key specifications, or executive summary). Do not write placeholder text.""",
		),
		(
			"human",
			"""Objective: {user_goal}

Research Findings:
{research_data}

Plan:
{plan}""",
		),
	]
)


def executor_node(state: AgentState) -> AgentState:
	plan_text = state.get("plan", "")
	code = extract_code(plan_text)

	if not code:
		if state.get("research_data"):
			try:
				model = get_llm(temperature=0.2, max_tokens=1024)
				synthesis = (synth_prompt | model).invoke(
					{
						"user_goal": state.get("user_goal", ""),
						"research_data": state.get("research_data", ""),
						"plan": plan_text,
					}
				).content
				state["execution_result"] = synthesis
			except Exception as err:
				state["execution_result"] = f"RESEARCH DATA:\n{state.get('research_data')}"
		else:
			state["execution_result"] = "Plan verified: No executable Python code required."
		state["error"] = ""
		return state

	tmp_path = ""
	try:
		with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as file:
			file.write(code)
			tmp_path = file.name

		environment = {
			key: value
			for key, value in os.environ.items()
			if key not in {"OPENAI_API_KEY", "TAVILY_API_KEY"}
		}
		environment["PYTHONIOENCODING"] = "utf-8"
		result = subprocess.run(
			[sys.executable, tmp_path],
			capture_output=True,
			text=True,
			encoding="utf-8",
			errors="replace",
			timeout=30,
			env=environment,
			check=False,
		)
		if result.returncode == 0:
			state["execution_result"] = f"SUCCESS:\n{result.stdout or 'No output'}"
			state["error"] = ""
		else:
			state["execution_result"] = f"FAILED (code {result.returncode}):\n{result.stderr}"
			state["error"] = result.stderr
	except subprocess.TimeoutExpired:
		state["execution_result"] = "TIMEOUT: Execution exceeded 30 seconds"
		state["error"] = "Timeout"
	except Exception as error:
		state["execution_result"] = f"EXCEPTION: {error}"
		state["error"] = str(error)
	finally:
		if tmp_path:
			try:
				os.unlink(tmp_path)
			except OSError:
				pass
	return state
