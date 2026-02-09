"""
Generic pattern examples and guidance for SQL generation.
These patterns are database-agnostic and teach reasoning, not memorization.
"""

from typing import List, Dict


# Generic patterns that work with ANY database
GENERIC_PATTERNS = [
    {
        "name": "Table Selection",
        "description": "How to identify the correct table(s) for a query",
        "rule": "Look for entity names in the question that match table names. If question mentions 'customers', use 'customer' or 'customers' table.",
        "examples": [
            {
                "pattern": "How many [entities] are there?",
                "guidance": "Use COUNT(*) FROM [entity_table]",
                "note": "Match entity name in question to table name"
            },
            {
                "pattern": "Show all [entities]",
                "guidance": "SELECT * FROM [entity_table]",
                "note": "Don't confuse with related tables"
            }
        ]
    },
    {
        "name": "Column vs Function Disambiguation",
        "description": "When column names match SQL function names (Average, Count, etc.)",
        "rule": "If a column name matches a SQL function, check what the question asks for:\n- 'the average' or 'the count' → SELECT the column directly\n- 'calculate average' or 'count how many' → USE the function",
        "examples": [
            {
                "pattern": "What is the maximum capacity and the average?",
                "guidance": "SELECT MAX(capacity), average FROM table",
                "note": "'the average' means the column named 'average', NOT AVG()"
            },
            {
                "pattern": "Calculate the average capacity",
                "guidance": "SELECT AVG(capacity) FROM table",
                "note": "'calculate' means use the AVG() function"
            }
        ]
    },
    {
        "name": "Column Name Disambiguation",
        "description": "When multiple columns have similar names",
        "rule": "Read column descriptions and sample values:\n- More specific column name is usually correct (Product_Name vs Name)\n- Check sample values to verify content type\n- Match column purpose to question intent",
        "examples": [
            {
                "pattern": "Show song names",
                "guidance": "Use Song_Name column, not Name column",
                "note": "Song_Name is more specific for songs"
            },
            {
                "pattern": "List singer names",
                "guidance": "Use Name column or Singer_Name if available",
                "note": "Context determines which 'name' column"
            }
        ]
    },
    {
        "name": "JOIN Type Selection",
        "description": "Choosing between INNER JOIN, LEFT JOIN, RIGHT JOIN",
        "rule": "- Use INNER JOIN (default) for 'show X with Y' or 'X that have Y'\n- Use LEFT JOIN for 'all X including those without Y'\n- Use RIGHT JOIN rarely (usually can restructure as LEFT JOIN)",
        "examples": [
            {
                "pattern": "Show stadiums with concerts",
                "guidance": "INNER JOIN (only stadiums that have concerts)",
                "note": "'with' implies relationship must exist"
            },
            {
                "pattern": "Show all stadiums and their concert counts",
                "guidance": "LEFT JOIN (include stadiums with 0 concerts)",
                "note": "'all' means include those without matches"
            }
        ]
    },
    {
        "name": "SELECT Column Precision",
        "description": "What exactly to return in SELECT clause",
        "rule": "Return ONLY what the question asks for:\n- 'Which year' → SELECT year (not year + count)\n- 'How many' → SELECT COUNT(*) (just the count)\n- 'Show name and count' → SELECT name, COUNT(*)",
        "examples": [
            {
                "pattern": "Which year had the most concerts?",
                "guidance": "SELECT year FROM... ORDER BY COUNT(*) DESC LIMIT 1",
                "note": "Return year only, not the count"
            },
            {
                "pattern": "How many concerts were in 2014?",
                "guidance": "SELECT COUNT(*) FROM... WHERE year = 2014",
                "note": "Return count only, not year"
            }
        ]
    },
    {
        "name": "Aggregation and GROUP BY",
        "description": "When to use GROUP BY with aggregations",
        "rule": "- COUNT(*), AVG(), etc. with no GROUP BY → returns single row\n- Aggregation with dimension → need GROUP BY\n- 'for each X' → GROUP BY X",
        "examples": [
            {
                "pattern": "Count of concerts for each stadium",
                "guidance": "SELECT stadium_id, COUNT(*) FROM... GROUP BY stadium_id",
                "note": "'for each' requires GROUP BY"
            },
            {
                "pattern": "Total number of concerts",
                "guidance": "SELECT COUNT(*) FROM concerts",
                "note": "No 'for each' → no GROUP BY needed"
            }
        ]
    },
    {
        "name": "WHERE vs HAVING",
        "description": "Filter before vs after aggregation",
        "rule": "- WHERE: Filter rows before aggregation\n- HAVING: Filter groups after aggregation\n- Use WHERE for column values, HAVING for aggregate results",
        "examples": [
            {
                "pattern": "Singers from France with age > 30",
                "guidance": "WHERE country = 'France' AND age > 30",
                "note": "Filter individual rows → WHERE"
            },
            {
                "pattern": "Countries with more than 5 singers",
                "guidance": "GROUP BY country HAVING COUNT(*) > 5",
                "note": "Filter aggregated results → HAVING"
            }
        ]
    }
]


def get_pattern_guidance(pattern_name: str = None) -> str:
    """Get formatted guidance for SQL generation patterns.
    
    Args:
        pattern_name: Optional specific pattern to return. If None, returns all patterns.
        
    Returns:
        Formatted string with pattern guidance
    """
    if pattern_name:
        pattern = next((p for p in GENERIC_PATTERNS if p["name"] == pattern_name), None)
        if not pattern:
            return ""
        patterns_to_format = [pattern]
    else:
        patterns_to_format = GENERIC_PATTERNS
    
    guidance = []
    guidance.append("SQL GENERATION PATTERNS:")
    guidance.append("=" * 60)
    
    for pattern in patterns_to_format:
        guidance.append(f"\n## {pattern['name']}")
        guidance.append(f"{pattern['description']}")
        guidance.append(f"\n**Rule**: {pattern['rule']}")
        
        if pattern.get('examples'):
            guidance.append("\n**Examples**:")
            for ex in pattern['examples']:
                guidance.append(f"  • Pattern: \"{ex['pattern']}\"")
                guidance.append(f"    → {ex['guidance']}")
                guidance.append(f"    Note: {ex['note']}")
                guidance.append("")
    
    return "\n".join(guidance)


def get_relevant_patterns(question: str) -> List[Dict]:
    """Identify relevant patterns based on question keywords.
    
    Args:
        question: The natural language question
        
    Returns:
        List of relevant pattern dictionaries
    """
    question_lower = question.lower()
    relevant = []
    
    # Table selection - always relevant
    relevant.append(GENERIC_PATTERNS[0])
    
    # Column/function disambiguation - check for function names
    if any(word in question_lower for word in ['average', 'count', 'maximum', 'minimum', 'sum']):
        relevant.append(GENERIC_PATTERNS[1])
    
    # Column name disambiguation - check for 'name'
    if 'name' in question_lower:
        relevant.append(GENERIC_PATTERNS[2])
    
    # JOIN - check for multi-table indicators
    if any(word in question_lower for word in ['with', 'in', 'for', 'and']):
        relevant.append(GENERIC_PATTERNS[3])
    
    # SELECT precision - check for 'which', 'what'
    if any(word in question_lower for word in ['which', 'what']):
        relevant.append(GENERIC_PATTERNS[4])
    
    # GROUP BY - check for 'each', 'per'
    if any(word in question_lower for word in ['each', 'per', 'every']):
        relevant.append(GENERIC_PATTERNS[5])
    
    # WHERE vs HAVING - check for filters
    if any(word in question_lower for word in ['more than', 'less than', 'greater', 'where']):
        relevant.append(GENERIC_PATTERNS[6])
    
    return relevant


if __name__ == "__main__":
    # Test pattern guidance
    print(get_pattern_guidance())
    
    print("\n" + "=" * 60)
    print("TESTING PATTERN DETECTION")
    print("=" * 60)
    
    test_questions = [
        "How many singers are there?",
        "What is the maximum capacity and the average?",
        "Show song names for all singers",
        "Which year had the most concerts?",
        "Countries with more than 5 singers"
    ]
    
    for q in test_questions:
        print(f"\nQ: {q}")
        patterns = get_relevant_patterns(q)
        print(f"Relevant patterns: {[p['name'] for p in patterns]}")
