"""
Pydantic schemas for API request/response contracts.
Defines well-structured data models for all API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Note Schemas
# ============================================================================

class NoteCreateRequest(BaseModel):
    """Request schema for creating a new note."""
    content: str = Field(..., min_length=1, description="The content of the note")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Strip whitespace and validate content is not empty."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("content cannot be empty or whitespace only")
        return stripped


class NoteResponse(BaseModel):
    """Response schema for a note."""
    id: int = Field(..., description="Unique identifier for the note")
    content: str = Field(..., description="The content of the note")
    created_at: str = Field(..., description="ISO format timestamp when note was created")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "content": "Meeting notes from today",
                "created_at": "2024-12-27T10:30:00"
            }
        }


class NoteListResponse(BaseModel):
    """Response schema for a list of notes."""
    notes: list[NoteResponse] = Field(..., description="List of notes")
    count: int = Field(..., description="Total number of notes")


# ============================================================================
# Action Item Schemas
# ============================================================================

class ActionItemResponse(BaseModel):
    """Response schema for a single action item."""
    id: int = Field(..., description="Unique identifier for the action item")
    note_id: Optional[int] = Field(None, description="ID of the associated note, if any")
    text: str = Field(..., description="The action item text")
    done: bool = Field(..., description="Whether the action item is completed")
    created_at: str = Field(..., description="ISO format timestamp when action item was created")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "note_id": 5,
                "text": "Set up database",
                "done": False,
                "created_at": "2024-12-27T10:30:00"
            }
        }


class ActionItemListResponse(BaseModel):
    """Response schema for a list of action items."""
    items: list[ActionItemResponse] = Field(..., description="List of action items")
    count: int = Field(..., description="Total number of action items")


class ExtractActionItemsRequest(BaseModel):
    """Request schema for extracting action items from text."""
    text: str = Field(..., min_length=1, description="Text to extract action items from")
    save_note: bool = Field(default=False, description="Whether to save the text as a note")
    use_llm: bool = Field(default=False, description="Whether to use LLM extraction (vs heuristic)")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Strip whitespace and validate text is not empty."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("text cannot be empty or whitespace only")
        return stripped


class ExtractActionItemsResponse(BaseModel):
    """Response schema for action item extraction."""
    note_id: Optional[int] = Field(None, description="ID of the created note, if save_note was True")
    items: list[ActionItemResponse] = Field(..., description="Extracted action items")
    extraction_method: str = Field(..., description="Method used: 'llm' or 'heuristic'")


class MarkActionItemDoneRequest(BaseModel):
    """Request schema for marking an action item as done/undone."""
    done: bool = Field(default=True, description="Whether the action item should be marked as done")


class MarkActionItemDoneResponse(BaseModel):
    """Response schema for marking an action item as done."""
    id: int = Field(..., description="ID of the action item")
    done: bool = Field(..., description="New done status")


# ============================================================================
# Error Response Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str = Field(..., description="Error type or code")
    detail: str = Field(..., description="Detailed error message")
    status_code: int = Field(..., description="HTTP status code")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "detail": "text cannot be empty or whitespace only",
                "status_code": 400
            }
        }

