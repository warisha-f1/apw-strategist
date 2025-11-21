import sqlite3
import os
from datetime import datetime

DATABASE_FILE = "f1_strategies.db"

def initialize_db():
    """Ensures the database and the strategies table exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            topic TEXT NOT NULL,
            strategy_name TEXT,
            pit_lap INTEGER,
            tire_type TEXT,
            calculated_delta REAL
        )
    """)
    conn.commit()
    conn.close()

def save_strategy_to_db(topic: str, strategy_details: dict):
    """Saves a generated strategy and the calculated result into the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    s_name = strategy_details.get('strategy_name', 'N/A')
    p_lap = strategy_details.get('pit_lap', 0)
    t_type = strategy_details.get('tire_type', 'N/A')
    delta = strategy_details.get('calculated_delta', 0.0)

    cursor.execute("""
        INSERT INTO strategies (timestamp, topic, strategy_name, pit_lap, tire_type, calculated_delta)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, topic, s_name, p_lap, t_type, delta))
    
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def get_all_strategies_from_db():
    """Retrieves all saved strategies."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, topic, calculated_delta FROM strategies ORDER BY timestamp DESC")
    strategies = cursor.fetchall()
    conn.close()
    
    formatted_strategies = []
    for s_id, timestamp, topic, delta in strategies:
        date_str = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M')
        formatted_strategies.append({
            'id': s_id,
            'date': date_str,
            'topic': topic,
            'delta': delta
        })
    return formatted_strategies

def delete_strategy_by_id(strategy_id: int):
    """Deletes a strategy by its primary key ID."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_deleted