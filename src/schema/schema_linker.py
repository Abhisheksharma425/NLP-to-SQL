"""Schema linking using TF-IDF similarity."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple
import numpy as np
from .schema_extractor import SchemaExtractor


class SchemaLinker:
    """Link natural language questions to relevant database tables."""
    
    def __init__(self, schema_extractor: SchemaExtractor):
        """Initialize schema linker with schema information."""
        self.schema_extractor = schema_extractor
        self.table_names = schema_extractor.get_table_names()
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        
        # Create corpus for each table (name + column names + descriptions)
        self.table_corpus = self._build_table_corpus()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.table_corpus)
    
    def _build_table_corpus(self) -> List[str]:
        """Build text corpus for each table."""
        corpus = []
        
        for table_name in self.table_names:
            # Get table schema
            schema = self.schema_extractor.get_table_schema(table_name)
            
            # Extract meaningful text (table name, column names, comments)
            text_parts = [table_name.replace("_", " ")]
            
            # Parse schema to extract column names and comments
            for line in schema.split('\n'):
                line = line.strip()
                if line and not line.startswith('CREATE') and not line.startswith('FOREIGN'):
                    # Extract column name
                    parts = line.split()
                    if parts:
                        col_name = parts[0].replace("_", " ")
                        text_parts.append(col_name)
                    
                    # Extract comment if present
                    if '--' in line:
                        comment = line.split('--')[1].strip()
                        text_parts.append(comment)
            
            corpus.append(" ".join(text_parts))
        
        return corpus
    
    def link_tables(self, question: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Find the most relevant tables for a given question.
        
        Args:
            question: Natural language question
            top_k: Number of top tables to return
        
        Returns:
            List of (table_name, similarity_score) tuples
        """
        # Vectorize the question
        question_vector = self.vectorizer.transform([question.lower()])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(question_vector, self.tfidf_matrix)[0]
        
        # Get top-k tables
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = [
            (self.table_names[idx], similarities[idx])
            for idx in top_indices
            if similarities[idx] > 0  # Only return tables with non-zero similarity
        ]
        
        return results
    
    def get_relevant_schema(self, question: str, top_k: int = 3) -> str:
        """Get schema DDL for only the relevant tables."""
        relevant_tables = self.link_tables(question, top_k)
        
        schema_parts = []
        for table_name, score in relevant_tables:
            schema = self.schema_extractor.get_table_schema(table_name)
            schema_parts.append(f"-- Relevance: {score:.2f}\n{schema}")
        
        return "\n\n".join(schema_parts)
