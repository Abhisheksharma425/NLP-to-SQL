"""SQL query validator for syntax and semantic checking."""

import sqlparse
from typing import Dict, List, Tuple
from ..agents.state import SQLState
from sqlalchemy import create_engine, text
from ..config import get_settings


class SQLValidator:
    """Validate SQL queries for syntax and semantic correctness."""
    
    def __init__(self, database_url: str = None):
        """Initialize validator."""
        if database_url is None:
            settings = get_settings()
            database_url = settings.database_url
        self.engine = create_engine(database_url)
    
    def validate_syntax(self, sql: str) -> Tuple[bool, List[str]]:
        """
        Validate SQL syntax using sqlparse.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Parse the SQL
            parsed = sqlparse.parse(sql)
            
            if not parsed:
                errors.append("Empty or invalid SQL query")
                return False, errors
            
            # Check for basic SQL structure
            statement = parsed[0]
            
            # Check if it's a SELECT statement
            if not statement.get_type() == 'SELECT':
                errors.append("Only SELECT queries are allowed")
                return False, errors
            
            # Check for dangerous keywords
            sql_upper = sql.upper()
            dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
            for keyword in dangerous_keywords:
                if keyword in sql_upper:
                    errors.append(f"Dangerous keyword '{keyword}' found. Only SELECT queries allowed")
                    return False, errors
            
            return True, []
            
        except Exception as e:
            errors.append(f"Syntax error: {str(e)}")
            return False, errors
    
    def validate_semantics(self, sql: str) -> Tuple[bool, List[str]]:
        """
        Validate SQL semantics by attempting to explain the query.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            with self.engine.connect() as conn:
                # Try to EXPLAIN the query (works for SQLite)
                explain_sql = f"EXPLAIN QUERY PLAN {sql}"
                conn.execute(text(explain_sql))
            
            return True, []
            
        except Exception as e:
            error_msg = str(e)
            
            # Parse common errors
            if "no such table" in error_msg.lower():
                errors.append("Table does not exist in the database")
            elif "no such column" in error_msg.lower():
                errors.append("Column does not exist in the specified table")
            elif "ambiguous column" in error_msg.lower():
                errors.append("Ambiguous column name - specify table alias")
            else:
                errors.append(f"Semantic error: {error_msg}")
            
            return False, errors
    
    def validate(self, state: SQLState) -> Dict:
        """
        Full validation: syntax + semantics.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with validation results
        """
        sql = state["generated_sql"]
        
        # Syntax validation
        is_valid_syntax, syntax_errors = self.validate_syntax(sql)
        
        if not is_valid_syntax:
            return {
                "is_valid_syntax": False,
                "is_valid_semantics": False,
                "validation_errors": syntax_errors
            }
        
        # Semantic validation
        is_valid_semantics, semantic_errors = self.validate_semantics(sql)
        
        return {
            "is_valid_syntax": is_valid_syntax,
            "is_valid_semantics": is_valid_semantics,
            "validation_errors": syntax_errors + semantic_errors
        }


def validator_node(state: SQLState) -> Dict:
    """LangGraph node for SQL validation."""
    validator = SQLValidator()
    return validator.validate(state)
