# Running the Streamlit App

## Install Additional Dependencies

First, install the new web interface dependencies:

```bash
.\venv\Scripts\Activate.ps1
pip install streamlit plotly pandas
```

Or reinstall all requirements:

```bash
pip install -r requirements.txt
```

## Start the App

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

## Features

### Tab 1: 🔍 SQL Query
- Direct SQL query execution
- Quick example buttons
- Results displayed in interactive table
- Download results as CSV
- Auto-visualization (bar, line, pie charts)
- Safety: Only SELECT queries allowed

### Tab 2: 💬 AI Chatbot
- Natural language to SQL conversion
- Chat history with conversation context
- Generated SQL display
- Automatic query correction
- Results download
- Error handling and debugging

## Usage Examples

### SQL Query Tab
```sql
-- Find top spenders
SELECT c.first_name, c.last_name, SUM(o.total_amount) as total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id
ORDER BY total_spent DESC
LIMIT 5
```

### AI Chatbot Tab
Just ask in plain English:
- "Show me all customers from California"
- "What are the top 5 most expensive products?"
- "How many orders were placed in each city?"

## Tips

1. **Sidebar** shows database schema and table info
2. **Download** results as CSV from both tabs
3. **Visualizations** auto-generate for numeric data
4. **Chat history** is preserved during session
5. **Clear history** button to start fresh

## Troubleshooting

**"OPENAI_API_KEY not set"**
- Make sure your `.env` file has your OpenAI API key
- Restart the Streamlit app after adding the key

**Port already in use**
- Stop other Streamlit apps or use: `streamlit run app.py --server.port 8502`

**Database not found**
- Run: `python scripts\create_sample_db.py`
