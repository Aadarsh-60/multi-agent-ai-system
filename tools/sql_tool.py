"""
tools/sql_tool.py

Provides an agent with the ability to query a SQL database using natural language.
"""

import sqlite3
import re
from tools.llm import get_llm

def setup_dummy_db(db_path: str = "example.db"):
    """Creates a dummy SQLite database if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            signup_date TEXT NOT NULL,
            plan TEXT NOT NULL
        )
    ''')
    
    # Check if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ("Alice Smith", "alice@example.com", "2023-01-15", "Premium"),
            ("Bob Jones", "bob@example.com", "2023-02-20", "Basic"),
            ("Charlie Brown", "charlie@example.com", "2023-03-10", "Premium"),
            ("Diana Prince", "diana@example.com", "2023-04-05", "Enterprise"),
        ]
        cursor.executemany("INSERT INTO users (name, email, signup_date, plan) VALUES (?, ?, ?, ?)", sample_users)
        conn.commit()
    conn.close()


def ask_database(question: str, db_path: str = "example.db") -> str:
    """
    Translates a natural language question into a SQL query, 
    executes it against the database, and returns the result.
    """
    # 1. Ensure DB exists
    setup_dummy_db(db_path)
    
    # 2. Get schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    schema_info = "\n".join([row[0] for row in cursor.fetchall() if row[0]])
    
    # 3. Ask LLM for SQL query
    llm = get_llm(temperature=0)
    prompt = f"""You are a SQLite database expert.
Given the following database schema:
{schema_info}

Write a valid SQLite query to answer the user's question.
Return ONLY the SQL query, without markdown formatting or any other text.
Question: {question}
"""
    response = llm.invoke(prompt)
    sql_query = response.content.strip()
    
    # Clean up markdown if LLM returned it anyway
    sql_query = re.sub(r"^```sql\n", "", sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r"```$", "", sql_query).strip()
    
    # 4. Execute query
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []
        conn.close()
        
        if not results:
            return f"Query executed successfully, but returned no results.\nQuery: {sql_query}"
            
        # Format results nicely
        res_str = f"Query: {sql_query}\nResults:\n"
        res_str += " | ".join(columns) + "\n"
        for row in results:
            res_str += " | ".join(str(val) for val in row) + "\n"
        return res_str
        
    except Exception as e:
        conn.close()
        return f"Error executing query: {e}\nQuery attempted: {sql_query}"
