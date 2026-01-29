"""
Run Admin Models Migration
Executes the SQL migration to create admin tables
"""

import sqlite3
import os
from pathlib import Path

# Get database path
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "instance" / "khelo_coach.db"

def run_migration():
    """Run the admin models migration"""
    
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return False
    
    try:
        # Read migration SQL
        migration_file = Path(__file__).resolve().parent / "add_admin_models.sql"
        
        if not migration_file.exists():
            print(f"Error: Migration file not found at {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            sql_script = f.read()
        
        # Connect to database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Execute migration
        print("Running admin models migration...")
        cursor.executescript(sql_script)
        conn.commit()
        
        print("✓ Migration completed successfully!")
        print(f"✓ Database: {DB_PATH}")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'admin%'")
        tables = cursor.fetchall()
        
        print(f"\n✓ Created tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error running migration: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
