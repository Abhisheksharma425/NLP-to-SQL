"""
Quick test to verify the installation and system components.
This script tests basic functionality without requiring OpenAI API.
"""

import sys
import os

def test_imports():
    """Test that all required packages are installed."""
    print("Testing package imports...")
    
    try:
        import langgraph
        print("✅ langgraph")
    except ImportError as e:
        print(f"❌ langgraph: {e}")
        return False
    
    try:
        import langchain
        print("✅ langchain")
    except ImportError as e:
        print(f"❌ langchain: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✅ sqlalchemy")
    except ImportError as e:
        print(f"❌ sqlalchemy: {e}")
        return False
    
    try:
        import sqlparse
        print("✅ sqlparse")
    except ImportError as e:
        print(f"❌ sqlparse: {e}")
        return False
    
    try:
        import sklearn
        print("✅ scikit-learn")
    except ImportError as e:
        print(f"❌ scikit-learn: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv")
    except ImportError as e:
        print(f"❌ python-dotenv: {e}")
        return False
    
    return True


def test_database():
    """Test that the database exists and can be accessed."""
    print("\nTesting database...")
    
    db_path = "data/ecommerce.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(f"sqlite:///{db_path}")
        
        with engine.connect() as conn:
            # Test each table
            tables = ['customers', 'products', 'orders', 'order_items']
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"✅ {table}: {count} rows")
        
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_schema_extractor():
    """Test the schema extraction module."""
    print("\nTesting schema extractor...")
    
    try:
        from src.schema.schema_extractor import SchemaExtractor
        
        extractor = SchemaExtractor("sqlite:///data/ecommerce.db")
        schema = extractor.get_full_schema()
        
        if "customers" in schema and "products" in schema:
            print("✅ Schema extraction working")
            return True
        else:
            print("❌ Schema extraction incomplete")
            return False
    except Exception as e:
        print(f"❌ Schema extractor error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_linker():
    """Test the schema linking module."""
    print("\nTesting schema linker...")
    
    try:
        from src.schema.schema_extractor import SchemaExtractor
        from src.schema.schema_linker import SchemaLinker
        
        extractor = SchemaExtractor("sqlite:///data/ecommerce.db")
        linker = SchemaLinker(extractor)
        
        # Test with a sample question
        question = "Show me all customers"
        relevant_tables = linker.link_tables(question, top_k=2)
        
        if relevant_tables and relevant_tables[0][0] == "customers":
            print(f"✅ Schema linker working (found: {relevant_tables[0][0]})")
            return True
        else:
            print("❌ Schema linker not finding correct tables")
            return False
    except Exception as e:
        print(f"❌ Schema linker error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validator():
    """Test the SQL validator."""
    print("\nTesting SQL validator...")
    
    try:
        from src.agents.validator import SQLValidator
        
        validator = SQLValidator("sqlite:///data/ecommerce.db")
        
        # Test valid SQL
        valid, errors = validator.validate_syntax("SELECT * FROM customers")
        if valid:
            print("✅ Syntax validation working")
        else:
            print(f"❌ Syntax validation failed: {errors}")
            return False
        
        # Test invalid SQL (dangerous keyword)
        valid, errors = validator.validate_syntax("DELETE FROM customers")
        if not valid and any("DELETE" in err for err in errors):
            print("✅ Security validation working")
        else:
            print("❌ Security validation not blocking dangerous queries")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Validator error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("  NLP-to-SQL System Verification")
    print("="*60)
    
    tests = [
        ("Package Imports", test_imports),
        ("Database", test_database),
        ("Schema Extractor", test_schema_extractor),
        ("Schema Linker", test_schema_linker),
        ("SQL Validator", test_validator),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("="*60)
    print("  Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All systems operational! Ready to use the chatbot.")
        print("\nNext step: Add your OpenAI API key to .env file, then run:")
        print("  python main.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
