"""Self-correction agent for fixing SQL errors."""

from typing import Dict
from langchain_openai import ChatOpenAI
from ..config import get_settings
from ..prompts.templates import create_correction_prompt
from ..agents.state import SQLState


class SelfCorrector:
    """Correct SQL queries based on validation or execution errors."""
    
    def __init__(self):
        """Initialize corrector with LLM."""
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key
        )
        self.max_attempts = settings.max_correction_attempts
    
    def correct(self, state: SQLState) -> Dict:
        """
        Attempt to correct an invalid SQL query.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with corrected SQL
        """
        # Get error information
        validation_errors = state.get("validation_errors", [])
        execution_error = state.get("execution_error")
        
        # Determine error type and message
        if validation_errors:
            error_type = "Validation Error"
            error_message = "; ".join(validation_errors)
        elif execution_error:
            error_type = "Execution Error"
            error_message = execution_error
        else:
            # No error to correct
            return {}
        
        # Create correction prompt
        prompt = create_correction_prompt(
            question=state["question"],
            schema=state["schema_context"],
            incorrect_sql=state["generated_sql"],
            error_message=error_message,
            error_type=error_type
        )
        
        # Generate corrected SQL
        response = self.llm.invoke(prompt)
        corrected_sql = response.content.strip()
        
        # Clean up the SQL
        if corrected_sql.startswith("```sql"):
            corrected_sql = corrected_sql.replace("```sql", "").replace("```", "").strip()
        elif corrected_sql.startswith("```"):
            corrected_sql = corrected_sql.replace("```", "").strip()
        
        corrected_sql = corrected_sql.rstrip(';')
        
        # Update correction history
        correction_history = state.get("correction_history", [])
        correction_history.append(state["generated_sql"])
        
        return {
            "generated_sql": corrected_sql,
            "correction_attempt": state.get("correction_attempt", 0) + 1,
            "correction_history": correction_history,
            "validation_errors": [],  # Reset errors for new attempt
            "execution_error": None
        }


def corrector_node(state: SQLState) -> Dict:
    """LangGraph node for self-correction."""
    corrector = SelfCorrector()
    return corrector.correct(state)
