# agent/graph.py

from langgraph.graph import StateGraph, END
from agent.state import IntelligenceState
from agent.nodes import (
    load_data,
    find_gaps,
    enrich_gaps,
    classify_severity,
    escalate,
    monitor,
    log_healthy,
    generate_recommendation,
    route_by_severity
)


def build_graph():
    """
    Assembles all nodes and edges into a compiled LangGraph agent
    """
    graph = StateGraph(IntelligenceState)
    
    # --- Add all nodes ---
    graph.add_node("load_data", load_data)
    graph.add_node("find_gaps", find_gaps)
    graph.add_node("enrich_gaps", enrich_gaps)
    graph.add_node("classify_severity", classify_severity)
    graph.add_node("escalate", escalate)
    graph.add_node("monitor", monitor)
    graph.add_node("log_healthy", log_healthy)
    graph.add_node("generate_recommendation", generate_recommendation)
    
    # --- Add edges ---
    
    # Entry point
    graph.set_entry_point("load_data")
    
    # Fixed edges — always go to next node
    graph.add_edge("load_data", "find_gaps")
    graph.add_edge("find_gaps", "enrich_gaps")
    graph.add_edge("enrich_gaps", "classify_severity")
    
    # Conditional edge — branches based on severity
    graph.add_conditional_edges(
        "classify_severity",
        route_by_severity,
        {
            "escalate": "escalate",
            "monitor": "monitor",
            "log_healthy": "log_healthy"
        }
    )
    
    # All three severity paths converge into recommendation
    graph.add_edge("escalate", "generate_recommendation")
    graph.add_edge("monitor", "generate_recommendation")
    graph.add_edge("log_healthy", "generate_recommendation")
    
    # End
    graph.add_edge("generate_recommendation", END)
    
    return graph.compile()