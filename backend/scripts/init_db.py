#!/usr/bin/env python3
"""
Database initialization script.

Creates all tables defined in SQLAlchemy models.
"""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import engine
from models.base import Base
from models import (
    User,
    Project,
    AreaOfInterest,
    AnalysisJob,
    InfrastructureOSM
)

def init_database():
    """Create all database tables."""
    print("Creating database tables...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")

    # Print created tables
    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    init_database()
