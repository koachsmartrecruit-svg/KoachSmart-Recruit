#!/usr/bin/env python3
"""
Create database tables for KoachSmart platform
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app_factory import create_app
from core.extensions import db

def create_tables():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ All database tables created successfully!")
            
            # List created tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n📋 Created tables ({len(tables)}):")
            for table in sorted(tables):
                print(f"   - {table}")
                
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    return True

if __name__ == "__main__":
    create_tables()