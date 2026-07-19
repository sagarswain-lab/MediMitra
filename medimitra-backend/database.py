import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable (PostgreSQL on Render, SQLite for local dev)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to SQLite for local development
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'medimitra.db')}"
    print(f"[database] Using local SQLite: {DATABASE_URL}")
else:
    print(f"[database] Using PostgreSQL: {DATABASE_URL[:20]}...")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ══════════════════════════════════════════════
# DATABASE MODELS (SQLAlchemy ORM)
# ══════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    google_sub = Column(String, unique=True, nullable=False, index=True)
    email = Column(String)
    name = Column(String)
    picture = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())


class HealthProfile(Base):
    __tablename__ = "health_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    full_name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    blood_group = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    allergies = Column(Text)  # JSON array as text
    chronic_conditions = Column(Text)  # JSON array as text
    current_medications = Column(Text)  # JSON array as text
    past_surgeries = Column(Text)  # JSON array as text
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    emergency_contact_relation = Column(String)
    emergency_contact = Column(String)  # Legacy field
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class SymptomCheck(Base):
    __tablename__ = "symptom_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    symptoms = Column(Text, nullable=False)
    duration = Column(String)
    severity = Column(String)
    condition = Column(String)
    result_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class PrescriptionRead(Base):
    __tablename__ = "prescription_reads"
    
    id = Column(Integer, primary_key=True, index=True)
    language = Column(String)
    result_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class DrugInteraction(Base):
    __tablename__ = "drug_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    medicines = Column(Text, nullable=False)
    risk_level = Column(String)
    result_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class MedicineScan(Base):
    __tablename__ = "medicine_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String)
    safety_score = Column(Integer)
    verdict = Column(String)
    result_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class LifestylePlan(Base):
    __tablename__ = "lifestyle_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer)
    goal = Column(String)
    activity = Column(String)
    bmi = Column(Float)
    result_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)
    feedback = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


# ══════════════════════════════════════════════
# DATABASE HELPER FUNCTIONS
# ══════════════════════════════════════════════

def get_db() -> Session:
    """
    FastAPI dependency for getting database session.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class PostgreSQLConnectionWrapper:
    """
    Wrapper for psycopg2 connection that adds execute() method like sqlite3.
    Makes PostgreSQL connections behave like SQLite connections for backward compatibility.
    """
    def __init__(self, psycopg2_conn):
        self._conn = psycopg2_conn
        self._cursor = None
    
    def execute(self, sql, params=None):
        """Execute SQL and return cursor with results"""
        import psycopg2.extras
        self._cursor = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        return self._cursor
    
    def commit(self):
        return self._conn.commit()
    
    def rollback(self):
        return self._conn.rollback()
    
    def close(self):
        if self._cursor:
            self._cursor.close()
        return self._conn.close()
    
    def cursor(self, *args, **kwargs):
        import psycopg2.extras
        return self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor, *args, **kwargs)
    
    def __getattr__(self, name):
        # Delegate all other attributes to the wrapped connection
        return getattr(self._conn, name)


def get_connection():
    """
    Legacy function for raw SQL compatibility.
    Returns a connection that supports conn.execute() for both SQLite and PostgreSQL.
    """
    if "sqlite" in str(engine.url):
        # SQLite: use sqlite3 with Row factory
        import sqlite3
        conn = engine.raw_connection()
        conn.row_factory = sqlite3.Row
        return conn
    else:
        # PostgreSQL: wrap connection to add execute() method
        conn = engine.raw_connection()
        return PostgreSQLConnectionWrapper(conn)


def init_db():
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)
    print("[OK] Database initialized successfully with PostgreSQL/SQLite")


# Don't run init_db() at import time - let main.py handle it in startup event