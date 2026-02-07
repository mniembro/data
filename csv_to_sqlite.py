import sqlite3
import pandas as pd
import os
import argparse
from datetime import datetime
import hashlib

def create_tables(conn):
    """Create the database tables with the same structure as productos_old.db"""
    cursor = conn.cursor()
    
    # Drop existing tables if they exist (except sqlite_sequence which is system-managed)
    cursor.executescript('''
    DROP TABLE IF EXISTS productos;
    DROP TABLE IF EXISTS almacenes;
    DROP TABLE IF EXISTS users;
    
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_barras TEXT NOT NULL,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        descripcion_empaque TEXT,
        color TEXT,
        cantidad INTEGER NOT NULL DEFAULT 0,
        almacen TEXT NOT NULL,
        image_path TEXT,
        UNIQUE(codigo_barras, almacen)  -- Ensure unique barcode per warehouse
    );
    
    CREATE TABLE IF NOT EXISTS almacenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        direccion TEXT
    );
    
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        nombre TEXT,
        email TEXT,
        is_admin BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    
    # Insert default data
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO users (username, password_hash, nombre, email, is_admin) 
        VALUES (?, ?, ?, ?, ?)
        ''', ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Administrator', 'admin@example.com', 1))
    
    cursor.execute("SELECT COUNT(*) FROM almacenes WHERE nombre = 'Almacen Principal'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO almacenes (nombre, direccion) 
        VALUES (?, ?)
        ''', ('Almacen Principal', 'Ubicación principal'))
    
    conn.commit()

def map_csv_to_products(df):
    """Map the CSV columns to the productos table structure"""
    df = df.copy()
    
    df = df.dropna(how='all')
    barcode_col = None
    for col in ['Codigo de Barras', 'Código de Barras', 'Código']:
        if col in df.columns:
            barcode_col = col
            break
    
    if barcode_col:
        df[barcode_col] = df[barcode_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        # Remove rows with empty or NaN barcodes
        df = df[df[barcode_col].str.len() > 0]
        df = df[df[barcode_col] != 'nan']
    
    # 3. Create a new DataFrame with the required columns
    productos = pd.DataFrame()
    
    # Map columns from CSV to database schema
    column_mapping = {
        'Codigo de Barras': 'codigo_barras',
        'Código de Barras': 'codigo_barras',
        'Código': 'codigo_barras',
        'Articulo': 'nombre',
        'Producto': 'nombre',
        'Descripcion': 'descripcion',
        'Color': 'color',
        'Cantidad': 'cantidad',
        'Cant.': 'cantidad',
        'Almacen': 'almacen',
        'Imagen': 'image_path',
        'Empaque': 'descripcion_empaque'  # Map 'Empaque' to a new column
    }
    
    # Rename columns according to mapping
    for csv_col, db_col in column_mapping.items():
        if csv_col in df.columns:
            productos[db_col] = df[csv_col]
    
    # Set default values for required fields
    if 'codigo_barras' not in productos.columns or len(productos['codigo_barras']) == 0:
        # Generate unique codes if no barcode column or empty
        productos['codigo_barras'] = [f'COD{i:05d}' for i in range(1, len(df) + 1)]
    
    # Clean up barcodes - ensure they're strings and remove any .0 suffixes
    productos['codigo_barras'] = (
        productos['codigo_barras']
        .astype(str)
        .str.replace(r'\.0$', '', regex=True)
        .str.strip()
    )
    
    # Set default values for other required fields
    default_values = {
        'nombre': 'Producto sin nombre',
        'cantidad': 0,
        'almacen': 'Almacen Principal',
        'descripcion': '',
        'color': '',
        'image_path': ''
    }
    
    for field, default in default_values.items():
        if field not in productos.columns:
            productos[field] = default
    
    # Convert data types
    productos['cantidad'] = pd.to_numeric(productos['cantidad'], errors='coerce').fillna(0).astype(int)
    
    # Ensure no duplicate barcodes (keep first occurrence)
    productos = productos.drop_duplicates(subset=['codigo_barras'], keep='first')
    
    # Print summary
    print(f"\nProcessed {len(productos)} products")
    if len(productos) < len(df):
        print(f"Note: {len(df) - len(productos)} rows were removed due to missing or invalid data")
    
    return productos

def create_database(csv_file, db_name='productos.db'):
    """
    Create an SQLite database with the same structure as productos_old.db
    and import data from CSV.
    
    Args:
        csv_file (str): Path to the CSV file
        db_name (str): Name of the SQLite database
    """
    try:
        # Ensure .db extension
        if not db_name.endswith('.db'):
            db_name += '.db'
        
        # Remove existing database file if it exists
        if os.path.exists(db_name):
            os.remove(db_name)
        
        # Read the CSV file
        print(f"Reading CSV file: {csv_file}")
        df = pd.read_csv(csv_file)
        print(f"Found {len(df)} rows in CSV")
        
        # Create a connection to the SQLite database
        conn = sqlite3.connect(db_name)
        
        # Create tables with the same structure as productos_old.db
        print("\nCreating database structure...")
        create_tables(conn)
        
        # Map CSV data to productos table
        print("\nProcessing data...")
        productos = map_csv_to_products(df)
        print(f"Mapped {len(productos)} products")
        
        # Print sample of the data
        print("\nSample of data to be imported:")
        print(productos[['codigo_barras', 'nombre']].head())
        
        # Write the data to the SQLite database
        print(f"\nImporting {len(productos)} records...")
        productos.to_sql('productos', conn, if_exists='append', index=False)
        
        # Create indexes
        with conn:
            conn.execute('CREATE INDEX IF NOT EXISTS idx_codigo_barras ON productos(codigo_barras)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_almacen ON productos(almacen)')
        
        # Print database info
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM productos")
        row_count = cursor.fetchone()[0]
        
        print(f"\nSuccessfully created database: {os.path.abspath(db_name)}")
        print(f"Total products: {row_count:,}")
        
        # Show some stats
        print("\nProduct count by almacen:")
        cursor.execute("""
            SELECT almacen, COUNT(*) as count 
            FROM productos 
            GROUP BY almacen 
            ORDER BY count DESC
        """)
        for row in cursor.fetchall():
            print(f"- {row[0]}: {row[1]} productos")
        
        # Close the connection
        conn.close()
        
        return db_name
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Convert CSV to SQLite database matching productos_old.db structure')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--db', default='productos.db', 
                       help='Output database name (default: productos.db)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: File '{args.csv_file}' not found.")
        return 1
    
    db_path = create_database(
        csv_file=args.csv_file,
        db_name=args.db
    )
    
    if db_path:
        print(f"\nDatabase created successfully at: {os.path.abspath(db_path)}")
        print("\nYou can now use this database with your existing application.")
        print("Default admin credentials:")
        print("Username: admin")
        print("Password: admin123")
        
        print("\nTo query the database, you can use:")
        print(f"1. Command line: sqlite3 {os.path.abspath(db_path)}")
        print("2. Python: Use sqlite3 or pandas with the database path")
        print("3. DB Browser for SQLite (GUI tool)")

if __name__ == "__main__":
    main()
