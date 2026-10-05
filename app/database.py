from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "growth.db"


def get_connection():
    """Create and return a connection to the SQLite database."""
    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    """Create the required database tables if they don't exist."""
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            college TEXT NOT NULL,
            referral_code TEXT NOT NULL UNIQUE,
            referred_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()