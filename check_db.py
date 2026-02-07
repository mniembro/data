import sqlite3
import pandas as pd

def check_database(db_path):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\nTables in the database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check productos table
        if 'productos' in [t[0] for t in tables]:
            # Get table info
            cursor.execute("PRAGMA table_info(productos);")
            columns = cursor.fetchall()
            print("\nProductos table columns:")
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
            
            # Count rows
            cursor.execute("SELECT COUNT(*) FROM productos;")
            count = cursor.fetchone()[0]
            print(f"\nTotal products in database: {count}")
            
            # Show sample data
            if count > 0:
                print("\nSample data (first 5 rows):")
                df = pd.read_sql_query("SELECT * FROM productos LIMIT 5", conn)
                print(df)
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    db_path = "test_products.db"  # Change this to check a different database
    print(f"Checking database: {db_path}")
    check_database(db_path)
