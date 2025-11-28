"""
Database Configuration and Setup
SQLAlchemy database engine and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - change this based on your database
# For PostgreSQL: postgresql://user:password@localhost/dbname
# For MySQL: mysql+pymysql://user:password@localhost/dbname
# For SQLite (development): sqlite:///./blockly_platform.db

# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "sqlite:///./blockly_platform.db"  # Default to SQLite for development
# )

# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "mysql+pymysql://root:admin@localhost:3306/pictoblox"  # Default to SQLite for development
# )


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.autrofcnscovpjtkyibr:wb002119232n@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
  
)

# DATABASE_URL="postgresql://pictoblox:wb002119232n@aws-1-ap-southeast-2.supabase.com:6543/postgres"


# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    Use with FastAPI Depends()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def reset_db():
    """Reset database - drop and recreate all tables (USE WITH CAUTION!)"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset completed!")


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()