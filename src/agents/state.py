"""Shared state definition for the LangGraph workflow."""

from typing import List, Dict, Optional, TypedDict


class SQLState(TypedDict):
    """State shared across all nodes in the workflow."""
    
    # Input
    question: str
    
    # Schema Linking
    relevant_tables: List[str]
    schema_context: str
    
    # Example Selection
    selected_examples: List[Dict[str, str]]
    
    # SQL Generation
    generated_sql: str
    reasoning: str
    
    # Validation
    is_valid_syntax: bool
    is_valid_semantics: bool
    validation_errors: List[str]
    
    # Self-Correction
    correction_attempt: int
    correction_history: List[str]
    
    # Execution
    execution_successful: bool
    execution_error: Optional[str]
    query_results: Optional[List[Dict]]
    
    # Final Output
    final_sql: str
    final_answer: str
