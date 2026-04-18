import sqlite3
from pathlib import Path

DB_PATH = Path('app/data/supply_chain.db')

def inspect():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check table info
    print("--- Alerts Table Info ---")
    try:
        cursor.execute("PRAGMA table_info(alerts)")
        for col in cursor.fetchall():
            print(col)
    except Exception as e:
        print(f"Error checking table info: {e}")

    # Check for actual data and errors in the query
    print("\n--- Testing Query ---")
    query = """
        SELECT h3_cell, alert_tier, MAX(combined_severity) as severity, description
        FROM alerts
        WHERE combined_severity >= 0.3
        GROUP BY h3_cell
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"Query successful. Found {len(rows)} rows.")
        if rows:
            print(f"First row: {rows[0]}")
    except Exception as e:
        print(f"Query ERROR: {e}")
    
    conn.close()

if __name__ == "__main__":
    inspect()
