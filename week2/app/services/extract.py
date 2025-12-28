from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
from ollama import chat
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


class ActionItemsResponse(BaseModel):
    """Pydantic model for structured LLM response containing action items."""
    action_items: List[str]


def extract_action_items_llm(text: str) -> List[str]:
    """
    Extract action items from text using an LLM (Ollama) with structured outputs.
    Returns a list of action item strings. If the LLM fails, returns an empty list.
    Only uses LLM extraction - no fallback to manual extraction.
    """
    # Get model from environment or use default
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    # Create a prompt for extracting action items
    prompt = f"""Extract all action items from the following meeting notes or text. 
An action item is a specific task, todo, or item that requires action or follow-up.

Text:
{text}

Return the action items as a JSON object with an "action_items" array containing the extracted items."""
    
    try:
        # Use Ollama chat with structured output format using Pydantic schema
        response = chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format=ActionItemsResponse.model_json_schema(),  # Pass Pydantic schema for structured output
            options={"temperature": 0}  # Set temperature to 0 for more deterministic output
        )
        
        # Extract the message content from ChatResponse object
        if not hasattr(response, 'message') or not hasattr(response.message, 'content'):
            print("Error: Invalid response structure from LLM")
            return []
        
        content = response.message.content
        
        # Parse and validate the structured response using Pydantic
        action_items_data = ActionItemsResponse.model_validate_json(content)
        
        # Return the list of action items, filtering out empty strings
        return [item.strip() for item in action_items_data.action_items if item and item.strip()]
            
    except Exception as e:
        # If LLM extraction fails, log the error and return empty list
        # No fallback to manual extraction - only LLM is used
        print(f"Error in LLM extraction: {type(e).__name__}: {e}")
        return []

def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters
