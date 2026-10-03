import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "phoenix.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            balance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            game_id INTEGER,
            package_id INTEGER,
            package_name TEXT,
            player_id TEXT,
            server_id TEXT,
            amount REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            playpay_order_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_percent REAL DEFAULT 0,
            active INTEGER DEFAULT 1,
            max_uses INTEGER DEFAULT 0,
            used_count INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS promo_uses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            promo_id INTEGER NOT NULL,
            telegram_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS account_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_telegram_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            image_url TEXT,
            video_url TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def create_or_update_user(
    telegram_id: int,
    username: str = "",
    first_name: str = ""
):
    conn = get_connection()

    conn.execute("""
        INSERT INTO users (
            telegram_id,
            username,
            first_name
        )
        VALUES (?, ?, ?)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
    """, (
        telegram_id,
        username,
        first_name
    ))

    conn.commit()
    conn.close()


def get_user(telegram_id: int):
    conn = get_connection()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE telegram_id = ?
    """, (telegram_id,)).fetchone()

    conn.close()

    return dict(user) if user else None


def get_balance(telegram_id: int):
    user = get_user(telegram_id)

    if not user:
        return 0

    return float(user["balance"] or 0)


def add_balance(telegram_id: int, amount: float):
    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE telegram_id = ?
    """, (
        amount,
        telegram_id
    ))

    conn.commit()
    conn.close()


def subtract_balance(telegram_id: int, amount: float):
    conn = get_connection()

    cursor = conn.execute("""
        UPDATE users
        SET balance = balance - ?
        WHERE telegram_id = ?
        AND balance >= ?
    """, (
        amount,
        telegram_id,
        amount
    ))

    success = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return success
