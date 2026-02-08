"""
Streamlit Web Interface for NLP-to-SQL Chatbot

Features:
- Tab 1: Direct SQL Query Interface
- Tab 2: AI-Powered Natural Language Chatbot
"""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
from src.workflow.graph import text_to_sql_workflow
from src.config import get_settings
from src.schema.schema_extractor import SchemaExtractor
import time

# Page configuration
st.set_page_config(
    page_title="NLP-to-SQL Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sql-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        font-family: 'Courier New', monospace;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Load settings
@st.cache_resource
def get_db_connection():
    """Get database connection."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    return engine

@st.cache_resource
def get_schema_info():
    """Get database schema information."""
    settings = get_settings()
    extractor = SchemaExtractor(settings.database_url)
    return extractor

def execute_sql_query(query: str):
    """Execute a SQL query and return results."""
    try:
        engine = get_db_connection()
        with engine.connect() as conn:
            result = conn.execute(text(query))
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                columns = result.keys()
                rows = result.fetchall()
                df = pd.DataFrame(rows, columns=columns)
                return df, None
            else:
                return None, "Only SELECT queries are allowed for safety."
    except Exception as e:
        return None, str(e)

def format_query_for_display(sql: str) -> str:
    """Format SQL query for nice display."""
    # Simple formatting
    keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 
                'INNER JOIN', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT']
    
    formatted = sql
    for keyword in keywords:
        formatted = formatted.replace(f' {keyword} ', f'\n{keyword} ')
        formatted = formatted.replace(f' {keyword.lower()} ', f'\n{keyword} ')
    
    return formatted.strip()

# Main header
st.markdown('<div class="main-header">🤖 NLP-to-SQL Chatbot</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📊 Database Info")
    
    try:
        extractor = get_schema_info()
        tables = extractor.get_table_names()
        
        st.success(f"✅ Connected to database")
        st.metric("Tables", len(tables))
        
        with st.expander("📋 View Tables"):
            for table in tables:
                st.write(f"• {table}")
        
        with st.expander("🔍 View Full Schema"):
            schema = extractor.get_full_schema()
            st.code(schema, language="sql")
    
    except Exception as e:
        st.error(f"❌ Database connection error: {str(e)}")
    
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    
    settings = get_settings()
    st.info(f"**Model:** {settings.llm_model}")
    st.info(f"**Max Corrections:** {settings.max_correction_attempts}")

# Main tabs
tab1, tab2 = st.tabs(["🔍 SQL Query", "💬 AI Chatbot"])

# ==================== TAB 1: SQL Query ====================
with tab1:
    st.header("Direct SQL Query Interface")
    st.markdown("Execute SQL queries directly against the database. Only SELECT queries are allowed.")
    
    # SQL input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        sql_query = st.text_area(
            "Enter your SQL query:",
            height=150,
            placeholder="SELECT * FROM customers WHERE state = 'CA' LIMIT 10",
            key="sql_input"
        )
    
    with col2:
        st.markdown("**Quick Examples:**")
        if st.button("📋 All Customers"):
            st.session_state.sql_input = "SELECT * FROM customers LIMIT 10"
            st.rerun()
        if st.button("📦 All Products"):
            st.session_state.sql_input = "SELECT * FROM products LIMIT 10"
            st.rerun()
        if st.button("🛒 Recent Orders"):
            st.session_state.sql_input = "SELECT * FROM orders ORDER BY order_date DESC LIMIT 10"
            st.rerun()
        if st.button("💰 Top Spenders"):
            st.session_state.sql_input = """SELECT c.first_name, c.last_name, SUM(o.total_amount) as total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spent DESC
LIMIT 5"""
            st.rerun()
    
    # Execute button
    if st.button("▶️ Execute Query", type="primary", use_container_width=True):
        if sql_query.strip():
            with st.spinner("Executing query..."):
                df, error = execute_sql_query(sql_query)
                
                if error:
                    st.markdown(f'<div class="error-box">❌ Error: {error}</div>', unsafe_allow_html=True)
                else:
                    # Display results
                    st.markdown(f'<div class="success-box">✅ Query executed successfully! ({len(df)} rows returned)</div>', unsafe_allow_html=True)
                    
                    # Show data
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv"
                    )
                    
                    # Visualization options if numeric columns exist
                    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
                    if numeric_cols and len(df) > 1:
                        st.markdown("### 📊 Quick Visualization")
                        
                        viz_type = st.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Pie Chart"])
                        
                        if viz_type == "Bar Chart" and len(df) <= 20:
                            x_col = st.selectbox("X-axis", df.columns.tolist())
                            y_col = st.selectbox("Y-axis", numeric_cols)
                            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        elif viz_type == "Line Chart":
                            x_col = st.selectbox("X-axis", df.columns.tolist())
                            y_col = st.selectbox("Y-axis", numeric_cols)
                            fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} trend")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        elif viz_type == "Pie Chart" and len(df) <= 10:
                            label_col = st.selectbox("Labels", df.columns.tolist())
                            value_col = st.selectbox("Values", numeric_cols)
                            fig = px.pie(df, names=label_col, values=value_col, title=f"{value_col} distribution")
                            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Please enter a SQL query.")

# ==================== TAB 2: AI Chatbot ====================
with tab2:
    st.header("AI-Powered Natural Language Chatbot")
    st.markdown("Ask questions in plain English, and I'll convert them to SQL and fetch the results!")
    
    # Sample questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        **Simple Queries:**
        - Show me all customers
        - List all products in the Electronics category
        - What are the most expensive products?
        
        **Aggregations:**
        - How many orders were placed in 2025?
        - What's the total revenue by product category?
        - What's the average order value?
        
        **Complex Queries:**
        - Show me customers who have spent more than $1000
        - What are the top 5 best-selling products?
        - Which city has the most customers?
        - List orders with customer names and total amounts
        """)
    
    # Chat input
    user_question = st.text_input(
        "Ask your question:",
        placeholder="e.g., Show me the top 5 customers by total spending",
        key="chatbot_input"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        ask_button = st.button("🚀 Ask", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    # Process question
    if ask_button and user_question.strip():
        # Check if API key is set
        settings = get_settings()
        if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
            st.error("❌ Please set your OPENAI_API_KEY in the .env file to use the AI chatbot.")
        else:
            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            
            # Show processing
            with st.spinner("🤔 Thinking..."):
                # Initialize state
                initial_state = {
                    "question": user_question,
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
                    # Run workflow
                    final_state = text_to_sql_workflow.invoke(initial_state)
                    
                    # Extract results
                    generated_sql = final_state.get("final_sql", final_state.get("generated_sql", "N/A"))
                    execution_successful = final_state.get("execution_successful", False)
                    query_results = final_state.get("query_results", [])
                    execution_error = final_state.get("execution_error")
                    correction_attempts = final_state.get("correction_attempt", 0)
                    
                    # Create response
                    response = {
                        "role": "assistant",
                        "sql": generated_sql,
                        "success": execution_successful,
                        "results": query_results,
                        "error": execution_error,
                        "corrections": correction_attempts
                    }
                    
                    st.session_state.chat_history.append(response)
                    
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "error": str(e),
                        "success": False
                    })
            
            st.rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("### 💬 Conversation")
        
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.markdown(f'<div class="info-box">👤 <b>You:</b> {message["content"]}</div>', unsafe_allow_html=True)
            
            else:  # assistant
                st.markdown('<div class="sql-box">', unsafe_allow_html=True)
                st.markdown("🤖 **AI Assistant**")
                
                if message.get("success"):
                    # Show SQL
                    st.markdown("**Generated SQL:**")
                    st.code(message["sql"], language="sql")
                    
                    if message.get("corrections", 0) > 0:
                        st.info(f"ℹ️ Query was corrected {message['corrections']} time(s)")
                    
                    # Show results
                    results = message["results"]
                    if results:
                        st.success(f"✅ Success! ({len(results)} rows)")
                        
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True)
                        
                        # Download option
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download",
                            data=csv,
                            file_name=f"results_{i}.csv",
                            mime="text/csv",
                            key=f"download_{i}"
                        )
                    else:
                        st.warning("No results found.")
                
                else:
                    st.error(f"❌ Error: {message.get('error', 'Unknown error occurred')}")
                    if message.get("sql"):
                        st.markdown("**Attempted SQL:**")
                        st.code(message["sql"], language="sql")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.9rem;">
    Built with ❤️ using Streamlit, LangGraph, and OpenAI GPT-4 | 
    <a href="https://github.com" target="_blank">Documentation</a>
</div>
""", unsafe_allow_html=True)
