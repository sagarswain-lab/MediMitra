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
            age INTEGER,
            blood_group TEXT,
            allergies TEXT,        -- JSON array as text
            chronic_conditions TEXT, -- JSON array as text
            current_medications TEXT, -- JSON array as text
            emergency_contact TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully")