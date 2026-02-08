"""Database schema extraction and management."""

from sqlalchemy import create_engine, inspect, MetaData
from typing import List, Dict
import sqlparse


class SchemaExtractor:
    """Extract and manage database schema information."""
    
    def __init__(self, database_url: str):
        """Initialize schema extractor with database connection."""
        self.engine = create_engine(database_url)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self._schema_cache = None
    
    def get_full_schema(self) -> str:
        """Get complete database schema as formatted DDL."""
        if self._schema_cache:
            return self._schema_cache
        
        inspector = inspect(self.engine)
        schema_parts = []
        
        for table_name in inspector.get_table_names():
            schema_parts.append(self._get_table_ddl(table_name, inspector))
        
        self._schema_cache = "\n\n".join(schema_parts)
        return self._schema_cache
    
    def _get_table_ddl(self, table_name: str, inspector) -> str:
        """Generate DDL for a single table with comments."""
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
            
            # Add comment describing the column
            col_def += f"  -- {self._generate_column_description(col['name'], table_name)}"
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
    
    def _generate_column_description(self, column_name: str, table_name: str) -> str:
        """Generate natural language description for a column."""
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
    
    def get_table_names(self) -> List[str]:
        """Get list of all table names in the database."""
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def get_table_schema(self, table_name: str) -> str:
        """Get schema for a specific table."""
        inspector = inspect(self.engine)
        return self._get_table_ddl(table_name, inspector)
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """Get sample rows from a table."""
        with self.engine.connect() as conn:
            result = conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
