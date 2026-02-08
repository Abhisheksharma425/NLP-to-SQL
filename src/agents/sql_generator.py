"""SQL Generator agent using OpenAI LLM."""

from typing import Dict
from langchain_openai import ChatOpenAI
from ..config import get_settings
from ..prompts.templates import create_sql_generation_prompt
from ..agents.state import SQLState


class SQLGenerator:
    """Generate SQL queries from natural language using LLM."""
    
    def __init__(self):
        """Initialize SQL generator with LLM."""
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key
        )
    
    def generate(self, state: SQLState) -> Dict:
        """
        Generate SQL query from natural language question.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with generated SQL
        """
        # Create prompt with schema and examples
        prompt = create_sql_generation_prompt(
            question=state["question"],
            schema=state["schema_context"],
            examples=state.get("selected_examples", [])
        )
        
        # Generate SQL
        response = self.llm.invoke(prompt)
        generated_sql = response.content.strip()
        
        # Clean up the SQL (remove markdown formatting if present)
        if generated_sql.startswith("```sql"):
            generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        elif generated_sql.startswith("```"):
            generated_sql = generated_sql.replace("```", "").strip()
        
        # Remove any trailing semicolons for consistency
        generated_sql = generated_sql.rstrip(';')
        
        return {
            "generated_sql": generated_sql,
            "reasoning": "Generated SQL from natural language question",
            "correction_attempt": state.get("correction_attempt", 0)
        }


def sql_generator_node(state: SQLState) -> Dict:
    """LangGraph node for SQL generation."""
    generator = SQLGenerator()
    return generator.generate(state)
