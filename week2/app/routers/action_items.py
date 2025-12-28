"""
Action items API router with improved error handling and Pydantic schemas.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from .. import db
from ..exceptions import ActionItemNotFoundError, DatabaseError
from ..schemas import (
    ActionItemListResponse,
    ActionItemResponse,
    ExtractActionItemsRequest,
    ExtractActionItemsResponse,
    MarkActionItemDoneRequest,
    MarkActionItemDoneResponse,
)
from ..services.extract import extract_action_items, extract_action_items_llm

router = APIRouter(prefix="/action-items", tags=["action-items"])


@router.post(
    "/extract",
    response_model=ExtractActionItemsResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract action items from text",
    description="Extracts action items from the provided text using heuristic or LLM extraction.",
)
def extract(request: ExtractActionItemsRequest) -> ExtractActionItemsResponse:
    """
    Extract action items from text.
    
    Args:
        request: Extraction request with text and options
        
    Returns:
        Extracted action items with metadata
        
    Raises:
        HTTPException: If extraction or database operations fail
    """
    try:
        note_id: int | None = None
        
        # Save note if requested
        if request.save_note:
            note_id = db.insert_note(request.text)
        
        # Extract action items using selected method
        if request.use_llm:
            items = extract_action_items_llm(request.text)
            extraction_method = "llm"
        else:
            items = extract_action_items(request.text)
            extraction_method = "heuristic"
        
        # Insert action items into database
        if items:
            item_ids = db.insert_action_items(items, note_id=note_id)
        else:
            item_ids = []
        
        # Build response
        action_items = [
            ActionItemResponse(
                id=item_id,
                note_id=note_id,
                text=item_text,
                done=False,
                created_at="",  # Will be set by database
            )
            for item_id, item_text in zip(item_ids, items)
        ]
        
        # Fetch created_at from database for each item
        for action_item in action_items:
            db_item = db.get_action_item(action_item.id)
            if db_item:
                action_item.created_at = db_item["created_at"]
        
        return ExtractActionItemsResponse(
            note_id=note_id,
            items=action_items,
            extraction_method=extraction_method,
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}",
        ) from e


@router.post(
    "/extract-llm",
    response_model=ExtractActionItemsResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract action items from text using LLM",
    description="Extracts action items from the provided text using LLM-powered extraction.",
)
def extract_llm(request: ExtractActionItemsRequest) -> ExtractActionItemsResponse:
    """
    Extract action items from text using LLM extraction.
    
    Args:
        request: Extraction request with text and options
        
    Returns:
        Extracted action items with metadata
        
    Raises:
        HTTPException: If extraction or database operations fail
    """
    try:
        note_id: int | None = None
        
        # Save note if requested
        if request.save_note:
            note_id = db.insert_note(request.text)
        
        # Extract action items using LLM
        items = extract_action_items_llm(request.text)
        extraction_method = "llm"
        
        # Insert action items into database
        if items:
            item_ids = db.insert_action_items(items, note_id=note_id)
        else:
            item_ids = []
        
        # Build response
        action_items = [
            ActionItemResponse(
                id=item_id,
                note_id=note_id,
                text=item_text,
                done=False,
                created_at="",  # Will be set by database
            )
            for item_id, item_text in zip(item_ids, items)
        ]
        
        # Fetch created_at from database for each item
        for action_item in action_items:
            db_item = db.get_action_item(action_item.id)
            if db_item:
                action_item.created_at = db_item["created_at"]
        
        return ExtractActionItemsResponse(
            note_id=note_id,
            items=action_items,
            extraction_method=extraction_method,
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM extraction failed: {str(e)}",
        ) from e


@router.get(
    "",
    response_model=ActionItemListResponse,
    summary="List action items",
    description="Retrieves action items, optionally filtered by note_id.",
)
def list_all(
    note_id: int | None = Query(
        None,
        description="Optional note ID to filter action items",
    ),
) -> ActionItemListResponse:
    """
    List all action items, optionally filtered by note_id.
    
    Args:
        note_id: Optional note ID to filter by
        
    Returns:
        List of action items with count
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        rows = db.list_action_items(note_id=note_id)
        items = [
            ActionItemResponse(
                id=row["id"],
                note_id=row["note_id"],
                text=row["text"],
                done=bool(row["done"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]
        return ActionItemListResponse(items=items, count=len(items))
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/{action_item_id}/done",
    response_model=MarkActionItemDoneResponse,
    summary="Mark action item as done/undone",
    description="Updates the done status of an action item.",
)
def mark_done(
    action_item_id: int,
    request: MarkActionItemDoneRequest,
) -> MarkActionItemDoneResponse:
    """
    Mark an action item as done or undone.
    
    Args:
        action_item_id: The action item ID
        request: Request with done status
        
    Returns:
        Updated action item status
        
    Raises:
        HTTPException: If action item not found or update fails
    """
    try:
        db.mark_action_item_done(action_item_id, request.done)
        return MarkActionItemDoneResponse(id=action_item_id, done=request.done)
    except ActionItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
