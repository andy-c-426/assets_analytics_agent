from agent_service.app.state import AgentState
from agent_service.app.graph import build_graph


def test_build_graph_compiles():
    graph = build_graph()
    assert graph is not None
    compiled = graph.compile()
    assert compiled is not None


def test_initial_state_has_next_action_plan():
    state: AgentState = {
        "symbol": "AAPL",
        "llm_config": {"provider": "claude", "model": "claude-sonnet-4-6", "api_key": "test"},
        "plan": [],
        "tool_results": [],
        "messages": [],
        "steps": [],
        "final_report": None,
        "next_action": "plan",
        "error": None,
    }
    assert state["next_action"] == "plan"
    assert state["symbol"] == "AAPL"


def test_graph_nodes_exist():
    graph = build_graph()
    compiled = graph.compile()
    nodes = compiled.get_graph().nodes
    node_names = {n for n in nodes.keys() if n != "__start__" and n != "__end__"}
    assert "plan" in node_names
    assert "execute_tools" in node_names
    assert "observe" in node_names
    assert "synthesize" in node_names
