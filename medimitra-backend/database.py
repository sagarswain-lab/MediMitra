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
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'medimitra.db')
    print(f"[database] Using local SQLite: {DATABASE_URL}")
else:
    SQLITE_DB_PATH = None
if DATABASE_URL and "sqlite" not in DATABASE_URL:
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


class _PostgreSQLCursorWrapper:
    """
    Wraps a psycopg2 RealDictCursor to add SQLite-compatible helpers:
    - `lastrowid`: populated after INSERT ... RETURNING id
    """
    def __init__(self, cursor):
        self._cur = cursor
        self.lastrowid = None

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __iter__(self):
        return iter(self._cur)

    def __getattr__(self, name):
        return getattr(self._cur, name)


def _adapt_sql(sql, params):
    """
    Translate SQLite-style queries to PostgreSQL-compatible ones:
    - Replace ? placeholders with %s
    - Inject RETURNING id after INSERT statements so lastrowid works
    Returns (adapted_sql, adapted_params, needs_returning)
    """
    adapted = sql.replace("?", "%s")
    needs_returning = False
    # Only inject RETURNING if it's a plain INSERT without an existing RETURNING clause
    stripped = adapted.strip().upper()
    if stripped.startswith("INSERT") and "RETURNING" not in stripped:
        adapted = adapted.rstrip().rstrip(";") + " RETURNING id"
        needs_returning = True
    return adapted, params, needs_returning


class PostgreSQLConnectionWrapper:
    """
    Wrapper for psycopg2 connection that makes it behave like sqlite3:
    - Translates ? → %s placeholders automatically
    - Supports lastrowid via RETURNING id injection on INSERTs
    - Returns dict-like rows (RealDictCursor)
    """
    def __init__(self, psycopg2_conn):
        self._conn = psycopg2_conn
        self._last_cursor = None

    def execute(self, sql, params=None):
        """Execute SQL (translating ? → %s) and return a cursor wrapper."""
        import psycopg2.extras
        raw_cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        adapted_sql, adapted_params, needs_returning = _adapt_sql(sql, params)

        if adapted_params:
            raw_cur.execute(adapted_sql, adapted_params)
        else:
            raw_cur.execute(adapted_sql)

        wrapper = _PostgreSQLCursorWrapper(raw_cur)
        if needs_returning:
            row = raw_cur.fetchone()
            if row:
                wrapper.lastrowid = row["id"]

        self._last_cursor = wrapper
        return wrapper

    def cursor(self, *args, **kwargs):
        """Return a cursor wrapper (used by feedback.py which calls conn.cursor())."""
        import psycopg2.extras
        raw_cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return _RawCursorAdapter(raw_cur)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


class _RawCursorAdapter:
    """
    Wraps a psycopg2 cursor obtained via conn.cursor() so that raw
    cursor.execute(sql, params) calls also get ? → %s translation.
    """
    def __init__(self, cur):
        self._cur = cur
        self.lastrowid = None

    def execute(self, sql, params=None):
        adapted_sql, adapted_params, needs_returning = _adapt_sql(sql, params)
        if adapted_params:
            self._cur.execute(adapted_sql, adapted_params)
        else:
            self._cur.execute(adapted_sql)
        if needs_returning:
            row = self._cur.fetchone()
            if row:
                self.lastrowid = row["id"]

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __iter__(self):
        return iter(self._cur)

    def __getattr__(self, name):
        return getattr(self._cur, name)


def get_connection():
    """
    Legacy function for raw SQL compatibility.
    Returns a connection that supports conn.execute() for both SQLite and PostgreSQL.
    Rows are dict-accessible via row['column'] on both backends.
    """
    if "sqlite" in str(engine.url):
        # SQLite: open a NATIVE sqlite3 connection directly so row_factory works.
        # We deliberately avoid engine.raw_connection() because SQLAlchemy wraps it
        # in a proxy that silently ignores the row_factory assignment.
        import sqlite3
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        # PostgreSQL: wrap psycopg2 connection with our compatibility adapter.
        conn = engine.raw_connection()
        return PostgreSQLConnectionWrapper(conn)


def init_db():
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)
    print("[OK] Database initialized successfully with PostgreSQL/SQLite")


# Don't run init_db() at import time - let main.py handle it in startup event