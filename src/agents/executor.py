"""SQL query executor."""

from typing import Dict, List
from sqlalchemy import create_engine, text
from ..agents.state import SQLState
from ..config import get_settings


class SQLExecutor:
    """Execute SQL queries against the database."""
    
    def __init__(self, database_url: str = None):
        """Initialize executor."""
        if database_url is None:
            settings = get_settings()
            database_url = settings.database_url
        self.engine = create_engine(database_url)
    
    def execute(self, state: SQLState) -> Dict:
        """
        Execute the validated SQL query.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with execution results
        """
        sql = state["generated_sql"]
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                
                # Fetch results
                columns = result.keys()
                rows = result.fetchall()
                
                # Convert to list of dictionaries
                query_results = [
                    dict(zip(columns, row))
                    for row in rows
                ]
                
                return {
                    "execution_successful": True,
                    "execution_error": None,
                    "query_results": query_results,
                    "final_sql": sql
                }
        
        except Exception as e:
            return {
                "execution_successful": False,
                "execution_error": str(e),
                "query_results": None
            }


def executor_node(state: SQLState) -> Dict:
    """LangGraph node for SQL execution."""
    executor = SQLExecutor()
    return executor.execute(state)
