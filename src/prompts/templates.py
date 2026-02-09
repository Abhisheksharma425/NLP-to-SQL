"""Prompt templates for SQL generation and correction."""

from typing import List, Dict


SYSTEM_PROMPT = """You are an expert SQL query generator. Your task is to convert natural language questions into accurate SQL queries.

CRITICAL RULES:
1. Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP)
2. Use ONLY the tables and columns provided in the schema
3. Return ONLY the SQL query without explanations or formatting
4. Use proper SQL syntax (JOIN, WHERE, GROUP BY, ORDER BY as needed)
5. Be precise with column names and table names
6. For aggregations, use appropriate GROUP BY clauses
7. Use table aliases for better readability when joining tables

COLUMN DISAMBIGUATION - VERY IMPORTANT:
- When multiple columns have similar names, READ THE DESCRIPTIONS CAREFULLY
- Example: If there's both "Name" and "Song_Name", check which one the question asks for
- Pay attention to the SAMPLE VALUES in the schema - they show the data format
- When in doubt, prefer the more specific column name
- For columns named like SQL functions (e.g., "Average"), use the column NOT the function unless explicitly asked to calculate

EXAMPLE FORMAT:
- Column description says "Song title" → use Song_Name for song-related questions
- Column description says "Singer's name" → use Name for person-related questions
- Sample values like "Shake It Off", "Bad Romance" → clearly song titles
- Sample values like "Taylor Swift", "Lady Gaga" → clearly person names"""


def create_sql_generation_prompt(question: str, schema: str, examples: List[Dict[str, str]] = None) -> str:
    """Create prompt for SQL generation."""
    
    prompt_parts = [SYSTEM_PROMPT]
    
    # Add schema
    prompt_parts.append("\n\nDATABASE SCHEMA:")
    prompt_parts.append(schema)
    
    # Add examples if provided
    if examples:
        prompt_parts.append("\n\nEXAMPLES:")
        for i, example in enumerate(examples, 1):
            prompt_parts.append(f"\nExample {i}:")
            prompt_parts.append(f"Question: {example['question']}")
            prompt_parts.append(f"SQL: {example['sql']}")
    
    # Add the actual question
    prompt_parts.append("\n\nQUESTION TO CONVERT:")
    prompt_parts.append(f"Question: {question}")
    prompt_parts.append("SQL:")
    
    return "\n".join(prompt_parts)


def create_correction_prompt(question: str, schema: str, incorrect_sql: str, 
                            error_message: str, error_type: str) -> str:
    """Create prompt for SQL correction."""
    
    prompt = f"""{SYSTEM_PROMPT}

DATABASE SCHEMA:
{schema}

TASK: Fix the following SQL query that has an error.

ORIGINAL QUESTION: {question}

INCORRECT SQL:
{incorrect_sql}

ERROR TYPE: {error_type}
ERROR MESSAGE: {error_message}

INSTRUCTIONS:
1. Identify the specific issue in the SQL query
2. Generate a corrected version
3. Ensure the corrected query answers the original question
4. Return ONLY the corrected SQL query

CORRECTED SQL:"""
    
    return prompt


def create_validation_prompt(question: str, sql: str, schema: str) -> str:
    """Create prompt for semantic validation."""
    
    prompt = f"""{SYSTEM_PROMPT}

DATABASE SCHEMA:
{schema}

TASK: Validate if the following SQL query correctly answers the question.

QUESTION: {question}

SQL QUERY:
{sql}

VALIDATION CHECKLIST:
1. Does the query use only the columns and tables from the schema?
2. Are all JOINs semantically correct?
3. Are aggregations (SUM, COUNT, AVG) used appropriately?
4. Is GROUP BY used when needed?
5. Does the query logically answer the question?

Respond with ONLY:
- "VALID" if the query is correct
- "INVALID: [brief explanation]" if there are issues

RESPONSE:"""
    
    return prompt
