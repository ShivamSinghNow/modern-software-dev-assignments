"""
Custom exception classes for the application.
Provides structured error handling throughout the codebase.
"""

from __future__ import annotations


class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class NoteNotFoundError(DatabaseError):
    """Raised when a requested note is not found."""
    def __init__(self, note_id: int):
        self.note_id = note_id
        super().__init__(f"Note with id {note_id} not found")


class ActionItemNotFoundError(DatabaseError):
    """Raised when a requested action item is not found."""
    def __init__(self, action_item_id: int):
        self.action_item_id = action_item_id
        super().__init__(f"Action item with id {action_item_id} not found")


class ExtractionError(Exception):
    """Base exception for extraction-related errors."""
    pass


class LLMExtractionError(ExtractionError):
    """Raised when LLM extraction fails."""
    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(f"LLM extraction failed: {message}")

