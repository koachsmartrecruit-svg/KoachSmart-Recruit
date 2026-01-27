"""
Database Migration Script
Run this script to add employer onboarding columns to the user table.
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

def run_migration():
    """Run the migration to add employer onboarding columns."""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    try:
        # Parse database URL
        # Format: postgresql://user:password@host:port/database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔄 Running migration: Add employer onboarding columns...")
        
        # Add employer_onboarding_step column
        try:
            cursor.execute("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS employer_onboarding_step INTEGER DEFAULT 1;
            """)
            print("✅ Added employer_onboarding_step column")
        except Exception as e:
            print(f"⚠️  employer_onboarding_step: {e}")
        
        # Add employer_onboarding_completed column
        try:
            cursor.execute("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS employer_onboarding_completed BOOLEAN DEFAULT FALSE;
            """)
            print("✅ Added employer_onboarding_completed column")
        except Exception as e:
            print(f"⚠️  employer_onboarding_completed: {e}")
        
        # Update existing records
        try:
            cursor.execute("""
                UPDATE "user" 
                SET employer_onboarding_step = 1, employer_onboarding_completed = FALSE 
                WHERE employer_onboarding_step IS NULL OR employer_onboarding_completed IS NULL;
            """)
            print(f"✅ Updated {cursor.rowcount} existing user records")
        except Exception as e:
            print(f"⚠️  Update existing records: {e}")
        
        # Verify columns exist
        cursor.execute("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'user' 
            AND column_name IN ('employer_onboarding_step', 'employer_onboarding_completed');
        """)
        
        results = cursor.fetchall()
        if results:
            print("\n✅ Migration completed successfully!")
            print("\nColumns added:")
            for col_name, data_type, default in results:
                print(f"  - {col_name}: {data_type} (default: {default})")
        else:
            print("⚠️  Warning: Could not verify columns were added")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Employer Onboarding Columns")
    print("=" * 60)
    run_migration()
    print("=" * 60)

