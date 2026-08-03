from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.agents.nodes import scrapbook_node, logistics_node, booking_node, supervisor_node

def build_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("Orchestrator Agent", supervisor_node)
    workflow.add_node("Scrapbook Agent", scrapbook_node)
    workflow.add_node("Logistics Agent", logistics_node)
    workflow.add_node("Booking Agent", booking_node)

    # Routing edges
    workflow.add_edge(START, "Orchestrator Agent")

    # All workers report back to orchestrator
    workflow.add_edge("Scrapbook Agent", "Orchestrator Agent")
    workflow.add_edge("Logistics Agent", "Orchestrator Agent")
    workflow.add_edge("Booking Agent", "Orchestrator Agent")

    def router(state: AgentState):
        return state.get("next", "FINISH")

    workflow.add_conditional_edges(
        "Orchestrator Agent",
        router,
        {
            "Scrapbook Agent": "Scrapbook Agent",
            "Logistics Agent": "Logistics Agent",
            "Booking Agent": "Booking Agent",
            "FINISH": END
        }
    )

    return workflow
