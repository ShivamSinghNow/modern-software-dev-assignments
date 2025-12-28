"""
Database layer with improved error handling and connection management.
Provides a clean interface for database operations.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Optional

from .config import settings
from .exceptions import ActionItemNotFoundError, DatabaseError, NoteNotFoundError


@contextmanager
def get_connection():
    """
    Context manager for database connections.
    Ensures proper connection cleanup and error handling.
    """
    connection = None
    try:
        # Ensure data directory exists
        settings.database_dir.mkdir(parents=True, exist_ok=True)
        
        # Create connection
        connection = sqlite3.connect(str(settings.database_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        
        yield connection
        connection.commit()
    except sqlite3.Error as e:
        if connection:
            connection.rollback()
        raise DatabaseError(f"Database operation failed: {e}") from e
    except Exception as e:
        if connection:
            connection.rollback()
        raise DatabaseError(f"Unexpected database error: {e}") from e
    finally:
        if connection:
            connection.close()


def init_db() -> None:
    """
    Initialize the database schema.
    Creates tables if they don't exist.
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            
            # Create notes table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                """
            )
            
            # Create action_items table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS action_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id INTEGER,
                    text TEXT NOT NULL,
                    done INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE SET NULL
                );
                """
            )
            
            # Create indexes for better query performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_action_items_note_id ON action_items(note_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_action_items_done ON action_items(done)"
            )
            
            connection.commit()
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to initialize database: {e}") from e


# ============================================================================
# Note Operations
# ============================================================================

def insert_note(content: str) -> int:
    """
    Insert a new note into the database.
    
    Args:
        content: The note content
        
    Returns:
        The ID of the created note
        
    Raises:
        DatabaseError: If the insertion fails
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
            return int(cursor.lastrowid)
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to insert note: {e}") from e


def get_note(note_id: int) -> Optional[dict]:
    """
    Retrieve a note by ID.
    
    Args:
        note_id: The note ID
        
    Returns:
        Dictionary with note data, or None if not found
        
    Raises:
        DatabaseError: If the query fails
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, content, created_at FROM notes WHERE id = ?",
                (note_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to get note: {e}") from e


def list_notes() -> list[dict]:
    """
    List all notes, ordered by ID descending (newest first).
    
    Returns:
        List of note dictionaries
        
    Raises:
        DatabaseError: If the query fails
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, content, created_at FROM notes ORDER BY id DESC"
            )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to list notes: {e}") from e


# ============================================================================
# Action Item Operations
# ============================================================================

def insert_action_items(items: list[str], note_id: Optional[int] = None) -> list[int]:
    """
    Insert multiple action items into the database.
    
    Args:
        items: List of action item texts
        note_id: Optional note ID to associate with items
        
    Returns:
        List of created action item IDs
        
    Raises:
        DatabaseError: If the insertion fails
    """
    if not items:
        return []
    
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            ids: list[int] = []
            
            # Insert items one by one to get individual IDs
            # (SQLite doesn't support returning multiple IDs from executemany)
            for item in items:
                cursor.execute(
                    "INSERT INTO action_items (note_id, text) VALUES (?, ?)",
                    (note_id, item),
                )
                ids.append(int(cursor.lastrowid))
            
            return ids
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to insert action items: {e}") from e


def get_action_item(action_item_id: int) -> Optional[dict]:
    """
    Retrieve an action item by ID.
    
    Args:
        action_item_id: The action item ID
        
    Returns:
        Dictionary with action item data, or None if not found
        
    Raises:
        DatabaseError: If the query fails
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, note_id, text, done, created_at FROM action_items WHERE id = ?",
                (action_item_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to get action item: {e}") from e


def list_action_items(note_id: Optional[int] = None) -> list[dict]:
    """
    List action items, optionally filtered by note_id.
    
    Args:
        note_id: Optional note ID to filter by
        
    Returns:
        List of action item dictionaries
        
    Raises:
        DatabaseError: If the query fails
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            if note_id is None:
                cursor.execute(
                    "SELECT id, note_id, text, done, created_at FROM action_items ORDER BY id DESC"
                )
            else:
                cursor.execute(
                    "SELECT id, note_id, text, done, created_at FROM action_items WHERE note_id = ? ORDER BY id DESC",
                    (note_id,),
                )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to list action items: {e}") from e


def mark_action_item_done(action_item_id: int, done: bool) -> None:
    """
    Mark an action item as done or undone.
    
    Args:
        action_item_id: The action item ID
        done: Whether the item should be marked as done
        
    Raises:
        ActionItemNotFoundError: If the action item doesn't exist
        DatabaseError: If the update fails
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE action_items SET done = ? WHERE id = ?",
                (1 if done else 0, action_item_id),
            )
            
            # Check if any row was updated
            if cursor.rowcount == 0:
                raise ActionItemNotFoundError(action_item_id)
    except ActionItemNotFoundError:
        raise
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to update action item: {e}") from e
