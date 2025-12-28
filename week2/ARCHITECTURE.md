# Architecture Writeup: Action Item Extractor

## Overview

This is a **FastAPI-based web application** that extracts actionable items from free-form text notes. The application follows a **layered architecture pattern** with clear separation between presentation, business logic, and data access layers. It uses SQLite for persistence and provides a simple HTML/JavaScript frontend.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│                    (HTML/JavaScript)                         │
│                  /frontend/index.html                        │
└───────────────────────────┬─────────────────────────────────┘
                             │ HTTP Requests
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│                    /app/main.py                              │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  Notes Router        │  │  Action Items Router │        │
│  │  /app/routers/       │  │  /app/routers/       │        │
│  │  notes.py            │  │  action_items.py     │        │
│  └──────────┬───────────┘  └──────────┬───────────┘        │
└─────────────┼──────────────────────────┼────────────────────┘
              │                          │
              ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│              /app/services/extract.py                        │
│         (Action Item Extraction Logic)                       │
└───────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│                    /app/db.py                                │
│         (SQLite Database Operations)                         │
└───────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                          │
│              /data/app.db (SQLite)                           │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  notes table     │  │ action_items     │                │
│  │  - id            │  │  - id            │                │
│  │  - content       │  │  - note_id (FK)  │                │
│  │  - created_at    │  │  - text          │                │
│  └──────────────────┘  │  - done          │                │
│                        │  - created_at    │                │
│                        └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Application Entry Point (`app/main.py`)

**Purpose**: Initializes the FastAPI application and wires together all components.

**Key Responsibilities**:
- Creates the FastAPI app instance with title "Action Item Extractor"
- Initializes the database schema on startup via `init_db()`
- Registers API routers (notes and action_items)
- Serves the frontend HTML at the root endpoint (`/`)
- Mounts static files from the frontend directory

**Key Code Sections**:
```python
# Database initialization happens at module import time
init_db()

# FastAPI app creation
app = FastAPI(title="Action Item Extractor")

# Root endpoint serves HTML
@app.get("/", response_class=HTMLResponse)
def index() -> str:
    html_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    return html_path.read_text(encoding="utf-8")

# Router registration
app.include_router(notes.router)
app.include_router(action_items.router)
```

**Design Decisions**:
- Database initialization happens at import time, ensuring the schema exists before any requests
- HTML is served directly from the file system rather than using a template engine (simplicity)
- Static files are mounted separately for potential CSS/JS assets

---

### 2. Database Layer (`app/db.py`)

**Purpose**: Provides a clean abstraction over SQLite database operations.

**Key Responsibilities**:
- Manages database connection lifecycle
- Defines and initializes database schema
- Provides CRUD operations for notes and action items
- Handles data directory creation

**Database Schema**:

**Notes Table**:
- `id`: INTEGER PRIMARY KEY (auto-increment)
- `content`: TEXT (the note content)
- `created_at`: TEXT (timestamp, defaults to current datetime)

**Action Items Table**:
- `id`: INTEGER PRIMARY KEY (auto-increment)
- `note_id`: INTEGER (foreign key to notes.id, nullable)
- `text`: TEXT (the action item text)
- `done`: INTEGER (0 or 1, boolean flag)
- `created_at`: TEXT (timestamp, defaults to current datetime)

**Key Functions**:

1. **Connection Management**:
   ```python
   def get_connection() -> sqlite3.Connection:
       # Ensures data directory exists
       # Returns connection with row_factory set to sqlite3.Row
       # This allows dictionary-like access to rows
   ```

2. **Schema Initialization**:
   ```python
   def init_db() -> None:
       # Creates both tables if they don't exist
       # Uses IF NOT EXISTS to be idempotent
   ```

3. **Notes Operations**:
   - `insert_note(content: str) -> int`: Creates a new note, returns its ID
   - `list_notes() -> list[sqlite3.Row]`: Returns all notes, newest first
   - `get_note(note_id: int) -> Optional[sqlite3.Row]`: Retrieves a single note

4. **Action Items Operations**:
   - `insert_action_items(items: list[str], note_id: Optional[int]) -> list[int]`: Bulk inserts action items, returns their IDs
   - `list_action_items(note_id: Optional[int]) -> list[sqlite3.Row]`: Lists all action items, optionally filtered by note_id
   - `mark_action_item_done(action_item_id: int, done: bool) -> None`: Updates the done status

**Design Decisions**:
- Uses context managers (`with get_connection()`) for automatic connection cleanup
- `sqlite3.Row` factory enables dictionary-like access: `row["id"]` instead of `row[0]`
- Foreign key relationship allows action items to be optionally linked to notes
- All timestamps stored as TEXT (SQLite doesn't have native datetime type)
- Boolean values stored as INTEGER (0/1) for SQLite compatibility

---

### 3. Notes Router (`app/routers/notes.py`)

**Purpose**: Handles HTTP endpoints for note management.

**API Endpoints**:

1. **POST `/notes`** - Create a new note
   - Request body: `{"content": "note text"}`
   - Response: `{"id": 1, "content": "note text", "created_at": "..."}`
   - Validates that content is not empty (400 error if empty)

2. **GET `/notes/{note_id}`** - Retrieve a specific note
   - Path parameter: `note_id` (integer)
   - Response: `{"id": 1, "content": "...", "created_at": "..."}`
   - Returns 404 if note not found

**Design Decisions**:
- Uses FastAPI's automatic request/response serialization
- Validates input at the API boundary (empty content check)
- Returns appropriate HTTP status codes (400 for bad input, 404 for not found)
- Router is prefixed with `/notes` and tagged for API documentation

---

### 4. Action Items Router (`app/routers/action_items.py`)

**Purpose**: Handles HTTP endpoints for action item extraction and management.

**API Endpoints**:

1. **POST `/action-items/extract`** - Extract action items from text
   - Request body: `{"text": "...", "save_note": true/false}`
   - Response: `{"note_id": 1, "items": [{"id": 1, "text": "..."}, ...]}`
   - If `save_note` is true, creates a note first, then links action items to it
   - Uses the extraction service to parse action items from text

2. **GET `/action-items`** - List all action items
   - Query parameter (optional): `note_id` to filter by note
   - Response: `[{"id": 1, "note_id": 1, "text": "...", "done": false, "created_at": "..."}, ...]`
   - Returns all action items, newest first

3. **POST `/action-items/{action_item_id}/done`** - Mark action item as done/undone
   - Path parameter: `action_item_id` (integer)
   - Request body: `{"done": true/false}`
   - Response: `{"id": 1, "done": true}`

**Design Decisions**:
- Extraction endpoint combines note creation and action item extraction in one operation
- Supports optional note saving for workflow flexibility
- Done status can be toggled (not just set to done)
- Returns structured data with IDs for frontend state management

---

### 5. Extraction Service (`app/services/extract.py`)

**Purpose**: Contains the core business logic for identifying action items in text.

**Key Function**: `extract_action_items(text: str) -> List[str]`

**Extraction Strategy**:

The function uses a **multi-stage heuristic approach**:

1. **Pattern-Based Detection**:
   - Detects bullet points: `-`, `*`, `•`, or numbered lists (`1.`, `2.`, etc.)
   - Detects keyword prefixes: `todo:`, `action:`, `next:`
   - Detects checkbox markers: `[ ]` or `[todo]`

2. **Cleaning**:
   - Removes bullet prefixes and numbering
   - Strips checkbox markers
   - Trims whitespace

3. **Fallback Strategy**:
   - If no patterns match, splits text into sentences
   - Uses imperative verb detection (words like "add", "create", "implement", "fix", etc.)
   - Only extracts sentences that start with imperative verbs

4. **Deduplication**:
   - Removes duplicate action items (case-insensitive)
   - Preserves order of first occurrence

**Helper Functions**:
- `_is_action_line(line: str) -> bool`: Checks if a line matches action item patterns
- `_looks_imperative(sentence: str) -> bool`: Heuristically determines if a sentence is imperative

**Design Decisions**:
- Rule-based approach (no ML/AI) for deterministic extraction
- Multiple detection strategies for robustness
- Deduplication prevents redundant action items
- Case-insensitive matching for duplicates

**Note**: The code imports `ollama` and `dotenv` but doesn't use them in the current implementation. This suggests the codebase is prepared for LLM-based extraction (as mentioned in the assignment).

---

### 6. Frontend (`frontend/index.html`)

**Purpose**: Provides a simple, self-contained user interface.

**Structure**:
- Single HTML file with embedded CSS and JavaScript
- No build process or external dependencies
- Uses vanilla JavaScript (no frameworks)

**Features**:
1. **Text Input**: Large textarea for pasting notes
2. **Save Note Checkbox**: Option to save the input as a note
3. **Extract Button**: Triggers action item extraction
4. **Action Items Display**: Shows extracted items as checkboxes
5. **Interactive Checkboxes**: Clicking updates the done status via API

**JavaScript Flow**:
```javascript
1. User clicks "Extract" button
2. Sends POST to /action-items/extract with text and save_note flag
3. Receives list of action items with IDs
4. Renders checkboxes for each item
5. Each checkbox change event sends POST to /action-items/{id}/done
```

**Design Decisions**:
- Minimalist design (no external CSS framework)
- Self-contained for easy deployment
- Uses modern JavaScript (async/await, fetch API)
- Real-time updates when toggling checkboxes

---

### 7. Testing (`tests/test_extract.py`)

**Purpose**: Unit tests for the extraction service.

**Current Test Coverage**:
- `test_extract_bullets_and_checkboxes()`: Tests extraction of various bullet formats and checkboxes

**Test Structure**:
- Uses pytest framework
- Tests multiple input formats (bullets, checkboxes, numbered lists)
- Validates that expected items are extracted

---

## Data Flow Examples

### Example 1: Extracting Action Items from Text

```
1. User enters text in frontend textarea
2. Frontend sends POST /action-items/extract
   {
     "text": "- [ ] Set up database\n* implement API",
     "save_note": true
   }
3. Action Items Router receives request
4. Router calls db.insert_note() → creates note, returns note_id
5. Router calls extract.extract_action_items() → returns ["Set up database", "implement API"]
6. Router calls db.insert_action_items() → saves items with note_id
7. Router returns response with note_id and items
8. Frontend displays checkboxes for each item
```

### Example 2: Marking Action Item as Done

```
1. User clicks checkbox in frontend
2. Frontend sends POST /action-items/{id}/done
   {
     "done": true
   }
3. Action Items Router receives request
4. Router calls db.mark_action_item_done(id, done=True)
5. Database updates the done column
6. Router returns confirmation
7. Frontend checkbox state reflects the change
```

### Example 3: Retrieving a Note

```
1. Frontend or API client sends GET /notes/1
2. Notes Router receives request
3. Router calls db.get_note(1)
4. Database queries notes table
5. Returns note data or None
6. Router returns JSON or raises 404
```

---

## Design Patterns and Principles

### 1. **Layered Architecture**
- Clear separation: API → Business Logic → Data Access → Database
- Each layer has a single responsibility
- Dependencies flow downward (API depends on services, services depend on DB)

### 2. **Dependency Injection (Implicit)**
- Routers import and use database functions directly
- Services are imported and used by routers
- No explicit DI container, but structure supports it

### 3. **Repository Pattern (Simplified)**
- `db.py` acts as a repository, abstracting database operations
- Routers don't know about SQLite specifics
- Could be swapped for PostgreSQL, MySQL, etc. with minimal changes

### 4. **Single Responsibility Principle**
- Each module has one clear purpose
- Routers handle HTTP concerns
- Services handle business logic
- Database module handles persistence

### 5. **Fail-Fast Validation**
- Input validation happens at API boundaries
- Early error returns (400, 404) before database operations

---

## Technology Stack

- **Backend Framework**: FastAPI (Python web framework)
- **Database**: SQLite (file-based, no server required)
- **Language**: Python 3.x (uses type hints and `__future__` annotations)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Testing**: pytest
- **Package Management**: Poetry (inferred from assignment instructions)

---

## File Structure

```
week2/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── db.py                # Database operations
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── notes.py         # Notes API endpoints
│   │   └── action_items.py  # Action items API endpoints
│   └── services/
│       └── extract.py       # Action item extraction logic
├── frontend/
│   └── index.html           # Single-page frontend
├── tests/
│   ├── __init__.py
│   └── test_extract.py      # Unit tests
├── data/
│   └── app.db               # SQLite database file
├── assignment.md            # Assignment instructions
└── writeup.md               # Assignment writeup template
```

---

## API Contract Summary

### Notes Endpoints
- `POST /notes` - Create note
- `GET /notes/{note_id}` - Get note by ID

### Action Items Endpoints
- `POST /action-items/extract` - Extract action items from text
- `GET /action-items?note_id={id}` - List action items (optional filter)
- `POST /action-items/{id}/done` - Update done status

### Frontend Endpoints
- `GET /` - Serve HTML frontend
- `GET /static/*` - Serve static files

---

## Potential Improvements

1. **Error Handling**: More comprehensive error handling and logging
2. **Validation**: Use Pydantic models for request/response validation
3. **Authentication**: Add user authentication if multi-user support needed
4. **Pagination**: Add pagination for list endpoints
5. **LLM Integration**: Implement the LLM-based extraction mentioned in assignment
6. **Testing**: Expand test coverage (integration tests, API tests)
7. **Configuration**: Externalize configuration (database path, etc.)
8. **Migrations**: Use a migration tool for schema changes
9. **API Documentation**: FastAPI auto-generates docs at `/docs`, but could add more detail
10. **Frontend**: Consider a modern framework for better UX

---

## Conclusion

This codebase demonstrates a **clean, layered architecture** that separates concerns effectively. The FastAPI framework provides excellent type safety and automatic API documentation. The SQLite database is appropriate for a small-scale application, and the simple frontend keeps the stack minimal. The code is well-structured for extension, as evidenced by the assignment's requirement to add LLM-based extraction.

The architecture follows best practices for a small-to-medium web application, with clear boundaries between layers and a focus on maintainability and testability.

