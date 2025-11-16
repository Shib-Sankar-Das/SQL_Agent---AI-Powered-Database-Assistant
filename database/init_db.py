"""
Database initialization script for SQL Agent
Creates SQLite database with schema and sample data
"""

import sqlite3
import os
from pathlib import Path

def init_database():
    """Initialize the SQLite database with schema and sample data"""
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    # Database file path
    db_path = script_dir / "sql_agent.db"
    
    # Read schema and sample data files
    schema_file = script_dir / "schema.sql"
    sample_data_file = script_dir / "sample_data.sql"
    
    try:
        # Connect to SQLite database (creates if doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Initializing database at: {db_path}")
        
        # Execute schema
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            cursor.executescript(schema_sql)
            print("✓ Database schema created successfully")
        else:
            print("❌ Schema file not found")
            return False
        
        # Execute sample data
        if sample_data_file.exists():
            with open(sample_data_file, 'r') as f:
                sample_data_sql = f.read()
            cursor.executescript(sample_data_sql)
            print("✓ Sample data inserted successfully")
        else:
            print("❌ Sample data file not found")
            return False
        
        # Commit changes
        conn.commit()
        
        # Verify the setup
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✓ Tables created: {[table[0] for table in tables]}")
        
        # Count records in each table
        for table in ['customers', 'offers', 'subscriptions']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✓ {table}: {count} records")
        
        conn.close()
        print(f"✅ Database initialization completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def get_database_info():
    """Get information about the database structure"""
    script_dir = Path(__file__).parent
    db_path = script_dir / "sql_agent.db"
    
    if not db_path.exists():
        print("Database not found. Run init_database() first.")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table information
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        info = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            info[table] = {
                'columns': [col[1] for col in columns],
                'schema': columns
            }
        
        conn.close()
        return info
        
    except sqlite3.Error as e:
        print(f"Error getting database info: {e}")
        return None

if __name__ == "__main__":
    # Initialize the database
    success = init_database()
    
    if success:
        print("\n" + "="*50)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*50)
        
        # Show database info
        info = get_database_info()
        if info:
            print("\nDatabase Structure:")
            for table, details in info.items():
                print(f"\n📋 Table: {table}")
                for col in details['columns']:
                    print(f"   - {col}")
    else:
        print("\n❌ Database initialization failed!")
