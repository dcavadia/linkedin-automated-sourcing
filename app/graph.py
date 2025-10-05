import sys
import os
# Optional path patch (skip if using -m)
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.state import AppState, Candidate
from typing import Dict, Any

# Initialize checkpointer
checkpointer = MemorySaver()

# Create the graph builder
workflow = StateGraph(AppState)

# Dummy node function
def dummy_node(state: AppState) -> AppState:
    """Placeholder: Just echoes the config and adds a dummy candidate."""
    print(f"Running dummy node with config: {state.config}")
    dummy_cand = Candidate(
        linkedin_id="dummy456",
        name="Test Candidate",
        profile_data={"skills": ["AI", "Python"]},
        relevance_score=0.9,
        status="pending"
    )
    state.candidates.append(dummy_cand)
    state.metrics["total_processed"] += 1
    return state  # Return the updated state (LangGraph merges it)

# Add the dummy node
workflow.add_node("dummy", dummy_node)

# Set entry point
workflow.set_entry_point("dummy")

# Simple edge to end
workflow.add_edge("dummy", END)

# Compile the graph
graph = workflow.compile(checkpointer=checkpointer)

# Updated __main__ block (as above)
if __name__ == "__main__":
    # Sample config
    initial_config = {"keywords": ["AI Engineer"], "min_exp": 2}
    initial_state = AppState(config=initial_config)
    
    thread_id = "test_run_1"
    config = {"configurable": {"thread_id": thread_id}}
    
    result_raw = graph.invoke(initial_state, config=config)
    result = AppState.parse_obj(result_raw)
    
    print("Final state:")
    print(f"Candidates: {len(result.candidates)}")
    print(f"Metrics: {result.metrics}")
    print(f"Run ID: {result.run_id}")
