"""LangGraph workflow for Text-to-SQL conversion."""

from langgraph.graph import StateGraph, END
from typing import Literal
from ..agents.state import SQLState
from ..agents.schema_linker_node import schema_linker_node
from ..agents.sql_generator import sql_generator_node
from ..agents.validator import validator_node
from ..agents.executor import executor_node
from ..agents.self_corrector import corrector_node
from ..config import get_settings


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow for Text-to-SQL."""
    
    # Create the graph
    workflow = StateGraph(SQLState)
    
    # Add nodes
    workflow.add_node("schema_linker", schema_linker_node)
    workflow.add_node("sql_generator", sql_generator_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("corrector", corrector_node)
    
    # Define routing logic
    def should_correct(state: SQLState) -> Literal["corrector", "executor"]:
        """Decide if we need to correct the SQL or proceed to execution."""
        settings = get_settings()
        
        # Check if we've exceeded max correction attempts
        if state.get("correction_attempt", 0) >= settings.max_correction_attempts:
            return "executor"  # Give up and try to execute anyway
        
        # Check validation results
        if not state.get("is_valid_syntax", True) or not state.get("is_valid_semantics", True):
            return "corrector"
        
        return "executor"
    
    def should_retry_after_execution(state: SQLState) -> Literal["corrector", END]:
        """Decide if we need to retry after execution failure."""
        settings = get_settings()
        
        # Check if execution was successful
        if state.get("execution_successful", False):
            return END
        
        # Check if we've exceeded max correction attempts
        if state.get("correction_attempt", 0) >= settings.max_correction_attempts:
            return END  # Give up
        
        return "corrector"
    
    # Set entry point
    workflow.set_entry_point("schema_linker")
    
    # Add edges
    workflow.add_edge("schema_linker", "sql_generator")
    workflow.add_edge("sql_generator", "validator")
    workflow.add_conditional_edges(
        "validator",
        should_correct,
        {
            "corrector": "corrector",
            "executor": "executor"
        }
    )
    workflow.add_edge("corrector", "validator")  # After correction, validate again
    workflow.add_conditional_edges(
        "executor",
        should_retry_after_execution,
        {
            "corrector": "corrector",
            END: END
        }
    )
    
    return workflow.compile()


# Create the compiled workflow
text_to_sql_workflow = create_workflow()
