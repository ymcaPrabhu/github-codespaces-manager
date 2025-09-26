"""
Database models and initialization for the web application
"""

import sqlite3
import aiosqlite
from typing import Dict, List, Any, Optional
from datetime import datetime


class Database:
    """Simple SQLite database manager for the web application"""

    def __init__(self, db_path: str = "codespaces_web.db"):
        self.db_path = db_path

    async def init_database(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Sessions table for tracking operations
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    operation_type TEXT NOT NULL,
                    codespace_name TEXT,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data TEXT
                )
            """)

            # Logs table for operation history
            await db.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                )
            """)

            # Configuration table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Metrics table for historical tracking
            await db.execute("""
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

    async def create_session(self, session_id: str, operation_type: str,
                           codespace_name: str = None, data: Dict[str, Any] = None) -> int:
        """Create a new operation session"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO sessions (session_id, operation_type, codespace_name, status, data)
                VALUES (?, ?, ?, 'started', ?)
            """, (session_id, operation_type, codespace_name, str(data) if data else None))

            await db.commit()
            return cursor.lastrowid

    async def update_session_status(self, session_id: str, status: str, data: Dict[str, Any] = None):
        """Update session status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE sessions
                SET status = ?, updated_at = CURRENT_TIMESTAMP, data = ?
                WHERE session_id = ?
            """, (status, str(data) if data else None, session_id))

            await db.commit()

    async def log_operation(self, session_id: str, level: str, message: str, details: str = None):
        """Log operation message"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO operation_logs (session_id, level, message, details)
                VALUES (?, ?, ?, ?)
            """, (session_id, level, message, details))

            await db.commit()

    async def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Get logs for a specific session"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM operation_logs
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_recent_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent operation sessions"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM sessions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def store_metrics(self, metric_type: str, data: Dict[str, Any]):
        """Store metrics for historical tracking"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO metrics_history (metric_type, metric_data)
                VALUES (?, ?)
            """, (metric_type, str(data)))

            await db.commit()

    async def get_metrics_history(self, metric_type: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for specified period"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM metrics_history
                WHERE metric_type = ?
                AND timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp ASC
            """.format(hours), (metric_type,))

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def set_config(self, key: str, value: str):
        """Set configuration value"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))

            await db.commit()

    async def get_config(self, key: str) -> Optional[str]:
        """Get configuration value"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT value FROM config WHERE key = ?
            """, (key,))

            row = await cursor.fetchone()
            return row[0] if row else None

    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data to keep database size manageable"""
        async with aiosqlite.connect(self.db_path) as db:
            # Remove old logs
            await db.execute("""
                DELETE FROM operation_logs
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))

            # Remove old sessions
            await db.execute("""
                DELETE FROM sessions
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))

            # Keep only recent metrics
            await db.execute("""
                DELETE FROM metrics_history
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))

            await db.commit()


# Global database instance
db = Database()


async def init_database():
    """Initialize the database"""
    await db.init_database()


async def get_database() -> Database:
    """Get database instance"""
    return db