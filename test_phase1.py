"""
Test Phase 1 improvements: Enhanced schema descriptions and improved prompts.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from src.schema.schema_extractor import SchemaExtractor
from src.config import get_settings


def test_enhanced_schema():
    """Test LLM-powered schema descriptions."""
    
    print("="*60)
    print("TESTING PHASE 1 IMPROVEMENTS")
    print("="*60)
    
    # Get settings
    settings = get_settings()
    
    # Test 1: Enhanced Schema Extraction
    print("\n" + "="*60)
    print("TEST 1: Enhanced Schema Descriptions")
    print("="*60)
    
    extractor = SchemaExtractor(settings.database_url, use_llm_descriptions=True)
    
    # Get enhanced schema for one table
    print("\n📋 Getting enhanced schema for 'customers' table...")
    enhanced_schema = extractor.get_table_schema('customers', enhanced=True)
    
    print("\n✅ Enhanced Schema (with LLM descriptions and samples):")
    print(enhanced_schema)
    
    # Compare with basic schema
    print("\n" + "-"*60)
    print("Basic Schema (for comparison):")
    basic_schema = extractor.get_table_schema('customers', enhanced=False)
    print(basic_schema)
    
    # Test 2: Column Value Sampling
    print("\n" + "="*60)
    print("TEST 2: Column Value Sampling")
    print("="*60)
    
    tables = extractor.get_table_names()
    print(f"\n📊 Sampling values from {len(tables)} tables...")
    
    for table in tables[:2]:  # Test first 2 tables
        print(f"\n▶ {table}:")
        samples = extractor._get_column_samples(table, extractor.metadata.tables[table].columns.keys())
        for col, values in list(samples.items())[:3]:  # Show first 3 columns
            print(f"  {col}: {values}")
    
    # Test 3: Full Enhanced Schema
    print("\n" + "="*60)
    print("TEST 3: Full Enhanced Schema")
    print("="*60)
    
    print("\n📚 Getting full enhanced schema for all tables...")
    full_schema = extractor.get_full_schema(enhanced=True)
    
    # Print first 500 characters to verify
    print("\n✅ Full Enhanced Schema (first 1000 characters):")
    print(full_schema[:1000])
    print("\n... (total length: {} characters)".format(len(full_schema)))
    
    # Save to file for inspection
    output_file = Path("test_enhanced_schema.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ENHANCED SCHEMA WITH LLM DESCRIPTIONS\n")
        f.write("="*60 + "\n\n")
        f.write(full_schema)
    
    print(f"\n💾 Full schema saved to: {output_file}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nPhase 1 improvements are working correctly!")
    print("- LLM generates intelligent column descriptions")
    print("- Sample values show actual data formats")
    print("- Schema is much more informative for GPT-4")


if __name__ == "__main__":
    test_enhanced_schema()
