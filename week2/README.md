# Action Item Extractor

A FastAPI application that extracts and manages action items from free-form meeting notes and text. The application supports both heuristic-based and LLM-powered extraction methods, with a clean REST API and web frontend for interaction.

## Overview

This application processes unstructured text (such as meeting notes) and extracts actionable items from them. It provides:

- **Heuristic Extraction**: Rule-based extraction using patterns like bullet points, keywords, and checkboxes
- **LLM-Powered Extraction**: Advanced extraction using Ollama and large language models for better understanding of context
- **Note Management**: Store and retrieve meeting notes with full CRUD operations
- **Action Item Tracking**: Create, list, and mark action items as complete
- **Web Interface**: User-friendly frontend for interacting with the application

The backend is built with FastAPI and SQLite, providing a lightweight yet powerful solution for action item management.

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)
- Conda (for environment management)
- Ollama (optional, required for LLM-based extraction)

### Installation Steps

1. **Activate your conda environment**:
   ```bash
   conda activate cs146s
   ```

2. **Install dependencies** (if using Poetry):
   ```bash
   poetry install
   ```

3. **Set up Ollama** (optional, for LLM extraction):
   - Install Ollama from https://ollama.com/download
   - Pull a model (e.g., `ollama pull llama3.2`)
   - Set environment variable or use default: `OLLAMA_MODEL=llama3.2`

4. **Configure environment variables** (optional):
   Create a `.env` file in the project root with:
   ```
   OLLAMA_MODEL=llama3.2
   OLLAMA_BASE_URL=http://localhost:11434
   DEBUG=false
   ```

## Running the Application

### Start the Server

From the project root directory, run:

```bash
poetry run uvicorn week2.app.main:app --reload
```

Or if not using Poetry:

```bash
uvicorn week2.app.main:app --reload
```

The server will start on `http://127.0.0.1:8000` (default port 8000).

### Access the Application

- **Web Interface**: Open your browser and navigate to `http://127.0.0.1:8000/`
- **API Documentation**: FastAPI automatically provides interactive docs at:
  - Swagger UI: `http://127.0.0.1:8000/docs`
  - ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

### Health Check

- **GET `/health`**
  - Returns the health status of the application
  - Response: `{"status": "healthy", "app": "Action Item Extractor", "version": "1.0.0"}`

### Notes Endpoints

- **POST `/notes`**
  - Creates a new note with the provided content
  - Request Body: `{"content": "Meeting notes here..."}`
  - Response: Note object with ID, content, and created_at timestamp

- **GET `/notes`**
  - Retrieves all notes, ordered by creation date (newest first)
  - Response: `{"notes": [...], "count": N}`

- **GET `/notes/{note_id}`**
  - Retrieves a specific note by its ID
  - Response: Note object with ID, content, and created_at timestamp

### Action Items Endpoints

- **POST `/action-items/extract`**
  - Extracts action items from text using either heuristic or LLM extraction
  - Request Body:
    ```json
    {
      "text": "Meeting notes with action items...",
      "save_note": false,
      "use_llm": false
    }
    ```
  - Query Parameters:
    - `text` (required): Text to extract action items from
    - `save_note` (optional, default: false): Whether to save the text as a note
    - `use_llm` (optional, default: false): Whether to use LLM extraction (true) or heuristic extraction (false)
  - Response: Extracted action items with metadata including extraction method used

- **POST `/action-items/extract-llm`**
  - Extracts action items from text using LLM-powered extraction only
  - Request Body: Same as `/action-items/extract`
  - Response: Extracted action items with `extraction_method: "llm"`

- **GET `/action-items`**
  - Lists all action items, optionally filtered by note_id
  - Query Parameters:
    - `note_id` (optional): Filter action items by note ID
  - Response: `{"items": [...], "count": N}`

- **POST `/action-items/{action_item_id}/done`**
  - Marks an action item as done or undone
  - Request Body: `{"done": true}` or `{"done": false}`
  - Response: Updated action item status

### Frontend

- **GET `/`**
  - Serves the web frontend HTML page

## Running the Test Suite

The project uses `pytest` for testing. Test files are located in the `tests/` directory.

### Run All Tests

```bash
pytest
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Specific Test Files

```bash
# Test heuristic extraction
pytest tests/test_extract.py

# Test LLM extraction
pytest tests/test_extract_llm.py
```

### Run Tests from Project Root

If running from the project root, you may need to specify the module path:

```bash
python -m pytest tests/
```

### Test Coverage

The test suite covers:
- Heuristic extraction with various input formats (bullet lists, keywords, checkboxes)
- LLM-powered extraction with different text inputs
- Edge cases (empty input, narrative text, etc.)

## Project Structure

```
week2/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and settings
│   ├── db.py                # Database layer and operations
│   ├── exceptions.py        # Custom exception classes
│   ├── schemas.py           # Pydantic models for API contracts
│   ├── routers/
│   │   ├── notes.py         # Notes API endpoints
│   │   └── action_items.py  # Action items API endpoints
│   └── services/
│       └── extract.py       # Extraction logic (heuristic & LLM)
├── tests/
│   ├── test_extract.py      # Tests for heuristic extraction
│   └── test_extract_llm.py  # Tests for LLM extraction
├── frontend/
│   └── index.html           # Web frontend
├── data/
│   └── app.db               # SQLite database (created automatically)
└── README.md                # This file
```

## Database

The application uses SQLite for data persistence. The database file is automatically created at `data/app.db` when the application starts. The database schema includes:

- **notes** table: Stores meeting notes with ID, content, and timestamps
- **action_items** table: Stores action items with ID, note_id (optional), text, done status, and timestamps

## Configuration

Configuration is managed through the `app/config.py` file using Pydantic Settings. Key settings include:

- `app_name`: Application name (default: "Action Item Extractor")
- `app_version`: Application version (default: "1.0.0")
- `debug`: Debug mode flag
- `database_path`: Path to SQLite database file
- `ollama_model`: Ollama model name (default: "llama3.2")
- `ollama_base_url`: Ollama API base URL (default: "http://localhost:11434")

Settings can be overridden via environment variables or a `.env` file.

## Error Handling

The application includes comprehensive error handling:

- **Validation Errors**: Returns 422 status with detailed validation messages
- **Database Errors**: Returns 500 status with error details
- **Not Found Errors**: Returns 404 status for missing resources
- **General Exceptions**: Returns 500 status with error information (detailed in debug mode)

All error responses follow a consistent format:
```json
{
  "error": "ErrorType",
  "detail": "Error message",
  "status_code": 400
}
```

## Development

### Code Structure

The codebase follows a clean architecture pattern:

- **Routers**: Handle HTTP requests and responses
- **Services**: Business logic (extraction algorithms)
- **Database Layer**: Data access and persistence
- **Schemas**: API contracts and data validation using Pydantic
- **Config**: Centralized configuration management

### Contributing

When making changes:

1. Follow the existing code style and patterns
2. Add appropriate error handling
3. Update tests for new functionality
4. Ensure all tests pass before committing

## License

This project is part of a course assignment.

