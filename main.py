"""Main CLI application for NLP-to-SQL chatbot."""

import sys
from typing import Optional
from src.workflow.graph import text_to_sql_workflow
from src.config import get_settings
from src.schema.schema_extractor import SchemaExtractor
import json


def format_results(results: list) -> str:
    """Format query results for display."""
    if not results:
        return "No results found."
    
    # Get column names from first result
    columns = list(results[0].keys())
    
    # Calculate column widths
    col_widths = {}
    for col in columns:
        col_widths[col] = max(
            len(str(col)),
            max(len(str(row.get(col, ""))) for row in results)
        )
    
    # Create header
    header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
    separator = "-+-".join("-" * col_widths[col] for col in columns)
    
    # Create rows
    rows = []
    for row in results:
        rows.append(" | ".join(
            str(row.get(col, "")).ljust(col_widths[col])
            for col in columns
        ))
    
    return "\n".join([header, separator] + rows)


def show_schema_info():
    """Display database schema information."""
    settings = get_settings()
    extractor = SchemaExtractor(settings.database_url)
    
    print("\n" + "="*60)
    print("DATABASE SCHEMA")
    print("="*60)
    print(extractor.get_full_schema())
    print("="*60 + "\n")


def run_query(question: str, verbose: bool = False) -> Optional[dict]:
    """
    Run a single query through the Text-to-SQL workflow.
    
    Args:
        question: Natural language question
        verbose: Whether to show detailed workflow information
    
    Returns:
        Final state after workflow execution
    """
    print(f"\n📝 Question: {question}\n")
    
    # Initialize state
    initial_state = {
        "question": question,
        "relevant_tables": [],
        "schema_context": "",
        "selected_examples": [],
        "generated_sql": "",
        "reasoning": "",
        "is_valid_syntax": False,
        "is_valid_semantics": False,
        "validation_errors": [],
        "correction_attempt": 0,
        "correction_history": [],
        "execution_successful": False,
        "execution_error": None,
        "query_results": None,
        "final_sql": "",
        "final_answer": ""
    }
    
    try:
        # Run the workflow
        if verbose:
            print("🔄 Running workflow...\n")
        
        final_state = text_to_sql_workflow.invoke(initial_state)
        
        # Display results
        if verbose:
            print(f"🔗 Relevant Tables: {', '.join(final_state.get('relevant_tables', []))}")
            print(f"🔄 Correction Attempts: {final_state.get('correction_attempt', 0)}")
        
        print(f"\n💾 Generated SQL:")
        print(f"   {final_state.get('final_sql', final_state.get('generated_sql', 'N/A'))}\n")
        
        if final_state.get("execution_successful"):
            results = final_state.get("query_results", [])
            print(f"✅ Query executed successfully! ({len(results)} row(s) returned)\n")
            
            if results:
                print(format_results(results))
            else:
                print("No results found.")
        else:
            error = final_state.get("execution_error", "Unknown error")
            print(f"❌ Query execution failed: {error}")
            
            if final_state.get("validation_errors"):
                print(f"\nValidation errors:")
                for err in final_state["validation_errors"]:
                    print(f"  - {err}")
        
        print()
        return final_state
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None


def interactive_mode():
    """Run the chatbot in interactive mode."""
    print("\n" + "="*60)
    print("  NLP-to-SQL Chatbot (Interactive Mode)")
    print("="*60)
    print("\nCommands:")
    print("  /schema  - Show database schema")
    print("  /verbose - Toggle verbose mode")
    print("  /quit    - Exit the chatbot")
    print("  Or just type your question!\n")
    
    verbose = False
    
    while True:
        try:
            question = input("💬 You: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['/quit', '/exit', '/q']:
                print("\n👋 Goodbye!\n")
                break
            
            if question.lower() == '/schema':
                show_schema_info()
                continue
            
            if question.lower() == '/verbose':
                verbose = not verbose
                print(f"\n✓ Verbose mode: {'ON' if verbose else 'OFF'}\n")
                continue
            
            if question.startswith('/'):
                print(f"\n❌ Unknown command: {question}\n")
                continue
            
            # Run the query
            run_query(question, verbose=verbose)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}\n")


def main():
    """Main entry point."""
    # Check if OpenAI API key is set
    try:
        settings = get_settings()
        if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
            print("\n❌ Error: OPENAI_API_KEY not set in .env file")
            print("Please add your OpenAI API key to the .env file and try again.\n")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Configuration error: {str(e)}\n")
        sys.exit(1)
    
    # Check if we have command line arguments
    if len(sys.argv) > 1:
        # Single query mode
        question = " ".join(sys.argv[1:])
        run_query(question, verbose=True)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
