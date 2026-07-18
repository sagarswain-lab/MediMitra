import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "medimitra.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symptom_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms TEXT NOT NULL,
            duration TEXT,
            severity TEXT,
            condition TEXT,
            result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescription_reads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicines TEXT NOT NULL,
            risk_level TEXT,
            result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT,
            safety_score INTEGER,
            verdict TEXT,
            result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lifestyle_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER,
            goal TEXT,
            activity TEXT,
            bmi REAL,
            result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating INTEGER NOT NULL,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_sub TEXT UNIQUE NOT NULL,
            email TEXT,
            name TEXT,
            picture TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            full_name TEXT,
            age INTEGER,
            gender TEXT,
            blood_group TEXT,
            height_cm REAL,
            weight_kg REAL,
            allergies TEXT,            -- JSON array as text
            chronic_conditions TEXT,     -- JSON array as text
            current_medications TEXT,    -- JSON array as text
            past_surgeries TEXT,         -- JSON array as text
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            emergency_contact_relation TEXT,
            emergency_contact TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Migration: add new columns if DB already exists ──
    existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(health_profiles)").fetchall()}
    for col, definition in [
        ("full_name",                  "TEXT"),
        ("gender",                     "TEXT"),
        ("height_cm",                  "REAL"),
        ("weight_kg",                  "REAL"),
        ("past_surgeries",             "TEXT"),
        ("emergency_contact_name",     "TEXT"),
        ("emergency_contact_phone",    "TEXT"),
        ("emergency_contact_relation", "TEXT"),
    ]:
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE health_profiles ADD COLUMN {col} {definition}")

    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully")