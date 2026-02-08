"""Schema linking node for the workflow."""

from typing import Dict
from ..schema.schema_extractor import SchemaExtractor
from ..schema.schema_linker import SchemaLinker
from ..agents.state import SQLState
from ..config import get_settings


def schema_linker_node(state: SQLState) -> Dict:
    """
    Link question to relevant database tables and provide schema context.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state with relevant schema information
    """
    settings = get_settings()
    
    # Initialize schema tools
    extractor = SchemaExtractor(settings.database_url)
    linker = SchemaLinker(extractor)
    
    # Find relevant tables (top 3)
    relevant_tables_with_scores = linker.link_tables(state["question"], top_k=3)
    relevant_tables = [table for table, score in relevant_tables_with_scores]
    
    # Get schema for relevant tables only
    schema_context = linker.get_relevant_schema(state["question"], top_k=3)
    
    return {
        "relevant_tables": relevant_tables,
        "schema_context": schema_context
    }
