
import sqlite3
from config import DATABASE
from datetime import date, timedelta


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():

    conn = get_db()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meal_date TEXT,
        meal_type TEXT,
        menu TEXT,
        attendance INTEGER,
        prepared INTEGER,
        consumed INTEGER,
        wasted INTEGER
    );

    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        quantity REAL,
        unit TEXT,
        expiry TEXT
    );

    CREATE TABLE IF NOT EXISTS surplus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food TEXT,
        quantity REAL,
        unit TEXT,
        location TEXT,
        expiry TEXT,
        contact TEXT,
        status TEXT DEFAULT 'Available'
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    """)

    conn.commit()
    conn.close()

