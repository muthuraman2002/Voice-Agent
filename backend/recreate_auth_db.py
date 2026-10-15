#!/usr/bin/env python3
"""
Script to recreate the auth database with all new tables including GuestSession.
This will delete the existing database and create a fresh one.
"""

import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.auth import Base, engine, SessionLocal
from app.core.config import settings

def recreate_database():
    """Drop all tables and recreate them"""
    print(f"Database URL: {settings.AUTH_DATABASE_URL}")

    # Drop all existing tables
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)

    # Create all tables
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)

    print("Database recreated successfully!")
    print("Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

if __name__ == "__main__":
    response = input("This will delete all existing auth data. Continue? (yes/no): ")
    if response.lower() == 'yes':
        recreate_database()
    else:
        print("Cancelled.")
