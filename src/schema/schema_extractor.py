"""Database schema extraction and management with LLM-powered descriptions."""

from sqlalchemy import create_engine, inspect, MetaData, text
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from src.config import get_settings


class SchemaExtractor:
    """Extract and manage database schema information with intelligent descriptions."""
    
    def __init__(self, database_url: str, use_llm_descriptions: bool = True):
        """
        Initialize schema extractor with database connection.
        
        Args:
            database_url: SQLAlchemy connection string
            use_llm_descriptions: Whether to use LLM for generating column descriptions
        """
        self.engine = create_engine(database_url)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self._schema_cache = None
        self._enhanced_schema_cache = None
        self.use_llm_descriptions = use_llm_descriptions
        
        # Initialize LLM for descriptions if enabled
        if self.use_llm_descriptions:
            settings = get_settings()
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=0.1,  # Low temperature for consistent descriptions
                openai_api_key=settings.openai_api_key
            )
    
    def get_full_schema(self, enhanced: bool = True) -> str:
        """
        Get complete database schema as formatted DDL.
        
        Args:
            enhanced: If True, includes LLM-generated descriptions and sample values
        
        Returns:
            Complete schema as DDL string
        """
        if enhanced and self._enhanced_schema_cache:
            return self._enhanced_schema_cache
        elif not enhanced and self._schema_cache:
            return self._schema_cache
        
        inspector = inspect(self.engine)
        schema_parts = []
        
        for table_name in inspector.get_table_names():
            if enhanced:
                schema_parts.append(self._get_enhanced_table_ddl(table_name, inspector))
            else:
                schema_parts.append(self._get_table_ddl(table_name, inspector))
        
        result = "\n\n".join(schema_parts)
        
        if enhanced:
            self._enhanced_schema_cache = result
        else:
            self._schema_cache = result
        
        return result
    
    def _get_table_ddl(self, table_name: str, inspector) -> str:
        """Generate basic DDL for a single table."""
        columns = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        fk_constraints = inspector.get_foreign_keys(table_name)
        
        ddl = f"CREATE TABLE {table_name} (\n"
        
        col_defs = []
        for col in columns:
            col_def = f"    {col['name']} {col['type']}"
            
            if col['name'] in pk_constraint.get('constrained_columns', []):
                col_def += " PRIMARY KEY"
            
            if not col.get('nullable', True):
                col_def += " NOT NULL"
            
            col_defs.append(col_def)
        
        ddl += ",\n".join(col_defs)
        
        # Add foreign keys
        if fk_constraints:
            for fk in fk_constraints:
                fk_def = f"    FOREIGN KEY ({', '.join(fk['constrained_columns'])}) "
                fk_def += f"REFERENCES {fk['referred_table']}({', '.join(fk['referred_columns'])})"
                ddl += ",\n" + fk_def
        
        ddl += "\n);"
        
        return ddl
    
    def _get_enhanced_table_ddl(self, table_name: str, inspector) -> str:
        """Generate enhanced DDL with LLM descriptions and sample values."""
        columns = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        fk_constraints = inspector.get_foreign_keys(table_name)
        
        # Get column descriptions (LLM-powered if enabled)
        column_descriptions = self._generate_column_descriptions(table_name, columns, fk_constraints)
        
        # Get sample values for each column
        column_samples = self._get_column_samples(table_name, [col['name'] for col in columns])
        
        ddl = f"CREATE TABLE {table_name} (\n"
        
        col_defs = []
        for col in columns:
            col_name = col['name']
            col_def = f"    {col_name} {col['type']}"
            
            if col_name in pk_constraint.get('constrained_columns', []):
                col_def += " PRIMARY KEY"
            
            if not col.get('nullable', True):
                col_def += " NOT NULL"
            
            # Add intelligent description
            description = column_descriptions.get(col_name, col_name.replace('_', ' ').title())
            
            # Add sample values if available
            if col_name in column_samples and column_samples[col_name]:
                samples = column_samples[col_name]
                sample_str = ", ".join([f'"{s}"' for s in samples[:5]])
                col_def += f"  -- {description} (e.g., {sample_str})"
            else:
                col_def += f"  -- {description}"
            
            col_defs.append(col_def)
        
        ddl += ",\n".join(col_defs)
        
        # Add foreign keys with descriptions
        if fk_constraints:
            for fk in fk_constraints:
                fk_def = f"    FOREIGN KEY ({', '.join(fk['constrained_columns'])}) "
                fk_def += f"REFERENCES {fk['referred_table']}({', '.join(fk['referred_columns'])})"
                ddl += ",\n" + fk_def
        
        ddl += "\n);"
        
        return ddl
    
    def _generate_column_descriptions(self, table_name: str, columns: List[Dict], fk_constraints: List[Dict]) -> Dict[str, str]:
        """
        Generate intelligent descriptions for columns using LLM.
        
        Args:
            table_name: Name of the table
            columns: List of column information
            fk_constraints: Foreign key constraints
        
        Returns:
            Dictionary mapping column names to descriptions
        """
        if not self.use_llm_descriptions:
            # Fallback to heuristic descriptions
            return {col['name']: self._heuristic_description(col['name'], table_name) 
                    for col in columns}
        
        try:
            # Build foreign key map
            fk_map = {}
            for fk in fk_constraints:
                for col in fk['constrained_columns']:
                    fk_map[col] = {
                        'table': fk['referred_table'],
                        'column': fk['referred_columns'][0]
                    }
            
            # Create prompt for LLM
            column_info = []
            for col in columns:
                fk_info = ""
                if col['name'] in fk_map:
                    fk_info = f" (foreign key to {fk_map[col['name']]['table']}.{fk_map[col['name']]['column']})"
                
                column_info.append(f"- {col['name']} ({col['type']}){fk_info}")
            
            prompt = f"""You are a database expert. Generate concise, helpful descriptions for each column in the {table_name} table.

Table: {table_name}
Columns:
{chr(10).join(column_info)}

For each column, provide a brief, clear description (5-10 words) that explains what the column contains.
Focus on making it easy for someone to write SQL queries.

Rules:
1. For ID columns: mention if it's a primary key or references another table
2. For name/title columns: specify what kind of name (person, product, song, etc.)
3. For date/time columns: specify what event or action it represents
4. For amount/price columns: specify what it measures
5. Be specific and avoid generic terms

Respond in this format (one line per column):
column_name: description

Example:
customer_id: Unique identifier for each customer
first_name: Customer's first name
order_date: Date when the order was placed
total_amount: Total cost of the order in dollars"""

            # Get descriptions from LLM
            response = self.llm.invoke(prompt)
            descriptions = {}
            
            for line in response.content.strip().split('\n'):
                if ':' in line:
                    col_name, desc = line.split(':', 1)
                    descriptions[col_name.strip()] = desc.strip()
            
            return descriptions
            
        except Exception as e:
            # Fallback to heuristics if LLM fails
            print(f"Warning: LLM description failed for {table_name}, using heuristics: {e}")
            return {col['name']: self._heuristic_description(col['name'], table_name) 
                    for col in columns}
    
    def _heuristic_description(self, column_name: str, table_name: str) -> str:
        """Generate heuristic-based description for a column (fallback)."""
        # Simple heuristic-based descriptions
        if "id" in column_name.lower() and column_name.lower().endswith("id"):
            if column_name.lower() == f"{table_name}_id":
                return f"Unique identifier for {table_name}"
            else:
                ref_table = column_name.lower().replace("_id", "")
                return f"Foreign key referencing {ref_table}"
        
        if "name" in column_name.lower():
            return f"{column_name.replace('_', ' ').title()}"
        
        if "date" in column_name.lower():
            return f"Date of {column_name.replace('_', ' ').replace('date', '').strip()}"
        
        if "amount" in column_name.lower() or "price" in column_name.lower():
            return f"Monetary value for {column_name.replace('_', ' ')}"
        
        if "quantity" in column_name.lower() or "count" in column_name.lower():
            return f"Number of {column_name.replace('_', ' ').replace('quantity', '').replace('count', '').strip()}"
        
        return column_name.replace("_", " ").title()
    
    def _get_column_samples(self, table_name: str, column_names: List[str], limit: int = 5) -> Dict[str, List[str]]:
        """
        Get sample distinct values for each column.
        
        Args:
            table_name: Name of the table
            column_names: List of column names
            limit: Maximum number of sample values per column
        
        Returns:
            Dictionary mapping column names to sample values
        """
        samples = {}
        
        try:
            with self.engine.connect() as conn:
                for col_name in column_names:
                    try:
                        # Get distinct values
                        query = text(f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL LIMIT {limit}")
                        result = conn.execute(query)
                        values = [str(row[0]) for row in result.fetchall()]
                        
                        # Filter out very long values (probably not useful as examples)
                        values = [v for v in values if len(str(v)) < 50]
                        
                        if values:
                            samples[col_name] = values
                    except Exception:
                        # Skip columns that can't be sampled
                        continue
        except Exception as e:
            print(f"Warning: Failed to get column samples for {table_name}: {e}")
        
        return samples
    
    def get_table_names(self) -> List[str]:
        """Get list of all table names in the database."""
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def get_table_schema(self, table_name: str, enhanced: bool = True) -> str:
        """
        Get schema for a specific table.
        
        Args:
            table_name: Name of the table
            enhanced: Whether to include LLM descriptions and samples
        """
        inspector = inspect(self.engine)
        if enhanced:
            return self._get_enhanced_table_ddl(table_name, inspector)
        else:
            return self._get_table_ddl(table_name, inspector)
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """Get sample rows from a table."""
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
