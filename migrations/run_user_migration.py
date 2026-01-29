"""
Run User Onboarding Fields Migration
Adds missing columns to user table
"""

import os
from pathlib import Path
from urllib.parse import urlparse

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_U2DPvHTztLm1@ep-aged-firefly-ahgtok3g-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def run_migration():
    """Run the user onboarding fields migration"""
    
    try:
        import psycopg2
        
        # Parse PostgreSQL connection string
        parsed = urlparse(DATABASE_URL)
        
        print(f"Connecting to PostgreSQL: {parsed.hostname}/{parsed.path.lstrip('/')}")
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        cursor = conn.cursor()
        
        # Read migration SQL
        migration_file = Path(__file__).resolve().parent / "add_user_onboarding_fields.sql"
        
        if not migration_file.exists():
            print(f"Error: Migration file not found at {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            sql_script = f.read()
        
        # Execute migration
        print("Running user onboarding fields migration...")
        cursor.execute(sql_script)
        conn.commit()
        
        print("✓ Migration completed successfully!")
        
        # Verify columns were added
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='user' AND column_name IN ('onboarding_completed_at', 'membership_status', 'membership_expires_at')
        """)
        columns = cursor.fetchall()
        
        print(f"\n✓ Added columns:")
        for col in columns:
            print(f"  - {col[0]}")
        
        cursor.close()
        conn.close()
        return True
            
    except ImportError:
        print("Error: psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"Error running migration: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
