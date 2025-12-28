"""
Notes API router with improved error handling and Pydantic schemas.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from .. import db
from ..exceptions import DatabaseError, NoteNotFoundError
from ..schemas import NoteCreateRequest, NoteListResponse, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
    description="Creates a new note with the provided content.",
)
def create_note(request: NoteCreateRequest) -> NoteResponse:
    """
    Create a new note.
    
    Args:
        request: Note creation request with content
        
    Returns:
        Created note with ID and timestamp
        
    Raises:
        HTTPException: If note creation fails
    """
    try:
        note_id = db.insert_note(request.content)
        note = db.get_note(note_id)
        
        if note is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Note was created but could not be retrieved",
            )
        
        return NoteResponse(
            id=note["id"],
            content=note["content"],
            created_at=note["created_at"],
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get a note by ID",
    description="Retrieves a specific note by its ID.",
)
def get_single_note(note_id: int) -> NoteResponse:
    """
    Get a single note by ID.
    
    Args:
        note_id: The note ID
        
    Returns:
        Note data
        
    Raises:
        HTTPException: If note is not found or retrieval fails
    """
    try:
        note = db.get_note(note_id)
        if note is None:
            raise NoteNotFoundError(note_id)
        
        return NoteResponse(
            id=note["id"],
            content=note["content"],
            created_at=note["created_at"],
        )
    except NoteNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "",
    response_model=NoteListResponse,
    summary="List all notes",
    description="Retrieves all notes, ordered by creation date (newest first).",
)
def list_all_notes() -> NoteListResponse:
    """
    List all notes.
    
    Returns:
        List of all notes with count
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        notes_data = db.list_notes()
        notes = [
            NoteResponse(
                id=note["id"],
                content=note["content"],
                created_at=note["created_at"],
            )
            for note in notes_data
        ]
        return NoteListResponse(notes=notes, count=len(notes))
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
