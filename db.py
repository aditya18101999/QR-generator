import sqlite3
import os
import hashlib
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "tags.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def hash_passcode(passcode: str) -> str:
    if not passcode:
        return ""
    return hashlib.sha256(passcode.encode("utf-8")).hexdigest()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                tag_id TEXT PRIMARY KEY,
                claimed INTEGER DEFAULT 0,
                passcode_hash TEXT,
                name TEXT,
                title TEXT,
                phone TEXT,
                email TEXT,
                whatsapp TEXT,
                scan_count INTEGER DEFAULT 0,
                last_scanned_at TEXT,
                created_at TEXT
            )
        """)
        # Create an index on claimed status to make scans faster
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tags_claimed ON tags(claimed)")

def get_tag(tag_id: str):
    tag_id = tag_id.upper()
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tags WHERE tag_id = ?", (tag_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_tag(tag_id: str) -> bool:
    tag_id = tag_id.upper()
    created_at = datetime.utcnow().isoformat()
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO tags (tag_id, claimed, created_at) VALUES (?, 0, ?)",
                (tag_id, created_at)
            )
            return True
        except sqlite3.IntegrityError:
            return False  # Already exists

def claim_tag(tag_id: str, name: str, title: str, phone: str, email: str, whatsapp: str, passcode: str) -> bool:
    tag_id = tag_id.upper()
    p_hash = hash_passcode(passcode)
    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE tags 
            SET claimed = 1, 
                passcode_hash = ?, 
                name = ?, 
                title = ?, 
                phone = ?, 
                email = ?, 
                whatsapp = ?
            WHERE tag_id = ?
            """,
            (p_hash, name, title, phone, email, whatsapp, tag_id)
        )
        return cursor.rowcount > 0

def update_tag(tag_id: str, name: str, title: str, phone: str, email: str, whatsapp: str) -> bool:
    tag_id = tag_id.upper()
    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE tags 
            SET name = ?, 
                title = ?, 
                phone = ?, 
                email = ?, 
                whatsapp = ?
            WHERE tag_id = ?
            """,
            (name, title, phone, email, whatsapp, tag_id)
        )
        return cursor.rowcount > 0

def verify_passcode(tag_id: str, passcode: str) -> bool:
    tag_id = tag_id.upper()
    tag = get_tag(tag_id)
    if not tag or not tag.get("passcode_hash"):
        return False
    return tag["passcode_hash"] == hash_passcode(passcode)

def increment_scan(tag_id: str):
    tag_id = tag_id.upper()
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            """
            UPDATE tags
            SET scan_count = scan_count + 1,
                last_scanned_at = ?
            WHERE tag_id = ?
            """,
            (now, tag_id)
        )

def get_all_tags():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tags ORDER BY tag_id ASC")
        return [dict(row) for row in cursor.fetchall()]

def get_stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        claimed = conn.execute("SELECT COUNT(*) FROM tags WHERE claimed = 1").fetchone()[0]
        unclaimed = total - claimed
        total_scans = conn.execute("SELECT SUM(scan_count) FROM tags").fetchone()[0] or 0
        return {
            "total": total,
            "claimed": claimed,
            "unclaimed": unclaimed,
            "total_scans": total_scans
        }
